#pragma once
// Fixed CUDA12.4/API22 control policy; never retry unsupported direct kind 36.
// Retained record kinds are NOT a requirement that unused operations occur.
namespace ep_timeline {
inline constexpr const char* activity_policy_version="cupti-api22-activity-policy/0.2.0";
inline constexpr CUpti_ActivityKind explicit_activity_kinds[]={
    CUPTI_ACTIVITY_KIND_RUNTIME,CUPTI_ACTIVITY_KIND_DRIVER,
    CUPTI_ACTIVITY_KIND_CONCURRENT_KERNEL,CUPTI_ACTIVITY_KIND_MEMCPY,CUPTI_ACTIVITY_KIND_MEMSET,
    CUPTI_ACTIVITY_KIND_SYNCHRONIZATION,CUPTI_ACTIVITY_KIND_CONTEXT,CUPTI_ACTIVITY_KIND_STREAM};
}
