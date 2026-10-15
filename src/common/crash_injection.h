#pragma once

#include <cstdlib>
#include <cstring>

#include <unistd.h>

namespace raftbox::testhook {

inline bool crash_point_enabled(const char* name) {
#ifdef RAFTBOX_ENABLE_CRASH_TEST
    if (!name) return false;
    const char* target = std::getenv("RAFTBOX_ENABLE_CRASH_POINT");
    return target != nullptr && std::strcmp(name, target) == 0;
#else
    (void)name;
    return false;
#endif
}

inline void crash_point(const char* name) {
#ifdef RAFTBOX_ENABLE_CRASH_TEST
    if (!name) {
        return;
    }
    if (crash_point_enabled(name)) {
        ::_exit(137);
    }
#else
    (void)name;
#endif
}

}  // namespace raftbox::testhook