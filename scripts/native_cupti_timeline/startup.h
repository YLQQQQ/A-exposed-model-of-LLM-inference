#pragma once
#include <array>
#include <cstdint>
#include <cstring>
#include <stdexcept>

namespace ep_timeline {
// Host facts only. No vendor call, clock read, synchronization or retry.
struct StartupStep {
    char operation[96]{},domain[16]{},detail[96]{};
    int64_t code=0;int kind=-1;bool success=false;
};
struct StartupLog {
    std::array<StartupStep,64> steps{};
    size_t count=0,first_failure=SIZE_MAX;unsigned overflow=0;bool succeeded=false;
    static void copy(char* target,size_t capacity,const char* value) {
        if(!value || std::strlen(value)>=capacity)throw std::runtime_error("STARTUP_TEXT_CAPACITY");
        std::memcpy(target,value,std::strlen(value)+1);
    }
    void record(const char* operation,const char* domain,int64_t code,bool success,int kind=-1,const char* detail="") {
        if(count==steps.size()){++overflow;throw std::runtime_error("STARTUP_RECORD_CAPACITY");}
        auto& s=steps[count];copy(s.operation,sizeof(s.operation),operation);copy(s.domain,sizeof(s.domain),domain);
        copy(s.detail,sizeof(s.detail),detail);s.code=code;s.kind=kind;s.success=success;
        if(!success && first_failure==SIZE_MAX)first_failure=count;
        ++count;
    }
    void exception(const char* reason) noexcept {
        // An exception must not replace the actual API's first failure.
        if(first_failure==SIZE_MAX && !overflow) {
            try{record("UNHANDLED_EXCEPTION","EXCEPTION",0,false,-1,reason);}
            catch(...){++overflow;}
        }
    }
};
}
