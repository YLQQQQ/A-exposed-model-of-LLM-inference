// Executes ONLY our CPU DLL through a genuine Detours trampoline.
#include "recorder.h"
#include <tlhelp32.h>
#include <iostream>
#include <string>
#include <filesystem>
#include <stdexcept>

template<class T> T symbol(HMODULE m,const char* n) {
    auto p=GetProcAddress(m,n); if (!p) throw std::runtime_error(n); return reinterpret_cast<T>(p);
}
struct HostFacts { std::uint64_t count; std::uintptr_t ptr,stream; int value,calls; DWORD entry_error; };
int main(int argc,char** argv) {
    try {
        if (argc!=2) return 2;
        auto root=std::filesystem::current_path();
        auto target=LoadLibraryExW((root/L"host_target.dll").c_str(),nullptr,LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR|LOAD_LIBRARY_SEARCH_DEFAULT_DIRS);
        auto recorder=LoadLibraryExW((root/L"host_recorder.dll").c_str(),nullptr,LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR|LOAD_LIBRARY_SEARCH_DEFAULT_DIRS);
        if (!target || !recorder) throw std::runtime_error("CPU_DLL_LOAD");
        auto fn=symbol<MemsetFn>(target,"EpHostMemset");
        auto facts=symbol<HostFacts* (*)()>(target,"EpHostFacts")();
        const std::string mode=argv[1];
        if(mode=="wrong_entry") {
            const LONG rc=symbol<StartFn>(recorder,"ep_start")(GetModuleHandleW(L"kernel32.dll"),"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa");
            std::cout<<"{\"attach_rejected\":"<<(rc==ERROR_INVALID_ADDRESS?"true":"false")<<"}\n";
            return rc==ERROR_INVALID_ADDRESS ? 0 : 2;
        }
        if (mode!="zero" && mode!="positive" && mode!="large" && mode!="failed" && mode!="reentry") return 2;
        const std::uint64_t count=mode=="zero" ? 0 : mode=="large" ? (1ULL<<63)+7 : 64;
        symbol<void (*)(int)>(target,"EpHostResult")(mode=="failed" ? 1 : 0);
        if (symbol<StartFn>(recorder,"ep_start")(target,"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa") ||
            symbol<ArmFn>(recorder,"ep_arm")(1)) throw std::runtime_error("CPU_ATTACH_ARM");
        if(mode=="reentry") symbol<void (*)(MemsetFn)>(target,"EpHostReenter")(fn);
        SetLastError(1234);
        const auto rc=fn(reinterpret_cast<void*>(0x1234),123,static_cast<size_t>(count),reinterpret_cast<cudaStream_t>(0x12345678));
        const auto error=GetLastError();
        unsigned n=0; LONG fault=0; auto r=symbol<RecordsFn>(recorder,"ep_records")(&n,&fault);
        const LONG detach=symbol<StopFn>(recorder,"ep_stop")();
        if (n!=1 || fault!=(mode=="reentry"?3:0) || detach) throw std::runtime_error("CPU_RECORD_OR_DETACH");
        const int calls=facts->calls; const DWORD entry=facts->entry_error;
        const auto targetCount=facts->count; const auto targetStream=facts->stream;
        const bool pointer=facts->ptr==0x1234; const int value=facts->value;
        fn(nullptr,0,0,nullptr); // after detach, direct original call
        bool cuda=false;
        auto snapshot=CreateToolhelp32Snapshot(TH32CS_SNAPMODULE,GetCurrentProcessId());
        if (snapshot==INVALID_HANDLE_VALUE) throw std::runtime_error("MODULE_SNAPSHOT");
        MODULEENTRY32W module{}; module.dwSize=sizeof(module);
        if (Module32FirstW(snapshot,&module)) do {
            std::wstring name(module.szModule);
            for (auto& ch:name) ch=static_cast<wchar_t>(towlower(ch));
            if (name.find(L"cudart")!=std::wstring::npos || name.find(L"nvcuda")!=std::wstring::npos || name.find(L"cupti")!=std::wstring::npos) cuda=true;
        } while (Module32NextW(snapshot,&module));
        CloseHandle(snapshot);
        std::cout << "{\"actual_target_calls\":"<<calls<<",\"count\":"<<r[0].count
            <<",\"actual_target_count\":"<<targetCount<<",\"actual_target_stream_hex\":\""<<std::hex<<targetStream<<std::dec<<"\""
            <<",\"return_code\":"<<static_cast<int>(rc)<<",\"target_entry_last_error\":"<<entry
            <<",\"caller_last_error\":"<<error<<",\"return_last_error\":"<<r[0].return_error
            <<",\"native_stream_hex\":\""<<std::hex<<r[0].stream<<std::dec
            <<"\",\"forwarded_pointer_matches\":"<<(pointer?"true":"false")
            <<",\"forwarded_value\":"<<value<<",\"detach_code\":"<<detach
            <<",\"after_detach_calls\":"<<facts->calls<<",\"recorder_error\":"<<fault
            <<",\"cuda_module_loaded\":"<<(cuda?"true":"false")<<"}\n";
        return 0;
    } catch (const std::exception& e) { std::cerr<<e.what()<<"\n"; return 2; }
}
