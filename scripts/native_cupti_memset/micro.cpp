// Standalone API22 client. Never launched by Stage A. No Torch, Nsight or hooks.
#define NOMINMAX
#include "core.h"
#include <windows.h>
#include <bcrypt.h>
#include <atomic>
#include <fstream>
#include <iomanip>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <vector>

namespace {
using namespace ep_cupti;
void need(bool ok,const char* why) {if(!ok)throw std::runtime_error(why);}
std::string utf8(const std::wstring& w) {
    if(w.empty())return {};
    int n=WideCharToMultiByte(CP_UTF8,WC_ERR_INVALID_CHARS,w.data(),static_cast<int>(w.size()),nullptr,0,nullptr,nullptr);
    need(n>0,"UTF8");std::string s(static_cast<size_t>(n),'\0');
    need(WideCharToMultiByte(CP_UTF8,WC_ERR_INVALID_CHARS,w.data(),static_cast<int>(w.size()),s.data(),n,nullptr,nullptr)==n,"UTF8");return s;
}
std::string hash_file(const std::wstring& path) {
    BCRYPT_ALG_HANDLE alg=nullptr;BCRYPT_HASH_HANDLE h=nullptr;
    need(BCryptOpenAlgorithmProvider(&alg,BCRYPT_SHA256_ALGORITHM,nullptr,0)==0,"SHA_OPEN");
    DWORD bytes=0,obj_size=0;
    need(BCryptGetProperty(alg,BCRYPT_OBJECT_LENGTH,reinterpret_cast<PUCHAR>(&obj_size),sizeof(obj_size),&bytes,0)==0,"SHA_SIZE");
    std::vector<UCHAR> object(obj_size);UCHAR result[32]{};
    need(BCryptCreateHash(alg,&h,object.data(),obj_size,nullptr,0,0)==0,"SHA_CREATE");
    std::ifstream f(path,std::ios::binary);need(f.good(),"SHA_FILE");char block[65536];
    while(f.read(block,sizeof(block)) || f.gcount())
        need(BCryptHashData(h,reinterpret_cast<PUCHAR>(block),static_cast<ULONG>(f.gcount()),0)==0,"SHA_DATA");
    need(f.eof() && BCryptFinishHash(h,result,32,0)==0,"SHA_FINISH");
    BCryptDestroyHash(h);BCryptCloseAlgorithmProvider(alg,0);
    std::ostringstream o;for(auto c:result)o<<std::hex<<std::setw(2)<<std::setfill('0')<<static_cast<unsigned>(c);
    return o.str();
}
HMODULE load_exact(const std::wstring& path) {
    need(path.size()>3 && path[1]==L':',"DLL_ABSOLUTE_PATH");
    HMODULE m=LoadLibraryExW(path.c_str(),nullptr,LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR|LOAD_LIBRARY_SEARCH_SYSTEM32);
    need(m!=nullptr,"DLL_LOAD");wchar_t actual[32768]{};
    need(GetModuleFileNameW(m,actual,32768)>0 && _wcsicmp(path.c_str(),actual)==0,"DLL_LOADED_PATH");return m;
}
template<class F> F symbol(HMODULE m,const char* name) {
    auto p=GetProcAddress(m,name);need(p!=nullptr,name);return reinterpret_cast<F>(p);
}
struct Client {
    Core core;
    decltype(&cuptiActivityGetNextRecord) next=nullptr;
    decltype(&cuptiActivityGetNumDroppedRecords) dropped=nullptr;
    static constexpr size_t BUFFER_COUNT=8,BUFFER_BYTES=65536;
    struct Buffer {alignas(8) std::uint8_t data[BUFFER_BYTES]{};std::atomic<bool> busy{false};};
    std::array<Buffer,BUFFER_COUNT> buffers{};
    std::atomic<unsigned> exhausted{0},errors{0},queries{0},query_errors{0};
    std::atomic<std::uint64_t> lost{0};
    static Client* current;
    static void CUPTIAPI callback(void*,CUpti_CallbackDomain domain,CUpti_CallbackId id,const void* raw) {
        const DWORD saved=GetLastError();
        if(!raw) {std::lock_guard<std::mutex> lock(current->core.mutex);++current->core.error;}
        else current->core.callback(domain,id,*static_cast<const CUpti_CallbackData*>(raw),GetCurrentProcessId(),GetCurrentThreadId());
        SetLastError(saved);
    }
    static void CUPTIAPI request(std::uint8_t** data,size_t* size,size_t* max_records) {
        *data=nullptr;*size=0;*max_records=0;
        for(auto& b:current->buffers) {
            bool available=false;
            if(b.busy.compare_exchange_strong(available,true)) {*data=b.data;*size=BUFFER_BYTES;return;}
        }
        ++current->exhausted;
    }
    void query_loss(CUcontext ctx,uint32_t stream) {
        size_t n=0;const auto code=dropped(ctx,stream,&n);++queries;
        if(code!=CUPTI_SUCCESS)++query_errors;else lost.fetch_add(n);
    }
    static void CUPTIAPI complete(CUcontext ctx,uint32_t stream,std::uint8_t* data,size_t,size_t valid) {
        auto& self=*current;bool owned=false;
        for(auto& b:self.buffers)if(b.data==data) {
            owned=b.busy.load();if(!owned){++self.errors;return;}
            if(valid>BUFFER_BYTES) {++self.errors;b.busy=false;return;}
            CUpti_Activity* record=nullptr;CUptiResult code=CUPTI_SUCCESS;
            while((code=self.next(data,valid,&record))==CUPTI_SUCCESS)self.core.activity(record);
            if(code!=CUPTI_ERROR_MAX_LIMIT_REACHED)++self.errors;
            self.query_loss(ctx,stream);b.busy=false;break;
        }
        if(!owned)++self.errors;
    }
};
Client* Client::current=nullptr;
struct Life {int subscribe=-1,register_buffers=-1,enable=-1,flush=-1,disable=-1,unsubscribe=-1,finalize=-1;};
struct Reference {std::array<unsigned char,64> bytes{};bool ok=false;};
void json_write(std::ostream& o,Client& s,const Life& life,const std::string& run,const std::string& rt_hash,
                const std::string& cp_hash,int rv,uint32_t cv,uint32_t uid,uint32_t sid,uint32_t device,
                CUcontext ctx,cudaStream_t stream,const std::array<Reference,2>& refs,const std::string& error,
                const std::wstring& runtime_path,const std::wstring& cupti_path,
                const char* source="TARGET_GPU") {
    unsigned outstanding=0;for(const auto& b:s.buffers)if(b.busy)++outstanding;
    o<<"{\"schema_version\":\"independent-cupti-memset/0.1.0\",\"source\":\""<<source<<"\","
     <<"\"role\":\"ENGINEERING_PARAMETER_DIAGNOSTIC\",\"run_id\":"<<std::quoted(run)
     <<",\"pid\":"<<GetCurrentProcessId()<<",\"tid\":"<<GetCurrentThreadId()
     <<",\"clock\":\"CUPTI_TIMESTAMP_NS\",\"runtime_version\":"<<rv<<",\"cupti_api_version\":"<<cv
     <<",\"callback_names\":{\"ordinary\":"<<std::quoted(s.core.ordinary_name)
     <<",\"ptsz\":"<<std::quoted(s.core.ptsz_name)<<"},\"callback_name_source\":"
     <<std::quoted(std::string(source)=="TARGET_GPU"?"CUPTI_GET_CALLBACK_NAME":"HOST_CALLBACK_DOUBLE")
     <<",\"runtime_sha256\":"<<std::quoted(rt_hash)<<",\"cupti_sha256\":"<<std::quoted(cp_hash)
     <<",\"runtime_loaded_path\":"<<std::quoted(utf8(runtime_path))
     <<",\"cupti_loaded_path\":"<<std::quoted(utf8(cupti_path))<<",\"error\":"<<std::quoted(error)
     <<",\"lifecycle\":{\"subscribe\":"<<life.subscribe<<",\"register_buffers\":"<<life.register_buffers
     <<",\"enable\":"<<life.enable<<",\"flush\":"<<life.flush<<",\"disable\":"<<life.disable
     <<",\"unsubscribe\":"<<life.unsubscribe<<",\"finalize\":"<<life.finalize
     <<",\"closed\":"<<(life.unsubscribe==0 && life.finalize==0?"true":"false")<<'}'
     <<",\"loss\":{\"callback_overflow\":"<<s.core.callback_overflow
     <<",\"activity_overflow\":"<<s.core.activity_overflow<<",\"callback_error\":"<<s.core.error
     <<",\"activity_error\":"<<s.errors.load()<<",\"buffer_exhaustion\":"<<s.exhausted.load()
     <<",\"dropped_records\":"<<s.lost.load()<<",\"dropped_queries\":"<<s.queries.load()
     <<",\"dropped_query_errors\":"<<s.query_errors.load()<<",\"outstanding_buffers\":"<<outstanding<<'}'
     <<",\"stream_binding\":{\"context_uid\":"<<uid<<",\"native_context\":";
    hex(o,reinterpret_cast<std::uintptr_t>(ctx));o<<",\"native_stream\":";hex(o,reinterpret_cast<std::uintptr_t>(stream));
    o<<",\"stream_id\":"<<sid<<",\"device_id\":"<<device<<",\"query_status\":"<<(uid && sid?0:-1)<<'}'
     <<",\"callbacks\":";write_calls(o,s.core);o<<",\"api_records\":[";
    for(size_t i=0;i<s.core.api_count;++i) {
        const auto& a=s.core.apis[i];if(i)o<<',';
        o<<"{\"domain\":\""<<(a.runtime?"RUNTIME":"DRIVER")<<"\",\"cbid\":"<<a.value.cbid
         <<",\"correlation_id\":"<<a.value.correlationId<<",\"pid\":"<<a.value.processId
         <<",\"tid\":"<<a.value.threadId<<",\"start\":"<<a.value.start<<",\"end\":"<<a.value.end
         <<",\"return_value\":"<<a.value.returnValue<<'}';
    }
    o<<"],\"effects\":[";
    for(size_t i=0;i<s.core.effect_count;++i) {
        const auto& e=s.core.effects[i];if(i)o<<',';
        o<<"{\"record_id\":\"memset:"<<i+1<<"\",\"correlation_domain\":\"DRIVER\",\"correlation_id\":"<<e.correlationId
         <<",\"context_uid\":"<<e.contextId<<",\"stream_id\":"<<e.streamId<<",\"device_id\":"<<e.deviceId
         <<",\"bytes\":"<<e.bytes<<",\"value\":"<<e.value<<",\"start\":"<<e.start<<",\"end\":"<<e.end
         <<",\"graph_id\":"<<e.graphId<<'}';
    }
    o<<"],\"references\":[";
    for(size_t i=0;i<2;++i) {
        if(i)o<<',';o<<"{\"case_index\":"<<i<<",\"count\":"<<(i?64:0)<<",\"value\":123,\"success\":"
            <<(refs[i].ok?"true":"false")<<",\"readback\":[";
        for(size_t j=0;j<64;++j) {if(j)o<<',';o<<static_cast<unsigned>(refs[i].bytes[j]);}o<<"]}";
    }o<<"]}\n";
}
}

int wmain(int argc,wchar_t** argv) {
    if(argc!=8 || std::wstring(argv[1])!=L"--run-reviewed-gpu-micro")return 2;
    const std::wstring rt_path=argv[2],cp_path=argv[3],out=argv[5];
    const std::string run=utf8(argv[4]),rt_expected=utf8(argv[6]),cp_expected=utf8(argv[7]);
    if(run.empty() || run.find_first_not_of("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")!=std::string::npos)return 2;
    if(GetFileAttributesW(out.c_str())!=INVALID_FILE_ATTRIBUTES)return 2;
    // Only this explicit B binary entry may load vendor libraries or initialize CUDA.
    auto client=std::make_unique<Client>();Client::current=client.get();Life life;
    CUpti_SubscriberHandle subscriber=nullptr;HMODULE cp=nullptr,rt=nullptr;
    decltype(&cuptiUnsubscribe) unsub=nullptr;decltype(&cuptiFinalize) finalize=nullptr;
    decltype(&cuptiActivityDisable) disable=nullptr;decltype(&cuptiActivityFlushAll) flush=nullptr;
    const CUpti_ActivityKind kinds[]={CUPTI_ACTIVITY_KIND_RUNTIME,CUPTI_ACTIVITY_KIND_DRIVER,CUPTI_ACTIVITY_KIND_MEMSET};
    size_t enabled=0;std::array<Reference,2> refs{};std::string error,rt_hash,cp_hash;
    int rv=0;uint32_t cv=0,uid=0,sid=0,device=0;CUcontext context=nullptr;cudaStream_t stream=nullptr;void* ptr=nullptr;
    try {
        for(const auto* key:{L"CUDA_INJECTION64_PATH",L"NVTX_INJECTION64_PATH",L"NV_COMPUTE_PROFILER_INJECTION_PATH"})
            need(GetEnvironmentVariableW(key,nullptr,0)==0,"EXTERNAL_PROFILER_ENVIRONMENT");
        need(GetModuleHandleW(L"torch_cuda.dll")==nullptr && GetModuleHandleW(L"kineto.dll")==nullptr,
            "MODEL_OR_PROFILER_CLIENT_NOT_ALLOWED");
        need(rt_expected.size()==64 && cp_expected.size()==64,"EXPECTED_FILE_HASH");
        rt_hash=hash_file(rt_path);cp_hash=hash_file(cp_path);
        need(rt_hash==rt_expected && cp_hash==cp_expected,"DLL_HASH_CONFLICT");
        need(GetModuleHandleW(L"cupti64_129.dll")==nullptr && GetModuleHandleW(L"cupti64_2024.1.1.dll")==nullptr,
            "EXISTING_CUPTI_CLIENT");
        cp=load_exact(cp_path);
#define CP(name) symbol<decltype(&name)>(cp,#name)
        need(CP(cuptiGetVersion)(&cv)==CUPTI_SUCCESS && cv==22,"CUPTI_VERSION");
        const char* ordinary=nullptr;const char* ptsz=nullptr;
        need(CP(cuptiGetCallbackName)(CUPTI_CB_DOMAIN_RUNTIME_API,51,&ordinary)==CUPTI_SUCCESS && ordinary &&
            std::strlen(ordinary)<128,"CALLBACK_NAME_ORDINARY");
        need(CP(cuptiGetCallbackName)(CUPTI_CB_DOMAIN_RUNTIME_API,235,&ptsz)==CUPTI_SUCCESS && ptsz &&
            std::strlen(ptsz)<128,"CALLBACK_NAME_PTSZ");
        client->core.ordinary_name=ordinary;client->core.ptsz_name=ptsz;
        unsub=CP(cuptiUnsubscribe);finalize=CP(cuptiFinalize);disable=CP(cuptiActivityDisable);flush=CP(cuptiActivityFlushAll);
        client->next=CP(cuptiActivityGetNextRecord);client->dropped=CP(cuptiActivityGetNumDroppedRecords);
        life.subscribe=static_cast<int>(CP(cuptiSubscribe)(&subscriber,Client::callback,nullptr));
        need(life.subscribe==0,"SUBSCRIBER_CONFLICT_OR_INIT_FAILURE");
        life.register_buffers=static_cast<int>(CP(cuptiActivityRegisterCallbacks)(Client::request,Client::complete));
        need(life.register_buffers==0,"REGISTER_BUFFERS");
        need(CP(cuptiSetThreadIdType)(CUPTI_ACTIVITY_THREAD_ID_TYPE_SYSTEM)==CUPTI_SUCCESS,"THREAD_ID_TYPE");
        rt=load_exact(rt_path);
#define RT(name) symbol<decltype(&name)>(rt,#name)
        need(RT(cudaRuntimeGetVersion)(&rv)==cudaSuccess && rv==12040,"RUNTIME_VERSION");
        need(RT(cudaSetDevice)(0)==cudaSuccess,"SET_DEVICE");
        need(RT(cudaStreamCreateWithFlags)(&stream,cudaStreamNonBlocking)==cudaSuccess,"STREAM_CREATE");
        need(RT(cudaMalloc)(&ptr,64)==cudaSuccess,"ALLOCATE");
        std::array<unsigned char,64> initial{};initial.fill(58);
        need(RT(cudaMemcpy)(ptr,initial.data(),64,cudaMemcpyHostToDevice)==cudaSuccess,"INITIALIZE_BUFFER");
        HMODULE driver=LoadLibraryExW(L"nvcuda.dll",nullptr,LOAD_LIBRARY_SEARCH_SYSTEM32);need(driver!=nullptr,"DRIVER_LOAD");
        need(symbol<decltype(&cuCtxGetCurrent)>(driver,"cuCtxGetCurrent")(&context)==CUDA_SUCCESS && context,"CURRENT_CONTEXT");
        need(CP(cuptiGetContextId)(context,&uid)==CUPTI_SUCCESS,"CONTEXT_ID");
        need(CP(cuptiGetDeviceId)(context,&device)==CUPTI_SUCCESS,"DEVICE_ID");
        need(CP(cuptiGetStreamIdEx)(context,reinterpret_cast<CUstream>(stream),0,&sid)==CUPTI_SUCCESS,"STREAM_ID");
        // The predeclared target scope begins after initialization, not during CUDA startup.
        for(auto id:{CUPTI_RUNTIME_TRACE_CBID_cudaMemsetAsync_v3020,CUPTI_RUNTIME_TRACE_CBID_cudaMemsetAsync_ptsz_v7000})
            need(CP(cuptiEnableCallback)(1,subscriber,CUPTI_CB_DOMAIN_RUNTIME_API,id)==CUPTI_SUCCESS,"ENABLE_RUNTIME_CALLBACK");
        need(CP(cuptiEnableDomain)(1,subscriber,CUPTI_CB_DOMAIN_DRIVER_API)==CUPTI_SUCCESS,"ENABLE_DRIVER_CALLBACK");
        for(auto kind:kinds) {
            life.enable=static_cast<int>(CP(cuptiActivityEnable)(kind));
            need(life.enable==0,"ACTIVITY_ENABLE");++enabled;
        }
        for(size_t i=0;i<2;++i) {
            const auto code=RT(cudaMemsetAsync)(ptr,123,i?64:0,stream);
            need(code==cudaSuccess,"TARGET_RETURN");
            need(RT(cudaStreamSynchronize)(stream)==cudaSuccess,"CASE_COMPLETION");
            need(RT(cudaMemcpy)(refs[i].bytes.data(),ptr,64,cudaMemcpyDeviceToHost)==cudaSuccess,"READBACK");
            refs[i].ok=true;
            for(auto b:refs[i].bytes)if(b!=(i?123:58))refs[i].ok=false;
            need(refs[i].ok,"READBACK_MISMATCH");
        }
        // Context, stream and allocation stay alive through flush/drop queries.
    } catch(const std::exception& e) {error=e.what();}
    if(life.subscribe==0) {
        if(flush)life.flush=static_cast<int>(flush(CUPTI_ACTIVITY_FLAG_FLUSH_FORCED));
        if(client->dropped)client->query_loss(nullptr,0);
        life.disable=0;
        while(enabled) {const auto c=disable(kinds[--enabled]);if(c!=CUPTI_SUCCESS)life.disable=static_cast<int>(c);}
        // Disable can enqueue records; drain them once more before closing the subscription.
        if(flush) {const auto c=flush(CUPTI_ACTIVITY_FLAG_FLUSH_FORCED);if(c!=CUPTI_SUCCESS)life.flush=static_cast<int>(c);}
        if(client->dropped)client->query_loss(nullptr,0);
        if(rt) {
            if(ptr && RT(cudaFree)(ptr)!=cudaSuccess)error="FREE_BUFFER";
            if(stream && RT(cudaStreamDestroy)(stream)!=cudaSuccess)error="STREAM_DESTROY";
        }
        life.unsubscribe=static_cast<int>(unsub(subscriber));life.finalize=static_cast<int>(finalize());
    }
    try {if(!rt_hash.empty())need(hash_file(rt_path)==rt_hash,"RUNTIME_CHANGED");
         if(!cp_hash.empty())need(hash_file(cp_path)==cp_hash,"CUPTI_CHANGED");}
    catch(const std::exception& e) {error=e.what();}
    std::ostringstream text;json_write(text,*client,life,run,rt_hash,cp_hash,rv,cv,uid,sid,device,
        context,stream,refs,error,rt_path,cp_path);const auto bytes=text.str();
    HANDLE f=CreateFileW(out.c_str(),GENERIC_WRITE,0,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);
    if(f==INVALID_HANDLE_VALUE)return 2;DWORD written=0;
    const bool saved=WriteFile(f,bytes.data(),static_cast<DWORD>(bytes.size()),&written,nullptr)!=0 && written==bytes.size();
    CloseHandle(f);
    return saved && error.empty() && life.finalize==0 && life.flush==0 && life.unsubscribe==0 &&
        client->core.error==0 && client->core.depth==0 && client->exhausted==0 && client->errors==0 &&
        client->lost==0 && client->query_errors==0 && !client->core.callback_overflow && !client->core.activity_overflow?0:2;
}
