"""Run the frozen standalone full11 proof; retain actual child exit and outputs."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import stat
import subprocess
import sys
import time
import zipfile

HERE = Path(__file__).resolve().parent
ARCHIVE_SHA = '2c875b0f12ef368cc730579f68ceaf708a33cdd1481a01abd15f2aa5fc51d874'
PROOF_MANIFEST_SHA = '575ac14eed411deecc2d57663c6c1bdd90e27fa2ea34188c2e8dd965d983fd3b'
MEMBERS = {'direct_nodes.jsonl.gz', 'frontier.json', 'group_math_v01.py', 'main_nodes.jsonl.gz',
           'MANIFEST_V01.json', 'policies.jsonl.gz', 'proof_index.json', 'README_EN.txt',
           'README_ZH.txt', 'replay_full11_v01.py'}


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def descriptor(path):
    raw = path.read_bytes()
    return {'name': path.name, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def save(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write('\n')
        handle.flush()
        os.fsync(handle.fileno())
    return descriptor(path)


def verify_source(expected):
    freeze_path = HERE / 'HOSTED_FREEZE_V01.json'
    require(descriptor(freeze_path)['sha256'] == expected, 'HOSTED_FREEZE_SHA_MISMATCH')
    freeze = json.loads(freeze_path.read_bytes())
    require(freeze['format'] == 'full11-hosted-source-freeze-v1', 'FREEZE_FORMAT')
    require(set(freeze['files']) == {'run_hosted_full11_v01.py', 'full11_direct_proof_v01.zip',
                                    'HOSTED_PROTOCOL_V01.json', 'README.txt'}, 'FREEZE_FILE_SET')
    for name, expected_file in freeze['files'].items():
        require(Path(name).name == name and not (HERE / name).is_symlink(), 'SOURCE_PATH')
        actual = descriptor(HERE / name)
        require((actual['bytes'], actual['sha256']) == (expected_file['bytes'], expected_file['sha256']),
                'FROZEN_SOURCE_CHANGED:' + name)
    require(descriptor(HERE / 'full11_direct_proof_v01.zip')['sha256'] == ARCHIVE_SHA, 'ARCHIVE_PIN')
    with zipfile.ZipFile(HERE / 'full11_direct_proof_v01.zip') as archive:
        require(set(archive.namelist()) == MEMBERS and len(archive.namelist()) == len(MEMBERS), 'ARCHIVE_MEMBERS')
        require(sum(i.file_size for i in archive.infolist()) <= 33554432, 'ARCHIVE_BYTE_CAP')
        for item in archive.infolist():
            require(Path(item.filename).name == item.filename and not item.is_dir()
                    and not stat.S_ISLNK(item.external_attr >> 16), 'ARCHIVE_PATH')
        require(hashlib.sha256(archive.read('MANIFEST_V01.json')).hexdigest() == PROOF_MANIFEST_SHA, 'PROOF_MANIFEST_PIN')
    return descriptor(freeze_path)


def execute_child(argv, cwd, output_dir, timeout=930):
    """Hold a real Popen handle, wait for exit, and record its actual return code."""
    start = utc()
    before = time.monotonic()
    child = subprocess.Popen(argv, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    save(output_dir / 'CHILD_START.json', {'pid': child.pid, 'started_utc': start, 'argv': argv})
    timed_out = False
    try:
        stdout, stderr = child.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        child.kill()
        stdout, stderr = child.communicate()
    # communicate() has waited for this retained process object; PID absence is unused.
    receipt = {'pid': child.pid, 'started_utc': start, 'observed_exit_utc': utc(),
               'actual_exit_code': child.returncode, 'retained_process_object': True,
               'exit_observation': 'Popen.communicate_returncode', 'timed_out_and_killed': timed_out,
               'wall_seconds': time.monotonic() - before}
    with (output_dir / 'proof_stdout.txt').open('xb') as handle:
        handle.write(stdout)
    with (output_dir / 'proof_stderr.txt').open('xb') as handle:
        handle.write(stderr)
    save(output_dir / 'CHILD_TERMINAL.json', receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expect-freeze-sha256', required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--execution-kind', choices=['local-review', 'github-actions'], default='local-review')
    parser.add_argument('--check-only', action='store_true', help='Source gate only; no certificate-execution success claim')
    args = parser.parse_args()
    require(sys.dont_write_bytecode, 'USE_PYTHON_B')
    require(re.fullmatch('[0-9a-f]{64}', args.expect_freeze_sha256), 'EXPECTED_FREEZE_SYNTAX')
    output = args.output_dir.resolve()
    require(HERE != output and HERE not in output.parents, 'OUTPUT_OUTSIDE_FROZEN_SOURCE')
    output.mkdir(parents=True, exist_ok=False)
    started = {'schema': 1, 'started_utc': utc(), 'parent_pid': os.getpid(),
               'execution_kind': args.execution_kind, 'check_only': args.check_only,
               'expected_freeze_sha256': args.expect_freeze_sha256,
               'runtime': {'python': platform.python_version(), 'system': platform.system(),
                           'python_full': sys.version, 'platform': platform.platform()},
               'github': {key: os.environ.get(key) for key in ['GITHUB_REPOSITORY', 'GITHUB_SHA',
                          'GITHUB_RUN_ID', 'GITHUB_RUN_ATTEMPT', 'GITHUB_WORKFLOW_REF', 'GITHUB_JOB']},
               'API_calls': 0, 'novelty_claim': False, 'human_review_claim': False}
    save(output / 'RUN_START.json', started)
    try:
        if args.execution_kind == 'github-actions':
            require(os.environ.get('GITHUB_ACTIONS') == 'true', 'NOT_GITHUB_ACTIONS')
            env = started['github']
            require(env['GITHUB_REPOSITORY'] == 'SHiJiE1115/newproj', 'GITHUB_REPOSITORY')
            require(re.fullmatch('[0-9a-f]{40}', env['GITHUB_SHA'] or ''), 'GITHUB_COMMIT')
            require(all(re.fullmatch('[1-9][0-9]*', env[key] or '') for key in ['GITHUB_RUN_ID', 'GITHUB_RUN_ATTEMPT']), 'GITHUB_RUN_IDENTITY')
        freeze = verify_source(args.expect_freeze_sha256)
        save(output / 'SOURCE_GATE.json', {'status': 'PASS_FROZEN_BYTES_ONLY', 'freeze': freeze,
                                          'archive': descriptor(HERE / 'full11_direct_proof_v01.zip')})
        if args.check_only:
            save(output / 'SUMMARY.json', {'status': 'PASS_SOURCE_GATE_ONLY_NO_CERTIFICATE_EXECUTION',
                                           'child_started': False, 'scientific_replay_completed': False,
                                           'API_calls': 0, 'ended_utc': utc()})
            return 0
        proof_dir = output / 'proof_input'
        proof_dir.mkdir(exist_ok=False)
        with zipfile.ZipFile(HERE / 'full11_direct_proof_v01.zip') as archive:
            archive.extractall(proof_dir)
        result_path = output / 'PROOF_RESULT.json'
        command = [sys.executable, '-I', '-X', 'utf8', '-B', str(proof_dir / 'replay_full11_v01.py'),
                   '--out', str(result_path), '--seconds', '900']
        receipt = execute_child(command, proof_dir, output)
        require(receipt['actual_exit_code'] == 0 and not receipt['timed_out_and_killed'], 'PROOF_CHILD_FAILED')
        result = json.loads(result_path.read_bytes())
        require(result['status'] == 'PASS_SELF_CONTAINED_EXACT_FULL11_AND16_MENUS', 'PROOF_STATUS')
        require(result['manifest_sha256'] == PROOF_MANIFEST_SHA and result['max_ratio'] == '5/4', 'PROOF_IDENTITY')
        require(result['AD_envelopes'] == result['complete_roots'] == 2193, 'COMPLETE_ROOTS')
        require(result['main_certificates']['nodes'] == 125288 and result['direct_certificates']['nodes'] == 5395, 'CERTIFICATE_COUNTS')
        require(result['policies'] == 293 and result['global_orders_checked'] == 5040, 'POLICIES_AND_LOWER_ORDERS')
        require(result['full_adaptive_at_lower'] == '4' and result['full_priority_at_lower'] == '5', 'TRUE_LOWER')
        require(not result['old7_or8_upper_or_lower_results_loaded'] and not result['human_review_claim']
                and not result['novelty_claim'] and result['API_calls'] == 0, 'SCOPE_FLAGS')
        verify_source(args.expect_freeze_sha256)
        save(output / 'SUMMARY.json', {'status': 'PASS_ACTUAL_FROZEN_FULL11_PROOF_REPLAY', 'ended_utc': utc(),
                                       'execution_kind': args.execution_kind, 'child_started': True,
                                       'scientific_replay_completed': False, 'mathematical_certificate_replay_completed': True,
                                       'proof_result': descriptor(result_path), 'child_terminal': descriptor(output / 'CHILD_TERMINAL.json'),
                                       'source_freeze': freeze, 'scope': 'One specified full11 source; no novelty or application-advantage claim.',
                                       'API_calls': 0})
        print('PASS_ACTUAL_FROZEN_FULL11_PROOF_REPLAY', flush=True)
        return 0
    except Exception as error:
        save(output / 'SUMMARY.json', {'status': 'FAIL_RETAINED_NO_RETRY', 'ended_utc': utc(),
                                       'error_type': type(error).__name__, 'reason': str(error),
                                       'child_started': (output / 'CHILD_START.json').exists(),
                                       'mathematical_certificate_replay_completed': False, 'API_calls': 0})
        print(type(error).__name__ + ': ' + str(error), file=sys.stderr, flush=True)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
