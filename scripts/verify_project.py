#!/usr/bin/env python3
"""Build and verify the smallest complete RaftBox cluster workflow."""

import os
import shutil
import signal
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


def configure_build_environment() -> None:
    """Use an available generator before importing the E2E build directory."""
    if os.environ.get("GENERATOR"):
        return

    configured_dir = os.environ.get("BUILD_DIR", "build")
    build_dir = Path(configured_dir)
    if not build_dir.is_absolute():
        build_dir = ROOT_DIR / build_dir

    cache = build_dir / "CMakeCache.txt"
    cached_generator = ""
    if cache.exists():
        for line in cache.read_text(errors="replace").splitlines():
            if line.startswith("CMAKE_GENERATOR:INTERNAL="):
                cached_generator = line.partition("=")[2]
                break

    if cached_generator == "Ninja" and shutil.which("ninja") is None:
        if "BUILD_DIR" in os.environ:
            raise RuntimeError(
                f"{build_dir} was configured with Ninja, but ninja is unavailable; "
                "install Ninja or choose another BUILD_DIR and GENERATOR='Unix Makefiles'"
            )
        if shutil.which("make") is None:
            raise RuntimeError("neither ninja nor make is available")
        os.environ["BUILD_DIR"] = "build-make"
        os.environ["GENERATOR"] = "Unix Makefiles"
        print("[verify] Ninja unavailable; using build-make with Unix Makefiles", flush=True)
    elif cached_generator:
        os.environ["GENERATOR"] = cached_generator
    elif shutil.which("ninja"):
        os.environ["GENERATOR"] = "Ninja"
    elif shutil.which("make"):
        os.environ["GENERATOR"] = "Unix Makefiles"
    else:
        raise RuntimeError("neither ninja nor make is available")


try:
    configure_build_environment()
except RuntimeError as exc:
    print(f"[verify] FAIL: {exc}", file=sys.stderr)
    raise SystemExit(1)

sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "test"))

from e2e.cluster import (  # noqa: E402
    RaftBoxCluster,
    BUILD_DIR,
    build_targets,
    clean_data_dirs,
    write_e2e_configs,
)


EXPECTED_OUTPUT = (
    "[ PASS ] create database:",
    "[ PASS ] create table:",
    "[ PASS ] table normal:",
    "[ PASS ] write and verify dataset: ok",
    "[ PASS ] overwrite and get the value: ok",
    "[ PASS ] delete key and get: ok",
    "[ PASS ] remove table: ok",
    "[ PASS ] recreate table read kvs: ok",
    "[ PASS ] basic_kv: pass",
)


def _interrupt(_signum, _frame):
    raise KeyboardInterrupt


def main() -> int:
    signal.signal(signal.SIGTERM, _interrupt)
    print("[verify] building Catalog, Topo, Storage, E2E client and CLI", flush=True)
    try:
        build_targets("topo topo_test catalog storage e2e_client raftboxctl")
        print(f"[verify] resetting local test data: {BUILD_DIR / 'e2e_test'}", flush=True)
        clean_data_dirs()
        write_e2e_configs()

        cluster = RaftBoxCluster()
        try:
            cluster.start()
            result = cluster.run_case(db="verify_db", table="verify_table", key_count=16)
            if result.returncode != 0:
                print(f"[verify] E2E client exited with {result.returncode}", file=sys.stderr)
                return 1
            missing = [marker for marker in EXPECTED_OUTPUT if marker not in result.stdout]
            if missing:
                print(f"[verify] missing expected output: {missing}", file=sys.stderr)
                return 1
        finally:
            cluster.stop()

        print("[verify] PASS: three-replica KV chain, overwrite, delete, table recreation", flush=True)
        print("[verify] all services started by this run have stopped", flush=True)
        return 0
    except KeyboardInterrupt:
        print("[verify] interrupted; local services are being stopped", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"[verify] FAIL: {exc}", file=sys.stderr)
        print(f"[verify] inspect local logs under {BUILD_DIR / 'e2e_test' / 'logs'}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
