"""Compile/link the tiny construction, never execute it or rebuild the collector."""
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def build(config,output):
    spec=importlib.util.spec_from_file_location('_coe_build_support',ROOT/'scripts/memset_micro.py')
    tools=importlib.util.module_from_spec(spec);spec.loader.exec_module(tools)
    out=Path(output).resolve();tools.require(not out.exists(),'NEW_OUTPUT');out.mkdir(parents=True)
    nvcc=Path(config['nvcc']).resolve();vc=Path(config['vc_root'])
    cl=vc/'bin/Hostx64/x64/cl.exe';dumpbin=vc/'bin/Hostx64/x64/dumpbin.exe'
    includes=[Path(config[k]).resolve() for k in ('cuda_include','crt_include','nvtx_include')]
    env=tools.compile_environment(config)
    tools.command([str(nvcc),'--version'],out,out/'nvcc_version',env=env)
    version=(out/'nvcc_version.stdout').read_text(encoding='utf8')
    tools.require('V12.4.131' in version,'FIXED_NVCC')
    source=ROOT/'scripts/coe_cupti_controlled.cu';target=out/'coe_controlled.dll'
    argv=[str(nvcc),'--shared','--cudart','shared','--default-stream','legacy','-std=c++17',
        '-gencode','arch=compute_89,code=sm_89','-ccbin',str(cl),
        *[x for inc in includes for x in ('-I',str(inc))],'-L',str(Path(config['runtime_lib']).resolve()),
        '-Xcompiler','/MT,/utf-8','-o',str(target),str(source)]
    if config.get('local_unsupported_host_compiler') is True:argv.insert(1,'--allow-unsupported-compiler')
    tools.command(argv,out,out/'compile',env=env,timeout=120)
    tools.require(target.is_file() and target.stat().st_size>0,'DLL_MISSING')
    tools.command([str(dumpbin),'/exports',str(target)],out,out/'exports',env=env)
    exports=(out/'exports.stdout').read_text(encoding='utf8')
    names=['ep_coe_abi','ep_memset','ep_init','ep_identity','ep_stream_handle','ep_prepare','ep_submit',
        'ep_copy','ep_wait','ep_read','ep_close']
    tools.require(all(n in exports for n in names),'ABI_EXPORTS')
    tools.command([str(dumpbin),'/imports',str(target)],out,out/'imports',env=env)
    imports=(out/'imports.stdout').read_text(encoding='utf8')
    tools.require('cudart64_12.dll' in imports.lower() and 'cupti64' not in imports.lower(),'SHARED_RUNTIME')
    headers=[includes[0]/'cuda_runtime.h',includes[0]/'cuda_runtime_api.h',includes[1]/'crt/host_defines.h']
    r=dict(schema_version='coe-controlled-build/0.1.0',program=dict(path=str(target),bytes=target.stat().st_size,
        sha256=tools.sha(target)),source_sha256={str(p.relative_to(ROOT)):tools.sha(p) for p in
        (source,ROOT/'scripts/gate8_qualification_token.cu')},
        headers={str(p):tools.sha(p) for p in headers},tools={str(p):tools.sha(p) for p in (nvcc,cl,dumpbin)},
        local_unsupported_host_compiler=config.get('local_unsupported_host_compiler',False),
        collector_rebuilt=False,program_executed=False,CUDA_initialized=False,exports_checked=names,
        target_qualification='NOT_GRANTED',explicit_arch='sm_89',runtime_link='SHARED')
    tools.write(out/'build.json',r);return r
