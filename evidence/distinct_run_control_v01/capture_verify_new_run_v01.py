"""One terminal-run capture and retained-signature verification; never dispatch/retry.

Requires the root controller's independently observed identity and terminal poll.
The frozen gate's decision functions are reused unchanged. Its subprocess I/O
is recorded; GH calls go through the frozen controller's credential-safe helper.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import types

sys.dont_write_bytecode = True
ROOT = Path('C:/Users/dongs/Documents/Codex/2026-09-23/ccfa-ccfa')
MAINT = ROOT/'maintenance/storage_resume_20261010'
ART = Path(__file__).resolve().parent
CLONE = Path('D:/CodexResearch/ccfa-ccfa-01a0ce5d/scratch/iteration276_wine_v09')
HELPERS = ROOT/'outputs/review_evidence_not_copies/diagnostics/wine_v07_hosted_execution_20261011'
CONTROLLER = MAINT/'control_iter311_distinct_run_v01.py'
PLAN_SHA = '069db47ddf868a6927839fd4cffa1a19c9ac8d2093d647cdae794b39f7cd5100'
CONTROLLER_SHA = '7f643d09a48da417b316c444ca51042c0431db75d54377e8ca4b3643ace9977a'
GATE_SHA = '721d1e28e0c279ff274f915f30acb637b46461d563fbfc65e3823784a996e783'
DIRECT_SHA = 'fb8234f9caafd1ae7a3b7008e914ce33b38f52e9e0e02c3b2de41e4eee210ec3'
DISPATCH_HELPER_SHA = '18b4c090682bc7c29a71e1374a1415315986f591a7385d3e6cd1faa8812f42c0'
REPO = 'SHiJiE1115/newproj'
COMMIT = '6f64dd2a7dd75ee14ca65d2e00c4e0a5ea0d131b'
BRANCH = 'trace-isolation-v09-fd-observation'
WORKFLOW = '.github/workflows/rrnc-wine-strace.yml'
ZIP_LIMIT = 20_000_000
LOG_LIMIT = 2_000_000
SIGNATURE_LIMIT = 1_000_000
SNAPSHOT = ART/'new_run_provider_snapshot_v01.json'
ZIP = ART/'new_run_artifact.zip'
GATE_OUT = ART/'new_run_release_gate'
SIGNATURE = ART/'new_run_signature'
LOGS = ART/'capture_process_logs'
EXECUTION = ART/'CAPTURE_EXECUTION_V01.json'
RESULT = ART/'CAPTURE_RESULT_V01.json'


def need(ok, code):
    if not ok:
        raise ValueError(code)


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def desc(path):
    data = path.read_bytes()
    return {'path': path.as_posix(), 'bytes': len(data), 'sha256': sha(data)}


def read(path, cap=3_000_000):
    need(path.stat().st_size <= cap, 'JSON_INPUT_CAP')
    def pairs(items):
        value = {}
        for k, v in items:
            need(k not in value, 'DUPLICATE_JSON_KEY')
            value[k] = v
        return value
    return json.loads(path.read_bytes(), object_pairs_hook=pairs)


def write_bytes(path, data, cap):
    need(len(data) <= cap, 'OUTPUT_BYTE_CAP')
    with path.open('xb') as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())


def write(path, obj):
    write_bytes(path, (json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode(), 3_000_000)


def load(name, path, expected_sha):
    need(desc(path)['sha256'] == expected_sha, 'MODULE_PIN_'+name)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class ProcessRecords:
    """I/O adapter only. No gate predicates, semantic code or sources are changed."""
    def __init__(self, controller):
        self.controller = controller
        self.events = []
        self.gh_counts = {}

    def perform(self, name, args, *, gh=False, timeout=120, stdout_cap=LOG_LIMIT,
                stdout_path=None, text=False, cwd=None):
        need(name not in {e['name'] for e in self.events}, 'ONE_ATTEMPT_PER_PROCESS_ROLE')
        event = {'name': name, 'started_utc': now(), 'attempts': 1, 'automatic_retry': False,
                 'command': [str(self.controller.GH), *args] if gh else list(map(str, args)),
                 'cwd': Path.cwd().as_posix() if cwd is None else Path(cwd).as_posix(),
                 'timeout_seconds': timeout, 'terminal': 'NOT_STARTED'}
        self.events.append(event)
        write(LOGS/(name+'.START.json'), event)
        started = time.perf_counter()
        try:
            if gh:
                # The controller alone obtains credentials; it rejects any output
                # containing the credential before this wrapper can persist it.
                completed = self.controller.gh_call(args, timeout=timeout)
            else:
                completed = subprocess.run(args, cwd=cwd, capture_output=True, timeout=timeout, check=False)
            event.update(terminal='EXITED', actual_returncode=completed.returncode)
            out, err = completed.stdout, completed.stderr
            need(isinstance(out, bytes) and isinstance(err, bytes), 'PROCESS_BYTES_REQUIRED')
            event.update(stdout_observed_bytes=len(out), stderr_observed_bytes=len(err))
            if len(out) > stdout_cap or len(err) > LOG_LIMIT:
                event.update(output_over_cap=True, stdout_sha256=sha(out), stderr_sha256=sha(err))
                raise ValueError('PROCESS_OUTPUT_CAP')
            outpath = stdout_path if stdout_path is not None else LOGS/(name+'.stdout.bin')
            errpath = LOGS/(name+'.stderr.bin')
            write_bytes(outpath, out, stdout_cap)
            write_bytes(errpath, err, LOG_LIMIT)
            event.update(stdout=desc(outpath), stderr=desc(errpath))
            if text:
                return subprocess.CompletedProcess(args, completed.returncode, out.decode('utf-8'), err.decode('utf-8'))
            return subprocess.CompletedProcess(args, completed.returncode, out, err)
        except BaseException as error:
            # Never persist exception text or TimeoutExpired partial GH output:
            # the controller has not necessarily completed its redaction check.
            event['exception_class'] = type(error).__name__
            if isinstance(error, subprocess.TimeoutExpired):
                event['terminal'] = 'TIMEOUT_CHILD_KILLED_AND_WAITED_BY_SUBPROCESS_RUN'
            elif event['terminal'] != 'EXITED':
                event['terminal'] = 'CALL_FAILED_NO_SUCCESS_CLAIM'
            raise
        finally:
            event.update(ended_utc=now(), elapsed_seconds=time.perf_counter()-started)
            write(LOGS/(name+'.END.json'), event)

    def gate_run(self, args, **kwargs):
        argv = list(map(str, args))
        if Path(argv[0]).name.lower() in {'gh', 'gh.exe'}:
            need(argv[1:3] == ['attestation', 'verify'], 'GATE_GH_ROLE')
            return self.perform('gate_live_attestation_verify', argv[1:], gh=True,
                                timeout=kwargs.get('timeout', 120))
        if len(argv) >= 2 and Path(argv[1]) == CLONE/'experiment/verify_receipt.py':
            return self.perform('gate_native_verifier', argv, timeout=kwargs.get('timeout', 120),
                                text=kwargs.get('text', False), cwd=kwargs.get('cwd'))
        need(argv[0] == 'git' and argv[1:] == ['rev-parse', 'HEAD'] and
             Path(kwargs.get('cwd')) == CLONE, 'GATE_NATIVE_ROLE')
        return self.perform('gate_checkout_identity', [str(self.controller.GIT), *argv[1:]],
                            timeout=kwargs.get('timeout', 15), text=kwargs.get('text', False), cwd=CLONE)


def terminal_snapshot(controller, plan):
    identity_path = ART/'NEW_RUN_IDENTITY_V01.json'
    identity = read(identity_path)
    run_id = identity.get('run_id')
    need(type(run_id) is int and run_id > 0 and run_id not in plan['prior_run_ids'], 'DISTINCT_PROVIDER_RUN_REQUIRED')
    need(identity == {'repository': REPO, 'run_id': run_id, 'attempt': 1, 'commit': COMMIT,
                      'branch': BRANCH, 'url': f'https://github.com/{REPO}/actions/runs/{run_id}'}, 'IDENTITY_CONTRACT')
    polls = sorted((ART/'polls').glob('POLL_[0-9][0-9][0-9].json'))
    need(bool(polls), 'POLL_REQUIRED')
    poll_path = polls[-1]
    poll = read(poll_path)
    need(poll.get('status') == 'TERMINAL' and poll.get('new_matching_runs') == 1 and
         poll.get('run_id') == run_id, 'LATEST_POLL_NOT_KNOWN_TERMINAL')
    records = poll['records']
    need(set(records) == {'run', 'jobs', 'artifacts'}, 'PROVIDER_RECORD_ROLES')
    run, jobs, artifacts = [records[k]['body'] for k in ['run', 'jobs', 'artifacts']]
    base = f'https://api.github.com/repos/{REPO}/actions/runs/{run_id}'
    need(records['run']['url'] == base and records['jobs']['url'] == base+'/attempts/1/jobs?per_page=100'
         and records['artifacts']['url'] == base+'/artifacts?per_page=100', 'PROVIDER_URLS')
    need(run.get('status') == 'completed' and run.get('id') == run_id and type(run.get('run_attempt')) is int
         and run['run_attempt'] == 1 and run.get('head_sha') == COMMIT and run.get('head_branch') == BRANCH
         and run.get('repository', {}).get('full_name') == REPO and run.get('event') == 'workflow_dispatch'
         and run.get('workflow_id') == plan['workflow_id'] and run.get('path', '').split('@', 1)[0] == WORKFLOW,
         'TERMINAL_RUN_IDENTITY')
    intent = read(ART/'DISPATCH_INTENT_V01.json')
    need(intent['plan'] == desc(ART/'PLAN_V01.json') and intent['single_post'] is True, 'DISPATCH_PLAN_BINDING')
    need(datetime.fromisoformat(run['created_at'].replace('Z', '+00:00')) >=
         datetime.fromisoformat(intent['created_utc']).replace(microsecond=0), 'RUN_PREDATES_INTENT')
    for body, key in [(jobs, 'jobs'), (artifacts, 'artifacts')]:
        need(type(body.get('total_count')) is int and isinstance(body.get(key), list)
             and body['total_count'] == len(body[key]), 'PROVIDER_LIST_INCOMPLETE')
    snap = {'schema': 1, 'observed_identity': identity, 'identity_file': desc(identity_path),
            'terminal_poll': desc(poll_path), 'records': records, 'plan': desc(ART/'PLAN_V01.json'),
            'scope': 'Exact root-captured terminal provider observation, not a newly invented run ID or a fresh API poll.'}
    write(SNAPSHOT, snap)
    return identity, snap


def retain_signature(controller, processes, gate, run_id, tar):
    SIGNATURE.mkdir()
    tar_sha = desc(tar)['sha256']
    acceptance = {'status': 'FAIL_RETAINED_SIGNATURE_BUNDLE', 'run_id': run_id, 'attempt': 1,
                  'source_commit': COMMIT, 'receipt_tar_sha256': tar_sha,
                  'bundle_name': None, 'bundle_sha256': None, 'verification_stdout_sha256': None,
                  'download_exit': None, 'verify_exit': None, 'match': None,
                  'trust_root_network_access_not_claimed_offline': True}
    try:
        oldcwd = Path.cwd()
        try:
            os.chdir(SIGNATURE)
            downloaded = processes.perform('signature_bundle_download',
                ['attestation', 'download', str(tar), '--repo', REPO, '--limit', '1'], gh=True,
                stdout_path=SIGNATURE/'download.stdout.txt')
        finally:
            os.chdir(oldcwd)
        acceptance['download_exit'] = downloaded.returncode
        need(type(downloaded.returncode) is int and downloaded.returncode == 0, 'SIGNATURE_DOWNLOAD_FAILED')
        bundle = SIGNATURE/('sha256-'+tar_sha+'.jsonl')
        bundles = list(SIGNATURE.glob('*.jsonl'))
        need(bundles == [bundle] and 0 < bundle.stat().st_size < SIGNATURE_LIMIT, 'EXACT_BOUNDED_SIGNATURE_BUNDLE')
        acceptance.update(bundle_name=bundle.name, bundle_sha256=desc(bundle)['sha256'])
        verified = processes.perform('retained_signature_verify',
            ['attestation', 'verify', str(tar), '--bundle', str(bundle), '--repo', REPO,
             '--signer-workflow', REPO+'/'+WORKFLOW, '--source-digest', COMMIT,
             '--source-ref', 'refs/heads/'+BRANCH, '--deny-self-hosted-runners', '--format', 'json'],
            gh=True, stdout_path=SIGNATURE/'verified.stdout.json')
        acceptance['verify_exit'] = verified.returncode
        acceptance['verification_stdout_sha256'] = sha(verified.stdout)
        need(type(verified.returncode) is int and verified.returncode == 0, 'RETAINED_SIGNATURE_VERIFY_FAILED')
        data = json.loads(verified.stdout)
        need(isinstance(data, list) and all(isinstance(x, dict) for x in data), 'VERIFIED_SIGNATURE_ARRAY')
        match = gate.match_verified_attestations(data, tar_sha, REPO, COMMIT, BRANCH, run_id, 1)
        acceptance['match'] = match
        need(match['matching_subject_count'] >= 1 and match['matching_signed_run_identity_count'] >= 1,
             'SIGNED_NEW_RUN_IDENTITY_MISMATCH')
        acceptance['status'] = 'PASS_RETAINED_SIGNATURE_BUNDLE'
        return acceptance
    except BaseException as error:
        acceptance['exception_class'] = type(error).__name__
        raise
    finally:
        write(SIGNATURE/'ACCEPTANCE.json', acceptance)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute-after-terminal', action='store_true', required=True)
    parser.parse_args()
    # Nothing is written before the dedicated fresh storage guard succeeds.
    guard_path = MAINT/'ITER311_CAPTURE_EXECUTION_GUARD_V01.json'
    guard_run = subprocess.run([sys.executable, '-I', '-X', 'utf8', '-B', str(MAINT/'storage_guard.py'),
        '--expected-local-bytes', '2097152', '--expected-external-bytes', '268435456', '--output', str(guard_path)],
        capture_output=True, timeout=60, check=False)
    if guard_run.returncode != 0:
        print(json.dumps({'status': 'STORAGE_GUARD_FAILED_NO_CAPTURE', 'guard_exit': guard_run.returncode}))
        return 1
    need(read(guard_path)['status'] == 'PASS', 'GUARD_STATUS')
    need(not any(p.exists() for p in [LOGS, GATE_OUT, SIGNATURE, ZIP, SNAPSHOT, EXECUTION, RESULT,
                                     ART/'CAPTURE_START_V01.json']), 'REFUSE_OVERWRITE_CAPTURE_OR_RETRY')
    LOGS.mkdir()
    write_bytes(LOGS/'storage_guard.stdout.json', guard_run.stdout, LOG_LIMIT)
    write_bytes(LOGS/'storage_guard.stderr.bin', guard_run.stderr, LOG_LIMIT)
    result = {'schema': 1, 'status': 'FAIL_OR_UNRESOLVED_NEW_RUN_EVIDENCE', 'human_review': False,
              'release_authorized': False, 'automatic_retry': False, 'workflow_posts_by_this_script': 0,
              'guard': desc(guard_path), 'script': desc(Path(__file__)), 'started_utc': now(),
              'scope': 'One provider-identified new prospective execution and selected-syscall/arithmetic evidence. No historical execution, complete byte-read set, statistical independence or method advantage.'}
    processes = None
    started = time.perf_counter()
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    for key in ['TMP', 'TEMP', 'TMPDIR']:
        os.environ[key] = str(ART/'temp')
    tempfile.tempdir = str(ART/'temp')
    try:
        need(ART.as_posix() == 'D:/CodexResearch/ccfa-ccfa-01a0ce5d/artifacts/iteration311', 'SCRIPT_DIRECTORY')
        need(desc(ART/'PLAN_V01.json')['sha256'] == PLAN_SHA, 'PLAN_PIN')
        controller = load('iter311_capture_controller', CONTROLLER, CONTROLLER_SHA)
        plan = controller.validate_plan()
        need((plan['repository'], plan['commit'], plan['branch']) == (REPO, COMMIT, BRANCH), 'PLAN_SOURCE_IDENTITY')
        need(controller.git('rev-parse', 'HEAD') == COMMIT and not controller.git('status', '--porcelain'), 'EXACT_CLEAN_CLONE')
        target = plan['common_target']
        need(sha(json.dumps(target, sort_keys=True, separators=(',', ':')).encode()) == plan['common_target_id'], 'COMMON_TARGET_DIGEST')
        protocol = read(CLONE/'experiment/PROTOCOL.json')
        need(all(target[k] == protocol[k] for k in ['author', 'data', 'target']) and
             target['native_protocol_sha256'] == desc(CLONE/'experiment/PROTOCOL.json')['sha256'], 'TARGET_NATIVE_CONTRACT')
        result.update(plan=desc(ART/'PLAN_V01.json'), controller=desc(CONTROLLER), common_target_id=plan['common_target_id'])
        identity, snapshot = terminal_snapshot(controller, plan)
        run_id = identity['run_id']
        result.update(identity=identity, provider_snapshot=desc(SNAPSHOT),
                      provider_conclusion=snapshot['records']['run']['body']['conclusion'])
        write(ART/'CAPTURE_START_V01.json', result)
        processes = ProcessRecords(controller)
        candidates = [a for a in snapshot['records']['artifacts']['body']['artifacts']
                      if a.get('name') == f'rrnc-wine-strace-{run_id}-1']
        need(len(candidates) == 1, 'ONE_MATCHING_ARTIFACT_REQUIRED')
        artifact = candidates[0]
        wr = artifact.get('workflow_run', {})
        need(type(artifact.get('id')) is int and artifact['id'] > 0 and artifact.get('expired') is False
             and type(artifact.get('size_in_bytes')) is int and 0 < artifact['size_in_bytes'] < ZIP_LIMIT
             and wr.get('id') == run_id and wr.get('head_sha') == COMMIT and wr.get('head_branch') == BRANCH,
             'ARTIFACT_IDENTITY_OR_SIZE')
        result['artifact_metadata'] = artifact
        downloaded = processes.perform('artifact_zip_download',
            ['api', f'repos/{REPO}/actions/artifacts/{artifact["id"]}/zip'], gh=True, timeout=120,
            stdout_cap=ZIP_LIMIT, stdout_path=ZIP)
        need(type(downloaded.returncode) is int and downloaded.returncode == 0, 'ARTIFACT_DOWNLOAD_FAILED')
        need(0 < ZIP.stat().st_size < ZIP_LIMIT and artifact.get('digest') == 'sha256:'+desc(ZIP)['sha256'],
             'ARTIFACT_PROVIDER_DIGEST')
        result['artifact_zip'] = desc(ZIP)
        direct = load('direct_fixed_baseline_v09', HELPERS/'direct_fixed_baseline_v09.py', DIRECT_SHA)
        load('dispatch_v09_once', HELPERS/'dispatch_v09_once.py', DISPATCH_HELPER_SHA)
        gate = load('iter311_frozen_postrun_gate', HELPERS/'postrun_v09_release_gate.py', GATE_SHA)
        need(direct.PACKAGE == CLONE and gate.direct is direct and (gate.REPO, gate.SHA, gate.BRANCH) ==
             (REPO, COMMIT, BRANCH), 'GATE_BINDING')
        # Only subprocess transport is adapted. Gate decision functions retain
        # their original code; credential values and environments are not logged.
        gate.subprocess = types.SimpleNamespace(run=processes.gate_run, TimeoutExpired=subprocess.TimeoutExpired)
        gate_result = gate.audit(SNAPSHOT, ZIP, run_id, 1, GATE_OUT)
        write(GATE_OUT/'POSTRUN_RELEASE_GATE.json', gate_result)
        result['release_gate'] = desc(GATE_OUT/'POSTRUN_RELEASE_GATE.json')
        result['release_gate_status'] = gate_result['status']
        need(gate_result.get('release_authorized') is True and gate_result['status'] ==
             'RELEASE_PROSPECTIVE_SELECTED_SYSCALL_OBSERVATION_ONLY', 'NEW_RUN_GATE_NOT_RELEASED')
        acceptance = retain_signature(controller, processes, gate, run_id, GATE_OUT/'receipt.tar')
        result['signature_acceptance'] = desc(SIGNATURE/'ACCEPTANCE.json')
        # Recheck frozen input/source descriptors after all observations.
        controller.validate_plan()
        need(controller.git('rev-parse', 'HEAD') == COMMIT and not controller.git('status', '--porcelain'), 'SOURCE_CHANGED')
        result.update(status='PASS_CAPTURED_NEW_RUN_AND_RETAINED_SIGNATURE', release_authorized=True,
                      receipt_tar=desc(GATE_OUT/'receipt.tar'), candidate=desc(GATE_OUT/'CANDIDATE_REPORT.json'),
                      direct_baseline=desc(GATE_OUT/'DIRECT_BASELINE_REPORT.json'), inputs_rehashed_unchanged=True)
    except BaseException as error:
        result.update(exception_class=type(error).__name__)
        # ValueError codes originate in this wrapper or hash-pinned helpers;
        # do not serialize arbitrary GH/OS exception messages.
        if isinstance(error, ValueError) and str(error).replace('_', '').isalnum():
            result['failure_code'] = str(error)
    finally:
        result.update(ended_utc=now(), elapsed_seconds=time.perf_counter()-started)
        execution = {'schema': 1, 'status': 'PASS' if result['release_authorized'] else 'FAIL_OR_UNRESOLVED',
                     'script': result['script'], 'guard': result['guard'], 'started_utc': result['started_utc'],
                     'ended_utc': result['ended_utc'], 'elapsed_seconds': result['elapsed_seconds'],
                     'processes': [] if processes is None else processes.events, 'automatic_retry': False,
                     'stdout_stderr_scope': 'Retained child output only after controller credential-output checks; timeout partial GH output is withheld.',
                     'output_cap_limitation': 'Provider ZIP size checked before download and all returned buffers capped before persistence; controller gh_call internally captures output in memory.',
                     'scope': 'Actual local capture/verification subprocess observations, not an OS-signed execution receipt or a repeat of author training.'}
        write(EXECUTION, execution)
        result['execution'] = desc(EXECUTION)
        write(RESULT, result)
        print(json.dumps({'status': result['status'], 'result': desc(RESULT), 'execution': desc(EXECUTION),
                          'failure_code': result.get('failure_code')}))
    return 0 if result['release_authorized'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
