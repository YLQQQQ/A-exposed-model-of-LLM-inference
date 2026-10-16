// No CUDA imports, queries, synchronization, allocation, copies or file I/O.
// The only device-runtime call is exactly one unmodified trampoline forward.
#include "recorder.h"
#include <detours.h>
#include <cstdlib>
#include <nvtx3/nvToolsExt.h>
#include <cstring>
#include <cstdio>

static_assert(DETOURS_VERSION == 0x4c0c1, "Reviewed Detours4.0.1 only");
static MemsetFn original = nullptr;
static CallRecord records[4]{};
static LONG used = 0, fault = 0, active = 0;
static std::uint64_t armed = 0;
static thread_local bool inside = false;
static char messages[2][96]{};
static nvtxDomainHandle_t domain = nullptr;

static int push(const char* message) {
#ifdef EP_CPU_TEST
    (void)message; SetLastError(9999); return 0; // explicit NVTX CPU boundary double
#else
    nvtxEventAttributes_t a{};
    a.version = NVTX_VERSION; a.size = NVTX_EVENT_ATTRIB_STRUCT_SIZE;
    a.messageType = NVTX_MESSAGE_TYPE_ASCII; a.message.ascii = message;
    return nvtxDomainRangePushEx(domain, &a);
#endif
}
static int pop() {
#ifdef EP_CPU_TEST
    SetLastError(8888); return 0;
#else
    return nvtxDomainRangePop(domain);
#endif
}

static cudaError_t CUDARTAPI intercept(void* ptr, int value, size_t count, cudaStream_t stream) {
    const DWORD prior = GetLastError();
    if (inside) {
        InterlockedExchange(&fault, 3);
        SetLastError(prior);
        return original(ptr, value, count, stream);
    }
    inside = true;
    const LONG slot = InterlockedIncrement(&used) - 1;
    const std::uint64_t id = armed; armed = 0;
    if (slot < 0 || slot >= 4 || id < 1 || id > 2) {
        InterlockedExchange(&fault, 4);
        SetLastError(prior);
        const cudaError_t rc = original(ptr, value, count, stream);
        const DWORD after = GetLastError(); inside = false; SetLastError(after); return rc;
    }
    auto& r = records[slot];
    r.call_id = id; r.count = static_cast<std::uint64_t>(count);
    r.pointer_alias = ptr ? 1 : 0; r.stream = reinterpret_cast<std::uintptr_t>(stream);
    r.pid = GetCurrentProcessId(); r.tid = GetCurrentThreadId(); r.entry_error = prior;
    r.value = value; r.push_level = push(messages[id-1]);
    SetLastError(prior);
    r.forwards = 1;
    const cudaError_t rc = original(ptr, value, count, stream);
    const DWORD after = GetLastError();
    r.return_error = after; r.return_code = static_cast<int>(rc); r.completed = 1;
    r.pop_level = pop(); inside = false; SetLastError(after); return rc;
}

extern "C" __declspec(dllexport) LONG ep_start(HMODULE runtime, const char* run) {
    if (active || !runtime || !run || std::strlen(run)!=32) return ERROR_INVALID_PARAMETER;
    for (const char* p=run; *p; ++p) if (!(*p>='0' && *p<='9') && !(*p>='a' && *p<='f')) return ERROR_INVALID_PARAMETER;
#ifdef EP_CPU_TEST
    const char* symbol = "EpHostMemset";
#else
    const char* symbol = "cudaMemsetAsync";
#endif
    auto address = GetProcAddress(runtime, symbol);
    HMODULE owner = nullptr;
    if (!address || !GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS |
        GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT, reinterpret_cast<LPCWSTR>(address), &owner)
        || owner!=runtime) return ERROR_INVALID_ADDRESS; // no forwarded/private copy fallback
    original = reinterpret_cast<MemsetFn>(address);
    for (unsigned i=0; i<2; ++i) std::snprintf(messages[i], sizeof(messages[i]), "EP_MEMSET:%s:%u", run, i+1);
#ifndef EP_CPU_TEST
    domain = nvtxDomainCreateA("EP_MEMSET_MICRO");
#endif
    LONG rc = DetourTransactionBegin(); if (rc) return rc;
    rc = DetourUpdateThread(GetCurrentThread());
    if (!rc) rc = DetourAttach(reinterpret_cast<PVOID*>(&original), reinterpret_cast<PVOID>(intercept));
    if (rc) { DetourTransactionAbort(); return rc; }
    rc = DetourTransactionCommit(); if (!rc) active=1; return rc;
}
extern "C" __declspec(dllexport) LONG ep_arm(std::uint64_t id) {
    if (!active || inside || armed || id<1 || id>2) return ERROR_INVALID_PARAMETER;
    armed=id; return 0;
}
extern "C" __declspec(dllexport) LONG ep_stop() {
    if (!active || inside || armed) return ERROR_INVALID_STATE;
    LONG rc=DetourTransactionBegin(); if (rc) return rc;
    rc=DetourUpdateThread(GetCurrentThread());
    if (!rc) rc=DetourDetach(reinterpret_cast<PVOID*>(&original), reinterpret_cast<PVOID>(intercept));
    if (rc) { DetourTransactionAbort(); return rc; }
    rc=DetourTransactionCommit(); if (!rc) active=0; return rc;
}
extern "C" __declspec(dllexport) const CallRecord* ep_records(unsigned* n, LONG* error) {
    *n=static_cast<unsigned>(used<0 ? 0 : used>4 ? 4 : used); *error=fault; return records;
}
