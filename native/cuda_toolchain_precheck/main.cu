#include <cuda_runtime.h>
__global__ void native_link_kernel(int *value) { *value += 1; }
// This program is compiled/linked ONLY. No command executes it.
int main() {
    int count = 0;
    return cudaGetDeviceCount(&count) == cudaSuccess ? 0 : 1;
}
