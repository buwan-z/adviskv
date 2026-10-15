add_executable(raftboxctl
    ${CMAKE_CURRENT_SOURCE_DIR}/src/raftboxctl.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/src/direct_catalog_client.cpp
)

target_link_libraries(raftboxctl PRIVATE
    raftbox_sdk
)

target_include_directories(raftboxctl PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/src
    ${CMAKE_SOURCE_DIR}/src
)
