// Declarations only for host syntax checking. No CUDA implementation/linking.
#pragma once
typedef int cudaError_t;
constexpr int cudaSuccess=0;
struct cudaUUID_t { char bytes[16]; };
const char * cudaGetErrorString(cudaError_t);
cudaError_t cudaGetDeviceCount(int *);
cudaError_t cudaGetDevice(int *);
cudaError_t cudaDeviceGetUuid(cudaUUID_t *,int);
cudaError_t cudaDeviceGetPCIBusId(char *,int,int);
cudaError_t cudaRuntimeGetVersion(int *);
cudaError_t cudaDriverGetVersion(int *);
