// Exercises the real client against a separately built CPU-only ABI double.
#include <windows.h>
#include <cstdlib>
#include <iostream>
#include <string>

int wmain(int argc,wchar_t** argv) {
    if(argc!=6)return 2;
    const std::wstring mode=argv[4];const int code=_wtoi(argv[5]);
    auto native=LoadLibraryW(argv[1]);if(!native)return 3;
    auto open=reinterpret_cast<int(*)(const wchar_t*,const char*)>(GetProcAddress(native,"ep_timeline_open"));
    auto close=reinterpret_cast<int(*)(const wchar_t*)>(GetProcAddress(native,"ep_timeline_close"));
    if(!open || !close)return 4;
    const wchar_t* library=argv[2];
    const char* (*controls)()=nullptr;
    if(mode!=L"missing_library") {
        auto cpu=LoadLibraryW(library);if(!cpu)return 5;
        auto configure=reinterpret_cast<void(*)(const char*,int,int,unsigned)>(GetProcAddress(cpu,"ep_startup_double_configure"));
        if(!configure)return 6;
        controls=reinterpret_cast<const char*(*)()>(GetProcAddress(cpu,"ep_startup_double_controls"));
        if(!controls)return 6;
        const char* operation="";int kind=-1;unsigned version=22;
        if(mode==L"stream_failure"){operation="cuptiActivityEnableAndDump";kind=37;}
        else if(mode==L"event_failure"){operation="cuptiActivityEnable";kind=36;}
        else if(mode==L"sync_failure"){operation="cuptiActivityEnable";kind=38;}
        else if(mode==L"disable_failure"){operation="cuptiActivityDisable";kind=38;}
        else if(mode==L"flush_failure")operation="cuptiActivityFlushAll";
        else if(mode==L"subscribe_failure")operation="cuptiSubscribe";
        else if(mode==L"thread_failure")operation="cuptiSetThreadIdType";
        else if(mode==L"buffers_failure")operation="cuptiActivityRegisterCallbacks";
        else if(mode==L"driver_domain_failure"){operation="cuptiEnableDomain";kind=1;}
        else if(mode==L"version_conflict")version=23;
        else if(mode!=L"success")return 7;
        configure(operation,kind,code,version);
    } else library=L"C:\\exposedpath_missing_cpu_double\\does_not_exist.dll";
    const int opened=open(library,"CPU_STARTUP_DOUBLE");const int closed=close(argv[3]);
    const bool vendor=GetModuleHandleW(L"nvcuda.dll") || GetModuleHandleW(L"cudart64_12.dll") || GetModuleHandleW(L"cupti64_2024.1.1.dll");
    std::cout<<"{\"role\":\"CPU_DLL_STARTUP_DOUBLE_NOT_GPU\",\"vendor_loaded\":"<<(vendor?"true":"false")
        <<",\"open_code\":"<<opened<<",\"close_code\":"<<closed<<",\"controls\":["<<(controls?controls():"")<<"]}\n";
    // Exit process; the client owns callbacks until its normal close completes.
    return vendor?8:0;
}
