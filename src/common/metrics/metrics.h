#pragma once

#include <chrono>
#include <cstdint>
#include <memory>
#include <string>

#include "common/define.h"
#include "common/metrics/latency_recorder.h"
#include "common/status.h"

namespace raftbox {

struct MetricsOptions {
    bool http_enable{false};
    std::string http_host{"127.0.0.1"};
    int32_t http_port{0};
    std::string http_path{"/metrics"};
};

class RaftBoxMetrics {
public:
    static RaftBoxMetrics& get_instance();

    Status init(const MetricsOptions& options);
    void stop();
    void record_latency(const std::string& name, int64_t latency_us);
    void record_counter(const std::string& name, int64_t delta = 1);
    int64_t counter_value(const std::string& name) const;
    void reset();
    std::string dump_prometheus() const;

private:
    class Registry;
    class HttpServer;

    RaftBoxMetrics();
    ~RaftBoxMetrics();

    DISALLOW_COPY_AND_ASSIGN(RaftBoxMetrics)

    bool initialized_{false};
    std::unique_ptr<Registry> registry_;
    std::unique_ptr<HttpServer> http_server_;
};

class ScopedMetricsTimer {
public:
    explicit ScopedMetricsTimer(std::string name);
    ~ScopedMetricsTimer();

    DISALLOW_COPY_AND_ASSIGN(ScopedMetricsTimer)

private:
    std::string name_;
    std::chrono::steady_clock::time_point start_;
};

}  // namespace raftbox

#define RAFTBOX_CONCAT_INNER(x, y) x##y
#define RAFTBOX_CONCAT(x, y) RAFTBOX_CONCAT_INNER(x, y)
#define RAFTBOX_METRICS_COUNTER(...) ::raftbox::RaftBoxMetrics::get_instance().record_counter(__VA_ARGS__)
#define RAFTBOX_METRICS_TIMER(name) ::raftbox::ScopedMetricsTimer RAFTBOX_CONCAT(raftbox_metrics_timer_, __LINE__)(name)
