// NULL-FIFO-D2H/0.1.0. Explicit controlled qualification, not a model.
// Build with --default-stream legacy; no stream/event creation in this DLL.
#include <cuda_runtime.h>
#include <nvtx3/nvToolsExt.h>
#include <cstring>
#include <cstdint>
#ifdef _WIN32
#define EP_EXPORT extern "C" __declspec(dllexport)
#else
#define EP_EXPORT extern "C"
#endif
static int* device_token=nullptr;
static int* host_token=nullptr;
static cudaStream_t stream=nullptr;
__global__ void g8q_token_kernel(int* output,int value) {
    if (blockIdx.x==0 && threadIdx.x==0) *output=value;
}
EP_EXPORT const char* ep_construction() { return "NULL-FIFO-D2H/0.1.0"; }
EP_EXPORT uintptr_t ep_stream_handle() { return reinterpret_cast<uintptr_t>(stream); }
EP_EXPORT int ep_current_device() {
    int value=-1; return cudaGetDevice(&value)==cudaSuccess ? value : -1;
}
EP_EXPORT int ep_init(int device) {
    if (device_token || host_token) return -1;
    cudaError_t e=cudaSetDevice(device);
    if(e!=cudaSuccess) return int(e);
    e=cudaMalloc(&device_token,sizeof(int));
    if(e!=cudaSuccess) return int(e);
    return int(cudaMallocHost(&host_token,sizeof(int)));
}
EP_EXPORT int ep_identity(unsigned char* uuid,char* pci,int capacity) {
    cudaDeviceProp properties{};
    cudaError_t e=cudaGetDeviceProperties(&properties,0);
    if(e!=cudaSuccess) return int(e);
    std::memcpy(uuid,properties.uuid.bytes,16);
    return int(cudaDeviceGetPCIBusId(pci,capacity,0));
}
EP_EXPORT int ep_prepare() { return int(cudaDeviceSynchronize()); }
EP_EXPORT int ep_submit(int value) {
    void* args[]={&device_token,&value};
    return int(cudaLaunchKernel(reinterpret_cast<const void*>(g8q_token_kernel),dim3(1),dim3(1),args,0,stream));
}
EP_EXPORT int ep_copy() { return int(cudaMemcpyAsync(host_token,device_token,sizeof(int),cudaMemcpyDeviceToHost,stream)); }
EP_EXPORT int ep_wait() { return int(cudaStreamSynchronize(stream)); }
EP_EXPORT int ep_read() { return *host_token; }
EP_EXPORT void ep_mark(const char* text) { nvtxMarkA(text); }
EP_EXPORT void ep_push(const char* text) { nvtxRangePushA(text); }
EP_EXPORT void ep_pop() { nvtxRangePop(); }
EP_EXPORT int ep_close() {
    cudaError_t result=cudaDeviceSynchronize();
    if(host_token) { cudaError_t e=cudaFreeHost(host_token); if(result==cudaSuccess) result=e; host_token=nullptr; }
    if(device_token) { cudaError_t e=cudaFree(device_token); if(result==cudaSuccess) result=e; device_token=nullptr; }
    return int(result);
}
