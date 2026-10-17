// Ordinary shared-runtime export only. No CUDA query/copy/sync or hook-time I/O.
#include "recorder.h"
#include <detours.h>
#include <tlhelp32.h>
#include <cstdlib>
#include <nvtx3/nvToolsExt.h>
#include <cstring>
#include <cstdio>
#include <vector>

static_assert(DETOURS_VERSION==0x4c0c1,"Fixed Detours4.0.1");
static constexpr unsigned capacity=4096;
static CallRecord records[capacity]{};
static char messages[capacity][96]{};
static void* pointers[capacity]{};
static unsigned aliases=0;
static LONG used=0,fault=0,enabled=0,attached=0,inflight=0,begun=0;
static DWORD primary=0;
static MemsetFn original=nullptr;
static thread_local bool inside=false;
static nvtxDomainHandle_t domain=nullptr;

static cudaError_t CUDARTAPI intercept(void* ptr,int value,size_t count,cudaStream_t stream) {
    const DWORD prior=GetLastError();
    if (!InterlockedCompareExchange(&enabled,0,0)) {SetLastError(prior);return original(ptr,value,count,stream);}
    if (inside || GetCurrentThreadId()!=primary) {
        InterlockedExchange(&fault,inside?3:5);SetLastError(prior);return original(ptr,value,count,stream);
    }
    inside=true;InterlockedIncrement(&inflight);
    const LONG slot=InterlockedIncrement(&used)-1;
    if (slot<0 || slot>=static_cast<LONG>(capacity)) {
        InterlockedExchange(&fault,4);SetLastError(prior);
        const auto rc=original(ptr,value,count,stream);const DWORD after=GetLastError();
        InterlockedDecrement(&inflight);inside=false;SetLastError(after);return rc;
    }
    unsigned alias=0;
    if(ptr) {
        while(alias<aliases && pointers[alias]!=ptr) ++alias;
        if(alias==aliases) pointers[aliases++]=ptr;
        ++alias;
    }
    auto& r=records[slot];r.call_id=static_cast<std::uint64_t>(slot)+1;
    r.count=static_cast<std::uint64_t>(count);r.value=value;r.pointer_alias=alias;
    r.stream=reinterpret_cast<std::uintptr_t>(stream);r.pid=GetCurrentProcessId();r.tid=primary;r.entry_error=prior;
#ifdef EP_CPU_TEST
    r.push_level=-1;
#else
    nvtxEventAttributes_t a{};a.version=NVTX_VERSION;a.size=NVTX_EVENT_ATTRIB_STRUCT_SIZE;
    a.messageType=NVTX_MESSAGE_TYPE_ASCII;a.message.ascii=messages[slot];
    r.push_level=nvtxDomainRangePushEx(domain,&a);
#endif
    SetLastError(prior);r.forwards=1;
    const auto rc=original(ptr,value,count,stream);const DWORD after=GetLastError();
    r.return_code=static_cast<int>(rc);r.return_error=after;r.completed=1;
#ifdef EP_CPU_TEST
    r.pop_level=-1;
#else
    r.pop_level=nvtxDomainRangePop(domain);
#endif
    InterlockedDecrement(&inflight);inside=false;SetLastError(after);return rc;
}

static LONG transaction(bool install) {
    // One bounded snapshot, never a resident monitor. New calls after commit
    // reach the patched export; other-thread calls during capture are faults.
    HANDLE snap=CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD,0);
    if(snap==INVALID_HANDLE_VALUE)return static_cast<LONG>(GetLastError());
    std::vector<HANDLE> handles;THREADENTRY32 e{};e.dwSize=sizeof(e);
    LONG rc=DetourTransactionBegin();
    if(!rc) {
        if(!Thread32First(snap,&e))rc=static_cast<LONG>(GetLastError());
        else do {
            if(e.th32OwnerProcessID!=GetCurrentProcessId())continue;
            if(e.th32ThreadID==GetCurrentThreadId())continue; // Detours current thread needs no enlistment.
            HANDLE h=OpenThread(THREAD_SUSPEND_RESUME|THREAD_GET_CONTEXT|THREAD_SET_CONTEXT|THREAD_QUERY_INFORMATION,FALSE,e.th32ThreadID);
            if(!h) {rc=static_cast<LONG>(GetLastError());break;}
            handles.push_back(h);rc=DetourUpdateThread(h);if(rc)break;
        } while(Thread32Next(snap,&e));
        if(!rc)rc=install?DetourAttach(reinterpret_cast<PVOID*>(&original),reinterpret_cast<PVOID>(intercept)):
            DetourDetach(reinterpret_cast<PVOID*>(&original),reinterpret_cast<PVOID>(intercept));
        if(rc)DetourTransactionAbort();else rc=DetourTransactionCommit();
    }
    for(auto h:handles)CloseHandle(h);CloseHandle(snap);return rc;
}

extern "C" __declspec(dllexport) LONG ep_prefill_start(HMODULE runtime,const char* run) {
    if(attached || begun || !runtime || !run || std::strlen(run)!=32)return ERROR_INVALID_PARAMETER;
    for(auto p=run;*p;++p)if(!(*p>='0'&&*p<='9')&&!(*p>='a'&&*p<='f'))return ERROR_INVALID_PARAMETER;
#ifdef EP_CPU_TEST
    auto address=GetProcAddress(runtime,"EpHostMemset");
#else
    auto address=GetProcAddress(runtime,"cudaMemsetAsync");
#endif
    HMODULE owner=nullptr;
    if(!address || !GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
        reinterpret_cast<LPCWSTR>(address),&owner) || owner!=runtime)return ERROR_INVALID_ADDRESS;
    original=reinterpret_cast<MemsetFn>(address);primary=GetCurrentThreadId();
    for(unsigned i=0;i<capacity;++i)std::snprintf(messages[i],sizeof(messages[i]),"EP_MEMSET_PREFILL:%s:%u",run,i+1);
#ifndef EP_CPU_TEST
    domain=nvtxDomainCreateA("EP_MEMSET_PREFILL");
#endif
    const LONG rc=transaction(true);if(!rc)attached=1;return rc;
}
extern "C" __declspec(dllexport) LONG ep_prefill_begin() {
    if(!attached || begun || enabled || GetCurrentThreadId()!=primary)return ERROR_INVALID_STATE;
    begun=1;InterlockedExchange(&enabled,1);return 0;
}
extern "C" __declspec(dllexport) LONG ep_prefill_end() {
    if(!attached || !enabled || GetCurrentThreadId()!=primary || inflight)return ERROR_INVALID_STATE;
    InterlockedExchange(&enabled,0);return 0;
}
extern "C" __declspec(dllexport) LONG ep_prefill_stop() {
    if(!attached || enabled || inflight)return ERROR_INVALID_STATE;
    const LONG rc=transaction(false);if(!rc)attached=0;return rc;
}
extern "C" __declspec(dllexport) const CallRecord* ep_prefill_records(unsigned* n,LONG* error) {
    *n=static_cast<unsigned>(used<0?0:used>static_cast<LONG>(capacity)?capacity:used);*error=fault;return records;
}
