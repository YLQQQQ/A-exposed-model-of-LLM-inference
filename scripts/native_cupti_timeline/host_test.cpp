// SDK-structure Host doubles. Never loads or invokes a vendor library.
#include "writer.h"
#include <windows.h>
#include <iostream>
#include <memory>
#include <string>

using namespace ep_timeline;
void invoke(Core& c,CUpti_CallbackDomain domain,CUpti_CallbackId id,const char* name,
            uint32_t tid,uint32_t corr,bool enter,const void* params,uint64_t time) {
    CUpti_CallbackData d{};d.callbackSite=enter?CUPTI_API_ENTER:CUPTI_API_EXIT;
    d.functionName=name;d.correlationId=corr;d.context=reinterpret_cast<CUcontext>(uintptr_t(0x1230));
    d.contextUid=3;d.functionParams=params;cudaError_t rt=cudaSuccess;CUresult dr=CUDA_SUCCESS;
    d.functionReturnValue=domain==CUPTI_CB_DOMAIN_RUNTIME_API?static_cast<void*>(&rt):static_cast<void*>(&dr);
    c.callback(domain,id,d,7,tid,time);
}
int main(int argc,char** argv) {
    if(argc<2)return 2;const std::string mode=argv[1];
    if(mode=="load") {
        if(argc!=3)return 2;auto lib=LoadLibraryA(argv[2]);if(!lib)return 3;
        auto abi=reinterpret_cast<int(*)()>(GetProcAddress(lib,"ep_timeline_abi_version"));
        if(!abi)return 4;
        bool vendor=GetModuleHandleW(L"cupti64_2024.1.1.dll") || GetModuleHandleW(L"cupti64_129.dll") || GetModuleHandleW(L"nvcuda.dll");
        std::cout<<"{\"loaded\":true,\"vendor_loaded\":"<<(vendor?"true":"false")<<",\"abi_version\":"<<abi()<<"}\n";
        FreeLibrary(lib);return 0;
    }
    auto cp=std::make_unique<Core>(mode=="capacity"?1:128,128,32);auto& c=*cp;
    if(mode=="driver_sync") {
        cuStreamSynchronize_params p{};p.hStream=reinterpret_cast<CUstream>(uintptr_t(0x3450));
        invoke(c,CUPTI_CB_DOMAIN_DRIVER_API,CUPTI_DRIVER_TRACE_CBID_cuStreamSynchronize,"cuStreamSynchronize",9,111,true,&p,10);
        p.hStream=nullptr;
        invoke(c,CUPTI_CB_DOMAIN_DRIVER_API,CUPTI_DRIVER_TRACE_CBID_cuStreamSynchronize,"cuStreamSynchronize",9,111,false,nullptr,20);
        const auto& d=c.calls[0];
        std::cout<<"{\"native_stream\":"<<d.native_stream<<",\"params\":"<<(d.params?"true":"false")
            <<",\"errors\":"<<c.errors<<",\"vendor_calls\":0}\n";return 0;
    }
    if(mode=="evidence") {
        auto rt=[&](CUpti_CallbackId id,const char* name,uint32_t corr,const void* params,uint64_t a,uint64_t b,
                    CUpti_CallbackId driver,const char* driver_name,uint32_t dcorr) {
            auto index=c.call_count;invoke(c,CUPTI_CB_DOMAIN_RUNTIME_API,id,name,9,corr,true,params,a);c.bind(index,0,4,0);
            if(driver) {
                cuStreamSynchronize_params ds{};
                auto child=c.call_count;
                invoke(c,CUPTI_CB_DOMAIN_DRIVER_API,driver,driver_name,9,dcorr,true,
                    driver==CUPTI_DRIVER_TRACE_CBID_cuStreamSynchronize?&ds:nullptr,a+1);
                c.bind(child,0,4,0);
                invoke(c,CUPTI_CB_DOMAIN_DRIVER_API,driver,driver_name,9,dcorr,false,nullptr,b-1);
            }
            invoke(c,CUPTI_CB_DOMAIN_RUNTIME_API,id,name,9,corr,false,nullptr,b);
            CUpti_ActivityAPI api{};api.kind=CUPTI_ACTIVITY_KIND_RUNTIME;api.cbid=id;api.processId=7;api.threadId=9;
            api.start=a;api.end=b;api.correlationId=corr;c.activity(reinterpret_cast<CUpti_Activity*>(&api));
        };
        rt(CUPTI_RUNTIME_TRACE_CBID_cudaDeviceSynchronize_v3020,"cudaDeviceSynchronize",16,nullptr,1,5,0,"",0);
        cudaLaunchKernel_v7000_params launch{};
        rt(CUPTI_RUNTIME_TRACE_CBID_cudaLaunchKernel_v7000,"cudaLaunchKernel",11,&launch,10,16,307,"cuLaunchKernel",101);
        cudaMemsetAsync_v3020_params zero{};
        rt(51,"cudaMemsetAsync",12,&zero,17,19,0,"",0);
        cudaMemsetAsync_v3020_params set{};set.count=64;set.value=123;
        rt(51,"cudaMemsetAsync",13,&set,20,26,216,"cuMemsetD8Async",102);
        cudaMemcpyAsync_v3020_params copy{};copy.count=8;copy.kind=cudaMemcpyDeviceToHost;
        rt(CUPTI_RUNTIME_TRACE_CBID_cudaMemcpyAsync_v3020,"cudaMemcpyAsync",14,&copy,40,44,42,"cuMemcpyDtoHAsync",103);
        cudaStreamSynchronize_v3020_params syncp{};
        rt(CUPTI_RUNTIME_TRACE_CBID_cudaStreamSynchronize_v3020,"cudaStreamSynchronize",15,&syncp,45,70,126,"cuStreamSynchronize",104);
        CUpti_ActivityKernel9 k{};k.kind=CUPTI_ACTIVITY_KIND_CONCURRENT_KERNEL;k.name="independent kernel";
        k.correlationId=101;k.deviceId=0;k.contextId=3;k.streamId=4;k.start=30;k.end=55;c.activity(reinterpret_cast<CUpti_Activity*>(&k));
        CUpti_ActivityMemset4 m{};m.kind=CUPTI_ACTIVITY_KIND_MEMSET;m.correlationId=102;m.contextId=3;m.streamId=4;
        m.start=56;m.end=60;m.bytes=64;m.value=123;c.activity(reinterpret_cast<CUpti_Activity*>(&m));
        CUpti_ActivityMemcpy5 d{};d.kind=CUPTI_ACTIVITY_KIND_MEMCPY;d.correlationId=103;d.runtimeCorrelationId=14;
        d.contextId=3;d.streamId=4;d.start=61;d.end=62;d.bytes=8;d.copyKind=2;c.activity(reinterpret_cast<CUpti_Activity*>(&d));
        CUpti_ActivitySynchronization sy{};sy.kind=CUPTI_ACTIVITY_KIND_SYNCHRONIZATION;sy.contextId=3;
        sy.streamId=4;sy.start=47;sy.end=68;sy.correlationId=104;sy.type=CUPTI_ACTIVITY_SYNCHRONIZATION_TYPE_STREAM_SYNCHRONIZE;
        c.activity(reinterpret_cast<CUpti_Activity*>(&sy));
        sy.streamId=UINT32_MAX;sy.start=2;sy.end=4;sy.correlationId=16;sy.type=CUPTI_ACTIVITY_SYNCHRONIZATION_TYPE_CONTEXT_SYNCHRONIZE;
        c.activity(reinterpret_cast<CUpti_Activity*>(&sy));
        CUpti_ActivityContext2 ctx{};ctx.kind=CUPTI_ACTIVITY_KIND_CONTEXT;ctx.contextId=3;ctx.nullStreamId=4;
        c.activity(reinterpret_cast<CUpti_Activity*>(&ctx));
        c.marker(1,"EXPOSEDPATH_DRAIN_V1:{\"identity\":{\"run_id\":\"run\"},\"kind\":\"drain\"}",9,0);
        c.marker(2,"",9,6);
        c.marker(0,"EXPOSEDPATH_BOUNDARY_V1:{\"identity\":{\"run_id\":\"run\"},\"kind\":\"request_start\"}",9,10);
        c.marker(1,"EXPOSEDPATH_JSON_V1:{\"run_id\":\"run\",\"kind\":\"sync\"}",9,39);
        c.marker(0,"EXPOSEDPATH_BOUNDARY_V1:{\"identity\":{\"run_id\":\"run\"},\"kind\":\"token_ready\"}",9,75);
        c.marker(2,"",9,76);
        capture_json(std::cout,c,"same-session",7,"HOST_SDK_DOUBLE",true,0,0,0,{{3,4}});return 0;
    }
    cudaMemsetAsync_v3020_params p{};p.count=(uint64_t(1)<<63)+7;p.value=123;p.devPtr=reinterpret_cast<void*>(uintptr_t(0x5670));
    invoke(c,CUPTI_CB_DOMAIN_RUNTIME_API,51,"cudaMemsetAsync",9,11,true,mode=="missing_params"?nullptr:&p,10);
    const auto copied=c.calls[0].count;p.count=64;
    if(mode=="snapshot") {
        invoke(c,CUPTI_CB_DOMAIN_DRIVER_API,216,"cuMemsetD8Async",9,101,true,nullptr,11);
        invoke(c,CUPTI_CB_DOMAIN_RUNTIME_API,51,"cudaMemsetAsync",10,12,true,&p,12);
        invoke(c,CUPTI_CB_DOMAIN_DRIVER_API,216,"cuMemsetD8Async",10,102,true,nullptr,13);
        invoke(c,CUPTI_CB_DOMAIN_DRIVER_API,216,"cuMemsetD8Async",9,101,false,nullptr,14);
        invoke(c,CUPTI_CB_DOMAIN_RUNTIME_API,51,"cudaMemsetAsync",9,11,false,nullptr,15);
        invoke(c,CUPTI_CB_DOMAIN_DRIVER_API,216,"cuMemsetD8Async",10,102,false,nullptr,16);
        invoke(c,CUPTI_CB_DOMAIN_RUNTIME_API,51,"cudaMemsetAsync",10,12,false,nullptr,17);
        std::cout<<"{\"thread_stacks\":"<<c.thread_count<<",\"copied_count\":"<<copied
            <<",\"copied_stream\":"<<c.calls[0].native_stream<<",\"parent_ids\":[null,"<<c.calls[1].parent<<",null,"<<c.calls[3].parent
            <<"],\"errors\":"<<c.errors<<",\"vendor_calls\":0}\n";return 0;
    }
    if(mode=="wrong_exit")invoke(c,CUPTI_CB_DOMAIN_RUNTIME_API,51,"cudaMemsetAsync",9,99,false,nullptr,20);
    else if(mode=="capacity")invoke(c,CUPTI_CB_DOMAIN_RUNTIME_API,51,"cudaMemsetAsync",10,12,true,&p,20);
    else if(mode=="activity_kind") {CUpti_Activity a{};a.kind=CUPTI_ACTIVITY_KIND_OVERHEAD;c.activity(&a);}
    else if(mode=="long_kernel_name") {
        std::string name(1024,'x');CUpti_ActivityKernel9 k{};k.kind=CUPTI_ACTIVITY_KIND_CONCURRENT_KERNEL;k.name=name.c_str();c.activity(reinterpret_cast<CUpti_Activity*>(&k));
    } else if(mode=="activities") {
        CUpti_ActivityAPI a{};a.kind=CUPTI_ACTIVITY_KIND_RUNTIME;c.activity(reinterpret_cast<CUpti_Activity*>(&a));
        char name[]="original kernel";CUpti_ActivityKernel9 k{};k.kind=CUPTI_ACTIVITY_KIND_CONCURRENT_KERNEL;k.name=name;c.activity(reinterpret_cast<CUpti_Activity*>(&k));name[0]='X';
        CUpti_ActivityMemcpy5 copy{};copy.kind=CUPTI_ACTIVITY_KIND_MEMCPY;copy.runtimeCorrelationId=77;c.activity(reinterpret_cast<CUpti_Activity*>(&copy));
        CUpti_ActivityMemset4 set{};set.kind=CUPTI_ACTIVITY_KIND_MEMSET;c.activity(reinterpret_cast<CUpti_Activity*>(&set));
        CUpti_ActivitySynchronization sync{};sync.kind=CUPTI_ACTIVITY_KIND_SYNCHRONIZATION;c.activity(reinterpret_cast<CUpti_Activity*>(&sync));
        CUpti_ActivityStream stream{};stream.kind=CUPTI_ACTIVITY_KIND_STREAM;c.activity(reinterpret_cast<CUpti_Activity*>(&stream));
        CUpti_ActivityContext2 ctx{};ctx.kind=CUPTI_ACTIVITY_KIND_CONTEXT;c.activity(reinterpret_cast<CUpti_Activity*>(&ctx));
        CUpti_ActivityCudaEvent ev{};ev.kind=CUPTI_ACTIVITY_KIND_CUDA_EVENT;c.activity(reinterpret_cast<CUpti_Activity*>(&ev));
        std::cout<<"{\"kinds\":[";
        for(size_t i=0;i<c.record_count;++i){if(i)std::cout<<',';string(std::cout,kind_name(c.records[i].kind));}
        std::cout<<"],\"kernel_name\":";string(std::cout,c.records[1].name);
        std::cout<<",\"copy_runtime_correlation\":"<<c.records[2].runtime_correlation<<",\"errors\":"<<c.errors<<",\"vendor_calls\":0}\n";return 0;
    }
    std::cout<<"{\"errors\":"<<c.errors<<",\"overflow\":"<<c.overflow<<",\"vendor_calls\":0}\n";return 0;
}
