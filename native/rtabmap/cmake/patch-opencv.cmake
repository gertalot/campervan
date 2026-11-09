# OpenCV 4.12 selects Cocoa unconditionally for Apple Clang. Honor the
# explicitly disabled backend while retaining highgui's upstream no-GUI stubs.
file(SHA256 "${CMAKE_CURRENT_LIST_FILE}" actual_patch_hash)
if(NOT actual_patch_hash STREQUAL PATCH_INPUT_HASH)
  message(FATAL_ERROR "OpenCV patch changed during the build; rerun make scan-native.")
endif()
set(path "${SOURCE_DIR}/cmake/OpenCVFindLibsGUI.cmake")
file(READ "${path}" contents)
set(old "if(NOT IOS AND NOT XROS AND CV_CLANG)")
set(new "if(WITH_COCOA AND NOT IOS AND NOT XROS AND CV_CLANG)")
string(REGEX MATCHALL "if\\(NOT IOS AND NOT XROS AND CV_CLANG\\)" pristine "${contents}")
string(REGEX MATCHALL "if\\(WITH_COCOA AND NOT IOS AND NOT XROS AND CV_CLANG\\)" patched "${contents}")
list(LENGTH pristine pristine_count)
list(LENGTH patched patched_count)
if(pristine_count EQUAL 1 AND patched_count EQUAL 0)
  string(REPLACE "${old}" "${new}" contents "${contents}")
  file(WRITE "${path}" "${contents}")
elseif(pristine_count EQUAL 0 AND patched_count EQUAL 1)
  # Already applied by this patch; do not touch source timestamps.
else()
  message(FATAL_ERROR "OpenCV Cocoa selection changed. Remove "
    ".local/native-rtabmap/external/Source/opencv, .local/native-rtabmap/external/Build/opencv "
    "and the opencv-{mkdir,download,update,patch,configure,build,install,done} files under "
    ".local/native-rtabmap/external/Stamp/opencv, then rerun make scan-native.")
endif()
