"""Compile the new client and Host harness only. Never open a CUPTI session."""
from pathlib import Path
import importlib.util

_path=Path(__file__).resolve().with_name('memset_micro.py')
_spec=importlib.util.spec_from_file_location('_exposedpath_cupti_build_support',_path)
tools=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(tools)


def build(config,output):
    out=Path(output);out.mkdir(parents=True,exist_ok=True)
    src=Path(__file__).resolve().parent/'native_cupti_timeline'
    vc=Path(config['vc_root']);compiler=vc/'bin/Hostx64/x64/cl.exe';dumpbin=vc/'bin/Hostx64/x64/dumpbin.exe'
    includes=[str(Path(config[k])) for k in ('cuda_include','crt_include','cupti_include')]
    env=tools.compile_environment(config);built={};imports={}
    for stem,dll in [('client',True),('host_test',False)]:
        target=out/(stem+('.dll' if dll else '.exe'))
        argv=[str(compiler),'/nologo','/std:c++17','/EHsc','/MT','/Od','/W4','/WX','/utf-8',
            '/DWIN32_LEAN_AND_MEAN','/DNOMINMAX',*['/I'+i for i in includes]]
        if dll:argv.append('/LD')
        argv += [str(src/(stem+'.cpp')),'/Fo:'+str(out/(stem+'.obj')),'/Fe:'+str(target),'/link']
        tools.command(argv,out,out/('build_'+stem),env=env)
        imports[stem]=tools.pe_imports(target,str(dumpbin),env,out)
        built[stem]=str(target)
    built.update(schema_version='cupti-timeline-build/0.1.0',imports=imports,vendor_gpu_executed=False,
        binaries=[dict(path=Path(built[k]).name,bytes=Path(built[k]).stat().st_size,sha256=tools.sha(built[k])) for k in ('client','host_test')])
    tools.write(out/'build.json',built)
    return built
