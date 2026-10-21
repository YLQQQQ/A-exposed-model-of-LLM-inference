// API22 evidence copying only. No CUDA/CUPTI calls, I/O, or callback allocation.
#pragma once
#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable:4324)
#endif
#include <cupti.h>
#ifdef _MSC_VER
#pragma warning(pop)
#endif
#include <array>
#include <cstdint>
#include <cstring>
#include <mutex>
#include <vector>

static_assert(CUPTI_API_VERSION==22 && CUDART_VERSION==12040,"Fixed SDK required");
namespace ep_timeline {
struct Call {
    uint64_t id=0,parent=0,start=0,end=0,enter=0,exit=0,count=0,native_stream=0,native_context=0,exit_native_context=0;
    uint32_t pid=0,tid=0,correlation=0,cbid=0,context=0,device=0,stream=0,exit_context=0;
    int status=0,value=0,copy_kind=0,binding_status=-1;
    bool runtime=false,params=false,ptsz=false,closed=false;
    char name[128]{};
};
struct Record {
    enum Kind {API,KERNEL,MEMCPY,MEMSET,SYNC,STREAM,CONTEXT,CUDA_EVENT} kind=API;
    uint64_t start=0,end=0,bytes=0,graph_node=0;
    uint32_t correlation=0,runtime_correlation=0,pid=0,tid=0,cbid=0,status=0;
    uint32_t device=0,context=0,stream=0,graph=0,value=0,copy_kind=0,src_kind=0,dst_kind=0;
    int grid[3]{},block[3]{};uint32_t dynamic_shared=0,flags=0,event=0;
    bool runtime=false;char name[1024]{};
};
struct Thread {
    uint32_t pid=0,tid=0;size_t depth=0;std::array<size_t,64> stack{};
};
struct Marker {uint64_t time=0;uint32_t tid=0;int action=0;char label[8192]{};};
struct Core {
    std::vector<Call> calls;std::vector<Record> records;std::vector<Marker> markers;
    std::array<Thread,128> threads{};size_t call_count=0,record_count=0,marker_count=0,thread_count=0;
    uint64_t seq=0;unsigned errors=0,overflow=0;std::mutex mutex;
    explicit Core(size_t c=131072,size_t r=131072,size_t m=2048):calls(c),records(r),markers(m){}
    template<size_t N> bool text(char (&dest)[N],const char* src) {
        if(!src){++errors;return false;}
        size_t n=0;while(n<N && src[n])++n;
        if(n==N){++errors;return false;}std::memcpy(dest,src,n+1);return true;
    }
    Thread* thread(uint32_t pid,uint32_t tid) {
        for(size_t i=0;i<thread_count;++i)if(threads[i].pid==pid && threads[i].tid==tid)return &threads[i];
        if(thread_count==threads.size()){++overflow;return nullptr;}
        auto& t=threads[thread_count++];t.pid=pid;t.tid=tid;return &t;
    }
    static bool parameters(Call& c,const CUpti_CallbackData& d) {
        if(!d.functionParams)return false;
        if(!c.runtime) {
            switch(c.cbid) {
            case CUPTI_DRIVER_TRACE_CBID_cuLaunchKernel: {
                auto& p=*static_cast<const cuLaunchKernel_params*>(d.functionParams);
                c.native_stream=reinterpret_cast<uintptr_t>(p.hStream);return true;}
            case CUPTI_DRIVER_TRACE_CBID_cuMemsetD8Async: {
                auto& p=*static_cast<const cuMemsetD8Async_params*>(d.functionParams);
                c.count=p.N;c.value=p.uc;c.native_stream=reinterpret_cast<uintptr_t>(p.hStream);return true;}
            case CUPTI_DRIVER_TRACE_CBID_cuMemcpyDtoHAsync_v2: {
                auto& p=*static_cast<const cuMemcpyDtoHAsync_v2_params*>(d.functionParams);
                c.count=p.ByteCount;c.copy_kind=2;c.native_stream=reinterpret_cast<uintptr_t>(p.hStream);return true;}
            case CUPTI_DRIVER_TRACE_CBID_cuStreamSynchronize: {
                auto& p=*static_cast<const cuStreamSynchronize_params*>(d.functionParams);
                c.native_stream=reinterpret_cast<uintptr_t>(p.hStream);return true;}
            case CUPTI_DRIVER_TRACE_CBID_cuStreamSynchronize_ptsz: {
                auto& p=*static_cast<const cuStreamSynchronize_ptsz_params*>(d.functionParams);
                c.native_stream=reinterpret_cast<uintptr_t>(p.hStream);c.ptsz=true;return true;}
            default:return false;
            }
        }
        switch(c.cbid) {
        case CUPTI_RUNTIME_TRACE_CBID_cudaMemsetAsync_v3020: {
            auto& p=*static_cast<const cudaMemsetAsync_v3020_params*>(d.functionParams);
            c.count=p.count;c.value=p.value;c.native_stream=reinterpret_cast<uintptr_t>(p.stream);return true;}
        case CUPTI_RUNTIME_TRACE_CBID_cudaMemsetAsync_ptsz_v7000: {
            auto& p=*static_cast<const cudaMemsetAsync_ptsz_v7000_params*>(d.functionParams);
            c.count=p.count;c.value=p.value;c.native_stream=reinterpret_cast<uintptr_t>(p.stream);c.ptsz=true;return true;}
        case CUPTI_RUNTIME_TRACE_CBID_cudaMemcpyAsync_v3020: {
            auto& p=*static_cast<const cudaMemcpyAsync_v3020_params*>(d.functionParams);
            c.count=p.count;c.copy_kind=static_cast<int>(p.kind);c.native_stream=reinterpret_cast<uintptr_t>(p.stream);return true;}
        case CUPTI_RUNTIME_TRACE_CBID_cudaMemcpyAsync_ptsz_v7000: {
            auto& p=*static_cast<const cudaMemcpyAsync_ptsz_v7000_params*>(d.functionParams);
            c.count=p.count;c.copy_kind=static_cast<int>(p.kind);c.native_stream=reinterpret_cast<uintptr_t>(p.stream);c.ptsz=true;return true;}
        case CUPTI_RUNTIME_TRACE_CBID_cudaLaunchKernel_v7000: {
            auto& p=*static_cast<const cudaLaunchKernel_v7000_params*>(d.functionParams);
            c.native_stream=reinterpret_cast<uintptr_t>(p.stream);return true;}
        case CUPTI_RUNTIME_TRACE_CBID_cudaLaunchKernel_ptsz_v7000: {
            auto& p=*static_cast<const cudaLaunchKernel_ptsz_v7000_params*>(d.functionParams);
            c.native_stream=reinterpret_cast<uintptr_t>(p.stream);c.ptsz=true;return true;}
        case CUPTI_RUNTIME_TRACE_CBID_cudaStreamSynchronize_v3020: {
            auto& p=*static_cast<const cudaStreamSynchronize_v3020_params*>(d.functionParams);
            c.native_stream=reinterpret_cast<uintptr_t>(p.stream);return true;}
        case CUPTI_RUNTIME_TRACE_CBID_cudaStreamSynchronize_ptsz_v7000: {
            auto& p=*static_cast<const cudaStreamSynchronize_ptsz_v7000_params*>(d.functionParams);
            c.native_stream=reinterpret_cast<uintptr_t>(p.stream);c.ptsz=true;return true;}
        default:return false;
        }
    }
    size_t callback(CUpti_CallbackDomain domain,CUpti_CallbackId id,const CUpti_CallbackData& d,
                    uint32_t pid,uint32_t tid,uint64_t timestamp) {
        std::lock_guard<std::mutex> lock(mutex);
        if(domain!=CUPTI_CB_DOMAIN_RUNTIME_API && domain!=CUPTI_CB_DOMAIN_DRIVER_API){++errors;return SIZE_MAX;}
        auto* t=thread(pid,tid);if(!t)return SIZE_MAX;
        if(d.callbackSite==CUPTI_API_ENTER) {
            if(call_count==calls.size() || t->depth==t->stack.size()){++overflow;return SIZE_MAX;}
            size_t i=call_count++;auto& c=calls[i];c.id=i+1;c.parent=t->depth?calls[t->stack[t->depth-1]].id:0;
            c.pid=pid;c.tid=tid;c.cbid=id;c.correlation=d.correlationId;c.runtime=domain==CUPTI_CB_DOMAIN_RUNTIME_API;
            c.start=timestamp;c.enter=++seq;c.context=d.contextUid;c.native_context=reinterpret_cast<uintptr_t>(d.context);
            text(c.name,d.functionName);c.params=parameters(c,d);
            const bool needs=(!c.runtime && std::strstr(c.name,"cuStreamSynchronize")==c.name) || (c.runtime && (std::strstr(c.name,"cudaMemsetAsync")==c.name ||
                std::strstr(c.name,"cudaMemcpyAsync")==c.name || std::strstr(c.name,"cudaLaunchKernel")==c.name ||
                std::strstr(c.name,"cudaStreamSynchronize")==c.name));
            if(needs && !c.params)++errors;
            t->stack[t->depth++]=i;return i;
        }
        if(d.callbackSite!=CUPTI_API_EXIT || !t->depth){++errors;return SIZE_MAX;}
        auto i=t->stack[t->depth-1];auto& c=calls[i];
        if(c.cbid!=id || c.runtime!=(domain==CUPTI_CB_DOMAIN_RUNTIME_API) || c.correlation!=d.correlationId ||
            !d.functionName || std::strcmp(c.name,d.functionName)!=0 || !d.functionReturnValue || timestamp<c.start){++errors;return SIZE_MAX;}
        c.status=c.runtime?static_cast<int>(*static_cast<const cudaError_t*>(d.functionReturnValue)):
            static_cast<int>(*static_cast<const CUresult*>(d.functionReturnValue));
        c.exit_context=d.contextUid;c.exit_native_context=reinterpret_cast<uintptr_t>(d.context);
        c.end=timestamp;c.exit=++seq;c.closed=true;--t->depth;return i;
    }
    void bind(size_t i,uint32_t device,uint32_t stream,int code) {
        std::lock_guard<std::mutex> lock(mutex);
        if(i>=call_count){++errors;return;}auto& c=calls[i];c.device=device;c.stream=stream;c.binding_status=code;
    }
    void marker(int action,const char* label,uint32_t tid,uint64_t time) {
        std::lock_guard<std::mutex> lock(mutex);
        if(marker_count==markers.size()){++overflow;return;}
        auto& m=markers[marker_count++];m.time=time;m.tid=tid;m.action=action;text(m.label,label);
    }
    void activity(const CUpti_Activity* raw) {
        std::lock_guard<std::mutex> lock(mutex);
        if(record_count==records.size()){++overflow;return;}auto& r=records[record_count];
        switch(raw->kind) {
        case CUPTI_ACTIVITY_KIND_RUNTIME:case CUPTI_ACTIVITY_KIND_DRIVER: {
            auto& a=*reinterpret_cast<const CUpti_ActivityAPI*>(raw);r.kind=Record::API;
            r.runtime=raw->kind==CUPTI_ACTIVITY_KIND_RUNTIME;r.cbid=a.cbid;r.pid=a.processId;r.tid=a.threadId;
            r.start=a.start;r.end=a.end;r.correlation=a.correlationId;r.status=a.returnValue;break;}
        case CUPTI_ACTIVITY_KIND_KERNEL:case CUPTI_ACTIVITY_KIND_CONCURRENT_KERNEL: {
            auto& a=*reinterpret_cast<const CUpti_ActivityKernel9*>(raw);r.kind=Record::KERNEL;
            r.start=a.start;r.end=a.end;r.correlation=a.correlationId;r.device=a.deviceId;r.context=a.contextId;r.stream=a.streamId;
            r.graph=a.graphId;r.graph_node=a.graphNodeId;r.dynamic_shared=static_cast<uint32_t>(a.dynamicSharedMemory);
            r.grid[0]=a.gridX;r.grid[1]=a.gridY;r.grid[2]=a.gridZ;r.block[0]=a.blockX;r.block[1]=a.blockY;r.block[2]=a.blockZ;
            text(r.name,a.name);break;}
        case CUPTI_ACTIVITY_KIND_MEMCPY: {
            auto& a=*reinterpret_cast<const CUpti_ActivityMemcpy5*>(raw);r.kind=Record::MEMCPY;
            r.start=a.start;r.end=a.end;r.correlation=a.correlationId;r.runtime_correlation=a.runtimeCorrelationId;
            r.device=a.deviceId;r.context=a.contextId;r.stream=a.streamId;r.bytes=a.bytes;
            r.copy_kind=a.copyKind;r.src_kind=a.srcKind;r.dst_kind=a.dstKind;r.graph=a.graphId;r.graph_node=a.graphNodeId;break;}
        case CUPTI_ACTIVITY_KIND_MEMSET: {
            auto& a=*reinterpret_cast<const CUpti_ActivityMemset4*>(raw);r.kind=Record::MEMSET;
            r.start=a.start;r.end=a.end;r.correlation=a.correlationId;r.device=a.deviceId;r.context=a.contextId;r.stream=a.streamId;
            r.bytes=a.bytes;r.value=a.value;r.graph=a.graphId;r.graph_node=a.graphNodeId;break;}
        case CUPTI_ACTIVITY_KIND_SYNCHRONIZATION: {
            auto& a=*reinterpret_cast<const CUpti_ActivitySynchronization*>(raw);r.kind=Record::SYNC;
            r.start=a.start;r.end=a.end;r.correlation=a.correlationId;r.context=a.contextId;r.stream=a.streamId;
            r.flags=static_cast<uint32_t>(a.type);r.event=a.cudaEventId;break;}
        case CUPTI_ACTIVITY_KIND_STREAM: {
            auto& a=*reinterpret_cast<const CUpti_ActivityStream*>(raw);r.kind=Record::STREAM;
            r.context=a.contextId;r.stream=a.streamId;r.flags=static_cast<uint32_t>(a.flag);r.correlation=a.correlationId;break;}
        case CUPTI_ACTIVITY_KIND_CONTEXT: {
            auto& a=*reinterpret_cast<const CUpti_ActivityContext2*>(raw);r.kind=Record::CONTEXT;
            r.context=a.contextId;r.device=a.deviceId;r.stream=a.nullStreamId;r.flags=a.isGreenContext;break;}
        case CUPTI_ACTIVITY_KIND_CUDA_EVENT: {
            auto& a=*reinterpret_cast<const CUpti_ActivityCudaEvent*>(raw);r.kind=Record::CUDA_EVENT;
            r.correlation=a.correlationId;r.context=a.contextId;r.stream=a.streamId;r.event=a.eventId;break;}
        default:++errors;return;
        }
        ++record_count;
    }
    bool closed()const {
        for(size_t i=0;i<thread_count;++i)if(threads[i].depth)return false;return true;
    }
};
}
