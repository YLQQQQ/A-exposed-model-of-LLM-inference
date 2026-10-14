"""Exact native build representation contract, not measurement semantics."""
CHECK_LEGACY='exposedpath-native-compile-link/0.1.0'
CHECK_VERSION='exposedpath-native-compile-link/0.2.0'
MSVC_RAW_VERSIONS=('19.38.33135','19.38.33135.0')
CUDA_RAW_VERSION='12.4.131'


def valid_compiler_versions(value,kind,*,legacy=False):
    keys={'C','CXX'} if kind=='cxx' else {'CXX','CUDA'} if kind=='cuda' else set()
    if not keys or not isinstance(value,dict) or set(value)!=keys:return False
    allowed=MSVC_RAW_VERSIONS[:1] if legacy else MSVC_RAW_VERSIONS
    return all(v==CUDA_RAW_VERSION if k=='CUDA' else v in allowed for k,v in value.items())


def cmake_path(value):
    # Representation only: neither resolve/rebase nor rewrite source bytes.
    text=str(value)
    if not text or any(x in text for x in ('\x00','\n','\r',';','$','"')):
        raise ValueError('NATIVE_CMAKE_PATH_UNREPRESENTABLE')
    return text.replace('\\','/')


def cmake_path_argument(key,value,kind='FILEPATH'):
    if kind not in ('PATH','FILEPATH'):raise ValueError('NATIVE_CMAKE_PATH_TYPE')
    return '-D'+key+':'+kind+'='+cmake_path(value)
