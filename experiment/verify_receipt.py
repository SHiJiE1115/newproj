"""Fail-closed second-VM verifier for one prospective Wine trace receipt.

PASS proves a listed new run's output and selected raw syscall events. It
does not certify every byte consumed or the original paper's execution.
"""

from __future__ import annotations

import csv
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import statistics
import sys
import tarfile
import tempfile


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
MAX_TAR_BYTES = 150_000_000
MAX_EXTRACTED_BYTES = 180_000_000
MAX_MEMBERS = 180
MAX_JSON_BYTES = 200_000
MAX_INPUT_BYTES = 200_000
MAX_TRACE_BYTES = 80_000_000
WINE_SUFFIX = "/experiments/datasets/raw/wine.raw"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def limited(path: Path, cap: int) -> bytes:
    with path.open("rb") as stream:
        data = stream.read(cap + 1)
    if len(data) > cap:
        raise ValueError(f"OVERSIZE_{path.name}")
    return data


def obj(path: Path) -> dict:
    value = json.loads(limited(path, MAX_JSON_BYTES))
    if not isinstance(value, dict):
        raise ValueError("JSON_OBJECT_REQUIRED")
    return value


def expected_sources() -> tuple[dict, dict]:
    freeze = obj(HERE / "FREEZE.json")
    expected = freeze["sha256_by_relative_path"]
    if not isinstance(expected, dict) or len(expected) != 9:
        raise ValueError("BAD_SOURCE_FREEZE")
    actual = {name: sha((ROOT / name).read_bytes()) for name in expected}
    if actual != expected:
        raise ValueError("VERIFIER_CHECKOUT_NOT_FROZEN")
    return freeze, expected


def audit_tree(directory: Path, *, require_source_snapshot: bool = True,
               expected_identity: dict | None = None) -> dict:
    checks: dict[str, bool] = {}
    observations: dict = {}
    try:
        freeze, expected = expected_sources()
        if require_source_snapshot:
            copied = directory / "source"
            checks["frozen_source_snapshot"] = all(
                sha(limited(copied / name, 300_000)) == digest
                for name, digest in expected.items()) and (
                    limited(copied / "experiment/FREEZE.json", 50_000)
                    == (HERE / "FREEZE.json").read_bytes())
        protocol = obj(HERE / "PROTOCOL.json")
        checks["compatibility_runner_pin"] = (
            expected["experiment/author_25.py"] == protocol.get("runner_sha256"))
        host = obj(directory / "host_run.json")
        pin = obj(directory / "input_pin.json")
        checks["host_schema_and_scope"] = (
            host.get("schema") == "rrnc-hosted-wine-author-strace-v01"
            and host.get("status") == "PASS_PROSPECTIVE_STRACE_OBSERVATION_ONLY"
            and host.get("scope", "").startswith("New prospective"))
        checks["source_hashes"] = host.get("source_hashes") == expected
        checks["input_pins"] = all(
            pin.get(key, {}).get("bytes") == protocol[key]["bytes"]
            and pin.get(key, {}).get("sha256") == protocol[key]["sha256"]
            and pin.get(key, {}).get("url") == protocol[key]["url"]
            for key in ("author", "data")) and host.get("inputs") == pin
        retained = {"author": directory / "inputs/author.zip",
                    "data": directory / "inputs/wine.raw"}
        checks["retained_download_bytes"] = all(
            len(raw := limited(retained[key], MAX_INPUT_BYTES)) == protocol[key]["bytes"]
            and sha(raw) == protocol[key]["sha256"]
            for key in ("author", "data"))
        environment = host.get("github_environment", {})
        run_id = environment.get("GITHUB_RUN_ID")
        attempt = environment.get("GITHUB_RUN_ATTEMPT")
        commit = environment.get("GITHUB_SHA")
        checks["github_run_identity_shape"] = (
            isinstance(run_id, str) and run_id.isdecimal()
            and isinstance(attempt, str) and attempt.isdecimal()
            and isinstance(commit, str) and re.fullmatch(r"[0-9a-f]{40}", commit) is not None
            and environment.get("RUNNER_OS") == "Linux"
            and environment.get("RUNNER_ARCH") == "X64")
        identity_keys = ("GITHUB_REPOSITORY", "GITHUB_SHA", "GITHUB_RUN_ID",
                         "GITHUB_RUN_ATTEMPT")
        checks["github_run_identity_context"] = (
            isinstance(expected_identity, dict) and all(
                isinstance(expected_identity.get(key), str)
                and bool(expected_identity[key])
                and environment.get(key) == expected_identity[key]
                for key in identity_keys))
        nonce = sha(f"{commit}:{run_id}:{attempt}".encode())[:32]
        checks["nonce_binding"] = host.get("run_nonce") == nonce
        command = host.get("container_command", [])
        checks["container_policy"] = (
            isinstance(command, list) and len(command) > 20
            and command[:2] == ["docker", "run"]
            and command[-1] == nonce
            and all(item in command for item in (
                "--network", "none", "--read-only", "--cap-drop", "ALL",
                "--security-opt", "no-new-privileges", "--user", "65534:65534"))
            and host.get("build", {}).get("returncode") == 0
            and host.get("container", {}).get("returncode") == 0
            and str(host.get("image_id", "")).startswith("sha256:"))
        out = directory / "out"
        result = obj(out / f"author_result_{nonce}.json")
        checks["author_status"] = (
            result.get("status") == "success" and result.get("run_nonce") == nonce
            and result.get("shape") == [178, 13, 3]
            and result.get("network_attempts_python_guard") == 0)
        checks["trace_exit_zero"] = (
            limited(out / "trace_exit_code.txt", 20).strip() == b"0")
        csv_bytes = limited(directory / "results/ours.csv", 100_000)
        rows = list(csv.DictReader(io.StringIO(csv_bytes.decode("utf-8"))))
        checks["csv_identity_and_rows"] = (
            len(rows) == 25 and result.get("csv_rows") == 25
            and sha(csv_bytes) == result.get("csv_sha256")
            and result.get("first_row") == rows[0]
            and result.get("last_row") == rows[-1]
            and [int(row["draw"]) for row in rows] == list(range(25))
            and [int(row["seed"]) for row in rows] == list(range(1, 242, 10)))
        accuracies = [float(row["test_accuracy"]) for row in rows]
        mean, sd = statistics.mean(accuracies), statistics.pstdev(accuracies)
        rounded = [str(Decimal(str(x)).quantize(Decimal("0.001"),
                                                 rounding=ROUND_HALF_UP))
                   for x in (mean, sd)]
        checks["accuracy_grid_and_paper_cell"] = (
            all(0 <= x <= 1 and abs(x * 45 - round(x * 45)) < 1e-11
                for x in accuracies)
            and rounded == protocol["target"]["reported_mean_sd_3dp"])
        observations["mean"] = mean
        observations["population_sd"] = sd
        observations["rounded_mean_sd"] = rounded
        params = limited(directory / "results/ours_exp_params.py", 50_000)
        checks["params_hash"] = sha(params) == result.get("params_sha256")

        pid = result.get("pid_self_reported")
        if not isinstance(pid, int) or pid <= 0:
            raise ValueError("BAD_AUTHOR_PID")
        trace_paths = sorted(out.glob("trace.*"))
        checks["trace_file_set_bounded"] = 1 <= len(trace_paths) <= 64 and all(
            path.stat().st_size <= MAX_TRACE_BYTES for path in trace_paths)
        trace = limited(out / f"trace.{pid}", MAX_TRACE_BYTES).decode(
            "utf-8", errors="replace")
        lines = trace.splitlines()
        wine_path = ("/probe/src/paper-decision-trees-as-partitioning-machines-"
                     "0f354dac486a9845a9504419e31c84c7eb39507f" + WINE_SUFFIX)
        checks["main_trace_clean_exit"] = (
            bool(lines) and lines[-1].strip().endswith("+++ exited with 0 +++"))
        checks["wine_open_observed"] = any(
            "openat(" in line and f'"{wine_path}"' in line
            and re.search(r"=\s+\d+(?:\s|<|$)", line)
            for line in lines)
        checks["wine_positive_read_observed"] = any(
            "read(" in line and f"<{wine_path}>" in line
            and re.search(r"=\s+[1-9]\d*(?:\s|$)", line)
            for line in lines)
        observations["trace_files"] = len(trace_paths)
        observations["author_main_pid"] = pid
    except (OSError, ValueError, KeyError, TypeError, IndexError, UnicodeError,
            csv.Error, json.JSONDecodeError) as error:
        return {"schema": "rrnc-wine-strace-verification-v01",
                "status": "INVALID_OR_UNRUN", "checks": checks,
                "observations": observations, "error_class": type(error).__name__,
                "error_code": str(error)[:160],
                "scope": "Prospective selected syscall and arithmetic evidence only"}
    return {"schema": "rrnc-wine-strace-verification-v01",
            "status": "PASS_PROSPECTIVE_STRACE_OBSERVATION_ONLY"
                      if checks and all(checks.values()) else "INVALID_OR_UNRUN",
            "checks": checks, "observations": observations,
            "scope": "Prospective selected syscall and arithmetic evidence only"}


def safely_extract(tar_path: Path, directory: Path) -> None:
    if tar_path.stat().st_size > MAX_TAR_BYTES:
        raise ValueError("TAR_BYTE_CAP")
    total, seen = 0, set()
    with tarfile.open(tar_path, "r:") as archive:
        members = archive.getmembers()
        if len(members) > MAX_MEMBERS:
            raise ValueError("TAR_MEMBER_CAP")
        for member in members:
            pure = PurePosixPath(member.name)
            if (member.name != pure.as_posix() or pure.is_absolute()
                    or ".." in pure.parts or not pure.parts or not member.isfile()
                    or member.name in seen or member.size < 0):
                raise ValueError("UNSAFE_TAR_MEMBER")
            seen.add(member.name)
            total += member.size
            if total > MAX_EXTRACTED_BYTES:
                raise ValueError("TAR_EXTRACTED_BYTE_CAP")
            stream = archive.extractfile(member)
            if stream is None:
                raise ValueError("TAR_MEMBER_UNREADABLE")
            data = stream.read(member.size + 1)
            if len(data) != member.size:
                raise ValueError("TAR_MEMBER_SIZE_MISMATCH")
            target = directory.joinpath(*pure.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)


def main() -> None:
    if len(sys.argv) != 7:
        raise SystemExit("usage: verify_receipt.py TAR REPORT EXPECTED_REPOSITORY "
                         "EXPECTED_SHA EXPECTED_RUN_ID EXPECTED_RUN_ATTEMPT")
    tar_path, report_path = (Path(arg).resolve() for arg in sys.argv[1:3])
    expected_identity = dict(zip(
        ("GITHUB_REPOSITORY", "GITHUB_SHA", "GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT"),
        sys.argv[3:7]))
    report = {"schema": "rrnc-wine-strace-bundle-verification-v01",
              "status": "INVALID_OR_UNRUN",
              "scope": "Prospective selected syscall and arithmetic evidence only",
              "expected_github_identity_from_caller": expected_identity}
    try:
        report["tar_sha256"] = sha(limited(tar_path, MAX_TAR_BYTES))
        with tempfile.TemporaryDirectory(prefix="rrnc_wine_receipt_") as temporary:
            root = Path(temporary)
            safely_extract(tar_path, root)
            check = audit_tree(root, expected_identity=expected_identity)
            report["receipt_audit"] = check
            report["status"] = check["status"]
    except (OSError, ValueError, tarfile.TarError, json.JSONDecodeError) as error:
        report["error_class"] = type(error).__name__
        report["error_code"] = str(error)[:160]
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "tar_sha256": report.get("tar_sha256")}))
    if report["status"] != "PASS_PROSPECTIVE_STRACE_OBSERVATION_ONLY":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
