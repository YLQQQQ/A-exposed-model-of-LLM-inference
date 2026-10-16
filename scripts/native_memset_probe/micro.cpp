// Dynamic *shared* CUDART only; this EXE has no cudart/static runtime imports.
// Never executed by local/Stage-A checks. Exactly two armed calls in Stage B.
#include "recorder.h"
#include <cstdlib>
#include <nvtx3/nvToolsExt.h>
#include <array>
#include <cctype>
#include <fstream>
#include <filesystem>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>

template<class T> T load(HMODULE m,const char* n) {
    auto p=GetProcAddress(m,n); if (!p) throw std::runtime_error(std::string("EXPORT:")+n); return reinterpret_cast<T>(p);
}
static void check(cudaError_t v,const char* at) { if (v!=cudaSuccess) throw std::runtime_error(std::string(at)+":"+std::to_string(static_cast<int>(v))); }
static std::string hex(const unsigned char* p,size_t n) { std::ostringstream o; for (size_t i=0;i<n;++i) o<<std::hex<<std::setw(2)<<std::setfill('0')<<static_cast<unsigned>(p[i]); return o.str(); }
static std::string escape(const std::string& s) { std::string v; for(char c:s) { if(c=='\\'||c=='"') v+='\\'; if(static_cast<unsigned char>(c)<32) throw std::runtime_error("JSON_PATH"); v+=c; } return v; }
static std::string utf8(const std::wstring& s) { int n=WideCharToMultiByte(CP_UTF8,WC_ERR_INVALID_CHARS,s.data(),static_cast<int>(s.size()),nullptr,0,nullptr,nullptr); if(n<=0) throw std::runtime_error("UTF8"); std::string r(static_cast<size_t>(n),'\0'); WideCharToMultiByte(CP_UTF8,WC_ERR_INVALID_CHARS,s.data(),static_cast<int>(s.size()),&r[0],n,nullptr,nullptr); return r; }

int wmain(int argc,wchar_t** argv) {
    // argv: runtime_abs recorder_abs run_nonce output_abs UUID PCI (CUDA spelling)
    if(argc!=7) return 2;
    const auto output=std::filesystem::path(argv[4]);
    try {
        const std::filesystem::path runtime(argv[1]), recorderPath(argv[2]);
        if(!runtime.is_absolute() || !recorderPath.is_absolute() || !output.is_absolute() || std::filesystem::exists(output)) throw std::runtime_error("PATH_IDENTITY");
        const std::string run=utf8(argv[3]);
        auto rt=LoadLibraryExW(runtime.c_str(),nullptr,LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR|LOAD_LIBRARY_SEARCH_DEFAULT_DIRS);
        auto dll=LoadLibraryExW(recorderPath.c_str(),nullptr,LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR|LOAD_LIBRARY_SEARCH_DEFAULT_DIRS);
        if(!rt || !dll) throw std::runtime_error("EXPLICIT_DLL_LOAD");
        wchar_t actual[32768]{};
        if(!GetModuleFileNameW(rt,actual,32768) || std::filesystem::path(actual)!=runtime) throw std::runtime_error("RUNTIME_LOADED_PATH");
        int version=0,devices=0;
        check(load<decltype(&cudaRuntimeGetVersion)>(rt,"cudaRuntimeGetVersion")(&version),"VERSION");
        if(version!=12040) throw std::runtime_error("RUNTIME_VERSION");
        check(load<decltype(&cudaGetDeviceCount)>(rt,"cudaGetDeviceCount")(&devices),"DEVICE_COUNT");
        if(devices!=1) throw std::runtime_error("MASK_DEVICE_COUNT");
        check(load<decltype(&cudaSetDevice)>(rt,"cudaSetDevice")(0),"SET_DEVICE");
        cudaDeviceProp prop{};
        check(load<decltype(&cudaGetDeviceProperties)>(rt,"cudaGetDeviceProperties_v2")(&prop,0),"DEVICE_PROPERTIES");
        const std::string u=hex(reinterpret_cast<unsigned char*>(prop.uuid.bytes),16);
        const std::string uuid="GPU-"+u.substr(0,8)+"-"+u.substr(8,4)+"-"+u.substr(12,4)+"-"+u.substr(16,4)+"-"+u.substr(20);
        char pci[64]{};
        check(load<decltype(&cudaDeviceGetPCIBusId)>(rt,"cudaDeviceGetPCIBusId")(pci,64,0),"PCI");
        std::string pciCompare(pci),wantedPci=utf8(argv[6]);
        for(auto& c:pciCompare)c=static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
        for(auto& c:wantedPci)c=static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
        if(uuid!=utf8(argv[5]) || pciCompare!=wantedPci) throw std::runtime_error("GPU_IDENTITY");
        auto alloc=load<decltype(&cudaMalloc)>(rt,"cudaMalloc");
        auto release=load<decltype(&cudaFree)>(rt,"cudaFree");
        auto memset=load<MemsetFn>(rt,"cudaMemsetAsync");
        auto sync=load<decltype(&cudaStreamSynchronize)>(rt,"cudaStreamSynchronize");
        auto copy=load<decltype(&cudaMemcpy)>(rt,"cudaMemcpy");
        auto drain=load<decltype(&cudaDeviceSynchronize)>(rt,"cudaDeviceSynchronize");
        void* buffer=nullptr; check(alloc(&buffer,64),"ALLOC");
        check(memset(buffer,0x3c,64,nullptr),"SETUP");
        const auto setupDrain=drain(); check(setupDrain,"DRAIN");
        const std::string scope="EP_MICRO:"+run; nvtxRangePushA(scope.c_str());
        auto start=load<StartFn>(dll,"ep_start"); auto arm=load<ArmFn>(dll,"ep_arm");
        auto stop=load<StopFn>(dll,"ep_stop"); auto get=load<RecordsFn>(dll,"ep_records");
        const LONG attached=start(rt,run.c_str()); if(attached) throw std::runtime_error("ATTACH:"+std::to_string(attached));
        std::array<std::string,2> readbacks{};
        std::array<int,2> syncReturns{},copyReturns{};
        for(unsigned i=0;i<2;++i) {
            if(arm(i+1)) throw std::runtime_error("ARM");
            check(memset(buffer,0x7b,i==0?0:64,nullptr),"TEST_MEMSET");
            const std::string label="EP_VERIFY:"+run+":"+std::to_string(i+1);
            nvtxRangePushA(label.c_str()); const auto sr=sync(nullptr); nvtxRangePop();
            syncReturns[i]=static_cast<int>(sr);
            check(sr,"VERIFY_SYNC");
            unsigned char host[64]{};
            const auto cr=copy(host,buffer,64,cudaMemcpyDeviceToHost);
            copyReturns[i]=static_cast<int>(cr); check(cr,"VERIFY_COPY");
            readbacks[i]=hex(host,64);
            for(unsigned char b:host) if(b!=(i==0?0x3c:0x7b)) throw std::runtime_error("FUNCTIONAL_ORACLE");
        }
        const LONG detached=stop(); unsigned n=0; LONG fault=0; const auto records=get(&n,&fault);
        nvtxRangePop();
        check(release(buffer),"FREE");
        FILETIME created{},exited{},kernel{},user{};
        if(!GetProcessTimes(GetCurrentProcess(),&created,&exited,&kernel,&user)) throw std::runtime_error("PROCESS_INSTANCE");
        const std::uint64_t birth=(static_cast<std::uint64_t>(created.dwHighDateTime)<<32)|created.dwLowDateTime;
        std::ofstream f(output,std::ios::binary); if(!f) throw std::runtime_error("SIDE_WRITE");
        f<<"{\"schema_version\":\"memset-same-capture-side/0.1.0\",\"role\":\"ENGINEERING_MEMSET_MICRO\",\"run_id\":\""<<run
         <<"\",\"pid\":"<<GetCurrentProcessId()<<",\"creation_filetime\":"<<birth
         <<",\"entry\":\"cudaMemsetAsync\",\"recorder_kind\":\"CUDA_RUNTIME_EXPORT\",\"runtime_path\":\""<<escape(utf8(runtime.wstring()))
         <<"\",\"runtime_version\":"<<version<<",\"runtime_module_base_hex\":\""<<std::hex<<reinterpret_cast<std::uintptr_t>(rt)
         <<"\",\"export_address_hex\":\""<<reinterpret_cast<std::uintptr_t>(memset)<<std::dec
         <<"\",\"attach_code\":"<<attached<<",\"detach_code\":"<<detached<<",\"recorder_error\":"<<fault
         <<",\"setup_drain_return\":"<<static_cast<int>(setupDrain)
         <<",\"gpu_uuid\":\""<<uuid<<"\",\"pci_bus_id\":\""<<pci<<"\",\"calls\":[";
        for(unsigned i=0;i<n;++i) {
            const auto& r=records[i]; if(i) f<<',';
            f<<"{\"call_id\":"<<r.call_id<<",\"count\":"<<r.count<<",\"pointer_alias\":"<<r.pointer_alias
             <<",\"stream_hex\":\""<<std::hex<<r.stream<<std::dec<<"\",\"pid\":"<<r.pid<<",\"tid\":"<<r.tid
             <<",\"value\":"<<r.value<<",\"return_code\":"<<r.return_code<<",\"forwards\":"<<r.forwards
             <<",\"entry_last_error\":"<<r.entry_error<<",\"return_last_error\":"<<r.return_error
             <<",\"completed\":"<<(r.completed?"true":"false")<<",\"push_level\":"<<r.push_level<<",\"pop_level\":"<<r.pop_level<<'}';
        }
        f<<"],\"cases\":[";
        for(unsigned i=0;i<2;++i) { if(i) f<<','; f<<"{\"call_id\":"<<i+1<<",\"sync_return\":"<<syncReturns[i]
            <<",\"copy_return\":"<<copyReturns[i]<<",\"readback_hex\":\""<<readbacks[i]<<"\"}"; }
        f<<"]}\n"; f.flush(); if(!f) throw std::runtime_error("SIDE_FLUSH");
        return detached || fault || n!=2 ? 2 : 0;
    } catch(const std::exception& e) { std::cerr<<e.what()<<"\n"; return 2; }
}
