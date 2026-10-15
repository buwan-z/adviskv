#pragma once

#include <gtest/gtest.h>

#include <filesystem>
#include <string>

#include "common/path_util.h"
#include "common/status.h"

namespace raftbox::test {

inline std::filesystem::path test_data_dir() {
    return raftbox::path_from_config("data_dir");
}

inline std::filesystem::path make_unique_test_dir(const std::string& prefix,
                                                  int unique_id) {
    return test_data_dir() /
           (prefix + "_" +
            std::to_string(::testing::UnitTest::GetInstance()->random_seed()) +
            "_" + std::to_string(unique_id));
}

inline std::string status_debug_string(const Status& status) {
    return "code=" + std::to_string(static_cast<int>(status.code())) +
           ", msg=" + status.msg();
}

}  // namespace raftbox::test
