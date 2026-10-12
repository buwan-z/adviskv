# Get 读取链路（ReadIndex）

可编辑时序图：[`get_read_index_sequence.excalidraw`](get_read_index_sequence.excalidraw)

## 先记住这条顺序

```text
CLI/SDK 选 shard 和 Leader
→ Leader 用 ReadIndex 确认自己仍被多数派认可
→ 得到 read_index（当前 commit_index）
→ 把状态机应用到 read_index
→ 从本地 KV 引擎（当前是 Map）查 key
→ 返回 value 或 KEY_NOT_FOUND
```

Topo 只在 SDK 路由缓存缺失或需要刷新时参与；正常 Get 通常按缓存路由直达 Storage Leader。

## 代码沿线阅读

1. [`src/sdk/client.cpp`](../../src/sdk/client.cpp)：`KVClient::get()` 调用 `run_kv_request()`，解析路由并执行 RPC。
2. [`src/sdk/route_cache.cpp`](../../src/sdk/route_cache.cpp)：`lookup_cached_route()` 用 key 算 shard；缓存未命中时刷新路由。
3. [`src/sdk/storage_client.cpp`](../../src/sdk/storage_client.cpp)：`StorageClient::get()` 选路由里的 Leader，发 Storage Get RPC。
4. [`src/storage/handler/storage_service_impl.cpp`](../../src/storage/handler/storage_service_impl.cpp)：`StorageServiceImpl::Get()` 找到本地 `Replica` 并调用 `replica->get()`。
5. [`src/storage/replica/replica.cpp`](../../src/storage/replica/replica.cpp)：`Replica::get()` 先调用 `check_self_leader_and_get_read_index()`，再 apply 已提交日志，确认 `apply_index >= read_index`，最后读状态机。
6. [`src/storage/replica/replica_read_index_checker.cpp`](../../src/storage/replica/replica_read_index_checker.cpp)：向副本发送 AppendEntries/心跳并确认当前 Leader 仍有多数派支持。
7. [`src/storage/raft/core/raft_core_read.cpp`](../../src/storage/raft/core/raft_core_read.cpp)：`build_append_entries_for_read()` 检查本任期已提交日志，设置 `read_index = commit_index`，广播 AppendEntries。
8. [`src/storage/raft/state_machine/kv_state_machine.cpp`](../../src/storage/raft/state_machine/kv_state_machine.cpp)：状态机最终通过 `engine_->get()` 读取；当前 `EngineType::MAP` 对应 Map 引擎。

## 术语用白话说

- **commit_index**：Raft 已经确认提交到哪一条日志。
- **read_index**：这次读取至少要看到的日志位置。
- **apply_index**：状态机已经执行到哪一条日志。
- 正常读要求 `apply_index >= read_index`，否则 Map 可能还没反映已提交写入。
- 多数派确认不是为了给 Get 复制一条新数据，而是证明 Leader 身份仍有效。
- 新 Leader 尚未提交本任期日志时，ReadIndex 暂不可用；新 Leader 先提交 no-op 后再服务线性一致读。
