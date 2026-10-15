#pragma once
#include "common/background_task.h"
#include "common/model/type.h"

namespace raftbox::storage {

class ReplicaManager;

class RaftTickTask : public BackgroundTask {
public:
    explicit RaftTickTask(ReplicaManager* manager);

    void run() override;

private:
    ReplicaManager* manager_;
};

}  // namespace raftbox::storage