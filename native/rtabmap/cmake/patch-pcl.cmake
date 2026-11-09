# PCL 1.15 builds with only iostreams under C++17, but its generated package
# config unconditionally requests a separate Boost.System binary. Boost 1.86
# provides System header-only; keep its exported dependencies consistent.
set(path "${SOURCE_DIR}/cmake/pcl_pclconfig.cmake")
file(READ "${path}" contents)
set(old "set(PCLCONFIG_AVAILABLE_BOOST_MODULES \"system iostreams\")")
set(new "set(PCLCONFIG_AVAILABLE_BOOST_MODULES \"iostreams\")")
string(FIND "${contents}" "${old}" site)
if(site EQUAL -1)
  string(FIND "${contents}" "${new}" already_patched)
  if(already_patched EQUAL -1)
    message(FATAL_ERROR "PCL Boost export inventory changed")
  endif()
else()
  string(REPLACE "${old}" "${new}" contents "${contents}")
  file(WRITE "${path}" "${contents}")
endif()
