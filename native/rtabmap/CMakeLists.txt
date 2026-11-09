cmake_minimum_required(VERSION 3.25)
project(campervan_rtabmap_superbuild LANGUAGES C CXX)
include(ExternalProject)
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS
  "${CMAKE_CURRENT_SOURCE_DIR}/cmake/patch-flann.cmake"
  "${CMAKE_CURRENT_SOURCE_DIR}/cmake/patch-qhull.cmake"
  "${CMAKE_CURRENT_SOURCE_DIR}/cmake/patch-opencv.cmake"
  "${CMAKE_CURRENT_SOURCE_DIR}/cmake/patch-pcl.cmake"
  "${CMAKE_CURRENT_SOURCE_DIR}/cmake/patch-rtabmap.cmake"
  "${CMAKE_CURRENT_SOURCE_DIR}/extension/CMakeLists.txt"
  "${CMAKE_CURRENT_SOURCE_DIR}/extension/bridge.cpp")

get_filename_component(CACHE_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../../.local/native-rtabmap" ABSOLUTE)
set(PREFIX "${CACHE_ROOT}/prefix")
set(EP_BASE "${CACHE_ROOT}/external")
if(NOT EXISTS "${CMAKE_OSX_SYSROOT}/usr/lib/libz.tbd")
  message(FATAL_ERROR "The selected Apple SDK must provide usr/lib/libz.tbd")
endif()
set_property(DIRECTORY PROPERTY EP_BASE "${EP_BASE}")
set(COMMON
  -DCMAKE_INSTALL_PREFIX=${PREFIX}
  -DCMAKE_PREFIX_PATH=${PREFIX}
  -DCMAKE_IGNORE_PREFIX_PATH=/opt/homebrew|/usr/local|/opt/local
  -DCMAKE_FIND_USE_CMAKE_ENVIRONMENT_PATH=OFF -DCMAKE_FIND_USE_PACKAGE_REGISTRY=OFF -DCMAKE_FIND_USE_SYSTEM_PACKAGE_REGISTRY=OFF
  -DCMAKE_OSX_ARCHITECTURES=arm64 -DCMAKE_OSX_DEPLOYMENT_TARGET=14.0
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_STANDARD=17 -DCMAKE_POSITION_INDEPENDENT_CODE=ON
  -DCMAKE_C_VISIBILITY_PRESET=hidden -DCMAKE_CXX_VISIBILITY_PRESET=hidden
  -DCMAKE_VISIBILITY_INLINES_HIDDEN=ON -DBUILD_SHARED_LIBS=OFF
  -DBUILD_TESTING=OFF -DBUILD_TESTS=OFF -DBUILD_EXAMPLES=OFF)

# Keep source and object trees so an interrupted build can resume incrementally.
# All build inputs and outputs remain under the private cache root.
function(component name url hash)
  cmake_parse_arguments(C "" "SUBDIR;PATCH" "ARGS" ${ARGN})
  set(patch_command "")
  if(C_PATCH)
    # Include the patch content in the command identity, not only its path.
    file(SHA256 "${C_PATCH}" patch_input_hash)
    set(patch_command ${CMAKE_COMMAND} -DSOURCE_DIR=<SOURCE_DIR> -DTOOL_DIR=${CACHE_ROOT}/tools
      -DPRIVATE_PREFIX=${PREFIX} -DPATCH_INPUT_HASH=${patch_input_hash} -P ${C_PATCH})
  endif()
  ExternalProject_Add(${name} URL "${url}" URL_HASH "SHA256=${hash}"
    DOWNLOAD_DIR "${CACHE_ROOT}/archives" LIST_SEPARATOR "|" DOWNLOAD_NAME "${name}.tar.gz" DOWNLOAD_EXTRACT_TIMESTAMP TRUE
    SOURCE_SUBDIR "${C_SUBDIR}" PATCH_COMMAND ${patch_command}
    CMAKE_ARGS ${COMMON} ${C_ARGS}
    DEPENDS ${previous})
  set(previous ${name} PARENT_SCOPE)
endfunction()

component(eigen https://gitlab.com/libeigen/eigen/-/archive/3147391d946bb4b6c68edd901f2add6ac1f31f8c/eigen-3147391d946bb4b6c68edd901f2add6ac1f31f8c.tar.gz 0c8c490764f9c2a793133491adca0cd073b73e0bde965c68cbe58d91b5ed4261 ARGS -DEIGEN_BUILD_DOC=OFF)
component(lz4 https://codeload.github.com/lz4/lz4/tar.gz/ebb370ca83af193212df4dcbadcc5d87bc0de2f0 eb1a93e934d4fd29df6e2061ba0bf447568561764d758f4a5662c0e29370ffa9 SUBDIR build/cmake ARGS -DLZ4_BUILD_CLI=OFF -DLZ4_BUILD_LEGACY_LZ4C=OFF -DLZ4_BUILD_SHARED=OFF -DLZ4_BUILD_STATIC=ON)
component(flann https://codeload.github.com/flann-lib/flann/tar.gz/c50f296b0b27e14667d272b37acc63f949b305c4 f8d004c21d3a565154dc742ede0e31d50cecc06e49f60b5431ca947fbf5de037 PATCH ${CMAKE_CURRENT_SOURCE_DIR}/cmake/patch-flann.cmake ARGS -DBUILD_C_BINDINGS=OFF -DBUILD_PYTHON_BINDINGS=OFF -DBUILD_MATLAB_BINDINGS=OFF -DBUILD_DOC=OFF -DBUILD_TESTS=OFF -DBUILD_EXAMPLES=OFF -DUSE_OPENMP=OFF)
component(qhull https://codeload.github.com/qhull/qhull/tar.gz/613debeaea72ee66626dace9ba1a2eff11b5d37d b4504a190dc15c3ae932b998a2eed3cba8c7bdda1ab2a886e7e09d0526ee8143 PATCH ${CMAKE_CURRENT_SOURCE_DIR}/cmake/patch-qhull.cmake)
component(suitesparse https://codeload.github.com/DrTimothyAldenDavis/SuiteSparse/tar.gz/d3c4926d2c47fd6ae558e898bfc072ade210a2a1 d1ddf6027190821091198682a6b880cd5cb905fece9bf81aaa5379b415ab32c9 ARGS -DSUITESPARSE_ENABLE_PROJECTS=suitesparse_config|cxsparse -DBUILD_STATIC_LIBS=ON -DSUITESPARSE_USE_OPENMP=OFF)
component(g2o https://codeload.github.com/RainerKuemmerle/g2o/tar.gz/eec325a1da1273e87bc97887d49e70570f28570c 2f664ae1e0661341d6715cfe3f0b013da5873d042d2fc13ba83e80a2f29a07a3 ARGS -DG2O_USE_CSPARSE=ON -DG2O_USE_CHOLMOD=OFF -DG2O_USE_OPENGL=OFF -DG2O_USE_LOGGING=OFF -DG2O_USE_OPENMP=OFF -DG2O_BUILD_APPS=OFF -DG2O_BUILD_EXAMPLES=OFF -DG2O_BUILD_BENCHMARKS=OFF -DBUILD_UNITTESTS=OFF)
# Boost uses b2 rather than CMake.
ExternalProject_Add(boost URL https://archives.boost.io/release/1.86.0/source/boost_1_86_0.tar.gz URL_HASH SHA256=2575e74ffc3ef1cd0babac2c1ee8bdb5782a0ee672b1912da40e5b4b591ca01f DOWNLOAD_DIR "${CACHE_ROOT}/archives" DOWNLOAD_EXTRACT_TIMESTAMP TRUE BUILD_IN_SOURCE TRUE
  CONFIGURE_COMMAND <SOURCE_DIR>/bootstrap.sh --prefix=${PREFIX} --with-libraries=iostreams
  BUILD_COMMAND <SOURCE_DIR>/b2 -j2 link=static threading=multi variant=release "cxxflags=-fPIC -fvisibility=hidden -mmacosx-version-min=14.0 -arch arm64" cxxstd=17 -sNO_BZIP2=1 -sNO_LZMA=1 -sNO_ZSTD=1 -sZLIB_INCLUDE=/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk/usr/include -sZLIB_LIBPATH=/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk/usr/lib
  INSTALL_COMMAND <SOURCE_DIR>/b2 -j2 install --prefix=${PREFIX} link=static threading=multi variant=release "cxxflags=-fPIC -fvisibility=hidden -mmacosx-version-min=14.0 -arch arm64" cxxstd=17 -sNO_BZIP2=1 -sNO_LZMA=1 -sNO_ZSTD=1 -sZLIB_INCLUDE=/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk/usr/include -sZLIB_LIBPATH=/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk/usr/lib
  DEPENDS ${previous})
set(previous boost)
component(opencv https://codeload.github.com/opencv/opencv/tar.gz/49486f61fb25722cbcf586b7f4320921d46fb38e 8f00b42869ab2836be36090f6631ae4c38ba59171e22a69a8e0f92f8ef1771d4 PATCH ${CMAKE_CURRENT_SOURCE_DIR}/cmake/patch-opencv.cmake ARGS
  -DBUILD_LIST=core,imgproc,imgcodecs,features2d,flann,calib3d,photo,stitching,video,videoio,highgui,objdetect
  -DBUILD_TESTS=OFF -DBUILD_PERF_TESTS=OFF -DBUILD_opencv_apps=OFF -DBUILD_opencv_dnn=OFF -DBUILD_opencv_gapi=OFF
  -DWITH_PROTOBUF=OFF -DWITH_ADE=OFF -DBUILD_JPEG=ON -DBUILD_PNG=ON -DBUILD_ZLIB=OFF
  -DWITH_OPENCL=OFF -DWITH_CUDA=OFF -DWITH_IPP=OFF -DWITH_FFMPEG=OFF -DWITH_GSTREAMER=OFF -DWITH_AVFOUNDATION=OFF -DWITH_COCOA=OFF -DVIDEOIO_ENABLE_PLUGINS=OFF -DHIGHGUI_ENABLE_PLUGINS=OFF -DWITH_QT=OFF -DWITH_OPENGL=OFF -DWITH_TIFF=OFF -DWITH_WEBP=OFF -DWITH_OPENJPEG=OFF -DWITH_JASPER=OFF -DWITH_OPENEXR=OFF -DWITH_IMGCODEC_GIF=OFF -DWITH_IMGCODEC_SUNRASTER=OFF -DWITH_IMGCODEC_HDR=OFF -DWITH_IMGCODEC_PXM=OFF -DWITH_IMGCODEC_PFM=OFF)
component(pcl https://codeload.github.com/PointCloudLibrary/pcl/tar.gz/3346843ea6b97697a1577293aa9cdf236b5c7ffb 6769a75b1e1c38bab89408cb4f54566991bb6123823bdddec6f7754e859ec9b1 PATCH ${CMAKE_CURRENT_SOURCE_DIR}/cmake/patch-pcl.cmake ARGS
  -DPCL_SHARED_LIBS=OFF -DPCL_FLANN_REQUIRED_TYPE=STATIC -DPCL_QHULL_REQUIRED_TYPE=STATIC
  -DZLIB_INCLUDE_DIR=${CMAKE_OSX_SYSROOT}/usr/include -DZLIB_LIBRARY_RELEASE=${CMAKE_OSX_SYSROOT}/usr/lib/libz.tbd
  -DBUILD_global_tests=OFF -DUSE_HOMEBREW_FALLBACK=OFF -DWITH_VTK=OFF -DWITH_QT=NO -DWITH_CUDA=OFF -DWITH_OPENGL=OFF -DWITH_GLEW=OFF -DWITH_LIBUSB=OFF -DWITH_PCAP=OFF -DWITH_OPENNI=OFF -DWITH_OPENNI2=OFF -DWITH_OPENMP=OFF -DWITH_PNG=OFF -DWITH_SYSTEM_CJSON=OFF -DWITH_QHULL=ON
  -DBUILD_apps=OFF -DBUILD_tools=OFF -DBUILD_keypoints=OFF -DBUILD_visualization=OFF -DBUILD_recognition=OFF -DBUILD_people=OFF -DBUILD_tracking=OFF -DBUILD_outofcore=OFF -DBUILD_simulation=OFF -DBUILD_stereo=OFF -DBUILD_gpu=OFF)
component(rtabmap https://codeload.github.com/introlab/rtabmap/tar.gz/8cd2f81a735722402d1e220147c4e83a1a746eaf 9e81f80ccd7fc1b5dddbfbc754f9c1445707b6e4ed45136beea3d5e9cf4dd92a PATCH ${CMAKE_CURRENT_SOURCE_DIR}/cmake/patch-rtabmap.cmake ARGS
  -DWITH_QT=OFF -DWITH_G2O=ON -DWITH_GTSAM=OFF -DWITH_TORO=OFF -DWITH_CERES=OFF -DWITH_MRPT=OFF -DWITH_VERTIGO=OFF -DWITH_POINTMATCHER=OFF -DWITH_OPEN3D=OFF -DWITH_PDAL=OFF -DWITH_PYTHON=OFF -DWITH_TORCH=OFF -DWITH_OCTOMAP=OFF -DWITH_FREENECT=OFF -DWITH_FREENECT2=OFF -DWITH_K4W2=OFF -DWITH_K4A=OFF -DWITH_OPENNI=OFF -DWITH_OPENNI2=OFF -DWITH_DC1394=OFF -DWITH_FLYCAPTURE2=OFF -DWITH_ZED=OFF -DWITH_ZEDOC=OFF -DWITH_REALSENSE=OFF -DWITH_REALSENSE_SLAM=OFF -DWITH_REALSENSE2=OFF -DWITH_MYNTEYE=OFF -DWITH_FASTCV=OFF -DWITH_OPENMP=OFF -DWITH_OPENGV=OFF -DBUILD_APP=OFF -DBUILD_TOOLS=OFF -DBUILD_EXAMPLES=OFF -DBUILD_PERF_TESTS=OFF)

# The extension configures only after the private dependency prefix exists.
file(SHA256 "${CMAKE_CURRENT_SOURCE_DIR}/CMakeLists.txt" recipe_hash)
file(SHA256 "${CMAKE_CURRENT_SOURCE_DIR}/cmake/patch-flann.cmake" flann_patch_hash)
file(SHA256 "${CMAKE_CURRENT_SOURCE_DIR}/cmake/patch-rtabmap.cmake" rtabmap_patch_hash)
file(SHA256 "${CMAKE_CURRENT_SOURCE_DIR}/cmake/patch-qhull.cmake" qhull_patch_hash)
file(SHA256 "${CMAKE_CURRENT_SOURCE_DIR}/cmake/patch-opencv.cmake" opencv_patch_hash)
file(SHA256 "${CMAKE_CURRENT_SOURCE_DIR}/cmake/patch-pcl.cmake" pcl_patch_hash)
file(SHA256 "${CMAKE_CURRENT_SOURCE_DIR}/extension/CMakeLists.txt" extension_recipe_hash)
file(SHA256 "${CMAKE_CURRENT_SOURCE_DIR}/extension/bridge.cpp" bridge_hash)
string(SHA256 build_id "${recipe_hash}${flann_patch_hash}${rtabmap_patch_hash}${qhull_patch_hash}${opencv_patch_hash}${pcl_patch_hash}${extension_recipe_hash}${bridge_hash}")
ExternalProject_Add(extension SOURCE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/extension"
  BINARY_DIR "${CACHE_ROOT}/extension-build" LIST_SEPARATOR "|"
  DOWNLOAD_COMMAND "" UPDATE_COMMAND "" PATCH_COMMAND ""
  CMAKE_ARGS ${COMMON} -DCMAKE_INSTALL_PREFIX=${CMAKE_INSTALL_PREFIX}
    -DPython_EXECUTABLE=${Python_EXECUTABLE} -DTOOL_DIR=${CACHE_ROOT}/tools -DBUILD_ID=${build_id}
  DEPENDS rtabmap)
configure_file("${CMAKE_CURRENT_SOURCE_DIR}/build-info.json.in" "${CMAKE_CURRENT_BINARY_DIR}/build-info.json" @ONLY)
install(FILES "${CMAKE_CURRENT_BINARY_DIR}/build-info.json" DESTINATION campervan_rtabmap)
