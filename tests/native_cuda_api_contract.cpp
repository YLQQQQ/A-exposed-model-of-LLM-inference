// Compile-only CUDA12.4 contract for every Runtime API called by the adapter.
// No function invocation, linking, initialization or device access.
#include <cuda_runtime.h>
#include <type_traits>
static_assert(CUDART_VERSION == 12040, "fixed CUDA12.4 headers required");
using IntQuery = cudaError_t (CUDARTAPI *)(int *);
static_assert(std::is_same<decltype(&cudaGetDeviceCount), IntQuery>::value);
static_assert(std::is_same<decltype(&cudaGetDevice), IntQuery>::value);
static_assert(std::is_same<decltype(&cudaRuntimeGetVersion), IntQuery>::value);
static_assert(std::is_same<decltype(&cudaDriverGetVersion), IntQuery>::value);
using Properties = cudaError_t (CUDARTAPI *)(cudaDeviceProp *, int);
static_assert(std::is_same<decltype(&cudaGetDeviceProperties), Properties>::value);
static_assert(std::is_same<decltype(cudaDeviceProp::uuid), cudaUUID_t>::value);
static_assert(sizeof(cudaUUID_t) == 16);
using PciQuery = cudaError_t (CUDARTAPI *)(char *, int, int);
static_assert(std::is_same<decltype(&cudaDeviceGetPCIBusId), PciQuery>::value);
using ErrorText = const char * (CUDARTAPI *)(cudaError_t);
static_assert(std::is_same<decltype(&cudaGetErrorString), ErrorText>::value);
using StreamSync = cudaError_t (CUDARTAPI *)(cudaStream_t);
static_assert(std::is_same<decltype(&cudaStreamSynchronize), StreamSync>::value);
