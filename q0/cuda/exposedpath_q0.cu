#include <cuda.h>
#include <cuda_runtime.h>
#include <nvtx3/nvToolsExt.h>

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <functional>
#include <iostream>
#include <map>
#include <regex>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>

namespace {

constexpr const char* kExperimentId = "exposedpath-q0";
constexpr const char* kWmpcId = "q0-controlled";
constexpr const char* kRunRole = "Engineering";
constexpr const char* kPassId = "Pass1";
constexpr const char* kRepeatId = "repeat-0";

void cuda_check(cudaError_t status, const char* expression) {
  if (status != cudaSuccess) {
    throw std::runtime_error(std::string(expression) + ": " + cudaGetErrorString(status));
  }
}

void driver_check(CUresult status, const char* expression) {
  if (status != CUDA_SUCCESS) {
    const char* message = nullptr;
    cuGetErrorString(status, &message);
    throw std::runtime_error(std::string(expression) + ": " + (message ? message : "CUDA driver error"));
  }
}

#define CUDA_CHECK(expr) cuda_check((expr), #expr)
#define DRIVER_CHECK(expr) driver_check((expr), #expr)

class NvtxRange {
 public:
  explicit NvtxRange(const std::string& text) { nvtxRangePushA(text.c_str()); }
  NvtxRange(const NvtxRange&) = delete;
  NvtxRange& operator=(const NvtxRange&) = delete;
  ~NvtxRange() { nvtxRangePop(); }
};

std::string identity_json(const std::string& kind, const std::string& case_id,
                          const std::string& run_id, const std::string& phase,
                          const std::string& callsite = "", int ordinal = -1) {
  std::string result = "EXPOSEDPATH_JSON_V1:{\"kind\":\"" + kind +
      "\",\"experiment_id\":\"" + kExperimentId +
      "\",\"wmpc_id\":\"" + kWmpcId +
      "\",\"run_id\":\"" + run_id +
      "\",\"run_role\":\"" + kRunRole +
      "\",\"pass_id\":\"" + kPassId +
      "\",\"request_id\":\"" + case_id +
      "\",\"repeat_id\":\"" + kRepeatId +
      "\",\"phase\":\"" + phase + "\"";
  if (!callsite.empty()) {
    result += ",\"callsite_id\":\"" + callsite + "\"";
  }
  if (kind == "sync") {
    result += ",\"sync_origin\":\"q0_controlled\",\"sync_ordinal\":" +
              std::to_string(ordinal);
  }
  result += "}";
  return result;
}

NvtxRange request_range(const std::string& case_id, const std::string& run_id) {
  return NvtxRange(identity_json("request", case_id, run_id, "full_request"));
}

NvtxRange phase_range(const std::string& case_id, const std::string& run_id,
                      const std::string& phase) {
  return NvtxRange(identity_json("phase", case_id, run_id, phase));
}

NvtxRange marker_range(const std::string& case_id, const std::string& run_id,
                       const std::string& phase, const std::string& label) {
  return NvtxRange(identity_json("marker", case_id, run_id, phase, label));
}

NvtxRange sync_range(const std::string& case_id, const std::string& run_id,
                     const std::string& phase, const std::string& label, int ordinal) {
  return NvtxRange(identity_json("sync", case_id, run_id, phase, label, ordinal));
}

__global__ void q0_spin_kernel(std::uint64_t cycles) {
  const std::uint64_t start = clock64();
  while (clock64() - start < cycles) {
  }
}

struct Resources {
  cudaDeviceProp properties{};
  int clock_rate_khz{};
  cudaStream_t first{};
  cudaStream_t second{};
  cudaEvent_t event{};
  void* device_buffer{};
  void* host_buffer{};

  Resources() {
    CUDA_CHECK(cudaGetDeviceProperties(&properties, 0));
    CUDA_CHECK(cudaDeviceGetAttribute(&clock_rate_khz, cudaDevAttrClockRate, 0));
    CUDA_CHECK(cudaStreamCreateWithFlags(&first, cudaStreamNonBlocking));
    CUDA_CHECK(cudaStreamCreateWithFlags(&second, cudaStreamNonBlocking));
    CUDA_CHECK(cudaEventCreateWithFlags(&event, cudaEventDisableTiming));
    CUDA_CHECK(cudaMalloc(&device_buffer, 4096));
    CUDA_CHECK(cudaMallocHost(&host_buffer, 4096));
  }

  ~Resources() {
    cudaDeviceSynchronize();
    if (host_buffer) cudaFreeHost(host_buffer);
    if (device_buffer) cudaFree(device_buffer);
    if (event) cudaEventDestroy(event);
    if (second) cudaStreamDestroy(second);
    if (first) cudaStreamDestroy(first);
  }

  std::uint64_t cycles(int milliseconds) const {
    return static_cast<std::uint64_t>(clock_rate_khz) * milliseconds;
  }
};

void launch(Resources& resources, const std::string& case_id, const std::string& run_id,
            const std::string& phase, const std::string& label, cudaStream_t stream,
            int milliseconds) {
  auto marker = marker_range(case_id, run_id, phase, label);
  q0_spin_kernel<<<1, 1, 0, stream>>>(resources.cycles(milliseconds));
  CUDA_CHECK(cudaGetLastError());
}

template <typename Body>
void one_phase(const std::string& case_id, const std::string& run_id, Body body) {
  auto request = request_range(case_id, run_id);
  auto phase = phase_range(case_id, run_id, "decode");
  body();
}

void run_stream(Resources& r, const std::string& c, const std::string& id) {
  one_phase(c, id, [&] {
    launch(r, c, id, "decode", "K_S1_A", r.first, 5);
    launch(r, c, id, "decode", "K_S1_B", r.first, 40);
    launch(r, c, id, "decode", "K_OTHER", r.second, 70);
    auto sync = sync_range(c, id, "decode", "S_STREAM", 0);
    CUDA_CHECK(cudaStreamSynchronize(r.first));
  });
}

void run_device(Resources& r, const std::string& c, const std::string& id,
                const std::string& a, const std::string& b, const std::string& sync_label) {
  one_phase(c, id, [&] {
    launch(r, c, id, "decode", a, r.first, 25);
    launch(r, c, id, "decode", b, r.second, 45);
    auto sync = sync_range(c, id, "decode", sync_label, 0);
    CUDA_CHECK(cudaDeviceSynchronize());
  });
}

void run_context(Resources& r, const std::string& c, const std::string& id) {
  one_phase(c, id, [&] {
    launch(r, c, id, "decode", "K_CTX_A", r.first, 25);
    launch(r, c, id, "decode", "K_CTX_B", r.second, 45);
    auto sync = sync_range(c, id, "decode", "S_CONTEXT", 0);
    DRIVER_CHECK(cuCtxSynchronize());
  });
}

void run_event(Resources& r, const std::string& c, const std::string& id) {
  one_phase(c, id, [&] {
    launch(r, c, id, "decode", "K_BEFORE_RECORD", r.first, 35);
    CUDA_CHECK(cudaEventRecord(r.event, r.first));
    launch(r, c, id, "decode", "K_AFTER_RECORD", r.first, 60);
    auto sync = sync_range(c, id, "decode", "S_EVENT", 0);
    CUDA_CHECK(cudaEventSynchronize(r.event));
  });
}

void run_event_cross_stream(Resources& r, const std::string& c, const std::string& id) {
  one_phase(c, id, [&] {
    launch(r, c, id, "decode", "K_PRODUCER", r.first, 30);
    CUDA_CHECK(cudaEventRecord(r.event, r.first));
    CUDA_CHECK(cudaStreamWaitEvent(r.second, r.event, 0));
    launch(r, c, id, "decode", "K_CONSUMER", r.second, 35);
    auto sync = sync_range(c, id, "decode", "S_CONSUMER_STREAM", 0);
    CUDA_CHECK(cudaStreamSynchronize(r.second));
  });
}

void run_completed(Resources& r, const std::string& c, const std::string& id) {
  one_phase(c, id, [&] {
    launch(r, c, id, "decode", "K_DONE", r.first, 2);
    std::this_thread::sleep_for(std::chrono::milliseconds(50));
    auto sync = sync_range(c, id, "decode", "S_STREAM", 0);
    CUDA_CHECK(cudaStreamSynchronize(r.first));
  });
}

void run_empty(Resources& r, const std::string& c, const std::string& id) {
  one_phase(c, id, [&] {
    auto sync = sync_range(c, id, "decode", "S_EMPTY", 0);
    CUDA_CHECK(cudaStreamSynchronize(r.first));
  });
}

void run_kernel_memop(Resources& r, const std::string& c, const std::string& id) {
  one_phase(c, id, [&] {
    launch(r, c, id, "decode", "KERNEL_A", r.first, 35);
    {
      auto marker = marker_range(c, id, "decode", "MEMCPY_B");
      CUDA_CHECK(cudaMemcpyAsync(r.device_buffer, r.host_buffer, 4096,
                                 cudaMemcpyHostToDevice, r.second));
    }
    auto sync = sync_range(c, id, "decode", "S_DEVICE", 0);
    CUDA_CHECK(cudaDeviceSynchronize());
  });
}

void run_missing_event(Resources& r, const std::string& c, const std::string& id) {
  one_phase(c, id, [&] {
    launch(r, c, id, "decode", "K_EVENT", r.first, 30);
    auto sync = sync_range(c, id, "decode", "S_EVENT", 0);
    CUDA_CHECK(cudaEventSynchronize(r.event));
  });
}

void run_external(Resources& r, const std::string& c, const std::string& id) {
  launch(r, c, id, "decode", "K_EXTERNAL", r.first, 40);
  one_phase(c, id, [&] {
    auto sync = sync_range(c, id, "decode", "S_DEVICE", 0);
    CUDA_CHECK(cudaDeviceSynchronize());
  });
}

void run_legacy_default(Resources& r, const std::string& c, const std::string& id) {
  one_phase(c, id, [&] {
    launch(r, c, id, "decode", "K_NONDEFAULT", r.first, 25);
    launch(r, c, id, "decode", "K_LEGACY_DEFAULT", cudaStreamLegacy, 35);
    auto sync = sync_range(c, id, "decode", "S_DEFAULT", 0);
    CUDA_CHECK(cudaStreamSynchronize(cudaStreamLegacy));
  });
}

void run_ptds(Resources& r, const std::string& c, const std::string& id) {
  std::thread other([&] {
    auto request = request_range(c, id);
    auto phase = phase_range(c, id, "decode");
    launch(r, c, id, "decode", "K_OTHER_THREAD", cudaStreamPerThread, 60);
  });
  other.join();
  one_phase(c, id, [&] {
    launch(r, c, id, "decode", "K_PTDS", cudaStreamPerThread, 30);
    auto sync = sync_range(c, id, "decode", "S_PTDS", 0);
    CUDA_CHECK(cudaStreamSynchronize(cudaStreamPerThread));
  });
}

void run_multithread(Resources& r, const std::string& c, const std::string& id) {
  std::thread producer([&] {
    auto request = request_range(c, id);
    auto phase = phase_range(c, id, "decode");
    launch(r, c, id, "decode", "K_THREAD_A", r.first, 25);
    CUDA_CHECK(cudaEventRecord(r.event, r.first));
  });
  producer.join();
  std::thread consumer([&] {
    auto request = request_range(c, id);
    auto phase = phase_range(c, id, "decode");
    CUDA_CHECK(cudaStreamWaitEvent(r.second, r.event, 0));
    launch(r, c, id, "decode", "K_THREAD_B", r.second, 35);
    auto sync = sync_range(c, id, "decode", "S_THREAD_B", 0);
    CUDA_CHECK(cudaStreamSynchronize(r.second));
  });
  consumer.join();
}

void run_overlapping_sync(Resources& r, const std::string& c, const std::string& id) {
  {
    auto request = request_range(c, id);
    auto phase = phase_range(c, id, "decode");
    launch(r, c, id, "decode", "K_A", r.first, 40);
    launch(r, c, id, "decode", "K_B", r.second, 50);
  }
  std::thread first([&] {
    auto request = request_range(c, id);
    auto phase = phase_range(c, id, "decode");
    auto sync = sync_range(c, id, "decode", "S_A", 0);
    CUDA_CHECK(cudaStreamSynchronize(r.first));
  });
  std::thread second([&] {
    auto request = request_range(c, id);
    auto phase = phase_range(c, id, "decode");
    auto sync = sync_range(c, id, "decode", "S_B", 1);
    CUDA_CHECK(cudaStreamSynchronize(r.second));
  });
  first.join();
  second.join();
}

void run_phase_spill(Resources& r, const std::string& c, const std::string& id) {
  auto request = request_range(c, id);
  {
    auto prefill = phase_range(c, id, "prefill");
    launch(r, c, id, "prefill", "K_PREFILL_ORIGIN", r.first, 40);
  }
  {
    auto decode = phase_range(c, id, "decode");
    auto sync = sync_range(c, id, "decode", "S_DECODE_OWNER", 0);
    CUDA_CHECK(cudaStreamSynchronize(r.first));
  }
}

void run_invocation_bleed(Resources& r, const std::string& c, const std::string& id) {
  {
    auto prior = request_range("Q0-PRIOR-INVOCATION", id);
    auto phase = phase_range("Q0-PRIOR-INVOCATION", id, "decode");
    launch(r, "Q0-PRIOR-INVOCATION", id, "decode", "K_PRIOR_INVOCATION", r.first, 40);
  }
  one_phase(c, id, [&] {
    auto sync = sync_range(c, id, "decode", "S_CURRENT", 0);
    CUDA_CHECK(cudaDeviceSynchronize());
  });
}

void run_graph(Resources& r, const std::string& c, const std::string& id) {
  cudaGraph_t graph{};
  cudaGraphExec_t executable{};
  CUDA_CHECK(cudaStreamBeginCapture(r.first, cudaStreamCaptureModeGlobal));
  q0_spin_kernel<<<1, 1, 0, r.first>>>(r.cycles(30));
  CUDA_CHECK(cudaGetLastError());
  CUDA_CHECK(cudaStreamEndCapture(r.first, &graph));
  CUDA_CHECK(cudaGraphInstantiate(&executable, graph, nullptr, nullptr, 0));
  one_phase(c, id, [&] {
    {
      auto marker = marker_range(c, id, "decode", "GRAPH_NODE");
      CUDA_CHECK(cudaGraphLaunch(executable, r.first));
    }
    auto sync = sync_range(c, id, "decode", "S_GRAPH", 0);
    CUDA_CHECK(cudaStreamSynchronize(r.first));
  });
  CUDA_CHECK(cudaGraphExecDestroy(executable));
  CUDA_CHECK(cudaGraphDestroy(graph));
}

void run_sync_d2h(Resources& r, const std::string& c, const std::string& id) {
  one_phase(c, id, [&] {
    auto sync = sync_range(c, id, "decode", "S_SYNC_COPY", 0);
    auto marker = marker_range(c, id, "decode", "COPY_D2H");
    CUDA_CHECK(cudaMemcpy(r.host_buffer, r.device_buffer, 4096, cudaMemcpyDeviceToHost));
  });
}

void run_query(Resources& r, const std::string& c, const std::string& id) {
  one_phase(c, id, [&] {
    launch(r, c, id, "decode", "K_RUNNING", r.first, 50);
    CUDA_CHECK(cudaEventRecord(r.event, r.first));
    auto marker = marker_range(c, id, "decode", "Q_EVENT");
    const cudaError_t status = cudaEventQuery(r.event);
    if (status != cudaSuccess && status != cudaErrorNotReady) CUDA_CHECK(status);
  });
}

using CaseFunction = std::function<void(Resources&, const std::string&, const std::string&)>;

std::map<std::string, CaseFunction> cases() {
  return {
      {"Q0-STREAM-001", run_stream},
      {"Q0-DEVICE-001", [](auto& r, const auto& c, const auto& id) { run_device(r, c, id, "K_A", "K_B", "S_DEVICE"); }},
      {"Q0-CONTEXT-001", run_context},
      {"Q0-EVENT-001", run_event},
      {"Q0-EVENT-XSTREAM-001", run_event_cross_stream},
      {"Q0-COMPLETED-001", run_completed},
      {"Q0-EMPTY-001", run_empty},
      {"Q0-KERNEL-MEMOP-001", run_kernel_memop},
      {"Q0-MISSING-EVENT-001", run_missing_event},
      {"Q0-MISSING-CORR-001", [](auto& r, const auto& c, const auto& id) { one_phase(c, id, [&] { launch(r, c, id, "decode", "K_UNMAPPED", r.first, 35); auto sync = sync_range(c, id, "decode", "S_STREAM", 0); CUDA_CHECK(cudaStreamSynchronize(r.first)); }); }},
      {"Q0-DROPPED-001", [](auto& r, const auto& c, const auto& id) { one_phase(c, id, [&] { launch(r, c, id, "decode", "K_VISIBLE", r.first, 35); auto sync = sync_range(c, id, "decode", "S_DEVICE", 0); CUDA_CHECK(cudaDeviceSynchronize()); }); }},
      {"Q0-EXTERNAL-001", run_external},
      {"Q0-DEFAULT-LEGACY-001", run_legacy_default},
      {"Q0-DEFAULT-PTDS-001", run_ptds},
      {"Q0-MULTITHREAD-ORDERED-001", run_multithread},
      {"Q0-OVERLAPPING-HOST-SYNC-001", run_overlapping_sync},
      {"Q0-PHASE-SPILL-001", run_phase_spill},
      {"Q0-INVOCATION-BLEED-001", run_invocation_bleed},
      {"Q0-GRAPH-UNSUPPORTED-001", run_graph},
      {"Q0-SYNC-D2H-UNSUPPORTED-001", run_sync_d2h},
      {"Q0-QUERY-001", run_query},
  };
}

bool safe_identifier(const std::string& value) {
  static const std::regex pattern("^[A-Za-z0-9._-]+$");
  return std::regex_match(value, pattern);
}

}  // namespace

int main(int argc, char** argv) {
  const auto registry = cases();
  if (argc == 2 && std::string(argv[1]) == "--list-cases") {
    for (const auto& item : registry) std::cout << item.first << '\n';
    return 0;
  }
  if (argc != 5 || std::string(argv[1]) != "--case" ||
      std::string(argv[3]) != "--run-id") {
    std::cerr << "usage: exposedpath_q0 --case CASE_ID --run-id RUN_ID\n";
    return 2;
  }
  const std::string case_id = argv[2];
  const std::string run_id = argv[4];
  const auto selected = registry.find(case_id);
  if (selected == registry.end()) {
    std::cerr << "unknown case: " << case_id << '\n';
    return 2;
  }
  if (!safe_identifier(run_id)) {
    std::cerr << "invalid run id\n";
    return 2;
  }

  try {
    Resources resources;
    {
      NvtxRange capture("EXPOSEDPATH_Q0_CAPTURE");
      selected->second(resources, case_id, run_id);
    }
    return 0;
  } catch (const std::exception& error) {
    std::cerr << "CUDA case failed: " << error.what() << '\n';
    return 1;
  }
}
