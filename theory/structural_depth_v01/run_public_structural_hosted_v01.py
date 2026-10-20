"""Bounded hosted replay of a separately reviewed public R+C4 packet.

Python 3.10+ standard library. The packet hashes are mandatory caller inputs.
No API requests, credential reads, retries, or mathematical source rewrites.
This wrapper checks finite premises and process evidence, not the written theorem.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import signal
import stat
import subprocess
import sys
import time
import zipfile

TIME_LIMIT_SECONDS = 600
MAX_ZIP_BYTES = 16 * 1024 * 1024
MAX_EXPANDED_BYTES = 32 * 1024 * 1024
MAX_MEMBERS = 128
PUBLIC_GITHUB_KEYS = (
    'GITHUB_ACTIONS', 'GITHUB_REPOSITORY', 'GITHUB_SHA', 'GITHUB_RUN_ID',
    'GITHUB_RUN_ATTEMPT', 'GITHUB_JOB', 'GITHUB_EVENT_NAME', 'GITHUB_REF',
    'GITHUB_REF_TYPE', 'GITHUB_WORKFLOW',
)
EXPECTED_TAG_REF = 'refs/tags/rrnc-structural-depth-607-v01'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def save(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def pin(path):
    raw = path.read_bytes()
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def read_json(path):
    require(path.stat().st_size <= MAX_EXPANDED_BYTES, 'JSON_SIZE_LIMIT')
    return json.loads(path.read_bytes())


def safe_name(name):
    require(isinstance(name, str) and name, 'EMPTY_MEMBER_NAME')
    p = PurePosixPath(name)
    require(not p.is_absolute() and not any(x in ('', '.', '..') for x in name.split('/')),
            'UNSAFE_MEMBER_PATH')
    require('\\' not in name and ':' not in name and str(p) == name,
            'UNSAFE_MEMBER_SPELLING')
    require(all(ord(c) >= 32 and ord(c) != 127 for c in name), 'CONTROL_IN_MEMBER')
    return p.parts


def validate_manifest(package, expected_sha):
    require(pin(package / 'MANIFEST.json')['sha256'] == expected_sha, 'MANIFEST_HASH_MISMATCH')
    manifest = read_json(package / 'MANIFEST.json')
    names = []
    for row in manifest['files']:
        parts = safe_name(row['name'])
        target = package.joinpath(*parts)
        require(target.resolve().is_relative_to(package), 'MANIFEST_PATH_ESCAPE')
        require(target.is_file() and not target.is_symlink(), 'MANIFEST_FILE_MISSING_OR_LINK')
        require(not any(parent.is_symlink() for parent in target.parents if parent != package),
                'MANIFEST_PARENT_LINK')
        require(pin(target) == {'bytes': row['bytes'], 'sha256': row['sha256']},
                'MANIFEST_MEMBER_HASH_MISMATCH')
        names.append(row['name'])
    require(len(names) == len(set(n.casefold() for n in names)), 'MANIFEST_DUPLICATE')
    actual = {p.relative_to(package).as_posix() for p in package.rglob('*') if p.is_file()}
    require(actual == set(names) | {'MANIFEST.json'}, 'MANIFEST_MEMBER_SET_MISMATCH')


def extract_packet(packet, package, expected_zip, expected_manifest, deadline):
    require(packet.is_file() and not packet.is_symlink(), 'PACKET_MISSING_OR_LINK')
    require(packet.stat().st_size <= MAX_ZIP_BYTES, 'ZIP_SIZE_LIMIT')
    require(pin(packet)['sha256'] == expected_zip, 'ZIP_HASH_MISMATCH')
    package.mkdir()
    with zipfile.ZipFile(packet) as archive:
        entries = archive.infolist()
        require(0 < len(entries) <= MAX_MEMBERS, 'ZIP_MEMBER_COUNT_LIMIT')
        require(sum(x.file_size for x in entries) <= MAX_EXPANDED_BYTES, 'ZIP_EXPANSION_LIMIT')
        names = []
        for entry in entries:
            safe_name(entry.filename)
            require(not entry.is_dir(), 'EXPLICIT_DIRECTORY_MEMBER_NOT_SUPPORTED')
            require(not (entry.flag_bits & 1), 'ENCRYPTED_MEMBER')
            mode = (entry.external_attr >> 16) & 0xFFFF
            require(stat.S_IFMT(mode) in (0, stat.S_IFREG), 'NONREGULAR_MEMBER')
            names.append(entry.filename)
        require(len(names) == len(set(n.casefold() for n in names)), 'ZIP_DUPLICATE_MEMBER')
        for entry in entries:
            require(time.monotonic() < deadline, 'TOTAL_TIME_LIMIT_BEFORE_EXECUTION')
            target = package.joinpath(*safe_name(entry.filename))
            require(target.resolve().is_relative_to(package), 'ZIP_PATH_ESCAPE')
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as stream:
                stream.write(archive.read(entry))
    validate_manifest(package, expected_manifest)
    return {'archive': pin(packet), 'manifest': pin(package / 'MANIFEST.json'),
            'members': len(entries), 'expanded_bytes': sum(x.file_size for x in entries)}


def check_output_files(inner):
    for path in inner.rglob('*'):
        require(not path.is_symlink(), 'OUTPUT_SYMLINK')
        require(path.resolve().is_relative_to(inner), 'OUTPUT_PATH_ESCAPE')


def check_inner_receipt(inner, package, label, script):
    start = read_json(inner / (label + '.PROCESS_START.json'))
    terminal = read_json(inner / (label + '.PROCESS_TERMINAL.json'))
    require(type(start['pid']) is int and start['pid'] > 0 and start['pid'] == terminal['pid'],
            label + '_PID_MISMATCH')
    require(terminal['actual_exit_code'] == 0 and terminal['timed_out'] is False
            and terminal['retained_Popen_wait'] is True, label + '_NONTERMINAL_OR_FAILURE')
    require(start['script']['sha256'] == pin(package / script)['sha256'], label + '_SCRIPT_HASH')
    for key in ('stdout', 'stderr'):
        actual = pin(inner / (label + '.' + key + '.txt'))
        require(all(terminal[key][k] == actual[k] for k in ('bytes', 'sha256')),
                label + '_LOG_HASH')
    return terminal


def verify_contract(inner, package, outer_pid, expected_manifest):
    check_output_files(inner)
    result = read_json(inner / 'RESULT.json')
    r = read_json(inner / 'R_INDEPENDENT_RESULT.json')
    c_lines = (inner / 'C4.stdout.txt').read_text(encoding='utf-8').splitlines()
    require(c_lines, 'EMPTY_C4_OUTPUT')
    c = json.loads(c_lines[-1])
    require(result['status'] == 'PASS_RELOCATED_R64_AND_C4_64_STRUCTURAL_PREMISES'
            and result['actual_pid'] == outer_pid, 'PACKAGE_RESULT_STATUS_OR_PID')
    require(result['package_manifest']['sha256'] == expected_manifest, 'RESULT_MANIFEST_HASH')
    require(r['status'] == 'PASS_ALL64_REBUILT_AXIOMS_AND_COMPLETE_UNSAT_DERIVATIONS_LOCAL_R_ONLY'
            and r['attempted'] == 64 and r['verified_UNSAT_cases'] == 64
            and r['all64_UNSAT_verified'] is True and r['verified_SAT_countermodel'] is False
            and r['open_case_ids'] == [] and r['not_attempted'] == []
            and r['verified_proof_nodes'] == 35244 and r['verified_unit_inferences'] == 562548,
            'R_COMPLETE_CONTRACT_FAILED')
    require(c['status'] == 'PASS_PORTABLE_STRUCTURAL_PROOF' and c['cases'] == 64
            and c['unit_steps'] == 2331 and c['witness_splits'] == 0, 'C4_COMPLETE_CONTRACT_FAILED')
    require(result['R']['cases'] == result['C4']['cases'] == 64
            and result['R']['proof_nodes'] == 35244 and result['R']['unit_steps'] == 562548
            and result['C4']['unit_steps'] == 2331 and result['C4']['result'] == c,
            'PACKAGE_AGGREGATE_MISMATCH')
    r_pin = pin(inner / 'R_INDEPENDENT_RESULT.json')
    require(all(result['R']['result'][k] == r_pin[k] for k in ('bytes', 'sha256')),
            'PACKAGE_R_RESULT_HASH')
    for label, script in (('R', 'r/verify_reciprocal_portable_v01.py'), ('C4', 'c4/verify.py')):
        terminal = check_inner_receipt(inner, package, label, script)
        require(result[label]['receipt'] == terminal, label + '_AGGREGATE_RECEIPT_MISMATCH')
    for flag in ('human_review', 'proof_assistant_formalization', 'whole_project_complete',
                 'historical_paths_opened', 'new_theorem'):
        require(result[flag] is False, 'UNSUPPORTED_SCOPE_FLAG')
    require(result['new_model_API_calls'] == 0, 'UNEXPECTED_API_CLAIM')
    return {'R': {'cases': 64, 'all_UNSAT': True, 'open_cases': 0, 'not_attempted': 0,
                  'proof_nodes': 35244, 'unit_steps': 562548},
            'C4': {'cases': 64, 'unit_steps': 2331, 'witness_splits': 0}}


def terminate_actual_child(process):
    if os.name == 'posix':
        # start_new_session below ensures this group belongs to this invocation.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        method = 'SIGKILL_OWN_PROCESS_GROUP_THEN_RETAINED_PARENT_WAIT'
    else:
        process.kill()
        method = 'DIRECT_CHILD_KILL_ONLY_DESCENDANT_TERMINATION_NOT_CERTIFIED'
    process.wait()
    return method


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packet', required=True, type=Path)
    parser.add_argument('--expected-zip-sha256', required=True)
    parser.add_argument('--expected-manifest-sha256', required=True)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--execution-kind', choices=('local', 'github-actions'), default='local')
    args = parser.parse_args()
    for value in (args.expected_zip_sha256, args.expected_manifest_sha256):
        require(re.fullmatch('[0-9a-f]{64}', value) is not None, 'EXPECTED_SHA256_FORMAT')
    require(not sys.flags.optimize, 'ASSERTIONS_MUST_REMAIN_ENABLED')
    require(sys.version_info >= (3, 10), 'PYTHON_310_REQUIRED')
    out = args.out.resolve()
    require(not out.exists() and not args.out.is_symlink(), 'FRESH_OUTPUT_REQUIRED')
    require(not any(parent.is_symlink() for parent in args.out.absolute().parents),
            'OUTPUT_PARENT_SYMLINK')
    out.mkdir(parents=True)
    receipts = out / 'receipts'
    receipts.mkdir()
    package = out / 'extracted-packet'
    inner = receipts / 'inner'
    started = time.monotonic()
    deadline = started + TIME_LIMIT_SECONDS
    receipt = {'schema': 1, 'status': 'PRECHECK_PENDING', 'started_utc': now(),
               'execution_kind': args.execution_kind,
               'runtime': {'system': platform.system(), 'python': platform.python_version()},
               'outer_wrapper': pin(Path(__file__).resolve()),
               'total_time_limit_seconds': TIME_LIMIT_SECONDS,
               'automatic_retries': 0, 'new_model_API_calls': 0, 'human_review': False,
               'proof_assistant_formalization': False, 'independent_new_implementation': False,
               'scope': 'Finite R64 and C4_64 premises only; not written reduction/gluing, D2, B5, six-query replay or historical execution authentication.'}
    process = None
    try:
        if args.execution_kind == 'github-actions':
            public = {key: os.environ.get(key, '') for key in PUBLIC_GITHUB_KEYS}
            require(public['GITHUB_ACTIONS'] == 'true' and platform.system() == 'Linux',
                    'LINUX_GITHUB_CONTEXT_REQUIRED')
            require(public['GITHUB_REPOSITORY'] == 'SHiJiE1115/newproj', 'WRONG_REPOSITORY')
            require(re.fullmatch('[0-9a-f]{40}', public['GITHUB_SHA']) is not None,
                    'SOURCE_COMMIT_FORMAT')
            require(public['GITHUB_RUN_ID'].isdigit() and public['GITHUB_RUN_ATTEMPT'] == '1',
                    'FIRST_ATTEMPT_REQUIRED')
            require(public['GITHUB_EVENT_NAME'] == 'push' and public['GITHUB_REF_TYPE'] == 'tag'
                    and public['GITHUB_REF'] == EXPECTED_TAG_REF, 'EXACT_TAG_PUSH_REQUIRED')
            receipt['claimed_public_github_context'] = public
            receipt['provider_metadata_comparison_required'] = True
        receipt['extraction'] = extract_packet(args.packet.resolve(), package,
                                              args.expected_zip_sha256,
                                              args.expected_manifest_sha256, deadline)
        command = [sys.executable, '-I', '-X', 'utf8', '-B', str(package / 'verify.py'),
                   '--out-dir', str(inner)]
        # No inherited API credentials are needed by this isolated stdlib proof replay.
        child_env = {'TEMP': str(out), 'TMP': str(out), 'TMPDIR': str(out),
                     'PYTHONDONTWRITEBYTECODE': '1'}
        if os.name == 'nt':
            # Required by some Windows runtimes; never persisted as metadata.
            system_root = os.environ.get('SystemRoot')
            if system_root:
                child_env['SystemRoot'] = system_root
        with (receipts / 'stdout.txt').open('xb') as stdout, (receipts / 'stderr.txt').open('xb') as stderr:
            require(time.monotonic() < deadline, 'TOTAL_TIME_LIMIT_BEFORE_CHILD')
            process = subprocess.Popen(command, cwd=package, stdin=subprocess.DEVNULL,
                                       stdout=stdout, stderr=stderr, env=child_env,
                                       start_new_session=(os.name == 'posix'))
            save(receipts / 'PROCESS_START.json', {'pid': process.pid, 'started_utc': now(),
                 'retained_Popen': True, 'entrypoint': pin(package / 'verify.py'),
                 'command': command, 'new_posix_session': os.name == 'posix'})
            timed_out = False
            termination = None
            try:
                process.wait(timeout=max(0.001, deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                timed_out = True
                termination = terminate_actual_child(process)
            terminal = {'pid': process.pid, 'actual_exit_code': process.returncode,
                        'retained_Popen_wait': True, 'timed_out': timed_out,
                        'termination_method': termination, 'completed_utc': now(),
                        'wall_seconds_since_wrapper_start': time.monotonic() - started}
            save(receipts / 'PROCESS_TERMINAL.json', terminal)
        receipt['actual_child_terminal'] = terminal
        require(not timed_out and process.returncode == 0, 'ACTUAL_CHILD_FAILED_OR_TIMED_OUT')
        require(time.monotonic() < deadline, 'TOTAL_TIME_LIMIT_AFTER_CHILD')
        receipt['mathematical_projection'] = verify_contract(inner, package, process.pid,
                                                             args.expected_manifest_sha256)
        validate_manifest(package, args.expected_manifest_sha256)
        require(pin(args.packet.resolve()) == receipt['extraction']['archive'], 'ZIP_CHANGED_DURING_RUN')
        require(time.monotonic() < deadline, 'TOTAL_TIME_LIMIT_AFTER_CHECKS')
        receipt['status'] = 'PASS_ACTUAL_PUBLIC_R64_C4_64_FINITE_PREMISE_REPLAY'
    except BaseException as exc:
        if process is not None:
            method = None
            if process.poll() is None:
                method = terminate_actual_child(process)
            else:
                process.wait()
            if not (receipts / 'PROCESS_TERMINAL.json').exists():
                save(receipts / 'PROCESS_TERMINAL.json', {'pid': process.pid,
                     'actual_exit_code': process.returncode, 'retained_Popen_wait': True,
                     'timed_out': time.monotonic() >= deadline, 'termination_method': method,
                     'completed_utc': now(), 'exception_cleanup': True})
        receipt.update(status='FAILED_REPLAY_PRESERVED', error=type(exc).__name__ + ': ' + str(exc))
    receipt['completed_utc'] = now()
    receipt['wall_seconds'] = time.monotonic() - started
    receipt['retained_output_files'] = [dict(name=p.relative_to(receipts).as_posix(), **pin(p))
                                        for p in sorted(receipts.rglob('*')) if p.is_file() and not p.is_symlink()]
    save(receipts / 'RUN_RECEIPT.json', receipt)
    print(json.dumps({'status': receipt['status'], 'execution_kind': args.execution_kind,
                      'wall_seconds': receipt['wall_seconds']}), flush=True)
    return 0 if receipt['status'] == 'PASS_ACTUAL_PUBLIC_R64_C4_64_FINITE_PREMISE_REPLAY' else 1


if __name__ == '__main__':
    raise SystemExit(main())
