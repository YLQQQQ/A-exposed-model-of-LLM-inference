// Minimal syntax subset of CUDA12.4. Not ABI/layout or runtime evidence.
// Real SDK headers must win include resolution in SDK compilation tests.
#pragma once
typedef int cudaError_t;
constexpr int cudaSuccess=0;
struct cudaUUID_t { char bytes[16]; };
struct cudaDeviceProp { cudaUUID_t uuid; }; // deliberately incomplete layout
const char * cudaGetErrorString(cudaError_t);
cudaError_t cudaGetDeviceCount(int *);
cudaError_t cudaGetDevice(int *);
cudaError_t cudaGetDeviceProperties(cudaDeviceProp *,int);
cudaError_t cudaDeviceGetPCIBusId(char *,int,int);
cudaError_t cudaRuntimeGetVersion(int *);
cudaError_t cudaDriverGetVersion(int *);
