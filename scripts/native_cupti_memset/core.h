// Fixed CUDA12.4/API22 headers. This core never calls CUDA/CUPTI or writes files.
#pragma once
#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable:4324) // The fixed vendor ABI intentionally pads aligned records.
#endif
#include <cupti.h> // Includes generated metadata itself; those files lack include guards.
#ifdef _MSC_VER
#pragma warning(pop)
#endif
#include <array>
#include <cstdint>
#include <cstring>
#include <mutex>
#include <ostream>
#include <string>

static_assert(CUPTI_API_VERSION==22, "Reviewed CUPTI API22 required");
static_assert(CUDART_VERSION==12040, "Reviewed CUDA12.4 required");
static_assert(sizeof(size_t)==8, "x64 size_t required");

namespace ep_cupti {
constexpr size_t CALL_CAP=64, API_CAP=4096, EFFECT_CAP=128;
struct Call {
    std::uint64_t id=0,parent=0,enter=0,exit=0,count=0,stream=0,pointer=0,context=0;
    std::uint32_t pid=0,tid=0,uid=0,correlation=0,cbid=0;
    bool runtime=false,ptsz=false,copied=false,exited=false;
    int value=0,status=0; char name[128]{};
};
#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable:4324) // Wrapper keeps the vendor record's required alignment.
#endif
struct Api { bool runtime=false; CUpti_ActivityAPI value{}; };
#ifdef _MSC_VER
#pragma warning(pop)
#endif
struct Core {
    std::array<Call,CALL_CAP> calls{};size_t call_count=0;
    std::array<Api,API_CAP> apis{};size_t api_count=0;
    std::array<CUpti_ActivityMemset4,EFFECT_CAP> effects{};size_t effect_count=0;
    std::array<size_t,8> stack{};size_t depth=0;std::uint64_t seq=0;
    unsigned error=0,callback_overflow=0,activity_overflow=0;
    std::uint32_t owner=0;
    // Filled outside callbacks from the fixed SDK's metadata, never from observed arguments.
    std::string ordinary_name="cudaMemsetAsync",ptsz_name="cudaMemsetAsync_ptsz";
    std::mutex mutex;
    void callback(CUpti_CallbackDomain domain,CUpti_CallbackId cbid,
                  const CUpti_CallbackData& data,std::uint32_t pid,std::uint32_t tid) noexcept {
        std::lock_guard<std::mutex> lock(mutex);
        const bool rt=domain==CUPTI_CB_DOMAIN_RUNTIME_API;
        if (!rt && domain!=CUPTI_CB_DOMAIN_DRIVER_API) {++error;return;}
        if (rt && cbid!=CUPTI_RUNTIME_TRACE_CBID_cudaMemsetAsync_v3020 &&
            cbid!=CUPTI_RUNTIME_TRACE_CBID_cudaMemsetAsync_ptsz_v7000) {++error;return;}
        if (!rt && depth==0) return; // Driver setup outside target runtime is not a target callback.
        if (owner && owner!=tid) {++error;return;}
        if (!owner) owner=tid;
        if (data.callbackSite==CUPTI_API_ENTER) {
            if (call_count==CALL_CAP || depth==stack.size()) {++callback_overflow;++error;return;}
            // Single-thread, non-reentrant micro only. Do not flatten nested driver calls.
            if ((rt && depth) || (!rt && (depth!=1 || !calls[stack[0]].runtime))) {++error;return;}
            if (!data.functionName || !data.correlationId || !data.context || !data.contextUid) {++error;return;}
            auto& c=calls[call_count];c.id=call_count+1;c.parent=depth?calls[stack[depth-1]].id:0;
            c.enter=++seq;c.pid=pid;c.tid=tid;c.runtime=rt;c.cbid=cbid;c.uid=data.contextUid;
            c.context=reinterpret_cast<std::uintptr_t>(data.context);c.correlation=data.correlationId;
            if (std::strlen(data.functionName)>=sizeof(c.name)) {++error;return;}
            std::memcpy(c.name,data.functionName,std::strlen(data.functionName)+1);
            if (rt) {
                c.ptsz=cbid==CUPTI_RUNTIME_TRACE_CBID_cudaMemsetAsync_ptsz_v7000;
                const char* expected=c.ptsz?"cudaMemsetAsync_ptsz":"cudaMemsetAsync";
                const auto& metadata=c.ptsz?ptsz_name:ordinary_name;
                if ((std::strcmp(c.name,expected)!=0 && c.name!=metadata) || !data.functionParams) {++error;return;}
                if (c.ptsz) {
                    const auto& p=*static_cast<const cudaMemsetAsync_ptsz_v7000_params*>(data.functionParams);
                    c.count=p.count;c.value=p.value;c.pointer=reinterpret_cast<std::uintptr_t>(p.devPtr);
                    c.stream=reinterpret_cast<std::uintptr_t>(p.stream);
                } else {
                    const auto& p=*static_cast<const cudaMemsetAsync_v3020_params*>(data.functionParams);
                    c.count=p.count;c.value=p.value;c.pointer=reinterpret_cast<std::uintptr_t>(p.devPtr);
                    c.stream=reinterpret_cast<std::uintptr_t>(p.stream);
                }
                c.copied=true;
            }
            stack[depth++]=call_count++;
        } else if (data.callbackSite==CUPTI_API_EXIT) {
            if (!depth || !data.functionReturnValue) {++error;return;}
            auto& c=calls[stack[depth-1]];
            if (c.runtime!=rt || c.cbid!=cbid || c.correlation!=data.correlationId ||
                c.uid!=data.contextUid || c.context!=reinterpret_cast<std::uintptr_t>(data.context) ||
                !data.functionName || std::strcmp(c.name,data.functionName)!=0) {++error;return;}
            // Never dereference functionParams on EXIT; ENTRY pointers are no longer used.
            c.status=rt?static_cast<int>(*static_cast<const cudaError_t*>(data.functionReturnValue)):
                static_cast<int>(*static_cast<const CUresult*>(data.functionReturnValue));
            c.exit=++seq;c.exited=true;--depth;
        } else ++error;
    }
    void activity(const CUpti_Activity* a) noexcept {
        std::lock_guard<std::mutex> lock(mutex);
        if (a->kind==CUPTI_ACTIVITY_KIND_RUNTIME || a->kind==CUPTI_ACTIVITY_KIND_DRIVER) {
            if (api_count==API_CAP) {++activity_overflow;return;}
            apis[api_count++]={a->kind==CUPTI_ACTIVITY_KIND_RUNTIME,
                *reinterpret_cast<const CUpti_ActivityAPI*>(a)};
        } else if (a->kind==CUPTI_ACTIVITY_KIND_MEMSET) {
            if (effect_count==EFFECT_CAP) {++activity_overflow;return;}
            effects[effect_count++]=*reinterpret_cast<const CUpti_ActivityMemset4*>(a);
        } else ++error;
    }
};
inline void hex(std::ostream& o,std::uint64_t n) {o<<'"'<<"0x"<<std::hex<<n<<std::dec<<'"';}
inline void write_calls(std::ostream& o,const Core& s) {
    o<<'[';
    for(size_t i=0;i<s.call_count;++i) {
        const auto& c=s.calls[i];if(i)o<<',';
        o<<"{\"call_id\":"<<c.id<<",\"parent_call_id\":"<<c.parent
         <<",\"domain\":\""<<(c.runtime?"RUNTIME":"DRIVER")<<"\",\"cbid\":"<<c.cbid
         <<",\"name\":\""<<(c.runtime?(c.ptsz?"cudaMemsetAsync_ptsz":"cudaMemsetAsync"):c.name)
         <<"\",\"observed_name\":\""<<c.name<<"\",\"entry_kind\":\""<<(c.ptsz?"PTSZ":"ORDINARY")
         <<"\",\"pid\":"<<c.pid<<",\"tid\":"<<c.tid<<",\"context_uid\":"<<c.uid
         <<",\"native_context\":";hex(o,c.context);o<<",\"native_stream\":";hex(o,c.stream);
        o<<",\"pointer\":";hex(o,c.pointer);
        o<<",\"count\":"<<c.count<<",\"value\":"<<c.value<<",\"correlation_id\":"<<c.correlation
         <<",\"enter_seq\":"<<c.enter<<",\"exit_seq\":"<<c.exit
         <<",\"entry_seen\":true,\"exit_seen\":"<<(c.exited?"true":"false")
         <<",\"params_copied\":"<<(c.copied?"true":"false")<<",\"return_code\":"<<c.status<<'}';
    }
    o<<']';
}
}
