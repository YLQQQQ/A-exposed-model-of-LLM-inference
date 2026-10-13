// CPU substitute exercises the production orchestration, never loads llama/CUDA.
#include "producer_core.hpp"
#include <iostream>

struct FakeEngine : exposedpath_native::Engine {
    int index = 0;
    int calls = 0;
    bool fail = false;
    explicit FakeEngine(bool bad) : fail(bad) {}
    void reset() override { index = 0; }
    void drain() override {}
    void process(const std::vector<int32_t> & tokens) override {
        if (tokens.empty()) throw std::runtime_error("empty input");
        ++calls;
        if (fail && calls == 7) throw std::runtime_error("deliberate process failure");
    }
    int32_t sample() override {
        exposedpath_native::SyncObservation wait(0, 0, 123);
        wait.finish(0);
        return 10 + index++;
    }
    bool is_eog(int32_t) override { return false; }
};

int main(int argc, char ** argv) {
    if (argc != 4) return 2;
    using namespace exposedpath_native;
    auto spec = read_json(argv[1]);
    Observer observer(spec, sha_file(argv[1]), 3, 4);
    FakeEngine engine(std::string(argv[3]) == "fail");
    observer.document["execution_kind"] = "CPU_SUBSTITUTE";
    observer.document["actual_gpu"] = spec.at("expected_gpu"); // explicitly synthetic
    try {
        run_request(engine, read_tokens(spec.at("sources").at("token_input").at("path")), observer);
    } catch (const std::exception & error) {
        observer.document["status"] = "FAILED";
        observer.document["error"] = error.what();
    }
    observer.document["fake_engine_calls"] = engine.calls;
    observer.persist(argv[2]);
    return observer.document["status"] == "COMPLETE" ? 0 : 1;
}
