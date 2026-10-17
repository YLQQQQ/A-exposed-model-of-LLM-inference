"""Reuse pinned vendor/SDK build. Execute only the Host target in CPU tests."""
from pathlib import Path
from . import memset_micro as base


def build(config,output):
    out=Path(output);old=base.build_native(config,out/'shared')
    vc=Path(config['vc_root']);cl=vc/'bin/Hostx64/x64/cl.exe'
    includes=[config['cuda_include'],config['crt_include'],str(Path(config['detours'])/'src'),config['nvtx_include']]
    flags=[str(cl),'/nologo','/EHsc','/std:c++17','/MT','/Od','/W4','/WX','/utf-8',*['/I'+p for p in includes]]
    outputs={}
    for name,src,dll,cpu in [('recorder','prefill_recorder.cpp',True,False),
        ('host_recorder','prefill_recorder.cpp',True,True),('host_test','prefill_host_test.cpp',False,True)]:
        target=out/(('prefill_host_recorder' if name=='host_recorder' else name)+('.dll' if dll else '.exe'))
        base.command([*flags,*(['/DEP_CPU_TEST'] if cpu else []),*(['/LD'] if dll else []),
            str(base.ROOT/'scripts/native_memset_probe'/src),'/Fo:'+str(out/(name+'.obj')),
            '/Fe:'+str(target),'/link',str(out/'shared/detours.lib')],out,out/('build_'+name),env=base.compile_environment(config))
        base.pe_imports(target,str(vc/'bin/Hostx64/x64/dumpbin.exe'),base.compile_environment(config),out)
        outputs[name]=str(target)
    import shutil
    shutil.copyfile(old['host_target'],out/'host_target.dll')
    outputs['binary_files']=[dict(path=p.name,bytes=p.stat().st_size,sha256=base.sha(p)) for p in out.iterdir() if p.suffix in ('.dll','.exe')]
    outputs['cuda_programs_executed']=0
    base.write(out/'build.json',outputs)
    return outputs
