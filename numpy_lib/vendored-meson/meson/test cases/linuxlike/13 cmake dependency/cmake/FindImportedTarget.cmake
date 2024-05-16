find_package(ZLIB)

if(ZLIB_FOUND OR ZLIB_Found)
  set(ImportedTarget_FOUND ON)
  add_library(mesonTestLibDefs SHARED IMPORTED)
  set_property(TARGET mesonTestLibDefs PROPERTY IMPORTED_LOCATION ${ZLIB_LIBRARY})
  set_property(TARGET mesonTestLibDefs PROPERTY INTERFACE_INCLUDE_DIRECTORIES ${ZLIB_INCLUDE_DIR})
  set_property(TARGET mesonTestLibDefs APPEND PROPERTY INTERFACE_COMPILE_DEFINITIONS REQUIRED_MESON_FLAG1)
  set_property(TARGET mesonTestLibDefs APPEND PROPERTY INTERFACE_COMPILE_DEFINITIONS $<$<NOT:$<CONFIG:Debug>>:;QT_NO_DEBUG;>) # Error empty string
  set_property(TARGET mesonTestLibDefs APPEND PROPERTY INTERFACE_COMPILE_DEFINITIONS REQUIRED_MESON_FLAG2)
  set_target_properties(mesonTestLibDefs PROPERTIES IMPORTED_GLOBAL TRUE)
  add_library(MesonTest::TestLibDefs ALIAS mesonTestLibDefs)
else()
  set(ImportedTarget_FOUND OFF)
endif()
