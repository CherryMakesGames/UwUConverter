cmake_minimum_required(VERSION 3.21)
project(UwUConverterShell LANGUAGES CXX)

add_library(
    UwUConverterShell
    SHARED
    UwUConverterShell.cpp
    UwUConverterShell.def
)

target_compile_features(UwUConverterShell PRIVATE cxx_std_17)

target_compile_definitions(
    UwUConverterShell
    PRIVATE
    UNICODE
    _UNICODE
    WIN32_LEAN_AND_MEAN
    NOMINMAX
)

target_link_libraries(
    UwUConverterShell
    PRIVATE
    Ole32
    Shell32
    Shlwapi
)

set_target_properties(
    UwUConverterShell
    PROPERTIES
    PREFIX ""
    OUTPUT_NAME "UwUConverterShell"
)
