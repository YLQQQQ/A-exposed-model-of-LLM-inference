// Reuse the immutable NULL-FIFO-D2H kernel/copy/read program. Not a collector.
#include "gate8_qualification_token.cu"
static_assert(CUDART_VERSION == 12040, "Fixed CUDA 12.4 runtime headers required");
static_assert(sizeof(int) == 4, "Four-byte controlled token required");
EP_EXPORT int ep_coe_abi() { return 1; }
EP_EXPORT int ep_memset(size_t count, int value) {
    if (!device_token || (count != 0 && count != sizeof(int))) return -3;
    return int(cudaMemsetAsync(device_token, value, count, stream));
}
