"""Real pinned CMake metadata generation; no compiler or generated exe runs."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

import pytest


def fixed_cmake():
    p=Path(os.environ.get('EXPOSEDPATH_TEST_CMAKE','.local/vendor/cmake-stage1/cmake/data/bin/cmake.exe')).resolve()
    if not p.is_file():
        if 'EXPOSEDPATH_TEST_CMAKE' in os.environ:pytest.fail('Required bound CMake missing')
        pytest.skip('optional fixed local CMake audit asset absent; no download')
    return p


def fixed_ninja():
    p=Path(os.environ.get('EXPOSEDPATH_TEST_NINJA','.local/vendor/ninja-1.12.1-win/extract/ninja.exe')).resolve()
    if not p.is_file():
        if 'EXPOSEDPATH_TEST_NINJA' in os.environ:pytest.fail('Required bound Ninja missing')
        pytest.skip('optional fixed local Ninja audit asset absent; no download')
    return p


def generate_metadata(parent,tools,kind='cxx',version='19.38.33135.0'):
    from exposedpath import native_ninja as n,native_stage1 as s
    source=Path(tempfile.mkdtemp(prefix='t('+kind+') ',dir=parent))
    build=Path(parent)/kind
    # Only the generator is executed. Other "tools" are CPU byte fixtures;
    # LANGUAGES NONE never invokes cl/nvcc/link/rc or any generated program.
    for name,p in tools.items():
        p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
        if not p.exists():
            if name=='ninja':shutil.copyfile(fixed_ninja(),p)
            else:p.write_bytes(('CPU non-executable tool fixture '+name).encode())
    languages=('C','CXX') if kind=='cxx' else ('CXX','CUDA')
    lines=['cmake_minimum_required(VERSION 3.31)','project(metadata_roundtrip LANGUAGES NONE)']
    for lang in (*languages,'RC'):
        lines+=['configure_file("${CMAKE_ROOT}/Modules/CMake'+lang+'Compiler.cmake.in" "${CMAKE_BINARY_DIR}/CMakeFiles/3.31.10/CMake'+lang+'Compiler.cmake" @ONLY)',
            'include("${CMAKE_BINARY_DIR}/CMakeFiles/3.31.10/CMake'+lang+'Compiler.cmake")']
    (source/'CMakeLists.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    args=n.configure_arguments(source,build,tools)
    for lang in languages:args+=['-DCMAKE_'+lang+'_COMPILER_VERSION:STRING='+('12.4.131' if lang=='CUDA' else version)]
    result=subprocess.run([str(fixed_cmake()),*args],capture_output=True,timeout=60)
    assert result.returncode==0,result.stdout.decode('utf-8')+result.stderr.decode('utf-8')
    return build


def generated_build(parent,tools,kind='cxx',damage=None):
    assert damage is None
    build=generate_metadata(parent,tools,kind)
    exe=build/('native-toolchain-check.exe' if kind=='cxx' else 'native-cuda-link-check.exe')
    # External compile/link is the existing stage1 CPU substitute. Success
    # receipts are written by production consumers, never by this fixture.
    exe.write_bytes(b'CPU substitute link output; not an actual executable')
    return build,exe
