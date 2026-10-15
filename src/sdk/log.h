#pragma once

#include <string>
#include <string_view>

#include <fmt/format.h>

#include "sdk/config.h"

namespace raftbox::sdk {

inline std::string_view level_to_string(LogLevel level) {
    switch (level) {
        case LogLevel::DEBUG:
            return "DEBUG";
        case LogLevel::INFO:
            return "INFO";
        case LogLevel::WARN:
            return "WARN";
        case LogLevel::ERROR:
            return "ERROR";
    }
    return "UNKNOWN";
}

inline bool should_log(const KVClientConf& conf, LogLevel level) {
    return conf.log.callback && static_cast<int>(level) >= static_cast<int>(conf.log.level);
}

}  // namespace raftbox::sdk

#define RAFTBOX_SDK_LOG(level, ...)                                                            \
    do {                                                                                       \
        const auto& raftbox_sdk_log_conf = (conf_);                                            \
        const auto raftbox_sdk_log_level = (level);                                            \
        if (::raftbox::sdk::should_log(raftbox_sdk_log_conf, raftbox_sdk_log_level)) {         \
            const std::string raftbox_sdk_log_message = fmt::format(__VA_ARGS__);              \
            raftbox_sdk_log_conf.log.callback(raftbox_sdk_log_level, raftbox_sdk_log_message); \
        }                                                                                      \
    } while (0)
