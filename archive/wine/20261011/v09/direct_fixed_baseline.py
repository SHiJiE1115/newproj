"""Independent, fixed same-information receipt baseline for hosted Wine v09.

This reads the same tar and caller-supplied expected run identity as the
candidate verifier.  A PASS is only a new selected-syscall and retained-input
observation.  Provider job state and attestation must be checked separately.
"""

from __future__ import annotations

import csv
from decimal import Decimal, ROUND_HALF_UP, localcontext
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import sys
import tarfile


HERE = Path(__file__).resolve().parent
PACKAGE = None
PROTOCOL_SHA = "aeae194c6df93796bbcb50d1e70dc6fb240c570a07657052193e1a3a0d5434f5"
FREEZE_SHA = "8a17f6264bfce4a0c561be1c9b10179a1734beefc5b6d9cbd78f3691e4b72d85"
MAX_TAR_BYTES = 150_000_000
MAX_EXTRACTED_BYTES = 180_000_000
MAX_MEMBERS = 180
MAX_SMALL_BYTES = 300_000
MAX_TRACE_BYTES = 80_000_000
WINE_PATH = (
    "/probe/src/paper-decision-trees-as-partitioning-machines-"
    "0f354dac486a9845a9504419e31c84c7eb39507f/experiments/datasets/raw/wine.raw"
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def raw_tar_members(data: bytes) -> tuple[dict[str, bytes], dict[str, dict]]:
    if len(data) > MAX_TAR_BYTES:
        raise ValueError("TAR_BYTE_CAP")
    contents: dict[str, bytes] = {}
    metadata: dict[str, dict] = {}
    total = 0
    windows_names: set[str] = set()
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:") as archive:
        members = archive.getmembers()
        if len(members) > MAX_MEMBERS:
            raise ValueError("TAR_MEMBER_CAP")
        for member in members:
            path = PurePosixPath(member.name)
            parts = path.parts
            windows_name = "/".join(part.lower() for part in parts)
            reserved = {"con", "prn", "aux", "nul"}
            reserved.update(f"com{number}" for number in range(1, 10))
            reserved.update(f"lpt{number}" for number in range(1, 10))
            if (not member.isfile() or path.is_absolute() or ".." in path.parts
                    or member.name != path.as_posix() or member.name in contents
                    or windows_name in windows_names
                    or member.size < 0 or "\\" in member.name or ":" in member.name
                    or any(part in {".", ".."}
                           or re.fullmatch(r"[A-Za-z0-9._-]{1,120}", part) is None
                           or part.endswith(".")
                           or part.split(".", 1)[0].casefold() in reserved
                           for part in parts)):
                raise ValueError("UNSAFE_OR_DUPLICATE_TAR_MEMBER")
            total += member.size
            if total > MAX_EXTRACTED_BYTES:
                raise ValueError("TAR_EXTRACTED_BYTE_CAP")
            stream = archive.extractfile(member)
            if stream is None:
                raise ValueError("TAR_MEMBER_UNREADABLE")
            observed = stream.read(member.size + 1)
            if len(observed) != member.size:
                raise ValueError("TAR_MEMBER_SIZE_MISMATCH")
            contents[member.name] = observed
            windows_names.add(windows_name)
            metadata[member.name] = {
                "uid": member.uid, "gid": member.gid,
                "mode_octal": oct(member.mode),
            }
    return contents, metadata


def required(contents: dict[str, bytes], name: str, cap: int = MAX_SMALL_BYTES) -> bytes:
    data = contents[name]
    if len(data) > cap:
        raise ValueError(f"OVERSIZE_{name}")
    return data


def object_json(data: bytes) -> dict:
    value = json.loads(data)
    if not isinstance(value, dict):
        raise ValueError("JSON_OBJECT_REQUIRED")
    return value


def audit(tar_bytes: bytes, expected_identity: dict[str, str]) -> dict:
    checks: dict[str, bool] = {}
    observations: dict = {"tar_sha256": sha(tar_bytes)}

    def flag(name: str, condition: bool) -> None:
        checks[name] = bool(condition)

    try:
        freeze_bytes = (PACKAGE / "experiment/FREEZE.json").read_bytes()
        protocol_bytes = (PACKAGE / "experiment/PROTOCOL.json").read_bytes()
        flag("local_frozen_protocol", sha(freeze_bytes) == FREEZE_SHA
             and sha(protocol_bytes) == PROTOCOL_SHA)
        freeze = object_json(freeze_bytes)
        protocol = object_json(protocol_bytes)
        source_hashes = freeze["sha256_by_relative_path"]
        flag("local_source_freeze", len(source_hashes) == 9 and all(
            sha((PACKAGE / name).read_bytes()) == digest
            for name, digest in source_hashes.items()))
        contents, metadata = raw_tar_members(tar_bytes)
        flag("receipt_source_snapshot", (
            required(contents, "source/experiment/FREEZE.json") == freeze_bytes
            and all(sha(required(contents, "source/" + name)) == digest
                    for name, digest in source_hashes.items())))
        host = object_json(required(contents, "host_run.json"))
        pins = object_json(required(contents, "input_pin.json"))
        flag("reported_input_pins", host.get("inputs") == pins and all(
            pins.get(key, {}).get("url") == protocol[key]["url"]
            and pins.get(key, {}).get("bytes") == protocol[key]["bytes"]
            and pins.get(key, {}).get("sha256") == protocol[key]["sha256"]
            for key in ("author", "data")))
        retained = {
            "author": required(contents, "inputs/author.zip", 200_000),
            "data": required(contents, "inputs/wine.raw", 200_000),
        }
        flag("retained_input_bytes", all(
            len(retained[key]) == protocol[key]["bytes"]
            and sha(retained[key]) == protocol[key]["sha256"]
            for key in ("author", "data")))
        flag("host_status_and_source", (
            host.get("schema") == "rrnc-hosted-wine-author-strace-v01"
            and host.get("status") == "PASS_PROSPECTIVE_STRACE_OBSERVATION_ONLY"
            and str(host.get("scope", "")).startswith("New prospective")
            and host.get("source_hashes") == source_hashes
            and source_hashes.get("experiment/author_25.py")
            == protocol.get("runner_sha256")))
        env = host.get("github_environment", {})
        keys = ("GITHUB_REPOSITORY", "GITHUB_SHA", "GITHUB_RUN_ID",
                "GITHUB_RUN_ATTEMPT")
        flag("caller_identity", isinstance(expected_identity, dict) and all(
            isinstance(expected_identity.get(key), str)
            and bool(expected_identity[key])
            and env.get(key) == expected_identity[key] for key in keys))
        run_id, attempt, commit = (env.get("GITHUB_RUN_ID"),
                                   env.get("GITHUB_RUN_ATTEMPT"),
                                   env.get("GITHUB_SHA"))
        flag("provider_identity_shape", (
            isinstance(run_id, str) and run_id.isdecimal()
            and isinstance(attempt, str) and attempt.isdecimal()
            and isinstance(commit, str)
            and re.fullmatch(r"[0-9a-f]{40}", commit) is not None
            and env.get("RUNNER_OS") == "Linux"
            and env.get("RUNNER_ARCH") == "X64"))
        nonce = sha(f"{commit}:{run_id}:{attempt}".encode())[:32]
        command = host.get("container_command", [])
        def values_after(flag_name: str) -> list[str]:
            return [command[i + 1] for i, value in enumerate(command[:-1])
                    if value == flag_name]
        flag("nonce_and_container_policy", (
            host.get("run_nonce") == nonce
            and isinstance(command, list)
            and len(command) > 20
            and command[:2] == ["docker", "run"]
            and command[-1] == nonce
            and all(item in command for item in (
                "--network", "none", "--read-only", "--cap-drop", "ALL",
                "--security-opt", "no-new-privileges"))
            and values_after("--user") == ["0:0"]
            and values_after("--cap-add") == ["SETUID", "SETGID", "SYS_PTRACE", "DAC_READ_SEARCH"]
            and any(mount.startswith("type=bind,")
                    and "dst=/out" in mount.split(",")
                    and "readonly" not in mount.split(",")
                    and "ro" not in mount.split(",")
                    for mount in values_after("--mount"))
            and host.get("build", {}).get("returncode") == 0
            and host.get("container", {}).get("returncode") == 0
            and str(host.get("image_id", "")).startswith("sha256:")))
        result = object_json(required(contents, f"out/author_result_{nonce}.json"))
        flag("author_summary", (
            result.get("status") == "success"
            and result.get("run_nonce") == nonce
            and result.get("shape") == [178, 13, 3]
            and result.get("network_attempts_python_guard") == 0))
        flag("author_subject_permissions", (
            all(result.get(key) == 65534 for key in (
                "uid_self_reported", "euid_self_reported",
                "gid_self_reported", "egid_self_reported"))
            and result.get("groups_self_reported") == []
            and result.get("cap_eff_self_reported") == 0
            and result.get("observer_write_canary_denied") is True
            and result.get("observer_rename_canary_denied") is True
            and result.get("observer_fd_absent") is True))
        flag("trace_exit_code", required(contents, "out/trace_exit_code.txt", 20).strip()
             == b"0")
        csv_bytes = required(contents, "results/ours.csv", 100_000)
        rows = list(csv.DictReader(io.StringIO(csv_bytes.decode("utf-8"))))
        flag("csv_rows_and_hash", (
            len(rows) == 25 and result.get("csv_rows") == 25
            and sha(csv_bytes) == result.get("csv_sha256")
            and rows and result.get("first_row") == rows[0]
            and result.get("last_row") == rows[-1]
            and [int(row["draw"]) for row in rows] == list(range(25))
            and [int(row["seed"]) for row in rows] == list(range(1, 242, 10))))
        with localcontext() as context:
            context.prec = 80
            acc = [Decimal(row["test_accuracy"]) for row in rows]
            if not acc or any(not value.is_finite() for value in acc):
                raise ValueError("NONFINITE_OR_EMPTY_ACCURACY")
            mean = sum(acc) / len(acc)
            sd = (sum((value - mean) ** 2 for value in acc) / len(acc)).sqrt()
            rounded = [str(value.quantize(Decimal("0.001"),
                                          rounding=ROUND_HALF_UP))
                       for value in (mean, sd)]
            flag("accuracy_grid_and_paper_cell", (
                all(0 <= value <= 1
                    and abs(value * 45 - (value * 45).to_integral_value())
                    < Decimal("1e-11") for value in acc)
                and rounded == protocol["target"]["reported_mean_sd_3dp"]))
            observations["rounded_mean_sd"] = rounded
        flag("params_hash", sha(required(contents, "results/ours_exp_params.py", 50_000))
             == result.get("params_sha256"))
        pid = result.get("pid_self_reported")
        if not isinstance(pid, int) or pid <= 0:
            raise ValueError("BAD_AUTHOR_PID")
        trace_names = sorted(name for name in contents
                             if re.fullmatch(r"out/observer/trace\.\d+", name))
        flag("bounded_trace_files", 1 <= len(trace_names) <= 64 and all(
            len(contents[name]) <= MAX_TRACE_BYTES for name in trace_names))
        isolation = host.get("trace_isolation", {})
        reported_files = isolation.get("trace_files", {})
        flag("observer_directory_and_sticky_parent", (
            isolation.get("out_mode_octal") == "0o1777"
            and isolation.get("observer_pre_mode_text") == "0:0:700"
            and required(contents, "out/observer_pre_mode.txt", 30).strip()
            == b"0:0:700"
            and isolation.get("observer_uid") == 0
            and isolation.get("observer_gid") == 0
            and isolation.get("observer_post_mode_octal") == "0o755"
            and isinstance(reported_files, dict)
            and set(reported_files) == {name.rsplit("/", 1)[-1]
                                       for name in trace_names}
            and all(entry == {"uid": 0, "gid": 0, "mode_octal": "0o644"}
                    for entry in reported_files.values())))
        flag("tar_trace_owner_not_subject", all(
            metadata.get(name) == {"uid": 0, "gid": 0, "mode_octal": "0o644"}
            for name in trace_names))
        lines = required(contents, f"out/observer/trace.{pid}",
                         MAX_TRACE_BYTES).decode(
            "utf-8", errors="replace").splitlines()
        flag("main_trace_exit", bool(lines)
             and lines[-1].strip().endswith("+++ exited with 0 +++"))
        execve = re.compile(
            r'^\d+\.\d+ execve\("/usr/bin/python3", '
            r'\["/usr/bin/python3", "-I", "-B", "/probe/author_25.py", "'
            + re.escape(nonce) + r'"\], .*\) = 0$')
        executed = [i for i, line in enumerate(lines) if execve.fullmatch(line)]
        opened = [i for i, line in enumerate(lines)
                  if "openat(" in line and f'"{WINE_PATH}"' in line
                  and re.search(r"=\s+\d+(?:\s|<|$)", line)]
        read = [i for i, line in enumerate(lines)
                if "read(" in line and f"<{WINE_PATH}>" in line
                and re.search(r"=\s+[1-9]\d*(?:\s|$)", line)]
        flag("author_execve_same_pid", len(executed) == 1)
        flag("wine_open_and_read", bool(opened and read))
        flag("execve_wine_order", bool(executed and opened and read)
             and executed[0] < opened[0] < read[0])
        observations["trace_files"] = len(trace_names)
    except Exception as error:
        return {"schema": "rrnc_direct_fixed_baseline_v06",
                "status": "INVALID_OR_UNRUN", "checks": checks,
                "observations": observations,
                "error_class": type(error).__name__,
                "error_code": str(error)[:160],
                "scope": "Same receipt and caller identity; selected syscall and retained inputs only"}
    return {"schema": "rrnc_direct_fixed_baseline_v06",
            "status": ("PASS_PROSPECTIVE_STRACE_OBSERVATION_ONLY"
                       if checks and all(checks.values()) else "INVALID_OR_UNRUN"),
            "checks": checks, "observations": observations,
            "scope": "Same receipt and caller identity; selected syscall and retained inputs only"}


def main() -> None:
    global PACKAGE
    if len(sys.argv) != 8:
        raise SystemExit("usage: direct_fixed_baseline.py SOURCE_CHECKOUT TAR REPORT "
                         "EXPECTED_REPO EXPECTED_SHA EXPECTED_RUN_ID EXPECTED_ATTEMPT")
    PACKAGE = Path(sys.argv[1]).resolve()
    tar_path, output_path = Path(sys.argv[2]), Path(sys.argv[3])
    identity = dict(zip(("GITHUB_REPOSITORY", "GITHUB_SHA", "GITHUB_RUN_ID",
                         "GITHUB_RUN_ATTEMPT"), sys.argv[4:8]))
    try:
        with tar_path.open("rb") as stream:
            tar_bytes = stream.read(MAX_TAR_BYTES + 1)
        report = audit(tar_bytes, identity)
    except OSError as error:
        report = {"schema": "rrnc_direct_fixed_baseline_v06",
                  "status": "INVALID_OR_UNRUN", "error_class": type(error).__name__,
                  "error_code": str(error)[:160]}
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps({"status": report["status"]}))
    if report["status"] != "PASS_PROSPECTIVE_STRACE_OBSERVATION_ONLY":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
