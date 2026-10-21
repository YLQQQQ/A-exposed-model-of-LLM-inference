// Explicit same-process client. Loading the DLL alone does not initialize CUDA.
#include "writer.h"
#include <windows.h>
#include <atomic>
#include <memory>
#include <set>
#include <sstream>
#include <stdexcept>

namespace {
using namespace ep_timeline;
struct Client {
    Core core;StartupLog startup,shutdown;HMODULE module=nullptr;CUpti_SubscriberHandle subscriber=nullptr;
    std::string session;bool owns=false,closed=false;size_t enabled=0;
    std::atomic<unsigned> errors{0},query_errors{0};std::atomic<uint64_t> dropped_count{0};
    static constexpr size_t N=16,B=1024*1024;
    struct Buffer {alignas(8) std::array<uint8_t,B> data{};std::atomic<bool> busy{false};};
    std::array<Buffer,N> buffers{};
    std::set<std::pair<uint32_t,uint32_t>> queried;std::mutex loss_mutex;
    decltype(&cuptiActivityGetNextRecord) next=nullptr;
    decltype(&cuptiActivityGetNumDroppedRecords) dropped=nullptr;
    decltype(&cuptiGetTimestamp) timestamp=nullptr;
    decltype(&cuptiGetDeviceId) device_id=nullptr;
    decltype(&cuptiGetStreamIdEx) stream_id=nullptr;
    decltype(&cuptiActivityDisable) disable=nullptr;
    decltype(&cuptiActivityFlushAll) flush=nullptr;
    decltype(&cuptiUnsubscribe) unsubscribe=nullptr;
    decltype(&cuptiFinalize) finalize=nullptr;
    uint64_t now(){uint64_t t=0;if(!timestamp || timestamp(&t)!=CUPTI_SUCCESS)++errors;return t;}
    void loss(CUcontext ctx,uint32_t stream,uint32_t context_id) {
        size_t n=0;const auto code=dropped(ctx,stream,&n);
        if(code!=CUPTI_SUCCESS){++query_errors;return;}
        dropped_count.fetch_add(n);std::lock_guard<std::mutex> lock(loss_mutex);queried.insert({context_id,stream});
    }
};
std::unique_ptr<Client> client;
template<class F>F symbol(Client& c,const char* n){
    auto p=GetProcAddress(c.module,n);
    if(!p){const auto error=GetLastError();c.startup.record("GetProcAddress","WIN32",error,false,-1,n);throw std::runtime_error(n);}
    return reinterpret_cast<F>(p);
}
void CUPTIAPI callback(void*,CUpti_CallbackDomain domain,CUpti_CallbackId id,const void* data) {
    const auto saved=GetLastError();auto& c=*client;
    if(!data){++c.errors;return;}
    const auto& d=*static_cast<const CUpti_CallbackData*>(data);
    const auto i=c.core.callback(domain,id,d,GetCurrentProcessId(),GetCurrentThreadId(),c.now());
    if(d.callbackSite==CUPTI_API_ENTER && i!=SIZE_MAX) {
        // CUPTI queries only; never call a CUDA API or synchronize in a callback.
        Call local;
        {std::lock_guard<std::mutex> lock(c.core.mutex);local=c.core.calls[i];}
        if(local.params && d.context) {
            uint32_t device=0,stream=0;
            auto status=c.device_id(d.context,&device);
            if(status==CUPTI_SUCCESS)status=c.stream_id(d.context,reinterpret_cast<CUstream>(static_cast<uintptr_t>(local.native_stream)),local.ptsz?1:0,&stream);
            c.core.bind(i,device,stream,static_cast<int>(status));
        }
    }
    SetLastError(saved);
}
void CUPTIAPI request(uint8_t** ptr,size_t* size,size_t* max) {
    *ptr=nullptr;*size=0;*max=0;
    for(auto& b:client->buffers){bool available=false;if(b.busy.compare_exchange_strong(available,true)){*ptr=b.data.data();*size=Client::B;return;}}
    ++client->errors;std::lock_guard<std::mutex> lock(client->core.mutex);++client->core.overflow;
}
void CUPTIAPI complete(CUcontext ctx,uint32_t stream,uint8_t* data,size_t,size_t valid) {
    auto& c=*client;
    for(auto& b:c.buffers)if(b.data.data()==data) {
        if(!b.busy || valid>Client::B){++c.errors;return;}
        CUpti_Activity* record=nullptr;CUptiResult status;
        while((status=c.next(data,valid,&record))==CUPTI_SUCCESS)c.core.activity(record);
        if(status!=CUPTI_ERROR_MAX_LIMIT_REACHED)++c.errors;
        // This per-buffer query is supplemented by every observed context/stream.
        size_t n=0;if(c.dropped(ctx,stream,&n)==CUPTI_SUCCESS)c.dropped_count.fetch_add(n);else ++c.query_errors;
        b.busy=false;return;
    }
    ++c.errors;
}
void need(Client& c,const char* operation,CUptiResult code,int kind=-1,const char* detail="") {
    c.startup.record(operation,"CUPTI",static_cast<int>(code),code==CUPTI_SUCCESS,kind,detail);
    if(code!=CUPTI_SUCCESS)throw std::runtime_error("CUPTI_STATUS");
}
void write_new(const wchar_t* path,const std::string& bytes) {
    auto h=CreateFileW(path,GENERIC_WRITE,0,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);
    if(h==INVALID_HANDLE_VALUE)throw std::runtime_error("OUTPUT_EXISTS_OR_UNWRITABLE");
    bool good=true;size_t offset=0;
    while(offset<bytes.size()) {
        DWORD wrote=0;auto n=static_cast<DWORD>((std::min)(bytes.size()-offset,size_t(4*1024*1024)));
        if(!WriteFile(h,bytes.data()+offset,n,&wrote,nullptr) || wrote!=n){good=false;break;}offset+=wrote;
    }
    if(!CloseHandle(h) || !good)throw std::runtime_error("OUTPUT_WRITE");
}
}
extern "C" __declspec(dllexport) int ep_timeline_abi_version(){return 1;}
extern "C" __declspec(dllexport) int ep_timeline_open(const wchar_t* path,const char* session) {
    if(client || !path || !session || !*session)return 1;
    try {
        // No CUPTI coexistence, private Nsight library or automatic injection.
        for(auto name:{L"CUDA_INJECTION64_PATH",L"NVTX_INJECTION64_PATH",L"NV_COMPUTE_PROFILER_INJECTION_PATH"})
            if(GetEnvironmentVariableW(name,nullptr,0))return 2;
        if(GetModuleHandleW(L"cupti64_129.dll"))return 2;
        if(std::wcslen(path)<3 || path[1]!=L':')return 2;
        client=std::make_unique<Client>();auto& c=*client;c.session=session;
        c.module=LoadLibraryExW(path,nullptr,LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR|LOAD_LIBRARY_SEARCH_SYSTEM32);
        c.startup.record("LoadLibraryExW","WIN32",c.module?0:GetLastError(),c.module!=nullptr);
        if(!c.module)throw std::runtime_error("CUPTI_LOAD");
        wchar_t actual[32768]{};
        const auto length=GetModuleFileNameW(c.module,actual,32768);
        c.startup.record("GetModuleFileNameW","WIN32",length?0:GetLastError(),length!=0);
        if(!length)throw std::runtime_error("CUPTI_PATH");
        const bool same_path=_wcsicmp(path,actual)==0;
        c.startup.record("LOADED_CUPTI_PATH","CONTRACT",same_path?0:1,same_path);
        if(!same_path)throw std::runtime_error("CUPTI_PATH");
#define CP(n) symbol<decltype(&n)>(c,#n)
        uint32_t version=0;need(c,"cuptiGetVersion",CP(cuptiGetVersion)(&version));
        c.startup.record("CUPTI_API_VERSION","CONTRACT",version,version==22);
        if(version!=22)throw std::runtime_error("CUPTI_VERSION");
        c.next=CP(cuptiActivityGetNextRecord);c.dropped=CP(cuptiActivityGetNumDroppedRecords);c.timestamp=CP(cuptiGetTimestamp);
        c.device_id=CP(cuptiGetDeviceId);c.stream_id=CP(cuptiGetStreamIdEx);c.disable=CP(cuptiActivityDisable);c.flush=CP(cuptiActivityFlushAll);
        c.unsubscribe=CP(cuptiUnsubscribe);c.finalize=CP(cuptiFinalize);
        need(c,"cuptiSubscribe",CP(cuptiSubscribe)(&c.subscriber,callback,nullptr));c.owns=true;
        need(c,"cuptiSetThreadIdType",CP(cuptiSetThreadIdType)(CUPTI_ACTIVITY_THREAD_ID_TYPE_SYSTEM));
        need(c,"cuptiActivityRegisterCallbacks",CP(cuptiActivityRegisterCallbacks)(request,complete));
        need(c,"cuptiEnableDomain",CP(cuptiEnableDomain)(1,c.subscriber,CUPTI_CB_DOMAIN_RUNTIME_API),-1,"RUNTIME_API");
        need(c,"cuptiEnableDomain",CP(cuptiEnableDomain)(1,c.subscriber,CUPTI_CB_DOMAIN_DRIVER_API),-1,"DRIVER_API");
        for(auto k:explicit_activity_kinds) {
            if(k==CUPTI_ACTIVITY_KIND_CONTEXT || k==CUPTI_ACTIVITY_KIND_STREAM)need(c,"cuptiActivityEnableAndDump",CP(cuptiActivityEnableAndDump)(k),k);
            else need(c,"cuptiActivityEnable",CP(cuptiActivityEnable)(k),k);++c.enabled;
        }
        c.startup.succeeded=true;
        return 0;
    } catch(const std::exception& error) {if(client){++client->errors;client->startup.exception(error.what());}return 3;}
      catch(...) {if(client){++client->errors;client->startup.exception("UNKNOWN_EXCEPTION");}return 3;}
}
extern "C" __declspec(dllexport) int ep_timeline_mark(int action,const char* label) {
    if(!client || !client->owns || client->closed || action<0 || action>2 || !label)return 1;
    try{client->core.marker(action,label,GetCurrentThreadId(),client->now());return 0;}catch(...){++client->errors;return 2;}
}
extern "C" __declspec(dllexport) int ep_timeline_close(const wchar_t* output) {
    if(!client || client->closed || !output)return 1;auto& c=*client;
    try {
        auto closed_call=[&](const char* op,CUptiResult code,int kind=-1) {
            c.shutdown.record(op,"CUPTI",static_cast<int>(code),code==CUPTI_SUCCESS,kind);
            if(code!=CUPTI_SUCCESS)++c.errors;
        };
        if(c.owns) {
            closed_call("cuptiActivityFlushAll",c.flush(0));
            for(size_t i=c.enabled;i>0;--i)closed_call("cuptiActivityDisable",c.disable(explicit_activity_kinds[i-1]),explicit_activity_kinds[i-1]);
            closed_call("cuptiActivityFlushAll",c.flush(0));
            // Match activity context IDs to callback context handles, not stream adjacency.
            std::set<std::pair<uint32_t,uint32_t>> wanted;
            {
                std::lock_guard<std::mutex> lock(c.core.mutex);
                for(size_t i=0;i<c.core.record_count;++i) {
                    const auto& r=c.core.records[i];
                    if(r.kind==Record::KERNEL || r.kind==Record::MEMCPY || r.kind==Record::MEMSET ||
                        (r.kind==Record::SYNC && r.stream!=UINT32_MAX))wanted.insert({r.context,r.stream});
                }
            }
            for(auto scope:wanted) {
                uint64_t handle=0;
                {std::lock_guard<std::mutex> lock(c.core.mutex);
                    for(size_t i=0;i<c.core.call_count;++i)if(c.core.calls[i].context==scope.first && c.core.calls[i].native_context){handle=c.core.calls[i].native_context;break;}}
                if(!handle){++c.query_errors;continue;}
                c.loss(reinterpret_cast<CUcontext>(static_cast<uintptr_t>(handle)),scope.second,scope.first);
            }
            closed_call("cuptiUnsubscribe",c.unsubscribe(c.subscriber));
            closed_call("cuptiFinalize",c.finalize());
            c.closed=true;
        }
        c.shutdown.succeeded=c.closed && c.shutdown.first_failure==SIZE_MAX;
        for(const auto& b:c.buffers)if(b.busy)++c.errors;
        std::vector<std::array<uint32_t,2>> scopes;for(auto s:c.queried)scopes.push_back({s.first,s.second});
        std::ostringstream out;
        {std::lock_guard<std::mutex> lock(c.core.mutex);capture_json(out,c.core,c.session.c_str(),GetCurrentProcessId(),"TARGET_CUPTI",c.closed,c.errors.load(),c.dropped_count.load(),c.query_errors.load(),scopes,&c.startup,&c.shutdown);}
        write_new(output,out.str());return c.closed && c.errors==0 && c.query_errors==0 && c.core.errors==0 && c.core.overflow==0 && c.dropped_count==0 && c.core.closed()?0:4;
    }catch(...){++c.errors;return 5;}
}
