#pragma once
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <cuda_runtime_api.h>
#include <cstdint>

static_assert(CUDART_VERSION == 12040, "Only reviewed CUDA12.4 headers");
static_assert(sizeof(size_t) == 8, "x64 size_t required");
using MemsetFn = decltype(&cudaMemsetAsync);
struct CallRecord {
    std::uint64_t call_id, count, pointer_alias;
    std::uintptr_t stream;
    DWORD pid, tid, entry_error, return_error;
    int value, return_code, forwards, completed, push_level, pop_level;
};
using StartFn = LONG (*)(HMODULE, const char*);
using ArmFn = LONG (*)(std::uint64_t);
using StopFn = LONG (*)();
using RecordsFn = const CallRecord* (*)(unsigned*, LONG*);

