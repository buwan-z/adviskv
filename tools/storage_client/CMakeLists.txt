add_library(raftbox_tools_storage_client
    ${CMAKE_CURRENT_SOURCE_DIR}/storage_client.cpp
)

target_link_libraries(raftbox_tools_storage_client PUBLIC
    raftbox_common
)

target_include_directories(raftbox_tools_storage_client PUBLIC
    ${CMAKE_SOURCE_DIR}
    ${CMAKE_SOURCE_DIR}/src
)
