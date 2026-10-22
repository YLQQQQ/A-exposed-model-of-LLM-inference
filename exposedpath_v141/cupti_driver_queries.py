"""Narrow API22 support, independent of frozen A/synchronization registries.

These exact SDK identities describe queries, not a CPU-only/nonblocking
promise. Matching names, lack of activity, or a Get prefix are not evidence.
"""
VERSION='cupti-api22-driver-queries/0.1.0'
CUDA_DOCUMENTATION='12.4.1'
CBID_HEADER_SHA256='7cf5ee908f7254a188a8a6df3886b1d4bde84061b5cd57c0fcb0b7a6d40dd4f3'
BASE='https://docs.nvidia.com/cuda/archive/12.4.1/cuda-driver-api/'
RUNTIME_VERSION='cupti-api22-runtime-queries/0.1.0'
RUNTIME_BASE='https://docs.nvidia.com/cuda/archive/12.4.1/cuda-runtime-api/'
RUNTIME_RULES={
    'cudaGetDevice':(17,'group__CUDART__DEVICE.html','Returns the current device for the calling host thread.'),
    'cudaGetLastError':(10,'group__CUDART__ERROR.html','Returns and resets the calling host thread error state.'),
    'cudaDeviceGetAttribute':(200,'group__CUDART__DEVICE.html','Returns a device attribute.'),
    'cudaOccupancyMaxActiveBlocksPerMultiprocessor':(210,'group__CUDART__OCCUPANCY.html','Calculates maximum active blocks per multiprocessor.'),
}
RULES={
    'cuDevicePrimaryCtxGetState':(392,'group__CUDA__PRIMARY__CTX.html','Returns primary context flags and active state.'),
    'cuCtxGetCurrent':(304,'group__CUDA__CTX.html','Returns the context bound to the calling CPU thread.'),
    'cuKernelGetFunction':(683,'group__CUDA__LIBRARY.html','Returns the function handle for a kernel and current context.'),
    'cuFuncGetAttribute':(85,'group__CUDA__EXEC.html','Returns the requested function attribute.'),
    'cuOccupancyMaxActiveBlocksPerMultiprocessorWithFlags':(451,'group__CUDA__OCCUPANCY.html','Calculates maximum active blocks per multiprocessor.'),
}
# The already-supported callback bridges are not new independent query rules.
# These three may only occur under their explicit runtime query ancestor.
NESTED_HELPERS={
    ('cuCtxGetDevice',16):'cudaGetDevice',
    ('cuDeviceGetAttribute',9):'cudaDeviceGetAttribute',
    ('cuStreamIsCapturing',499):'cudaStreamIsCapturing',
}
DRIVER_OPERATIONS={('cuLaunchKernel',307),('cuMemsetD8Async',216),
    ('cuMemcpyDtoHAsync_v2',279),('cuStreamSynchronize',126)}


def query_rule(api,callback):
    name=callback['name']
    if name not in RULES:return None
    cbid,page,basis=RULES[name]
    if not (callback['domain']=='DRIVER' and type(callback.get('cbid')) is int and callback['cbid']==cbid):
        raise ValueError('SUBMIT_EFFECT_DRIVER_QUERY_IDENTITY')
    if api is None:
        if callback.get('parent_id') is None:raise ValueError('SUBMIT_EFFECT_DRIVER_API_COVERAGE')
    elif not (api['domain']=='DRIVER' and api['name']==name and
        type(api.get('cbid')) is int and api['cbid']==cbid and
        all(api[k]==callback[k] for k in ('pid','tid','correlation','return_code'))):
        raise ValueError('SUBMIT_EFFECT_DRIVER_QUERY_IDENTITY')
    return dict(policy_version=VERSION,name=name,domain='DRIVER',cbid=cbid,category='non_submit',
        scope='NO_DEVICE_WORK_SUBMISSION_OR_COMPLETION_GUARANTEE',pure_cpu_cost=False,
        source=BASE+page,basis=basis,cuda_documentation_version=CUDA_DOCUMENTATION)


def runtime_query_rule(api,callback):
    name=callback['name']
    if name not in RUNTIME_RULES:return None
    cbid,page,basis=RUNTIME_RULES[name]
    if not (api is not None and api['domain']==callback['domain']=='RUNTIME' and api['name']==name and
        type(api.get('cbid')) is int and api['cbid']==callback.get('cbid')==cbid and
        all(api[k]==callback[k] for k in ('pid','tid','correlation','return_code'))):
        raise ValueError('SUBMIT_EFFECT_RUNTIME_QUERY_IDENTITY')
    return dict(policy_version=RUNTIME_VERSION,name=name,domain='RUNTIME',cbid=cbid,category='non_submit',
        scope='NO_DEVICE_WORK_SUBMISSION_OR_COMPLETION_GUARANTEE',pure_cpu_cost=False,
        source=RUNTIME_BASE+page,basis=basis,cuda_documentation_version=CUDA_DOCUMENTATION)
