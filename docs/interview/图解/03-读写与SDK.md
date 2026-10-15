# 03｜读写与 SDK

先分别记住写的提交点和读的安全点，再用[题库](../分层面试题库.md)解释失败分支。

## 图 6：Put 的四个完成点

```mermaid
sequenceDiagram
    participant U as 调用方
    participant S as SDK
    participant L as Storage Leader / ReplicaLoop
    participant W as Leader WAL
    participant F as Raft Followers
    participant A as ReplicaApplier / Map

    U->>S: Put(key, value, request_id)
    S->>S: 按 key 解析 shard 路由
    S->>L: Put RPC 发往 Leader
    L->>L: 去重检查并提出 Raft 日志
    L->>W: 本地 WAL 持久化
    L->>F: AppendEntries
    F-->>L: 有效复制响应
    L->>L: 当前配置下达到多数派，推进 commit_index
    L-->>S: 提案已提交，返回 OK
    S-->>U: 明确成功
    L->>A: 后台 apply 已提交日志及 request record
    Note over L,A: apply 可晚于本次 Put 返回；Get 会追到 ReadIndex 再读取
```

**口述主线**：SDK 定位 Leader，ReplicaLoop 去重并提议；持久化层先写 Leader WAL，再发送 Raft 消息。多数派确认后推进提交位置并唤醒 Put 等待者；后台 applier 把已提交日志写入 Map 和 request record。

**易错点**：本地 WAL 成功不等于多数派提交；当前代码的 Put OK 以提交为条件，**不等待本次状态机 apply**。若超时，后续仍可能提交，不能断言失败。

**题库**：[4、21、40、45、53、66](../分层面试题库.md)；**源码**：[SDK 请求](../../../src/sdk/client.cpp)、[Replica::put](../../../src/storage/replica/replica.cpp)、[提案完成条件](../../../src/storage/replica/replica_loop.cpp)、[状态机应用](../../../src/storage/replica/replica_applier.cpp)。

## 图 7：SDK 如何决定重试和刷新路由

```mermaid
flowchart TD
    send["向当前 Leader 发一次 RPC"] --> result{"结果？"}
    result -->|OK| ok["返回 OK"]
    result -->|NOT_LEADER / REPLICA_NOT_FOUND<br/>ROUTE_NOT_FOUND / IS_RECOVERING / RPC_ERROR| refresh["可重试：刷新整表路由"]
    result -->|NOT_YET_COMMIT / READ_INDEX_NOT_READY<br/>RESOURCE_EXHAUSTED| same["可重试：沿当前路由再试"]
    result -->|其他错误| stop["返回具体错误"]
    refresh --> budget{"刷新次数、Storage 次数<br/>及总 deadline 仍允许？"}
    same --> budget
    budget -->|是| backoff["退避后再发；单次 RPC 受剩余时间约束"]
    backoff --> send
    budget -->|否| final["按最终结果语义返回"]
```

**口述主线**：错误分成“可能是路由失效”和“当前节点暂时未就绪”两类；前者刷新 Topo 路由，后者保留路由重试。Storage 尝试次数、刷新次数和总 deadline 各有限额。

**易错点**：不是所有错误都能重试，也不是每次重试都查 Topo；对写请求，只有曾出现 `RPC_ERROR` 或 `NOT_YET_COMMIT` 时，预算耗尽才由 SDK 归为 `UNKNOWN`。

**题库**：[15、19–21、24、28、86](../分层面试题库.md)；**源码**：[错误分类与重试](../../../src/sdk/client.cpp)、[SDK 配置](../../../src/sdk/config.h)、[路由缓存](../../../src/sdk/route_cache.cpp)。

## 图 8：`request_id`、去重与 `UNKNOWN`

```mermaid
flowchart TD
    logical["同一笔逻辑 Put / Delete<br/>固定 request_id + 固定内容"] --> lookup["Storage 查已应用的 request record"]
    lookup -->|同 ID、同内容| old["返回已完成结果"]
    lookup -->|同 ID、不同内容| conflict["INVALID_ARGUMENT"]
    lookup -->|未找到| inflight["查当前 Leader 的 inflight 提案"]
    inflight -->|同 ID、同内容| wait["等待原提案；已提交则返回 OK"]
    inflight -->|同 ID、不同内容| conflict
    inflight -->|未找到| raft["新建 Raft 提案"]
    raft --> uncertainty{"客户端在预算内<br/>确认提交结果？"}
    uncertainty -->|是| definite["返回明确结果"]
    uncertainty -->|否，曾发生不确定写错误| unknown["SDK 返回 UNKNOWN"]
    unknown --> retry["业务保留原 ID 和内容后重试"]
    retry --> lookup
```

**口述主线**：SDK 为逻辑写生成或接受 `request_id`，重试不换 ID；Storage 先查已应用记录，再查 inflight，最后才新提议。记录进入状态机和 Snapshot，以便恢复后去重。

**易错点**：`UNKNOWN` 表示客户端无法确认结果，写可能已提交；一次普通 Get 不能普遍证明原写是否提交。`request_id` 记录当前无 TTL，同 ID 换内容会报错。

**题库**：[14、21–23、45、78、93](../分层面试题库.md)；**源码**：[SDK request ID](../../../src/sdk/client.cpp)、[Storage 去重](../../../src/storage/replica/replica_loop.cpp)、[状态机记录](../../../src/storage/raft/state_machine/kv_state_machine.cpp)。

## 图 9：Get 的 ReadIndex 安全读路径

```mermaid
sequenceDiagram
    participant U as 调用方
    participant S as SDK
    participant L as Storage Leader
    participant Q as Raft Voters
    participant A as Applier / 内存 Map

    U->>S: Get(key)
    S->>L: 按路由请求 shard Leader
    L->>L: 检查当前任期已有已提交 entry
    alt 条件未满足
        L-->>S: READ_INDEX_NOT_READY
    else 条件满足
        L->>L: 记录 read_index = commit_index 与 read_term
        L->>Q: 发 AppendEntries / 心跳确认任期
        alt 无法确认当前任期的多数派
            L-->>S: 错误；不能返回旧 Map 值
        else 多数派确认
            L->>A: apply 已提交日志到 read_index
            A-->>L: apply_index >= read_index
            L->>A: 读取 key
            L-->>S: 返回 value 或 KEY_NOT_FOUND
        end
    end
    S-->>U: 结果或可重试错误
```

**口述主线**：旧 Leader 可能仍自认是 Leader，因此读前需要当前任期已提交条目，再向多数派确认身份。取得 read index 后，Replica 先让状态机追到该位置，再读 Map。

**易错点**：ReadIndex 不是纯本地读，也不要求这次 Get 写一条业务日志；项目未实现 Lease Read 或开放 Follower 陈旧读 API。多数派不可达时不能声称总能读到值。

**题库**：[5、25、46–47、67、88](../分层面试题库.md)；**源码**：[Raft 读入口](../../../src/storage/raft/core/raft_core_read.cpp)、[多数派确认](../../../src/storage/replica/replica_read_index_checker.cpp)、[Replica::get](../../../src/storage/replica/replica.cpp)。
