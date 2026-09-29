// Reuse the qualified tiny token kernel/memory helpers, NOT the old runner/profile.
// Every measured submit/copy receives the actual PyTorch current native stream.
#include "gate8_qualification_token.cu"
EP_EXPORT int ep_submit_on(uintptr_t handle, int value) {
    if (!handle) return -2;
    void* args[]={&device_token,&value};
    return int(cudaLaunchKernel(reinterpret_cast<const void*>(g8q_token_kernel),
        dim3(1),dim3(1),args,0,reinterpret_cast<cudaStream_t>(handle)));
}
EP_EXPORT int ep_copy_on(uintptr_t handle) {
    if (!handle) return -2;
    return int(cudaMemcpyAsync(host_token,device_token,sizeof(int),cudaMemcpyDeviceToHost,
        reinterpret_cast<cudaStream_t>(handle)));
}
EP_EXPORT int ep_flags(uintptr_t handle, unsigned int* flags) {
    return int(cudaStreamGetFlags(reinterpret_cast<cudaStream_t>(handle),flags));
}
