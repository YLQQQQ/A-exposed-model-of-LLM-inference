# Exact representations from pinned cl identity/CMake; preserve all raw values.
function(exposedpath_require_msvc)
  foreach(lang IN LISTS ARGN)
    if(NOT CMAKE_${lang}_COMPILER_VERSION STREQUAL "19.38.33135" AND
       NOT CMAKE_${lang}_COMPILER_VERSION STREQUAL "19.38.33135.0")
      message(FATAL_ERROR "PINNED_MSVC_VERSION: ${lang}=${CMAKE_${lang}_COMPILER_VERSION}")
    endif()
  endforeach()
endfunction()

function(exposedpath_require_cuda)
  if(NOT CMAKE_CUDA_COMPILER_VERSION STREQUAL "12.4.131")
    message(FATAL_ERROR "PINNED_CUDA_VERSION: ${CMAKE_CUDA_COMPILER_VERSION}")
  endif()
endfunction()
