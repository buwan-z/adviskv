# RaftBox naming migration

The project is now **RaftBox** (RaftBox｜基于 Raft 的分布式 KV 存储系统).
This is a single coordinated rename, without aliases for the previous interfaces.

## New development and deployment names

| Interface | Current name |
| --- | --- |
| C++ namespace and Protobuf package prefix | `raftbox` |
| CMake project and library target prefix | `raftbox`, `raftbox_` |
| Compile definitions, CMake options, environment variables | `RAFTBOX_` |
| CLI and default configuration | `raftboxctl`, `conf/raftboxctl.yaml` |
| Interactive demo | `./scripts/raftboxctl_demo.sh` |
| Local dependency root | `.raftbox_deps/` |
| Prometheus metrics | `raftbox_` |
| Repository | `git@github.com:buwan-z/raftbox.git` |

Recompile SDK clients together with Catalog, Topo, and Storage, and deploy them as
one version. The Protobuf package rename changes the gRPC service paths; mixing
old clients and new servers is unsupported. Update automation, compiler options,
environment variables, metric queries, and dashboard prefixes to the new names.

## Clean build and validation

Use Ubuntu 24.04 or a Linux environment with the prerequisites in the README.
Start a fresh build after renaming the checkout; existing CMake caches contain
absolute source paths and must not be reused.

```bash
git submodule update --init --recursive
./scripts/setup.sh
BUILD_DIR=build-raftbox ./scripts/build.sh
ctest --test-dir build-raftbox --output-on-failure
BUILD_DIR=build-raftbox ./scripts/e2e_pytest.sh -q
BUILD_DIR=build-raftbox python3 scripts/verify_project.py
BUILD_DIR=build-raftbox ./scripts/raftboxctl_demo.sh
```

The setup script uses the new dependency directory. An existing dependency cache
can be retained separately; no existing cache or runtime data is deleted by the
rename. Preserve live data directories and stop the old cluster before deploying
new binaries. The rename does not change WAL/Snapshot framing, format constants,
Protobuf field numbers, or stored message structures. Existing persistence and
restart tests remain the acceptance checks. Test/demo commands reset their own
test data, as documented in the README.

## Historical material

Original author and license information is unchanged. The external blog keeps its
original published title and URL. Benchmark JSON files under `docs/v0.1.0/` keep
the original machine paths as recorded measurement metadata. Original branding
and recordings are in [the historical media archive](assets/history/README.md).
These are intentional historical uses of the previous project name.

## Checkout location

The intended Windows checkout is `F:\agent\raftbox`. Reopen that folder after
moving the checkout, then configure a fresh build. Update other local clones with:

```bash
git remote set-url origin git@github.com:buwan-z/raftbox.git
```
