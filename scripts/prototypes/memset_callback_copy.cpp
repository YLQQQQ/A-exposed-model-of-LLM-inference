// CPU-only ABI spike, not an injection DLL or CUDA/CUPTI client.
// Compile using official CUDA12.4.127 headers. No vendor libraries are linked.
#include <cupti_version.h>
#include <cupti_callbacks.h>
#include <cupti_runtime_cbid.h>
#include <generated_cuda_runtime_api_meta.h>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <string>

static_assert(CUPTI_API_VERSION == 22, "Requires the reviewed CUDA12.4 headers");
static_assert(sizeof(size_t) == sizeof(std::uint64_t), "Requires x64 size_t");

struct Snapshot {
    std::uint64_t count = 0;
    std::uintptr_t stream = 0;
    int value = 0;
    int returnCode = 0;
};

static const char* copyCallback(CUpti_CallbackDomain domain, CUpti_CallbackId cbid,
                               const CUpti_CallbackData& data, Snapshot& result) {
    if (domain != CUPTI_CB_DOMAIN_RUNTIME_API ||
        cbid != CUPTI_RUNTIME_TRACE_CBID_cudaMemsetAsync_v3020 ||
        data.functionName == nullptr || std::strcmp(data.functionName, "cudaMemsetAsync") != 0)
        return "UNSUPPORTED_API";
    if (data.callbackSite == CUPTI_API_ENTER) {
        if (data.functionParams == nullptr) return "PARAMETERS_UNKNOWN";
        const auto& params = *static_cast<const cudaMemsetAsync_v3020_params*>(data.functionParams);
        result.count = static_cast<std::uint64_t>(params.count);
        result.stream = reinterpret_cast<std::uintptr_t>(params.stream);
        result.value = params.value;
    } else if (data.callbackSite == CUPTI_API_EXIT) {
        if (data.functionReturnValue == nullptr) return "RETURN_UNKNOWN";
        result.returnCode = static_cast<int>(*static_cast<const cudaError_t*>(data.functionReturnValue));
    } else return "CALLBACK_SITE_UNKNOWN";
    return nullptr;
}

int main(int argc, char** argv) {
    if (argc != 2) return 2;
    const std::string mode(argv[1]);
    if (mode != "zero" && mode != "positive" && mode != "large" && mode != "failed" &&
        mode != "missing_params" && mode != "missing_return") return 2;
    const std::uint64_t expected = mode == "zero" ? 0 : mode == "large" ? (1ULL << 63) + 7 : 1536;
    cudaMemsetAsync_v3020_params params{};
    params.devPtr = reinterpret_cast<void*>(static_cast<std::uintptr_t>(0x1234));
    params.value = 7;
    params.count = static_cast<size_t>(expected);
    params.stream = nullptr;  // Legitimate native handle 0 is preserved, not trace stream ID 0.
    CUpti_CallbackData event{};
    event.functionName = "cudaMemsetAsync";
    event.callbackSite = CUPTI_API_ENTER;
    event.functionParams = mode == "missing_params" ? nullptr : &params;
    Snapshot snapshot;
    const char* error = copyCallback(CUPTI_CB_DOMAIN_RUNTIME_API,
        CUPTI_RUNTIME_TRACE_CBID_cudaMemsetAsync_v3020, event, snapshot);
    // Make the source values unusable after callback. The snapshot must retain its copy.
    params.count = 17;
    params.value = 19;
    params.stream = reinterpret_cast<cudaStream_t>(static_cast<std::uintptr_t>(0xFFFF));
    const bool retained = snapshot.count == expected && snapshot.value == 7 && snapshot.stream == 0;
    if (error == nullptr) {
        event.callbackSite = CUPTI_API_EXIT;
        event.functionParams = nullptr;  // EXIT does not re-read an expired parameter pointer.
        cudaError_t status = mode == "failed" ? cudaErrorMemoryAllocation : cudaSuccess;
        event.functionReturnValue = mode == "missing_return" ? nullptr : &status;
        error = copyCallback(CUPTI_CB_DOMAIN_RUNTIME_API,
            CUPTI_RUNTIME_TRACE_CBID_cudaMemsetAsync_v3020, event, snapshot);
    }
    std::cout << "{\"cupti_api_version\":" << CUPTI_API_VERSION
              << ",\"cuda_calls\":0,\"cupti_calls\":0";
    if (error) std::cout << ",\"error\":\"" << error << "\"";
    else std::cout << ",\"count\":" << snapshot.count << ",\"stream_handle\":" << snapshot.stream
                   << ",\"value\":" << snapshot.value << ",\"return_code\":" << snapshot.returnCode
                   << ",\"copy_survives_parameter_mutation\":" << (retained ? "true" : "false");
    std::cout << "}\n";
    return 0;
}
