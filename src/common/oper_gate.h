#pragma once

#include <atomic>
#include <mutex>
#include <shared_mutex>
#include <utility>

#include "common/define.h"
#include "common/status.h"

namespace raftbox {

class OperGate {
public:
    class Guard {
    public:
        Guard() = default;
        DISALLOW_COPY_AND_ASSIGN(Guard)
        ALLOW_MOVE_AND_ASSIGN(Guard)

    private:
        friend class OperGate;
        explicit Guard(std::shared_lock<std::shared_mutex>&& lock) : lock_(std::move(lock)) {}

        std::shared_lock<std::shared_mutex> lock_;
    };

    OperGate() = default;
    DISALLOW_COPY_AND_ASSIGN(OperGate)

    Status acquire(Guard& guard) const {
        if (closed_.load()) {
            return Status::ERROR("oper gate is closed");
        }

        std::shared_lock lock(mutex_);

        if (closed_.load()) {
            return Status::ERROR("oper gate is closed");
        }

        guard = Guard(std::move(lock));
        return Status::OK();
    }

    void close_and_wait() {
        closed_.store(true);
        std::unique_lock lock(mutex_);
    }

private:
    std::atomic<bool> closed_{false};
    mutable std::shared_mutex mutex_;
};

#define RAFTBOX_OPER_GATE_CONCAT_INNER(x, y) x##y
#define RAFTBOX_OPER_GATE_CONCAT(x, y) RAFTBOX_OPER_GATE_CONCAT_INNER(x, y)

#define RETURN_IF_OPER_GUARD_ACQUIRE_FAILED(gate)                                       \
    ::raftbox::OperGate::Guard RAFTBOX_OPER_GATE_CONCAT(raftbox_oper_guard_, __LINE__); \
    RETURN_IF_INVALID_STATUS((gate).acquire(RAFTBOX_OPER_GATE_CONCAT(raftbox_oper_guard_, __LINE__)))

#define RETURN_IF_OPER_GUARD_ACQUIRE_FAILED_VOID(gate)                                  \
    ::raftbox::OperGate::Guard RAFTBOX_OPER_GATE_CONCAT(raftbox_oper_guard_, __LINE__); \
    if (((gate).acquire(RAFTBOX_OPER_GATE_CONCAT(raftbox_oper_guard_, __LINE__))).fail()) return;

}  // namespace raftbox