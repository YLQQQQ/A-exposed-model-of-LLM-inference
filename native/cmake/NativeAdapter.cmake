# Compile the same objects later linked by native-llama, not a parallel adapter.
# No llama/ggml backend dependency: this target must fail before that build.
function(exposedpath_native_adapter_targets)
  set(adapter_dir "${CMAKE_CURRENT_FUNCTION_LIST_DIR}/../llama_cpp")
  add_library(exposedpath-native-observer STATIC "${adapter_dir}/observer.cpp")
  target_include_directories(exposedpath-native-observer PUBLIC "${adapter_dir}" "${LLAMA_SOURCE_ROOT}/vendor")
  target_link_libraries(exposedpath-native-observer PUBLIC bcrypt)
  add_library(exposedpath-native-adapter-main OBJECT "${adapter_dir}/main.cpp")
  target_include_directories(exposedpath-native-adapter-main PRIVATE
    "${LLAMA_SOURCE_ROOT}/include" "${LLAMA_SOURCE_ROOT}/ggml/include" "${NVTX_INCLUDE_ROOT}")
  # The original llama target's actual interface flags, without its build dep.
  target_compile_definitions(exposedpath-native-adapter-main PRIVATE GGML_USE_CPU GGML_USE_CUDA)
  target_link_libraries(exposedpath-native-adapter-main PRIVATE exposedpath-native-observer CUDA::cudart)
  add_custom_target(native-adapter-headers DEPENDS exposedpath-native-adapter-main exposedpath-native-observer)
endfunction()
