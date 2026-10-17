// Real Detours execution on a Host replacement. No CUDA DLL or device program.
#include "recorder.h"
#include <iostream>
#include <thread>
#include <string>
#include <stdexcept>
template<class T>T symbol(HMODULE m,const char* n) {auto p=GetProcAddress(m,n);if(!p)throw std::runtime_error(n);return reinterpret_cast<T>(p);}
struct HostFacts {std::uint64_t count;std::uintptr_t ptr,stream;int value,calls;DWORD entry_error;};
int main(int argc,char** argv) {
    try {
        if(argc!=2)return 2;std::string mode=argv[1];
        HMODULE target=LoadLibraryW(L"host_target.dll"),rec=LoadLibraryW(L"prefill_host_recorder.dll");
        if(!target||!rec)throw std::runtime_error("LOAD");
        const auto start=symbol<StartFn>(rec,"ep_prefill_start");
        if(mode=="wrong_entry") {const bool rejected=start(GetModuleHandleW(L"kernel32.dll"),"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")==ERROR_INVALID_ADDRESS;
            std::cout<<"{\"attach_rejected\":"<<(rejected?"true":"false")<<",\"cuda_module_loaded\":false}";return rejected?0:2;}
        auto fn=symbol<MemsetFn>(target,"EpHostMemset");auto facts=symbol<HostFacts* (*)()>(target,"EpHostFacts")();
        if(start(target,"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"))throw std::runtime_error("START");
        fn(nullptr,0,0,nullptr);const bool before=facts->calls==1;
        if(symbol<StopFn>(rec,"ep_prefill_begin")())throw std::runtime_error("BEGIN");
        if(mode=="failed")symbol<void (*)(int)>(target,"EpHostResult")(1);
        if(mode=="reentry")symbol<void (*)(MemsetFn)>(target,"EpHostReenter")(fn);
        const int n=mode=="overflow"?4097:mode=="foreign"?1:3;
        bool errors=true;
        const std::uint64_t counts[]={0,64,(1ULL<<63)+7};
        auto call=[&](int i) {SetLastError(1234);fn(reinterpret_cast<void*>(static_cast<std::uintptr_t>((i%2)?0x2222:0x1111)),123,
            static_cast<size_t>(counts[i%3]),reinterpret_cast<cudaStream_t>(0));errors=errors&&GetLastError()==31337;};
        if(mode=="foreign") {std::thread worker([&](){call(0);});worker.join();}else for(int i=0;i<n;++i)call(i);
        if(symbol<StopFn>(rec,"ep_prefill_end")())throw std::runtime_error("END");
        unsigned used=0;LONG fault=0;auto r=symbol<RecordsFn>(rec,"ep_prefill_records")(&used,&fault);
        if(symbol<StopFn>(rec,"ep_prefill_stop")())throw std::runtime_error("STOP");
        fn(nullptr,0,0,nullptr);
        const bool cuda=GetModuleHandleW(L"nvcuda.dll")||GetModuleHandleW(L"cudart64_12.dll");
        std::cout<<"{\"used\":"<<used<<",\"fault\":"<<fault<<",\"outside_calls_preserved\":"<<(before?"true":"false")
            <<",\"forward_calls_exact\":"<<(facts->calls==n+2+(mode=="reentry"?1:0)?"true":"false")
            <<",\"last_error_preserved\":"<<(errors?"true":"false")<<",\"cuda_module_loaded\":"<<(cuda?"true":"false");
        for(const char* field:{"call_ids","counts","aliases","returns"}) {
            std::cout<<",\""<<field<<"\":[";
            for(unsigned i=0;i<used && i<3;++i) {if(i)std::cout<<',';
                const std::string f=field;if(f=="call_ids")std::cout<<r[i].call_id;
                else if(f=="counts")std::cout<<r[i].count;else if(f=="aliases")std::cout<<r[i].pointer_alias;else std::cout<<r[i].return_code;}
            std::cout<<']';
        }
        std::cout<<'}';return 0;
    }catch(const std::exception& e){std::cerr<<e.what();return 2;}
}
