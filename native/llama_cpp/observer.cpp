#include "observer.hpp"
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <sstream>
#include <stdexcept>
#ifdef _WIN32
#include <windows.h>
#include <bcrypt.h>
#include <fcntl.h>
#include <io.h>
#include <sys/stat.h>
#endif

namespace exposedpath_native {
static thread_local Observer * active = nullptr;
int64_t now_ns() {
    return std::chrono::duration_cast<std::chrono::nanoseconds>(
        std::chrono::steady_clock::now().time_since_epoch()).count();
}
json read_json(const std::string & path) {
    std::ifstream in(std::filesystem::u8path(path), std::ios::binary);
    if (!in) throw std::runtime_error("input missing: " + path);
    json v; in >> v; return v;
}
std::string sha_file(const std::string & path) {
#ifdef _WIN32
    BCRYPT_ALG_HANDLE alg = nullptr; BCRYPT_HASH_HANDLE hash = nullptr;
    if (BCryptOpenAlgorithmProvider(&alg, BCRYPT_SHA256_ALGORITHM, nullptr, 0) < 0)
        throw std::runtime_error("SHA256 provider failure");
    if (BCryptCreateHash(alg, &hash, nullptr, 0, nullptr, 0, 0) < 0) {
        BCryptCloseAlgorithmProvider(alg, 0); throw std::runtime_error("SHA256 init failure");
    }
    unsigned char value[32]; char buffer[1024*1024];
    try {
        std::ifstream in(std::filesystem::u8path(path), std::ios::binary);
        if (!in) throw std::runtime_error("hash input missing: " + path);
        while (in.read(buffer,sizeof(buffer)) || in.gcount()) {
            if (BCryptHashData(hash,reinterpret_cast<PUCHAR>(buffer),static_cast<ULONG>(in.gcount()),0)<0)
                throw std::runtime_error("SHA256 update failure");
        }
        if (!in.eof() || BCryptFinishHash(hash,value,sizeof(value),0)<0)
            throw std::runtime_error("SHA256 read/finalize failure");
    } catch (...) {
        BCryptDestroyHash(hash); BCryptCloseAlgorithmProvider(alg,0); throw;
    }
    BCryptDestroyHash(hash); BCryptCloseAlgorithmProvider(alg,0);
    std::ostringstream out;
    for (auto byte:value) out<<std::hex<<std::setw(2)<<std::setfill('0')<<static_cast<int>(byte);
    return out.str();
#else
    throw std::runtime_error("native target is Windows; no hash fallback");
#endif
}
std::vector<int32_t> read_tokens(const std::string & path) {
    std::ifstream in(std::filesystem::u8path(path),std::ios::binary);
    std::vector<unsigned char> bytes((std::istreambuf_iterator<char>(in)),{});
    if (bytes.size()!=128) throw std::runtime_error("input is not 32 int32 tokens");
    std::vector<int32_t> result;
    for (size_t i=0;i<bytes.size();i+=4) {
        uint32_t t=bytes[i]|(uint32_t(bytes[i+1])<<8)|(uint32_t(bytes[i+2])<<16)|(uint32_t(bytes[i+3])<<24);
        if (t>INT32_MAX) throw std::runtime_error("invalid input token");
        result.push_back(static_cast<int32_t>(t));
    }
    return result;
}
void write_new_json(const std::string & path,const json & value) {
    const auto data=value.dump(2)+"\n";
#ifdef _WIN32
    const auto wide=std::filesystem::u8path(path).wstring();
    int fd=_wopen(wide.c_str(),_O_WRONLY|_O_CREAT|_O_EXCL|_O_BINARY,_S_IREAD|_S_IWRITE);
    if (fd<0) throw std::runtime_error("refuse output overwrite/open failure: "+path);
    bool ok=_write(fd,data.data(),static_cast<unsigned>(data.size()))==static_cast<int>(data.size());
    ok=(_commit(fd)==0)&&ok; int close_status=_close(fd);
    if (!ok || close_status) throw std::runtime_error("output write failure: "+path);
#else
    throw std::runtime_error("native target is Windows");
#endif
}
Observer::Observer(const json & value,const std::string & hash,int process,int thread)
    :spec(value),spec_hash(hash),pid(process),tid(thread) {
    document={{"schema_version","exposedpath-native-llama-producer/0.1.0"},
        {"spec_sha256",hash},{"identity",value.at("identity")},{"pid",pid},{"tid",tid},
        {"status","STARTED"},{"error",nullptr},{"boundaries",json::array()},
        {"warmups",json::array()},{"tokens",json::array()},{"sync_calls",json::array()},
        {"observed_configuration",value.at("configuration")},
        {"sampling_branch_basis","CONTEXT_WITHOUT_BACKEND_SAMPLERS"}};
}
void Observer::boundary(int ordinal,int32_t token) {
    if (ordinal!=static_cast<int>(document["boundaries"].size())) throw std::runtime_error("boundary order");
    const auto observed=now_ns();
    json payload={{"schema_version","exposedpath-native-boundary/0.1.0"},
        {"profile","LLAMA-NATIVE-WINDOW/0.1.0"},{"identity",spec.at("identity")},
        {"spec_sha256",spec_hash},{"boundary_id",spec.at("identity").at("request_id").get<std::string>()+":"+std::to_string(ordinal)},
        {"boundary_kind",ordinal==0?"request_start":"token_ready"},
        {"token_index",ordinal==0?json(nullptr):json(ordinal-1)},
        {"token_id",ordinal==0?json(nullptr):json(token)},
        {"completion_mechanism",ordinal==0?"before_native_input_processing":"native_host_token_return"}};
    const auto label="EXPOSEDPATH_NATIVE_BOUNDARY_V1:"+payload.dump();
    const auto before=now_ns(); if (mark) mark(label); const auto after=now_ns();
    document["boundaries"].push_back({{"payload",payload},{"host_observed_ns",observed},
        {"host_before_marker_ns",before},{"host_after_marker_ns",after},{"host_clock_id","STD_STEADY_CLOCK_NS"}});
}
void Observer::persist(const std::string & path) const { write_new_json(path,document); }
ActiveFrame::ActiveFrame(Observer & o,const std::string & p,int token):previous(active) {
    if (active) throw std::runtime_error("nested native frame");
    active=&o; o.phase=p; o.token_index=token;
}
ActiveFrame::~ActiveFrame() { active=previous; }
SyncObservation::SyncObservation(int backend_device,int cuda_device,uintptr_t native_handle,const char * callsite):owner(active) {
    if (!owner) return; // no invented request identity for setup/other threads
    auto payload=owner->spec.at("identity");
    payload["schema_version"]="exposedpath-native-sync/0.1.0";
    payload["kind"]="sync"; payload["phase"]=owner->phase;
    payload["callsite_id"]=callsite;
    payload["sync_origin"]="native_backend_synchronize";
    payload["sync_ordinal"]=owner->next_sync++; payload["token_index"]=owner->token_index;
    payload["native_profile"]="LLAMA-NATIVE-WINDOW/0.1.0";
    payload["spec_sha256"]=owner->spec_hash;
    payload["backend_device_index"]=backend_device; payload["cuda_device"]=cuda_device;
    payload["native_handle"]=std::to_string(native_handle);
    const auto label="EXPOSEDPATH_JSON_V1:"+payload.dump();
    row={{"payload",payload},{"pid",owner->pid},{"tid",owner->tid},
        {"host_start_ns",now_ns()},{"return_value",nullptr}};
    if (owner->push) {owner->push(label);pushed=true;}
}
void SyncObservation::finish(int return_value) {
    if (!owner) return;
    if (finished) throw std::runtime_error("duplicate sync finish");
    row["return_value"]=return_value; row["host_end_ns"]=now_ns();
    if (pushed) {owner->pop();pushed=false;}
    owner->document["sync_calls"].push_back(row);finished=true;
}
SyncObservation::~SyncObservation() { if (pushed) owner->pop(); }
}
