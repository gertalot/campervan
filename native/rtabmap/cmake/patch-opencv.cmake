# OpenCV 4.12 selects Cocoa unconditionally for Apple Clang. Honor the
# explicitly disabled backend while retaining highgui's upstream no-GUI stubs.
set(path "${SOURCE_DIR}/cmake/OpenCVFindLibsGUI.cmake")
file(READ "${path}" contents)
set(old "if(NOT IOS AND NOT XROS AND CV_CLANG)")
string(REGEX MATCHALL "if\\(NOT IOS AND NOT XROS AND CV_CLANG\\)" sites "${contents}")
list(LENGTH sites count)
if(NOT count EQUAL 1)
  message(FATAL_ERROR "OpenCV Cocoa selection changed: ${count}")
endif()
string(REPLACE "${old}" "if(WITH_COCOA AND NOT IOS AND NOT XROS AND CV_CLANG)" contents "${contents}")
file(WRITE "${path}" "${contents}")
