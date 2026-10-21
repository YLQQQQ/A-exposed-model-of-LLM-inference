#pragma once
#include "core.h"
#include "activity_policy.h"
#include "startup.h"
#include <iomanip>
#include <ostream>
#include <string>

namespace ep_timeline {
inline void string(std::ostream& o,const char* s) {
    o<<'"';for(const unsigned char* p=reinterpret_cast<const unsigned char*>(s);*p;++p) {
        if(*p=='"' || *p=='\\')o<<'\\'<<static_cast<char>(*p);
        else if(*p<32)o<<"\\u00"<<std::hex<<std::setw(2)<<std::setfill('0')<<static_cast<unsigned>(*p)<<std::dec;
        else o<<static_cast<char>(*p);
    }o<<'"';
}
inline const char* kind_name(Record::Kind k) {
    const char* names[]={"API","KERNEL","MEMCPY","MEMSET","SYNC","STREAM","CONTEXT","CUDA_EVENT"};return names[k];
}
inline const char* startup_kind_name(int kind) {
    switch(kind) {
    case CUPTI_ACTIVITY_KIND_RUNTIME:return "RUNTIME";
    case CUPTI_ACTIVITY_KIND_DRIVER:return "DRIVER";
    case CUPTI_ACTIVITY_KIND_CONCURRENT_KERNEL:return "CONCURRENT_KERNEL";
    case CUPTI_ACTIVITY_KIND_MEMCPY:return "MEMCPY";
    case CUPTI_ACTIVITY_KIND_MEMSET:return "MEMSET";
    case CUPTI_ACTIVITY_KIND_SYNCHRONIZATION:return "SYNCHRONIZATION";
    case CUPTI_ACTIVITY_KIND_CONTEXT:return "CONTEXT";
    case CUPTI_ACTIVITY_KIND_STREAM:return "STREAM";
    case CUPTI_ACTIVITY_KIND_CUDA_EVENT:return "CUDA_EVENT";
    default:return "UNKNOWN";
    }
}
inline void startup_step_json(std::ostream& o,const StartupStep& s) {
    o<<"{\"operation\":";string(o,s.operation);o<<",\"status_domain\":";string(o,s.domain);
    o<<",\"status_code\":"<<s.code<<",\"success\":"<<(s.success?"true":"false")<<",\"activity_kind\":";
    if(s.kind<0)o<<"null";else o<<s.kind;
    o<<",\"activity_name\":";if(s.kind<0)o<<"null";else string(o,startup_kind_name(s.kind));
    o<<",\"detail\":";string(o,s.detail);o<<'}';
}
inline void startup_json(std::ostream& o,const StartupLog& log,bool shutdown=false) {
    if(shutdown)o<<"{\"schema_version\":\"cupti-timeline-shutdown/0.1.0\"";
    else {
    o<<"{\"schema_version\":\"cupti-timeline-startup/0.2.0\",\"activity_policy\":{\"schema_version\":";
    string(o,activity_policy_version);
    o<<",\"api_version\":22,\"explicit_enable_kinds\":[";
    for(size_t i=0;i<sizeof(explicit_activity_kinds)/sizeof(explicit_activity_kinds[0]);++i){if(i)o<<',';o<<explicit_activity_kinds[i];}
    o<<"],\"retained_record_kinds\":[5,4,10,1,2,38,9,37,36],\"dependent_records\":[{\"kind\":36,\"controlled_by\":38}]}";
    }
    o<<",\"succeeded\":"<<(log.succeeded?"true":"false")
     <<",\"overflow\":"<<log.overflow<<",\"steps\":[";
    for(size_t i=0;i<log.count;++i){if(i)o<<',';startup_step_json(o,log.steps[i]);}
    o<<"],\"failure\":";
    if(log.first_failure==SIZE_MAX)o<<"null";else startup_step_json(o,log.steps[log.first_failure]);
    o<<'}';
}
inline void capture_json(std::ostream& o,const Core& c,const char* session,uint32_t pid,const char* source,
                         bool closed,unsigned client_errors,uint64_t dropped,unsigned query_errors,
                         const std::vector<std::array<uint32_t,2>>& scopes,const StartupLog* startup=nullptr,const StartupLog* shutdown=nullptr) {
    o<<"{\"schema_version\":\"cupti-timeline-capture/0.1.0\",\"source\":";string(o,source);
    o<<",\"session_id\":";string(o,session);o<<",\"clock\":\"CUPTI_TIMESTAMP_NS\",\"pid\":"<<pid
     <<",\"quality\":{\"closed\":"<<(closed && c.closed()?"true":"false")
     <<",\"errors\":[";if(c.errors+client_errors)o<<c.errors+client_errors;
    o<<"],\"overflow\":"<<c.overflow<<",\"dropped\":"<<dropped<<",\"dropped_query_errors\":"<<query_errors
     <<",\"dropped_scopes\":[";
    for(size_t i=0;i<scopes.size();++i){if(i)o<<',';o<<'['<<scopes[i][0]<<','<<scopes[i][1]<<']';}
    o<<"]},\"callbacks\":[";
    for(size_t i=0;i<c.call_count;++i) {
        const auto& a=c.calls[i];if(i)o<<',';
        o<<"{\"id\":"<<a.id<<",\"parent_id\":";if(a.parent)o<<a.parent;else o<<"null";
        o<<",\"domain\":\""<<(a.runtime?"RUNTIME":"DRIVER")<<"\",\"correlation\":"<<a.correlation
         <<",\"cbid\":"<<a.cbid<<",\"name\":";string(o,a.name);
        o<<",\"pid\":"<<a.pid<<",\"tid\":"<<a.tid<<",\"context\":"<<a.context
         <<",\"device\":"<<a.device<<",\"stream\":"<<a.stream<<",\"native_context\":"<<a.native_context
         <<",\"exit_context\":"<<a.exit_context<<",\"exit_native_context\":"<<a.exit_native_context
         <<",\"binding_status\":"<<a.binding_status<<",\"start\":"<<a.start<<",\"end\":"<<a.end
         <<",\"enter_seq\":"<<a.enter<<",\"exit_seq\":"<<a.exit<<",\"return_code\":"<<a.status
         <<",\"closed\":"<<(a.closed?"true":"false")<<",\"ptsz\":"<<(a.ptsz?"true":"false")<<",\"params\":";
        if(a.params)o<<"{\"count\":"<<a.count<<",\"value\":"<<a.value<<",\"copy_kind\":"<<a.copy_kind<<",\"native_stream\":"<<a.native_stream<<'}';
        else o<<"null";
        o<<'}';
    }
    o<<"],\"records\":[";
    for(size_t i=0;i<c.record_count;++i) {
        const auto& r=c.records[i];if(i)o<<',';
        o<<"{\"id\":\"record:"<<i+1<<"\",\"kind\":";string(o,kind_name(r.kind));
        o<<",\"domain\":\""<<(r.kind==Record::API?(r.runtime?"RUNTIME":"DRIVER"):
            r.kind==Record::SYNC?"UNSPECIFIED":"DRIVER")<<"\",\"correlation\":"<<r.correlation
         <<",\"runtime_correlation\":"<<r.runtime_correlation<<",\"pid\":"<<(r.kind==Record::API?r.pid:pid)
         <<",\"tid\":"<<r.tid<<",\"cbid\":"<<r.cbid<<",\"return_code\":"<<r.status
         <<",\"start\":"<<r.start<<",\"end\":"<<r.end<<",\"device\":"<<r.device
         <<",\"context\":"<<r.context<<",\"stream\":"<<r.stream<<",\"bytes\":"<<r.bytes
         <<",\"value\":"<<r.value<<",\"copy_kind\":"<<r.copy_kind<<",\"src_kind\":"<<r.src_kind
         <<",\"dst_kind\":"<<r.dst_kind<<",\"graph\":"<<r.graph<<",\"graph_node\":"<<r.graph_node
         <<",\"flags\":"<<r.flags<<",\"event\":"<<r.event<<",\"name\":";string(o,r.name);
        o<<",\"grid\":["<<r.grid[0]<<','<<r.grid[1]<<','<<r.grid[2]<<"],\"block\":["<<r.block[0]<<','<<r.block[1]<<','<<r.block[2]
         <<"],\"dynamic_shared\":"<<r.dynamic_shared<<'}';
    }
    o<<"],\"markers\":[";
    for(size_t i=0;i<c.marker_count;++i) {
        const auto& m=c.markers[i];if(i)o<<',';
        o<<"{\"action\":"<<m.action<<",\"time\":"<<m.time<<",\"tid\":"<<m.tid<<",\"label\":";string(o,m.label);o<<'}';
    }o<<']';if(startup){o<<",\"initialization\":";startup_json(o,*startup);}
    if(shutdown){o<<",\"shutdown\":";startup_json(o,*shutdown,true);}o<<"}\n";
}
}
