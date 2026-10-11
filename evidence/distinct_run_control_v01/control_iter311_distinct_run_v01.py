"""Freeze and dispatch exactly one Wine v09 execution; never retry a POST."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request

ROOT = Path('C:/Users/dongs/Documents/Codex/2026-09-23/ccfa-ccfa')
MAINT = ROOT/'maintenance/storage_resume_20261010'
ART = Path('D:/CodexResearch/ccfa-ccfa-01a0ce5d/artifacts/iteration311')
CLONE = Path('D:/CodexResearch/ccfa-ccfa-01a0ce5d/scratch/iteration276_wine_v09')
GIT = Path('C:/Users/dongs/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe')
GH = Path(os.environ['LOCALAPPDATA'])/'Microsoft/WinGet/Packages/GitHub.cli_Microsoft.Winget.Source_8wekyb3d8bbwe/bin/gh.exe'
REPO = 'SHiJiE1115/newproj'
BRANCH = 'trace-isolation-v09-fd-observation'
COMMIT = '6f64dd2a7dd75ee14ca65d2e00c4e0a5ea0d131b'
WORKFLOW = 'rrnc-wine-strace.yml'
OLD_RUN = 38136338509
OLD = Path('D:/CodexResearch/ccfa-ccfa-01a0ce5d/artifacts/iteration276')
HELPERS = ROOT/'outputs/review_evidence_not_copies/diagnostics/wine_v07_hosted_execution_20261011'

def require(ok, msg):
    if not ok: raise ValueError(msg)
def now(): return datetime.now(timezone.utc).isoformat()
def sha(b): return hashlib.sha256(b).hexdigest()
def desc(p):
    b = p.read_bytes()
    return {'path': p.as_posix(), 'bytes': len(b), 'sha256': sha(b)}
def read(p): return json.loads(p.read_bytes())
def write(p, obj):
    with p.open('xb') as f:
        f.write((json.dumps(obj, indent=2, ensure_ascii=False)+'\n').encode())
        f.flush()
        os.fsync(f.fileno())
def git(*args):
    return subprocess.check_output([str(GIT), '-C', str(CLONE), *args], timeout=30).decode().strip()
def guard(tag, external=4194304):
    path = MAINT/('ITER311_'+tag+'_GUARD_V01.json')
    subprocess.run([sys.executable, '-I', '-X', 'utf8', '-B', str(MAINT/'storage_guard.py'),
        '--expected-local-bytes', '65536', '--expected-external-bytes', str(external), '--output', str(path)],
        check=True, stdout=subprocess.DEVNULL)
    return desc(path)
def public(route):
    require(route.startswith('repos/'+REPO+'/'), 'REPOSITORY_ROUTE')
    url = 'https://api.github.com/'+route
    req = urllib.request.Request(url, headers={'User-Agent': 'CodexResearch-DistinctRunControl',
        'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28'})
    with urllib.request.urlopen(req, timeout=30) as response:
        body = response.read(2000001)
        require(response.status == 200 and len(body) <= 2000000, 'API_RESPONSE_CAP')
        require(response.url == url, 'UNEXPECTED_METADATA_REDIRECT')
    return {'url': url, 'observed_utc': now(), 'body': json.loads(body)}
def credential():
    env = os.environ.copy()
    env['GIT_TERMINAL_PROMPT'] = '0'
    result = subprocess.run([str(GIT), '-C', str(CLONE), '-c', 'credential.interactive=false',
        '-c', 'core.askPass=', 'credential', 'fill'], input=b'protocol=https\nhost=github.com\n\n',
        capture_output=True, env=env, timeout=30)
    require(result.returncode == 0, 'NORMAL_GITHUB_AUTH_UNAVAILABLE_OUTPUT_WITHHELD')
    fields = dict(line.split(b'=', 1) for line in result.stdout.splitlines() if b'=' in line)
    secret = fields.get(b'password')
    require(bool(secret), 'NORMAL_GITHUB_AUTH_MISSING_OUTPUT_WITHHELD')
    return secret
def gh_call(args, timeout=90):
    secret = credential()
    env = os.environ.copy()
    env.update(GH_TOKEN=secret.decode(), GH_HOST='github.com', GH_PROMPT_DISABLED='1',
               TEMP=str(ART/'temp'), TMP=str(ART/'temp'), TMPDIR=str(ART/'temp'), PYTHONDONTWRITEBYTECODE='1')
    result = subprocess.run([str(GH), *args], capture_output=True, env=env, timeout=timeout)
    require(secret not in result.stdout and secret not in result.stderr, 'CREDENTIAL_BEARING_OUTPUT_WITHHELD')
    env.pop('GH_TOKEN', None)
    return result
def preflight():
    require(git('rev-parse', 'HEAD') == COMMIT and not git('status', '--porcelain'), 'EXACT_CLEAN_V09_CHECKOUT')
    require(git('ls-remote', 'origin', 'refs/heads/'+BRANCH) == COMMIT+'\trefs/heads/'+BRANCH, 'REMOTE_REF_DRIFT')
    wf = public('repos/'+REPO+'/actions/workflows/'+WORKFLOW)
    runs = public('repos/'+REPO+'/actions/workflows/'+WORKFLOW+'/runs?per_page=100')
    w, r = wf['body'], runs['body']
    require(w['path'] == '.github/workflows/'+WORKFLOW and w['state'] == 'active', 'WORKFLOW_NOT_ACTIVE')
    require(r['total_count'] == len(r['workflow_runs']) and len(r['workflow_runs']) < 100, 'INCOMPLETE_PRIOR_RUN_LIST')
    require(all(x['status'] == 'completed' for x in r['workflow_runs']), 'EXISTING_WORKFLOW_RUN_NOT_TERMINAL')
    require(any(x['id'] == OLD_RUN and x['head_sha'] == COMMIT and x['conclusion'] == 'success' for x in r['workflow_runs']), 'OLD_POSITIVE_EVENT_NOT_FOUND')
    return {'workflow': wf, 'runs': runs}
def validate_plan():
    p = read(ART/'PLAN_V01.json')
    require(p['controller'] == desc(Path(__file__)), 'FROZEN_CONTROLLER_CHANGED')
    for d in p['source_pins']+p['old_evidence']:
        require(desc(Path(d['path'])) == d, 'FROZEN_INPUT_CHANGED')
    return p
def prepare():
    require(not ART.exists(), 'ARTIFACT_DIRECTORY_ALREADY_EXISTS')
    g = guard('PREPARE', 8388608)
    state = preflight()
    ART.mkdir()
    (ART/'temp').mkdir()
    (ART/'polls').mkdir()
    write(ART/'INITIAL_PROVIDER_STATE_V01.json', state)
    paths = [CLONE/name for name in git('ls-tree', '-r', '--name-only', COMMIT).splitlines()]
    require(all(p.is_file() for p in paths), 'SOURCE_FILE_MISSING')
    helper_names = ['postrun_v09_release_gate.py', 'direct_fixed_baseline_v09.py', 'dispatch_v09_once.py']
    paths += [HELPERS/n for n in helper_names]
    protocol = read(CLONE/'experiment/PROTOCOL.json')
    require(desc(CLONE/'experiment/PROTOCOL.json')['sha256'] == 'aeae194c6df93796bbcb50d1e70dc6fb240c570a07657052193e1a3a0d5434f5', 'NATIVE_PROTOCOL_PIN')
    common = {'kind': 'ARTIFACT_VERSION', 'repository': REPO, 'source_commit': COMMIT,
        'native_protocol_sha256': desc(CLONE/'experiment/PROTOCOL.json')['sha256'],
        'author': protocol['author'], 'data': protocol['data'], 'target': protocol['target'],
        'meaning': 'Specified pinned Wine artifact/protocol numerical cell supported by scoped selected-syscall observations from admitted prospective executions.'}
    target_id = sha(json.dumps(common, sort_keys=True, separators=(',', ':')).encode())
    evidence = [OLD/'v09_release_gate_v01'/n for n in ['receipt.tar', 'CANDIDATE_REPORT.json', 'DIRECT_BASELINE_REPORT.json', 'POSTRUN_RELEASE_GATE.json']]
    evidence += [OLD/'v09_signed_bundle_v01'/n for n in ['ACCEPTANCE.json', 'verified.stdout.json']]
    evidence.append(next((OLD/'v09_signed_bundle_v01').glob('sha256-*.jsonl')))
    plan = {'schema': 1, 'status': 'FROZEN_BEFORE_NEW_RUN_DEVELOPMENT_CONTROL', 'created_utc': now(),
        'authority': 'Continuing direct user authorization 持续授权全部授权; ordinary CCF B/C direction controls current research.',
        'controller': desc(Path(__file__)), 'source_pins': [desc(p) for p in paths], 'old_evidence': [desc(p) for p in evidence],
        'initial_provider_state': desc(ART/'INITIAL_PROVIDER_STATE_V01.json'), 'guard': g,
        'repository': REPO, 'branch': BRANCH, 'commit': COMMIT, 'workflow_id': state['workflow']['body']['id'],
        'prior_run_ids': sorted(x['id'] for x in state['runs']['body']['workflow_runs']),
        'old_event': [REPO, OLD_RUN, 1], 'common_target': common, 'common_target_id': target_id,
        'support_conditions': ['Exact pre-frozen source and author/data hashes; no tolerance or target edits after observing output.',
            'Native candidate and independent direct v09 verifier pass on exactly the same newly downloaded tar with independently supplied provider identity.',
            'Both provider jobs complete successfully; artifact digest matches download; new run identity is absent from pre-dispatch IDs, matches branch/commit, workflow_dispatch and attempt 1.',
            'Fresh cryptographic verification matches tar SHA, pinned signer/source/ref and the new run invocation URI; retain the signature bundle and verification stdout.',
            'Arithmetic matches frozen 25 draws/seeds and reported 3dp target, within existing native verifier rules.'],
        'matrix': [
            {'id': 'two_references_one_event', 'events': ['old', 'old'], 'dimensions': ['run'], 'expected_r2_if_new_admitted': 'UNRESOLVED', 'expected_distinct_runs': 1},
            {'id': 'two_actual_events', 'events': ['old', 'new'], 'dimensions': ['run'], 'expected_r2_if_new_admitted': 'MET', 'expected_distinct_runs': 2},
            {'id': 'shared_input_and_implementation', 'events': ['old', 'new'], 'dimensions': ['run', 'dataset', 'implementation'], 'expected_r2_if_new_admitted': 'UNRESOLVED', 'expected_distinct_runs': 2}],
        'semantics': {'predicate': 'replication', 'r': 2, 'quantifier': 'EXISTS_GROUP_FOR_ALL_WORLDS', 'closed_scope': False,
            'source_unit': 'Actual (repository,run_id,attempt) event; never file name, tar hash, text similarity or source commit alone.',
            'experiment_design_id': 'One shared fixed design for both events.',
            'dataset_dimension': 'Identity of the pinned Wine raw input artifact, not a claim about new underlying measurements.',
            'implementation_dimension': 'Identity of the pinned author code artifact.',
            'failure': 'Keep failed/missing new evidence in retained output; do not admit it. The two-event r2 request remains UNRESOLVED.'},
        'same_information_baseline': 'Independent parsing and numeric/provenance checks of the same old/new originals, exact SQL identity joins and distinct event count/pair intersection. No candidate fact-table or certificate input.',
        'execution_limit': {'workflow_posts': 1, 'automatic_retries': 0, 'existing_workflow_job_limits_minutes': [25, 5]},
        'limits': ['One newly requested execution, not a new independent dataset/team/design, scientific replication study or natural-label accuracy benchmark.',
            'Environment is not fully locked: apt versions are not pinned. Same code/data/contract does not imply identical environments or CSV bytes.',
            'No historical-authentication, application-superiority, statistical independence or theoretical novelty claim.',
            'No P1 release, human labels, LLM calls, journal submission or manuscript revision.'],
        'old_outcome_known_before_plan': True, 'new_outcome_unknown_before_dispatch': True}
    write(ART/'PLAN_V01.json', plan)
    print(json.dumps({'status': plan['status'], 'plan': desc(ART/'PLAN_V01.json'), 'prior_run_ids': plan['prior_run_ids'], 'common_target_id': target_id}))
def dispatch():
    require(not (ART/'DISPATCH_INTENT_V01.json').exists(), 'INTENT_EXISTS_DO_NOT_REPEAT_POST')
    p = validate_plan()
    g = guard('DISPATCH', 8388608)
    state = preflight()
    require(sorted(x['id'] for x in state['runs']['body']['workflow_runs']) == p['prior_run_ids'], 'NEW_RUN_BEFORE_DISPATCH_INSPECT')
    require(state['workflow']['body']['id'] == p['workflow_id'], 'WORKFLOW_ID_CHANGED')
    review = read(ART/'PRE_DISPATCH_REVIEW_V01.json')
    require(review['status'].startswith('PASS') and review['plan_sha256'] == desc(ART/'PLAN_V01.json')['sha256'], 'PLAN_REVIEW_REQUIRED')
    write(ART/'PRE_DISPATCH_PROVIDER_STATE_V01.json', state)
    intent = {'schema': 1, 'created_utc': now(), 'plan': desc(ART/'PLAN_V01.json'), 'guard': g,
        'repository': REPO, 'branch': BRANCH, 'commit': COMMIT, 'prior_run_ids': p['prior_run_ids'], 'single_post': True}
    write(ART/'DISPATCH_INTENT_V01.json', intent)
    try:
        r = gh_call(['api', 'repos/'+REPO+'/actions/workflows/'+str(p['workflow_id'])+'/dispatches', '-X', 'POST', '-f', 'ref='+BRANCH])
        # gh exit 0 confirms accepted request; the run identity still comes from an independent API observation.
        result = {'status': 'REQUEST_ACCEPTED_RUN_NOT_YET_OBSERVED' if r.returncode == 0 else 'REQUEST_REJECTED_OR_UNCERTAIN',
            'exit_code': r.returncode, 'stdout_bytes': len(r.stdout), 'stderr_bytes': len(r.stderr),
            'ended_utc': now(), 'no_retry': True, 'credential_persisted': False}
    except Exception as e:
        result = {'status': 'AMBIGUOUS_REQUEST_INSPECT_RUNS_DO_NOT_RETRY', 'exception_class': type(e).__name__, 'ended_utc': now(), 'no_retry': True}
    write(ART/'DISPATCH_RESULT_V01.json', result)
    print(json.dumps(result))
    require(result['status'] == 'REQUEST_ACCEPTED_RUN_NOT_YET_OBSERVED', 'DISPATCH_NOT_CONFIRMED_INSPECT_NO_REPEAT')
def poll():
    p = validate_plan()
    intent = read(ART/'DISPATCH_INTENT_V01.json')
    n = len(list((ART/'polls').glob('POLL_*.json')))
    g = guard('POLL_'+str(n).zfill(3))
    state = public('repos/'+REPO+'/actions/workflows/'+WORKFLOW+'/runs?per_page=100')
    runs = state['body']['workflow_runs']
    selected = [r for r in runs if r['id'] not in p['prior_run_ids'] and r['head_sha'] == COMMIT and r['head_branch'] == BRANCH and r['event'] == 'workflow_dispatch']
    result = {'schema': 1, 'observed_utc': now(), 'guard': g, 'list': state, 'new_matching_runs': len(selected), 'status': 'AWAITING_PROVIDER_IDENTITY'}
    if len(selected) == 1:
        run = selected[0]
        require(run['run_attempt'] == 1, 'UNEXPECTED_RUN_ATTEMPT')
        require(datetime.fromisoformat(run['created_at'].replace('Z', '+00:00')) >= datetime.fromisoformat(intent['created_utc']).replace(microsecond=0), 'RUN_PREDATES_INTENT')
        record = public('repos/'+REPO+'/actions/runs/'+str(run['id']))
        jobs = public('repos/'+REPO+'/actions/runs/'+str(run['id'])+'/attempts/1/jobs?per_page=100')
        artifacts = public('repos/'+REPO+'/actions/runs/'+str(run['id'])+'/artifacts?per_page=100')
        result.update(status='TERMINAL' if record['body']['status'] == 'completed' else 'VERIFIED_LIVE_PROVIDER_RUN',
            run_id=run['id'], run_status=record['body']['status'], conclusion=record['body']['conclusion'],
            records={'run': record, 'jobs': jobs, 'artifacts': artifacts})
        identity = {'repository': REPO, 'run_id': run['id'], 'attempt': 1, 'commit': COMMIT, 'branch': BRANCH, 'url': run['html_url']}
        identity_path = ART/'NEW_RUN_IDENTITY_V01.json'
        if identity_path.exists(): require(read(identity_path) == identity, 'OBSERVED_RUN_IDENTITY_CHANGED')
        else: write(identity_path, identity)
    elif len(selected) > 1:
        result['status'] = 'AMBIGUOUS_MULTIPLE_NEW_RUNS_DO_NOT_ASSIGN_IDENTITY'
    output = ART/'polls'/('POLL_'+str(n).zfill(3)+'.json')
    write(output, result)
    print(json.dumps({k: result[k] for k in ['status', 'new_matching_runs', 'run_id', 'run_status', 'conclusion'] if k in result} | {'receipt': desc(output)}))

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('mode', choices=['prepare', 'dispatch', 'poll'])
    mode = ap.parse_args().mode
    {'prepare': prepare, 'dispatch': dispatch, 'poll': poll}[mode]()
