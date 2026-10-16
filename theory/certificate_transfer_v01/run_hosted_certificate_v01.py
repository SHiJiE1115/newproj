"""Frozen standard-library certificate replay with an actual retained child exit."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import time
import zipfile

HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--expect-freeze-sha256', required=True)
parser.add_argument('--output-dir', required=True)
parser.add_argument('--execution-kind', choices=['local', 'github-actions'], required=True)
args = parser.parse_args()
out = Path(args.output_dir).resolve()
assert not out.exists(), 'Use a fresh output directory'
out.mkdir(parents=True)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, data):
    with (out / name).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


receipt = {'schema': 1, 'at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'status': 'PRECHECK_PENDING', 'execution_kind': args.execution_kind,
    'runtime': {'python': platform.python_version(), 'system': platform.system()},
    'new_model_API_calls': 0, 'human_review': False, 'historical_scientific_authentication': False}
started = time.monotonic()
try:
    frozen_path = HERE / 'FREEZE.json'
    assert sha(frozen_path) == args.expect_freeze_sha256
    frozen = json.loads(frozen_path.read_bytes())
    assert sha(Path(__file__).resolve()) == frozen['wrapper_sha256']
    packet = HERE / 'certificate_transfer_v01.zip'
    assert sha(packet) == frozen['packet_sha256'] == 'c767adab75dec1eeac42db739d40722fa9f729756b916c3b1973c07643b95f0b'
    if args.execution_kind == 'github-actions':
        assert os.environ.get('GITHUB_ACTIONS') == 'true'
        assert os.environ.get('GITHUB_REPOSITORY') == 'SHiJiE1115/newproj'
        assert re.fullmatch('[0-9a-f]{40}', os.environ.get('GITHUB_SHA', ''))
        assert os.environ.get('GITHUB_RUN_ID', '').isdigit() and os.environ.get('GITHUB_RUN_ATTEMPT', '').isdigit()
        receipt['claimed_workflow_identity'] = {key: os.environ[key] for key in
            ['GITHUB_REPOSITORY', 'GITHUB_SHA', 'GITHUB_RUN_ID', 'GITHUB_RUN_ATTEMPT', 'GITHUB_JOB']}
    work = out / 'extracted'
    work.mkdir()
    with zipfile.ZipFile(packet) as archive:
        assert archive.testzip() is None and sum(info.file_size for info in archive.infolist()) < 8388608
        names = archive.namelist()
        assert len(names) == len(set(names)) and all('/' not in name and '\\' not in name for name in names)
        for name in names:
            with (work / name).open('xb') as stream:
                stream.write(archive.read(name))
    manifest = json.loads((work / 'CERTIFICATE_REPLAY_MANIFEST_V01.json').read_bytes())
    assert set(names) == {row['name'] for row in manifest['files']} | {'CERTIFICATE_REPLAY_MANIFEST_V01.json'}
    for row in manifest['files']:
        assert sha(work / row['name']) == row['sha256'] and (work / row['name']).stat().st_size == row['bytes']
    expected = work / 'INDEPENDENT_CERTIFICATE_TRANSFER_V01.json'
    assert sha(expected) == frozen['expected_windows_report_sha256'] == 'a6a270e862be8896571253968adbfcbc16a0313757a2381a7332524d5e940545'
    actual = out / 'ACTUAL_VERIFICATION.json'
    command = [sys.executable, '-I', '-X', 'utf8', '-B', str(work / 'verify_certificate_transfer_portable_v01.py'), '--out', str(actual)]
    with (out / 'stdout.txt').open('xb') as stdout, (out / 'stderr.txt').open('xb') as stderr:
        child = subprocess.Popen(command, cwd=work, stdout=stdout, stderr=stderr,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        save('PROCESS_START.json', {'pid': child.pid, 'retained_Popen': True, 'argv': command,
            'checker_sha256': sha(work / 'verify_certificate_transfer_portable_v01.py')})
        code = child.wait()
    save('PROCESS_TERMINAL.json', {'pid': child.pid, 'actual_exit_code': code, 'retained_Popen_wait': True})
    assert type(code) is int and code == 0
    result = json.loads(actual.read_bytes())
    assert result == json.loads(expected.read_bytes())
    canonical = (json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n').encode('utf-8')
    receipt.update(status='PASS_ACTUAL_CERTIFICATE_REPLAY_AND_FULL_PARSED_WINDOWS_COMPARISON',
        actual_child_exit_code=code, source_packet_sha256=sha(packet), wrapper_sha256=sha(Path(__file__).resolve()),
        freeze_sha256=sha(frozen_path), actual_result_sha256=sha(actual),
        canonical_mathematical_sha256=hashlib.sha256(canonical).hexdigest(),
        all_parsed_fields_equal_windows=True, byte_identity_across_newline_platforms_required=False,
        same_checker_across_systems_not_a_new_independent_implementation=True,
        mathematics={'RO_max_full_certificate_minimum': result['all_nonnegative_price_RO_minimum_maximum_full_certificate'],
            'unrestricted_free_probe_full_certificate_minimum': '4',
            'unrestricted_free_probe_pointwise_inflation_minimum': '2',
            'three_world_lower_certificate_triples': 48, 'attaining_function_inputs': 128},
        trust_limit='GitHub identity values in this receipt require comparison with separately trusted workflow API metadata; the receipt does not authenticate itself.')
except BaseException as exc:
    receipt.update(status='FAILED_REPLAY_PRESERVED', error=type(exc).__name__ + ': ' + str(exc))
receipt['wall_seconds'] = time.monotonic() - started
save('RUN_RECEIPT.json', receipt)
print(json.dumps({key: receipt[key] for key in ['status', 'execution_kind', 'runtime', 'new_model_API_calls']}), flush=True)
raise SystemExit(0 if receipt['status'] == 'PASS_ACTUAL_CERTIFICATE_REPLAY_AND_FULL_PARSED_WINDOWS_COMPARISON' else 1)
