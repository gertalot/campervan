# PCL 1.15 builds with only iostreams under C++17, but its generated package
# config unconditionally requests a separate Boost.System binary. Boost 1.86
# provides System header-only; keep its exported dependencies consistent.
file(SHA256 "${CMAKE_CURRENT_LIST_FILE}" actual_patch_hash)
if(NOT actual_patch_hash STREQUAL PATCH_INPUT_HASH)
  message(FATAL_ERROR "PCL patch changed during the build; rerun make scan-native.")
endif()
set(path "${SOURCE_DIR}/cmake/pcl_pclconfig.cmake")
file(READ "${path}" contents)
set(old "set(PCLCONFIG_AVAILABLE_BOOST_MODULES \"system iostreams\")")
set(new "set(PCLCONFIG_AVAILABLE_BOOST_MODULES \"iostreams\")")
string(REGEX MATCHALL "set\\(PCLCONFIG_AVAILABLE_BOOST_MODULES \"system iostreams\"\\)" pristine "${contents}")
string(REGEX MATCHALL "set\\(PCLCONFIG_AVAILABLE_BOOST_MODULES \"iostreams\"\\)" patched "${contents}")
list(LENGTH pristine pristine_count)
list(LENGTH patched patched_count)
if(pristine_count EQUAL 1 AND patched_count EQUAL 0)
  string(REPLACE "${old}" "${new}" contents "${contents}")
  file(WRITE "${path}" "${contents}")
elseif(NOT (pristine_count EQUAL 0 AND patched_count EQUAL 1))
  message(FATAL_ERROR "PCL Boost export inventory changed. Remove "
    ".local/native-rtabmap/external/Source/pcl, .local/native-rtabmap/external/Build/pcl "
    "and the pcl-{mkdir,download,update,patch,configure,build,install,done} files under "
    ".local/native-rtabmap/external/Stamp/pcl, then rerun make scan-native.")
endif()
