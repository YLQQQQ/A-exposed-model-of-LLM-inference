// Compile the actual client implementation but never call its GPU entry.
// The function pointer substitutes below are Host-only CUPTI-buffer test inputs.
#define wmain gpu_entry_not_called
#include "micro.cpp"
#undef wmain
#include <iostream>

namespace {
std::string test_mode;bool delivered=false;
CUpti_ActivityAPI test_api{};
CUptiResult CUPTIAPI fake_next(uint8_t*,size_t,CUpti_Activity** record) {
    if(test_mode=="parser_error")return CUPTI_ERROR_INVALID_PARAMETER;
    if(!delivered) {*record=reinterpret_cast<CUpti_Activity*>(&test_api);delivered=true;return CUPTI_SUCCESS;}
    return CUPTI_ERROR_MAX_LIMIT_REACHED;
}
CUptiResult CUPTIAPI fake_dropped(CUcontext,uint32_t,size_t* n) {
    *n=test_mode=="dropped"?7:0;
    return test_mode=="drop_error"?CUPTI_ERROR_INVALID_PARAMETER:CUPTI_SUCCESS;
}
}
int main(int argc,char** argv) {
    if(argc!=2)return 2;test_mode=argv[1];
    auto s=std::make_unique<Client>();Client::current=s.get();s->next=fake_next;s->dropped=fake_dropped;
    test_api.kind=CUPTI_ACTIVITY_KIND_RUNTIME;test_api.cbid=51;test_api.correlationId=101;
    test_api.processId=321;test_api.threadId=654;test_api.start=10;test_api.end=20;
    if(test_mode=="evidence") {
        const auto pid=GetCurrentProcessId(),tid=GetCurrentThreadId();
        cudaMemsetAsync_v3020_params p{};p.value=123;p.devPtr=reinterpret_cast<void*>(0x9000);
        p.stream=reinterpret_cast<cudaStream_t>(0x5670);
        CUpti_CallbackData d{};d.context=reinterpret_cast<CUcontext>(0x1230);d.contextUid=1;
        cudaError_t rt=cudaSuccess;CUresult driver=CUDA_SUCCESS;
        for(unsigned i=0;i<2;++i) {
            d.correlationId=101+i;d.functionName="cudaMemsetAsync";d.functionParams=&p;
            d.callbackSite=CUPTI_API_ENTER;p.count=i?64:0;
            s->core.callback(CUPTI_CB_DOMAIN_RUNTIME_API,51,d,pid,tid);
            if(i) {
                d.correlationId=901;d.functionName="cuMemsetD8Async";d.callbackSite=CUPTI_API_ENTER;
                s->core.callback(CUPTI_CB_DOMAIN_DRIVER_API,216,d,pid,tid);
                d.callbackSite=CUPTI_API_EXIT;d.functionReturnValue=&driver;
                s->core.callback(CUPTI_CB_DOMAIN_DRIVER_API,216,d,pid,tid);
            }
            d.correlationId=101+i;d.functionName="cudaMemsetAsync";d.functionParams=nullptr;
            d.callbackSite=CUPTI_API_EXIT;d.functionReturnValue=&rt;
            s->core.callback(CUPTI_CB_DOMAIN_RUNTIME_API,51,d,pid,tid);
        }
        for(size_t i=0;i<s->core.call_count;++i) {
            const auto& c=s->core.calls[i];test_api.kind=c.runtime?CUPTI_ACTIVITY_KIND_RUNTIME:CUPTI_ACTIVITY_KIND_DRIVER;
            test_api.cbid=c.cbid;test_api.correlationId=c.correlation;
            test_api.processId=pid;test_api.threadId=tid;s->core.activity(reinterpret_cast<CUpti_Activity*>(&test_api));
        }
        CUpti_ActivityMemset4 e{};e.kind=CUPTI_ACTIVITY_KIND_MEMSET;e.bytes=64;e.value=123;
        e.deviceId=0;e.contextId=1;e.streamId=7;e.correlationId=901;e.start=30;e.end=40;
        s->core.activity(reinterpret_cast<CUpti_Activity*>(&e));s->query_loss(nullptr,0);
        Life life;life.subscribe=life.register_buffers=life.enable=life.flush=life.disable=life.unsubscribe=life.finalize=0;
        std::array<Reference,2> refs{};refs[0].bytes.fill(58);refs[1].bytes.fill(123);refs[0].ok=refs[1].ok=true;
        json_write(std::cout,*s,life,"HOST-native-writer","HOST_ONLY","HOST_ONLY",12040,22,1,7,0,
            reinterpret_cast<CUcontext>(0x1230),p.stream,refs,"",L"HOST_ONLY",L"HOST_ONLY","HOST_CALLBACK_DOUBLE");
        return GetModuleHandleW(L"nvcuda.dll")||GetModuleHandleW(L"cupti64_2024.1.1.dll")?2:0;
    } else if(test_mode=="bridge") {
        cudaMemsetAsync_v3020_params p{};p.count=64;p.value=123;
        p.devPtr=reinterpret_cast<void*>(0x9000);p.stream=reinterpret_cast<cudaStream_t>(0x5670);
        CUpti_CallbackData d{};d.context=reinterpret_cast<CUcontext>(0x1230);d.contextUid=1;
        d.correlationId=101;d.functionName="cudaMemsetAsync";d.functionParams=&p;d.callbackSite=CUPTI_API_ENTER;
        s->core.callback(CUPTI_CB_DOMAIN_RUNTIME_API,51,d,321,654);
        d.correlationId=901;d.functionName="cuMemsetD8Async";d.functionParams=nullptr;
        s->core.callback(CUPTI_CB_DOMAIN_DRIVER_API,216,d,321,654);
        CUresult code=CUDA_SUCCESS;d.callbackSite=CUPTI_API_EXIT;d.functionReturnValue=&code;
        s->core.callback(CUPTI_CB_DOMAIN_DRIVER_API,216,d,321,654);
        cudaError_t rt=cudaSuccess;d.correlationId=101;d.functionName="cudaMemsetAsync";d.functionReturnValue=&rt;
        s->core.callback(CUPTI_CB_DOMAIN_RUNTIME_API,51,d,321,654);
    } else if(test_mode=="overflow") {
        for(size_t i=0;i<ep_cupti::API_CAP+1;++i)s->core.activity(reinterpret_cast<CUpti_Activity*>(&test_api));
    } else {
        std::array<uint8_t*,Client::BUFFER_COUNT+1> data{};size_t size=0,max=0;
        const size_t n=test_mode=="exhaust"?Client::BUFFER_COUNT+1:1;
        for(size_t i=0;i<n;++i)Client::request(&data[i],&size,&max);
        for(size_t i=0;i<n;++i)if(data[i]) {delivered=false;Client::complete(nullptr,0,data[i],Client::BUFFER_BYTES,1);}
    }
    bool loaded=GetModuleHandleW(L"nvcuda.dll")||GetModuleHandleW(L"cudart64_12.dll")||
        GetModuleHandleW(L"cupti64_2024.1.1.dll");
    std::cout<<"{\"api_count\":"<<s->core.api_count<<",\"buffer_exhaustion\":"<<s->exhausted
        <<",\"activity_error\":"<<s->errors<<",\"dropped_records\":"<<s->lost
        <<",\"dropped_query_errors\":"<<s->query_errors<<",\"activity_overflow\":"<<s->core.activity_overflow
        <<",\"driver_parent\":"<<s->core.calls[1].parent<<",\"vendor_dll_loaded\":"<<(loaded?"true":"false")<<"}\n";
    return loaded?2:0;
}
