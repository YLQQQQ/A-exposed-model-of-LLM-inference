// Independent CPU DLL, real SDK signature, no CUDA libraries or API execution.
#include "recorder.h"
struct HostFacts { std::uint64_t count; std::uintptr_t ptr,stream; int value,calls; DWORD entry_error; };
static HostFacts facts{};
static int result=0;
static MemsetFn recursive=nullptr;
extern "C" __declspec(dllexport) void EpHostResult(int rc) { result=rc; }
extern "C" __declspec(dllexport) void EpHostReenter(MemsetFn fn) { recursive=fn; }
extern "C" __declspec(dllexport) HostFacts* EpHostFacts() { return &facts; }
extern "C" __declspec(dllexport) __declspec(noinline) cudaError_t CUDARTAPI
EpHostMemset(void* ptr, int value, size_t count, cudaStream_t stream) {
    facts.entry_error=GetLastError(); facts.ptr=reinterpret_cast<std::uintptr_t>(ptr);
    facts.value=value; facts.count=static_cast<std::uint64_t>(count);
    facts.stream=reinterpret_cast<std::uintptr_t>(stream); ++facts.calls;
    if(recursive) { auto next=recursive; recursive=nullptr; next(ptr,value,count,stream); }
    SetLastError(31337); return static_cast<cudaError_t>(result);
}
