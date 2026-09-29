"""One prospective, bounded Wine author-code run on GitHub-hosted Ubuntu."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.request

import verify_receipt


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE_RELATIVE = (
    ".gitattributes", "README.md", ".github/workflows/rrnc-wine-strace.yml",
    "experiment/Dockerfile", "experiment/entrypoint.sh", "experiment/PROTOCOL.json",
    "experiment/author_25.py", "experiment/run_hosted.py",
    "experiment/verify_receipt.py",
)
SOURCE_PATHS = [ROOT / name for name in SOURCE_RELATIVE]
MAX_INPUT_BYTES = 200_000


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_freeze() -> dict:
    frozen = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    actual = {name: sha(path.read_bytes()) for name, path in zip(SOURCE_RELATIVE, SOURCE_PATHS)}
    if actual != frozen["sha256_by_relative_path"]:
        raise ValueError("SOURCE_FREEZE_MISMATCH")
    return frozen


def command(argv: list[str], timeout: int, directory: Path, stem: str) -> dict:
    start = time.monotonic()
    try:
        proc = subprocess.run(argv, capture_output=True, check=False, timeout=timeout)
        result = {"returncode": proc.returncode,
                  "stdout": proc.stdout, "stderr": proc.stderr}
    except subprocess.TimeoutExpired as error:
        result = {"returncode": 124, "stdout": error.stdout or b"",
                  "stderr": error.stderr or b"", "timed_out": True}
    except OSError as error:
        result = {"returncode": 127, "stdout": b"", "stderr": b"",
                  "error_class": type(error).__name__}
    result["wall_seconds"] = time.monotonic() - start
    (directory / f"{stem}.stdout.bin").write_bytes(result.pop("stdout"))
    (directory / f"{stem}.stderr.bin").write_bytes(result.pop("stderr"))
    return result


def download_input(spec: dict, destination: Path) -> dict:
    request = urllib.request.Request(spec["url"], headers={"User-Agent": "rrnc-wine-strace-v01"})
    start = time.monotonic()
    with urllib.request.urlopen(request, timeout=30) as response:
        final_url = response.geturl()
        if not final_url.startswith("https://"):
            raise ValueError("NON_HTTPS_SOURCE")
        data = response.read(MAX_INPUT_BYTES + 1)
    if len(data) > MAX_INPUT_BYTES:
        raise ValueError("SOURCE_BYTE_CAP")
    observed = {"url": spec["url"], "final_url": final_url,
                "bytes": len(data), "sha256": sha(data),
                "wall_seconds": time.monotonic() - start}
    if observed["bytes"] != spec["bytes"] or observed["sha256"] != spec["sha256"]:
        raise ValueError("SOURCE_HASH_OR_SIZE_MISMATCH")
    destination.write_bytes(data)
    return observed


def make_tar(directory: Path) -> None:
    with tarfile.open(directory / "receipt.tar", "w") as archive:
        for path in sorted(directory.rglob("*")):
            if path.is_file() and path.name != "receipt.tar":
                archive.add(path, arcname=path.relative_to(directory).as_posix())


def main() -> None:
    if sys.argv[1:] == ["--preflight"]:
        frozen = source_freeze()
        print(json.dumps({"status": "STATIC_SOURCE_FREEZE_PASS_REMOTE_UNRUN",
                          "files": len(frozen["sha256_by_relative_path"])}))
        return
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    attempt = os.environ.get("GITHUB_RUN_ATTEMPT", "")
    if not (run_id.isdecimal() and attempt.isdecimal()):
        raise SystemExit("GITHUB_RUN_ID and GITHUB_RUN_ATTEMPT required")
    directory = HERE / "run_receipts" / f"{run_id}_{attempt}"
    directory.mkdir(parents=True, exist_ok=False)
    nonce = sha(f"{os.environ.get('GITHUB_SHA', '')}:{run_id}:{attempt}".encode())[:32]
    host = {"schema": "rrnc-hosted-wine-author-strace-v01",
            "started_utc_client_clock": dt.datetime.now(dt.timezone.utc).isoformat(),
            "github_environment": {key: os.environ.get(key) for key in (
                "GITHUB_REPOSITORY", "GITHUB_SHA", "GITHUB_RUN_ID",
                "GITHUB_RUN_ATTEMPT", "RUNNER_OS", "RUNNER_ARCH", "ImageOS", "ImageVersion")},
            "run_nonce": nonce,
            "scope": "New prospective author run with raw strace only; no complete bytes read or historical certification",
            "status": "CAPABILITY_FAIL_OR_UNRUN"}
    try:
        source = directory / "source"
        source.mkdir()
        for name, path in zip(SOURCE_RELATIVE, SOURCE_PATHS):
            target = source / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
        shutil.copy2(HERE / "FREEZE.json", source / "experiment/FREEZE.json")
        frozen = source_freeze()
        host["source_hashes"] = frozen["sha256_by_relative_path"]
        protocol = json.loads((HERE / "PROTOCOL.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory(prefix="rrnc_wine_build_") as temporary:
            context = Path(temporary)
            shutil.copy2(HERE / "Dockerfile", context / "Dockerfile")
            shutil.copy2(HERE / "entrypoint.sh", context / "entrypoint.sh")
            shutil.copy2(HERE / "author_25.py", context / "author_25.py")
            host["inputs"] = {
                "author": download_input(protocol["author"], context / "author.zip"),
                "data": download_input(protocol["data"], context / "wine.raw"),
            }
            (directory / "input_pin.json").write_text(
                json.dumps(host["inputs"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
            tag = f"rrnc-wine-strace:{run_id}-{attempt}"
            build = command(["docker", "build", "--pull", "--no-cache", "--platform", "linux/amd64",
                             "--tag", tag, str(context)], 900, directory, "docker_build")
            host["build"] = build
            if build["returncode"] != 0:
                raise RuntimeError("DOCKER_BUILD_FAILED")
            inspect = command(["docker", "image", "inspect", tag, "--format", "{{.Id}}"],
                              30, directory, "docker_inspect")
            host["image_id"] = (directory / "docker_inspect.stdout.bin").read_text().strip()
            if inspect["returncode"] != 0 or not host["image_id"].startswith("sha256:"):
                raise RuntimeError("IMAGE_ID_UNAVAILABLE")
            out, results = directory / "out", directory / "results"
            out.mkdir(); results.mkdir()
            out.chmod(0o777); results.chmod(0o777)
            name = f"rrnc-wine-strace-{run_id}-{attempt}"
            argv = ["docker", "run", "--rm", "--name", name, "--network", "none",
                    "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
                    "--pids-limit", "64", "--memory", "1g", "--cpus", "1",
                    "--user", "65534:65534", "--tmpfs", "/tmp:rw,nosuid,nodev,size=64m",
                    "--mount", f"type=bind,src={out},dst=/out",
                    "--mount", "type=bind,src=" + str(results) + ",dst=/probe/src/"
                    "paper-decision-trees-as-partitioning-machines-0f354dac486a9845a9504419e31c84c7eb39507f/"
                    "experiments/results/wine/ac25",
                    "--env", "HOME=/tmp", "--env", "PYTHONDONTWRITEBYTECODE=1", tag, nonce]
            host["container_command"] = argv
            host["container"] = command(argv, 300, directory, "docker_run")
            cleanup = command(["docker", "rm", "-f", name], 20, directory, "docker_cleanup")
            host["cleanup_returncode"] = cleanup["returncode"]
            if host["container"]["returncode"] != 0:
                raise RuntimeError("AUTHOR_CONTAINER_FAILED")
            host["status"] = "PASS_PROSPECTIVE_STRACE_OBSERVATION_ONLY"
            (directory / "host_run.json").write_text(
                json.dumps(host, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            check = verify_receipt.audit_tree(
                directory, require_source_snapshot=True,
                expected_identity={key: os.environ.get(key) for key in (
                    "GITHUB_REPOSITORY", "GITHUB_SHA", "GITHUB_RUN_ID",
                    "GITHUB_RUN_ATTEMPT")})
            (directory / "first_job_verification.json").write_text(
                json.dumps(check, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            host["status"] = check["status"]
    except Exception as error:
        host["runner_error_class"] = type(error).__name__
        host["runner_error_code"] = str(error)[:160]
    finally:
        host["ended_utc_client_clock"] = dt.datetime.now(dt.timezone.utc).isoformat()
        (directory / "host_run.json").write_text(
            json.dumps(host, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        make_tar(directory)
        print(json.dumps({"status": host["status"], "receipt": str(directory / "receipt.tar")}))
        if host["status"] != "PASS_PROSPECTIVE_STRACE_OBSERVATION_ONLY":
            raise SystemExit(1)


if __name__ == "__main__":
    main()
