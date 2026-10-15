set(RAFTBOX_SDK_SOURCES
    ${CMAKE_CURRENT_SOURCE_DIR}/client.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/route_cache.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/topo_route_client.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/storage_client.cpp
)

add_library(raftbox_sdk
    ${RAFTBOX_SDK_SOURCES}
)

target_link_libraries(raftbox_sdk PUBLIC
    raftbox_common
)

target_include_directories(raftbox_sdk PUBLIC
    ${CMAKE_SOURCE_DIR}/src
)