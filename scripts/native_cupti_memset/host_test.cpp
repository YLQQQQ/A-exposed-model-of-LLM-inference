// Real API22 structs with Host inputs only; no vendor library is linked or loaded.
#include "core.h"
#include <windows.h>
#include <iostream>
#include <memory>

int main(int argc,char** argv) {
    if(argc!=2)return 2;
    const std::string mode=argv[1];auto s=std::make_unique<ep_cupti::Core>();
    const bool ptsz=mode=="ptsz";
    const auto id=ptsz?CUPTI_RUNTIME_TRACE_CBID_cudaMemsetAsync_ptsz_v7000:
        CUPTI_RUNTIME_TRACE_CBID_cudaMemsetAsync_v3020;
    std::uint64_t n=mode=="zero"?0:mode=="large"?(1ULL<<63)+7:64;
    cudaMemsetAsync_v3020_params p{};p.count=static_cast<size_t>(n);p.value=123;
    p.devPtr=reinterpret_cast<void*>(0x9000);p.stream=reinterpret_cast<cudaStream_t>(0x5670);
    cudaMemsetAsync_ptsz_v7000_params q{};q.count=p.count;q.value=p.value;q.devPtr=p.devPtr;q.stream=p.stream;
    CUpti_CallbackData d{};d.context=reinterpret_cast<CUcontext>(0x1230);d.contextUid=1;d.correlationId=100;
    if(mode=="context_uid_zero")d.contextUid=0;
    d.functionName=ptsz?"cudaMemsetAsync_ptsz":"cudaMemsetAsync";
    if(mode=="versioned_name") {s->ordinary_name="cudaMemsetAsync_v3020";d.functionName="cudaMemsetAsync_v3020";}
    if(mode=="wrong_name")d.functionName="not_the_expected_function";
    d.functionParams=mode=="missing_params"?nullptr:ptsz?static_cast<void*>(&q):&p;
    d.callbackSite=CUPTI_API_ENTER;
    s->callback(CUPTI_CB_DOMAIN_RUNTIME_API,id,d,321,654);
    p.count=17;p.value=19;p.stream=nullptr;q.count=17;q.value=19;q.stream=nullptr;
    if(mode=="reentry")s->callback(CUPTI_CB_DOMAIN_RUNTIME_API,id,d,321,654);
    if(mode=="wrong_thread")s->callback(CUPTI_CB_DOMAIN_RUNTIME_API,id,d,321,655);
    cudaError_t status=mode=="failed"?cudaErrorMemoryAllocation:cudaSuccess;
    d.functionParams=nullptr;d.functionReturnValue=mode=="missing_return"?nullptr:&status;
    d.callbackSite=CUPTI_API_EXIT;if(mode=="wrong_exit")d.correlationId=101;
    s->callback(CUPTI_CB_DOMAIN_RUNTIME_API,id,d,321,654);
    if(mode=="overflow") {
        d.functionParams=&p;d.functionReturnValue=&status;
        for(size_t i=0;i<ep_cupti::CALL_CAP+1;++i) {
            d.correlationId=static_cast<uint32_t>(200+i);d.callbackSite=CUPTI_API_ENTER;
            s->callback(CUPTI_CB_DOMAIN_RUNTIME_API,id,d,321,654);
            d.callbackSite=CUPTI_API_EXIT;s->callback(CUPTI_CB_DOMAIN_RUNTIME_API,id,d,321,654);
        }
    }
    const auto& c=s->calls[0];
    bool loaded=GetModuleHandleW(L"nvcuda.dll")||GetModuleHandleW(L"cudart64_12.dll")||
        GetModuleHandleW(L"cupti64_2024.1.1.dll");
    std::cout<<"{\"count\":"<<c.count<<",\"value\":"<<c.value<<",\"native_stream\":";
    ep_cupti::hex(std::cout,c.stream);
    std::cout<<",\"context_uid\":"<<c.uid<<",\"observed_name\":\""<<c.name<<"\",\"entry_kind\":\""<<(c.ptsz?"PTSZ":"ORDINARY")<<"\",\"return_code\":"<<c.status
        <<",\"callback_error\":"<<s->error<<",\"vendor_dll_loaded\":"<<(loaded?"true":"false")
        <<",\"cuda_calls\":0,\"cupti_calls\":0}\n";
    return loaded?2:0;
}
