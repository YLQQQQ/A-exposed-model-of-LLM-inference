#pragma once
#include <nlohmann/json.hpp>
#include <chrono>
#include <cstdint>
#include <functional>
#include <string>
#include <vector>

namespace exposedpath_native {
using json = nlohmann::json;
using MarkerSink = std::function<void(const std::string &)>;
int64_t now_ns();
json read_json(const std::string & path);
std::string sha_file(const std::string & path);
std::vector<int32_t> read_tokens(const std::string & path);
void write_new_json(const std::string & path, const json & value);

class Observer {
public:
    json document;
    json spec;
    std::string spec_hash;
    int pid, tid;
    MarkerSink mark, push;
    std::function<void()> pop;
    int next_sync = 0;
    std::string phase;
    int token_index = -1;
    Observer(const json &, const std::string &, int, int);
    void boundary(int ordinal, int32_t token = -1);
    void persist(const std::string & path) const;
};

// Only the calling thread's real active frame is eligible. No worker propagation.
class ActiveFrame {
    Observer * previous;
public:
    ActiveFrame(Observer &, const std::string &, int);
    ~ActiveFrame();
};

class SyncObservation {
    Observer * owner;
    json row;
    bool pushed = false;
    bool finished = false;
public:
    SyncObservation(int backend_device, int cuda_device, uintptr_t native_handle,
        const char * callsite = "llama.cpp.ggml_backend_cuda_synchronize");
    void finish(int return_value);
    ~SyncObservation();
};
}
