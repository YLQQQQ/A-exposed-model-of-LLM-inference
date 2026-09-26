// Engineering construction CONTROLLED-D2H-REQUEST/0.1.0; not historical Q0.
// Only the explicit Python execution entry loads this library.
#include <cuda_runtime.h>
#include <nvtx3/nvToolsExt.h>
#include <cstring>

#ifdef _WIN32
#define EP_EXPORT extern "C" __declspec(dllexport)
#else
#define EP_EXPORT extern "C"
#endif

static cudaStream_t stream = nullptr;
static cudaStream_t streams[3] = {nullptr, nullptr, nullptr};
static int request_index = 0;
static int* device_token = nullptr;
static int* host_token = nullptr;

__global__ void g8_token_kernel(int* output, int value) {
    if (blockIdx.x == 0 && threadIdx.x == 0) *output = value;
}

EP_EXPORT int ep_init(int logical_device) {
    if (stream || device_token || host_token) return -1;
    cudaError_t e = cudaSetDevice(logical_device);
    if (e != cudaSuccess) return int(e);
    for (int i=0; i<3; ++i) {
        e = cudaStreamCreateWithFlags(&streams[i], cudaStreamNonBlocking);
        if (e != cudaSuccess) return int(e);
    }
    stream = streams[0]; // Warmup only; each request has its own explicit stream.
    request_index = 0;
    e = cudaMalloc(&device_token, sizeof(int));
    if (e != cudaSuccess) return int(e);
    return int(cudaMallocHost(&host_token, sizeof(int)));
}
EP_EXPORT int ep_identity(unsigned char* uuid, char* pci, int capacity) {
    cudaDeviceProp properties{};
    cudaError_t e = cudaGetDeviceProperties(&properties, 0);
    if (e != cudaSuccess) return int(e);
    std::memcpy(uuid, properties.uuid.bytes, 16);
    return int(cudaDeviceGetPCIBusId(pci, capacity, 0));
}
EP_EXPORT int ep_prepare() {
    cudaError_t e = cudaDeviceSynchronize();
    if (e != cudaSuccess) return int(e);
    if (request_index >= 2) return -2;
    stream = streams[++request_index];
    return 0;
}
EP_EXPORT int ep_submit(int value) {
    g8_token_kernel<<<1, 1, 0, stream>>>(device_token, value);
    return int(cudaGetLastError());
}
EP_EXPORT int ep_copy() {
    return int(cudaMemcpyAsync(host_token, device_token, sizeof(int), cudaMemcpyDeviceToHost, stream));
}
EP_EXPORT int ep_wait() { return int(cudaStreamSynchronize(stream)); }
EP_EXPORT int ep_read() { return *host_token; }
EP_EXPORT void ep_mark(const char* label) { nvtxMarkA(label); }
EP_EXPORT void ep_push(const char* label) { nvtxRangePushA(label); }
EP_EXPORT void ep_pop() { nvtxRangePop(); }
EP_EXPORT int ep_close() {
    cudaError_t result = cudaDeviceSynchronize();
    if (host_token) { cudaError_t e=cudaFreeHost(host_token); if (result==cudaSuccess) result=e; host_token=nullptr; }
    if (device_token) { cudaError_t e=cudaFree(device_token); if (result==cudaSuccess) result=e; device_token=nullptr; }
    for (int i=0; i<3; ++i) {
        if (streams[i]) { cudaError_t e=cudaStreamDestroy(streams[i]); if (result==cudaSuccess) result=e; streams[i]=nullptr; }
    }
    stream=nullptr; request_index=0;
    return int(result);
}
