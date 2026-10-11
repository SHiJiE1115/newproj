"""Verify and unpack the fixed VPS3 delivery, then run its offline verifier."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import stat
import subprocess
import sys
import zipfile

BUNDLE_SHA256 = 'eca3ee145c0299b002bc973cd8e43c2b07350e5ebd24e5212c4d353766ae05f3'

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    out = args.output_dir.resolve()
    if out.exists():
        raise ValueError('Refuse existing output directory')
    archive = Path(__file__).resolve().parent / 'vps3_bundle_v01.zip'
    if archive.stat().st_size > 64 * 2**20:
        raise ValueError('Compressed size cap')
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    if digest != BUNDLE_SHA256:
        raise ValueError('Fixed bundle SHA256 mismatch')
    with zipfile.ZipFile(archive) as z:
        rows = z.infolist()
        if not 1 <= len(rows) <= 256 or sum(r.file_size for r in rows) > 128 * 2**20:
            raise ValueError('Uncompressed size or member count cap')
        seen = set()
        for row in rows:
            name = row.filename
            p = PurePosixPath(name)
            if (not name or '\\' in name or ':' in name or p.is_absolute()
                    or p.as_posix() != name or any(part in ('', '.', '..') for part in p.parts)
                    or row.is_dir() or name.casefold() in seen or row.file_size > 64 * 2**20
                    or not stat.S_ISREG(row.external_attr >> 16)):
                raise ValueError('Unsafe or duplicate archive member')
            seen.add(name.casefold())
        out.mkdir(parents=True)
        bundle = out / 'bundle'
        bundle.mkdir()
        for row in rows:
            dest = bundle / row.filename
            if not dest.resolve().is_relative_to(bundle):
                raise ValueError('Archive path escaped bundle')
            dest.parent.mkdir(parents=True, exist_ok=True)
            with dest.open('xb') as f:
                f.write(z.read(row))
    command = [sys.executable, '-I', '-X', 'utf8', '-B', str(bundle / 'verify_vps3.py'),
               '--bundle', str(bundle), '--output', str(out / 'verification.json')]
    stdout, stderr, exit_code, execution_error = b'', b'', None, None
    try:
        proc = subprocess.run(command, cwd=out, capture_output=True, timeout=180)
        stdout, stderr, exit_code = proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired as exc:
        stdout, stderr = exc.stdout or b'', exc.stderr or b''
        execution_error = 'VERIFIER_TIMEOUT'
    except OSError:
        execution_error = 'VERIFIER_PROCESS_START_FAILED'
    (out / 'stdout.txt').write_bytes(stdout)
    (out / 'stderr.txt').write_bytes(stderr)
    result = {'status': 'REJECTED_NO_VALID_RESULT'}
    try:
        candidate = json.loads((out / 'verification.json').read_text(encoding='utf-8'))
        if not isinstance(candidate, dict) or not isinstance(candidate.get('status'), str):
            raise ValueError('Invalid result shape')
        result = candidate
    except (OSError, ValueError):
        execution_error = execution_error or 'VERIFIER_RESULT_MISSING_OR_INVALID'
    status = {'bundle_sha256': digest, 'exit_code': exit_code, 'execution_error': execution_error,
              'python': platform.python_version(), 'platform': platform.system(),
              'verifier_status': result['status'], 'summary': result.get('summary', {}),
              'github_sha': os.environ.get('GITHUB_SHA'), 'github_run_id': os.environ.get('GITHUB_RUN_ID'),
              'github_run_attempt': os.environ.get('GITHUB_RUN_ATTEMPT'),
              'scope': 'Fresh offline audit of retained source bytes; no new VASP or historical execution.'}
    with (out / 'run_context.json').open('x', encoding='utf-8', newline='\n') as f:
        json.dump(status, f, indent=2)
        f.write('\n')
    print(json.dumps(status))
    if execution_error is not None or exit_code != 0 or result['status'] != 'PASS_CURRENT_BYTES_TYPED_PORTS_AND_NUMERICAL_COMPATIBILITY':
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
