// CPU-only ABI double. No CUDA/CUPTI import library, device call or model.
#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable:4324)
#endif
#include <cupti.h>
#ifdef _MSC_VER
#pragma warning(pop)
#endif
#include <cstring>
#include <sstream>
#include <string>

namespace {
char fail_operation[96]{};int fail_kind=-1;CUptiResult fail_code=CUPTI_SUCCESS;uint32_t api_version=22;
std::string controls;
CUptiResult status(const char* operation,int kind=-1) {
    return std::strcmp(operation,fail_operation)==0 && fail_kind==kind?fail_code:CUPTI_SUCCESS;
}
CUptiResult control(const char* operation,const char* label,int kind) {
    const auto code=status(operation,kind);
    if(!controls.empty())controls+=',';
    controls+="{\"operation\":\""+std::string(label)+"\",\"kind\":"+std::to_string(kind)+",\"code\":"+std::to_string(code)+"}";
    return code;
}
}
// Export through a .def file: the genuine SDK already declares these APIs,
// and adding dllexport to their definitions changes MSVC linkage.
#define EXPORT extern "C"
EXPORT void ep_startup_double_configure(const char* operation,int kind,int code,uint32_t version) {
    if(std::strlen(operation)>=sizeof(fail_operation))return;
    std::memcpy(fail_operation,operation,std::strlen(operation)+1);
    fail_kind=kind;fail_code=static_cast<CUptiResult>(code);api_version=version;
    controls.clear();
}
EXPORT const char* ep_startup_double_controls(){return controls.c_str();}
EXPORT CUptiResult CUPTIAPI cuptiGetVersion(uint32_t* version) {*version=api_version;return status("cuptiGetVersion");}
EXPORT CUptiResult CUPTIAPI cuptiGetTimestamp(uint64_t* timestamp) {*timestamp=100;return CUPTI_SUCCESS;}
EXPORT CUptiResult CUPTIAPI cuptiActivityGetNextRecord(uint8_t*,size_t,CUpti_Activity**) {return CUPTI_ERROR_MAX_LIMIT_REACHED;}
EXPORT CUptiResult CUPTIAPI cuptiActivityGetNumDroppedRecords(CUcontext,uint32_t,size_t* dropped) {*dropped=0;return CUPTI_SUCCESS;}
EXPORT CUptiResult CUPTIAPI cuptiGetDeviceId(CUcontext,uint32_t* device) {*device=0;return CUPTI_SUCCESS;}
EXPORT CUptiResult CUPTIAPI cuptiGetStreamIdEx(CUcontext,CUstream,uint8_t,uint32_t* stream) {*stream=7;return CUPTI_SUCCESS;}
EXPORT CUptiResult CUPTIAPI cuptiActivityDisable(CUpti_ActivityKind k) {return control("cuptiActivityDisable","disable",k);}
EXPORT CUptiResult CUPTIAPI cuptiActivityFlushAll(uint32_t) {return status("cuptiActivityFlushAll");}
EXPORT CUptiResult CUPTIAPI cuptiUnsubscribe(CUpti_SubscriberHandle) {return CUPTI_SUCCESS;}
EXPORT CUptiResult CUPTIAPI cuptiFinalize() {return CUPTI_SUCCESS;}
EXPORT CUptiResult CUPTIAPI cuptiSubscribe(CUpti_SubscriberHandle* subscriber,CUpti_CallbackFunc,void*) {
    const auto result=status("cuptiSubscribe");
    if(result==CUPTI_SUCCESS)*subscriber=reinterpret_cast<CUpti_SubscriberHandle>(uintptr_t(1));
    return result;
}
EXPORT CUptiResult CUPTIAPI cuptiSetThreadIdType(CUpti_ActivityThreadIdType) {return status("cuptiSetThreadIdType");}
EXPORT CUptiResult CUPTIAPI cuptiActivityRegisterCallbacks(CUpti_BuffersCallbackRequestFunc,CUpti_BuffersCallbackCompleteFunc) {
    return status("cuptiActivityRegisterCallbacks");
}
EXPORT CUptiResult CUPTIAPI cuptiEnableDomain(uint32_t,CUpti_SubscriberHandle,CUpti_CallbackDomain domain) {
    return status("cuptiEnableDomain",static_cast<int>(domain));
}
EXPORT CUptiResult CUPTIAPI cuptiActivityEnable(CUpti_ActivityKind kind) {return control("cuptiActivityEnable","enable",kind);}
#ifndef EP_STARTUP_DOUBLE_OMIT_DUMP
EXPORT CUptiResult CUPTIAPI cuptiActivityEnableAndDump(CUpti_ActivityKind kind) {return control("cuptiActivityEnableAndDump","dump",kind);}
#endif
