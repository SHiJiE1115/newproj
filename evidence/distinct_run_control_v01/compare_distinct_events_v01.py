"""Offline iteration311 comparison. No dispatch, author execution, or crypto call.

The three frozen requests use a common artifact target and actual event identities.
Both adapters read the same originals independently. Their existing source modules
are immutable; v09 is their schema alias, not the identity of the new event.
Invoke only after acquisition, with a fresh storage-guard receipt and a NEW output
directory. Missing/failed new evidence cannot become support. Location overrides
retain all exact byte/hash requirements; resource checks remain local to this host.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sqlite3
import sys

sys.dont_write_bytecode = True
ART = Path('D:/CodexResearch/ccfa-ccfa-01a0ce5d/artifacts')
HERE = ART / 'iteration311'
BUNDLE = ART / 'iteration309/package_build_v01/wine_layer_calibration_v02'
BASELINE = ART / 'iteration310/package_build_v01/wine_layer_calibration_v03/sql_baseline_v02.py'
INITIAL_PROVIDER_STATE = None
OLD_RELEASE_DIRECTORY = None
OLD_SIGNATURE_DIRECTORY = None
PLAN_SHA = '069db47ddf868a6927839fd4cffa1a19c9ac8d2093d647cdae794b39f7cd5100'
PINS = {
    'candidate': (BUNDLE / 'layer_candidate.py', '7d86bd4ede7e089a8325d7d57c89b7135f86f290eabd4b15bd149a64470e4918'),
    'baseline': (BASELINE, '347816748a8e5bbb63e50bf68557f581fdd385da67f0cd57bd67f2da3820d57a'),
    'protocol': (BUNDLE / 'protocol.json', '3d5f542359cc385cd6edacc3612994fecb034dcedae4e3322602c1aea934641f'),
    'core': (BUNDLE / 'semantic/rules_v2_core.py', '60988f369a01d71c04d838697e702f0f7c8307bd2de36a1eaa759a0aed48f9c6'),
    'checker': (BUNDLE / 'semantic/rules_v2_checker.py', 'e77ca753c64813839c17c3fb0bbef8ddd836a2836a25b234ec336f631570035b'),
}
RELEASE = 'RELEASE_PROSPECTIVE_SELECTED_SYSCALL_OBSERVATION_ONLY'
NATIVE_PASS = 'PASS_PROSPECTIVE_STRACE_OBSERVATION_ONLY'
GATE_FIELDS = (
    'provider_url_binding', 'run_external_identity', 'run_completed_success',
    'exact_two_attempt_jobs', 'author_job_success', 'second_job_success',
    'github_hosted_linux_jobs', 'second_job_verifier_and_attest_steps',
    'artifact_run_and_digest_binding', 'candidate_and_direct_same_tar_pass',
    'cryptographic_attestation_verified',
)
RUN_FILES = ('receipt.tar', 'CANDIDATE_REPORT.json', 'DIRECT_BASELINE_REPORT.json',
             'POSTRUN_RELEASE_GATE.json')
MATRIX = [
    ('two_references_one_event', ['old', 'old'], ['run'], 'UNRESOLVED', 1),
    ('two_actual_events', ['old', 'new'], ['run'], 'MET', 2),
    ('shared_input_and_implementation', ['old', 'new'],
     ['run', 'dataset', 'implementation'], 'UNRESOLVED', 2),
]


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def read_bytes(path, cap=16 * 1024 * 1024):
    path = Path(path)
    need(path.is_file(), 'MISSING_INPUT:' + str(path))
    need(path.stat().st_size <= cap, 'INPUT_SIZE_LIMIT:' + str(path))
    with path.open('rb') as handle:
        raw = handle.read(cap + 1)
    need(len(raw) <= cap, 'INPUT_GREW_OVER_LIMIT:' + str(path))
    return raw


def descriptor(path, raw=None):
    path = Path(path)
    raw = read_bytes(path) if raw is None else raw
    return {'path': path.as_posix(), 'bytes': len(raw), 'sha256': sha(raw)}


def pinned(spec):
    raw = read_bytes(spec['path'])
    need(len(raw) == spec['bytes'] and sha(raw) == spec['sha256'],
         'INPUT_PIN_MISMATCH:' + spec['path'])
    return raw


def parse(raw):
    def pairs(items):
        out = {}
        for key, value in items:
            need(key not in out, 'DUPLICATE_JSON_KEY:' + key)
            out[key] = value
        return out
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError('NONFINITE_JSON:' + x)))


def load_module(name, path):
    need(name not in sys.modules, 'MODULE_NAME_ALREADY_PRESENT:' + name)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def event_id(event):
    return json.dumps(event, separators=(',', ':'))


def check_identity(identity, plan):
    need(identity['repository'] == plan['repository'] and
         identity['commit'] == plan['commit'] and identity['branch'] == plan['branch'],
         'PROVIDER_IDENTITY_SOURCE_MISMATCH')
    need(type(identity['run_id']) is int and type(identity['attempt']) is int and
         identity['run_id'] > 0 and identity['attempt'] == 1, 'PROVIDER_EVENT_TYPES')
    need(identity['run_id'] not in plan['prior_run_ids'], 'NEW_EVENT_WAS_ALREADY_PRESENT')
    need(identity['url'] == 'https://github.com/' + plan['repository'] +
         '/actions/runs/' + str(identity['run_id']), 'PROVIDER_IDENTITY_URL')
    return [identity['repository'], identity['run_id'], identity['attempt']]


def provider_context(label, plan, parser):
    """Shared acquisition contract, reread separately by each intake path."""
    if label == 'old':
        spec = copy.deepcopy(plan['initial_provider_state'])
        if INITIAL_PROVIDER_STATE is not None:
            spec['path'] = INITIAL_PROVIDER_STATE.as_posix()
        obj = parser(pinned(spec))
        rows = [r for r in obj['runs']['body']['workflow_runs'] if r['id'] == plan['old_event'][1]]
        need(len(rows) == 1, 'OLD_PROVIDER_IDENTITY_NOT_UNIQUE')
        run = rows[0]
        need(run['head_sha'] == plan['commit'] and run['conclusion'] == 'success' and
             run['status'] == 'completed' and run['run_attempt'] == plan['old_event'][2],
             'OLD_PROVIDER_RUN_NOT_SUCCESSFUL')
        return {'event': plan['old_event'], 'descriptors': [spec], 'run': run,
                'source_kind': 'pre-dispatch retained provider state'}
    identity_path = HERE / 'NEW_RUN_IDENTITY_V01.json'
    identity_raw = read_bytes(identity_path)
    identity = parser(identity_raw)
    event = check_identity(identity, plan)
    intent_path = HERE / 'DISPATCH_INTENT_V01.json'
    intent_raw = read_bytes(intent_path)
    intent = parser(intent_raw)
    need(intent['plan']['sha256'] == PLAN_SHA and intent['single_post'] is True,
         'DISPATCH_INTENT_NOT_BOUND_TO_PLAN')
    candidates = []
    polls = sorted((HERE / 'polls').glob('POLL_*.json'))
    need(len(polls) <= 100, 'PROVIDER_POLL_COUNT_LIMIT')
    for path in polls:
        raw = read_bytes(path, 2 * 1024 * 1024)
        obj = parser(raw)
        if obj.get('status') == 'TERMINAL' and obj.get('run_id') == event[1]:
            candidates.append((path, raw, obj))
    need(bool(candidates), 'NEW_PROVIDER_TERMINAL_RECORD_PENDING')
    path, raw, terminal = candidates[-1]
    need(terminal['new_matching_runs'] == 1, 'AMBIGUOUS_NEW_PROVIDER_RUN')
    run = terminal['records']['run']['body']
    jobs = terminal['records']['jobs']['body']
    artifacts = terminal['records']['artifacts']['body']
    expected_url = 'https://api.github.com/repos/' + plan['repository'] + '/actions/runs/' + str(event[1])
    need(terminal['records']['run']['url'] == expected_url and
         terminal['records']['jobs']['url'] == expected_url + '/attempts/1/jobs?per_page=100' and
         terminal['records']['artifacts']['url'] == expected_url + '/artifacts?per_page=100',
         'PROVIDER_RECORD_URL_MISMATCH')
    need(type(run['id']) is int and run['id'] == event[1] and run['run_attempt'] == 1 and
         run['head_sha'] == plan['commit'] and run['head_branch'] == plan['branch'] and
         run['workflow_id'] == plan['workflow_id'] and run['event'] == 'workflow_dispatch' and
         run['repository']['full_name'] == plan['repository'] and run['html_url'] == identity['url'],
         'TERMINAL_PROVIDER_IDENTITY_MISMATCH')
    created = datetime.fromisoformat(run['created_at'].replace('Z', '+00:00'))
    dispatched = datetime.fromisoformat(intent['created_utc']).replace(microsecond=0)
    need(created >= dispatched, 'NEW_RUN_PREDATES_DISPATCH')
    need(run['status'] == 'completed' and run['conclusion'] == 'success',
         'NEW_PROVIDER_RUN_DID_NOT_SUCCEED')
    need(jobs['total_count'] == len(jobs['jobs']) == 2 and
         all(j['run_id'] == event[1] and j['status'] == 'completed' and
             j['conclusion'] == 'success' for j in jobs['jobs']), 'NEW_PROVIDER_JOBS_NOT_BOTH_SUCCESSFUL')
    return {'event': event, 'descriptors': [descriptor(identity_path, identity_raw),
            descriptor(intent_path, intent_raw), descriptor(path, raw)], 'run': run,
            'jobs': jobs, 'artifacts': artifacts, 'source_kind': 'retained terminal provider observation'}


def input_spec(label, plan, template, context):
    """Build per-event descriptors from actual files, never candidate output facts."""
    if label == 'old':
        named = {Path(d['path']).name: copy.deepcopy(d) for d in plan['old_evidence']}
        for name, descriptor_ in named.items():
            directory = OLD_RELEASE_DIRECTORY if name in RUN_FILES else OLD_SIGNATURE_DIRECTORY
            if directory is not None:
                descriptor_['path'] = (directory / name).as_posix()
    else:
        release = HERE / 'new_run_release_gate'
        signature = HERE / 'new_run_signature'
        named = {name: descriptor(release / name) for name in RUN_FILES}
        for name in ('ACCEPTANCE.json', 'verified.stdout.json'):
            named[name] = descriptor(signature / name)
        bundle_name = 'sha256-' + named['receipt.tar']['sha256'] + '.jsonl'
        named[bundle_name] = descriptor(signature / bundle_name)
    need(len(named) == 7, 'EXPECTED_SEVEN_PER_EVENT_ORIGINALS')
    for spec in named.values():
        pinned(spec)
    spec = copy.deepcopy(template['runs']['v09'])
    event = context['event']
    spec['files'] = {name: named[name] for name in RUN_FILES}
    spec['identity'] = {'GITHUB_REPOSITORY': event[0], 'GITHUB_SHA': plan['commit'],
                        'GITHUB_RUN_ID': str(event[1]), 'GITHUB_RUN_ATTEMPT': str(event[2])}
    spec['run_nonce'] = sha((plan['commit'] + ':' + str(event[1]) + ':' + str(event[2])).encode())[:32]
    need(spec['protocol_sha256'] == plan['common_target']['native_protocol_sha256'],
         'COMMON_NATIVE_PROTOCOL_MISMATCH')
    signatures = {n: d for n, d in named.items() if n not in RUN_FILES}
    return spec, signatures, named


def candidate_gate(run, raw, context, plan, parser):
    g, p = run['gate'], run['protocol']
    a = parser(raw['ACCEPTANCE.json'])
    k = run['key']
    checks = {
        'release_authorized': g.get('release_authorized') is True,
        'release_status': g.get('status') == RELEASE,
        'required_gate_checks': all(g.get('checks', {}).get(f) is True for f in GATE_FIELDS),
        'all_recorded_gate_checks': bool(g.get('checks')) and all(x is True for x in g['checks'].values()),
        'candidate_status': g.get('candidate_status') == NATIVE_PASS,
        'direct_status': g.get('direct_baseline_status') == NATIVE_PASS,
        'source_branch': g['expected_external_identity']['head_branch'] == plan['branch'],
        'common_author': p['author'] == plan['common_target']['author'],
        'common_data': p['data'] == plan['common_target']['data'],
        'common_numeric_target': p['target'] == plan['common_target']['target'],
        'actual_event': [k['repository'], int(k['run_id']), int(k['attempt'])] == context['event'],
        'acceptance_strict_exit_types': all(type(a.get(f)) is int and a[f] == 0
                                            for f in ('download_exit', 'verify_exit')),
        'acceptance_match_counts': all(type(a['match'].get(f)) is int and a['match'][f] == 1
                                      for f in ('matching_subject_count', 'matching_signed_run_identity_count')),
        'gate_crypto_status': g['attestation']['status'] == 'CRYPTO_VERIFIED',
    }
    if 'artifacts' in context:
        observed = g['provider_observed']
        artifacts = context['artifacts']['artifacts']
        hits = [x for x in artifacts if x['id'] == observed['artifact_id']]
        checks['provider_artifact_digest'] = len(hits) == 1 and hits[0]['digest'] == 'sha256:' + g['zip_sha256'] == observed['artifact_provider_digest']
        checks['provider_run_url'] = observed['run_html_url'] == context['run']['html_url']
    return {'admitted': all(checks.values()), 'checks': checks}


def baseline_gate(run, raw_by_path, signatures, context, plan, parser):
    """Direct baseline guard, using its own parsed objects; no candidate results."""
    gate = run['gate']
    acceptance = parser(raw_by_path[signatures['ACCEPTANCE.json']['path']])
    checks = []
    def check(name, ok):
        checks.append({'edge': name, 'pass': bool(ok)})
    check('authorized_exactly_true', gate['release_authorized'] is True)
    check('released_scoped_layer', gate['status'] == RELEASE)
    for name in GATE_FIELDS:
        check('gate.' + name, gate['checks'].get(name) is True)
    check('no_failed_extra_gate_flag', bool(gate['checks']) and all(v is True for v in gate['checks'].values()))
    check('native_report_statuses', gate['candidate_status'] == gate['direct_baseline_status'] == NATIVE_PASS)
    check('branch', gate['expected_external_identity']['head_branch'] == plan['branch'])
    for name in ('author', 'data', 'target'):
        check('common_' + name, run['protocol'][name] == plan['common_target'][name])
    key = run['key']
    check('event_identity', [key['repository'], int(key['run_id']), int(key['attempt'])] == context['event'])
    for field in ('download_exit', 'verify_exit'):
        check('acceptance.' + field, type(acceptance.get(field)) is int and acceptance[field] == 0)
    for field in ('matching_subject_count', 'matching_signed_run_identity_count'):
        check('acceptance.match.' + field, type(acceptance['match'].get(field)) is int and acceptance['match'][field] == 1)
    check('crypto_verified_status', gate['attestation']['status'] == 'CRYPTO_VERIFIED')
    if 'artifacts' in context:
        matches = [a for a in context['artifacts']['artifacts'] if a['id'] == gate['provider_observed']['artifact_id']]
        check('provider_artifact_digest', len(matches) == 1 and matches[0]['digest'] ==
              gate['provider_observed']['artifact_provider_digest'] == 'sha256:' + gate['zip_sha256'])
        check('provider_run_url', gate['provider_observed']['run_html_url'] == context['run']['html_url'])
    return {'positive': all(c['pass'] for c in checks), 'checks': checks}


def baseline_connection():
    con = sqlite3.connect(':memory:')
    con.executescript('''
      CREATE TABLE tar_members(run TEXT,member TEXT,bytes INTEGER,sha TEXT,PRIMARY KEY(run,member));
      CREATE TABLE run_identity(run TEXT PRIMARY KEY,repository TEXT,source_commit TEXT,run_id TEXT,attempt TEXT,protocol_sha256 TEXT,tar_sha256 TEXT);
      CREATE TABLE csv_rows(scenario TEXT,draw INTEGER,seed INTEGER,test_accuracy TEXT,row_sha TEXT,PRIMARY KEY(scenario,draw));
      CREATE TABLE output_edges(scenario TEXT,donor TEXT,actual_sha TEXT,summary_sha TEXT);
    ''')
    return con


def intake(label, mode, module, plan, template):
    info = {'label': label, 'mode': mode, 'admitted': False, 'event': None,
            'status': 'NOT_ADMITTED', 'input_descriptors': [], 'provider_descriptors': []}
    try:
        parser = parse if mode == 'candidate' else module.parse
        context = provider_context(label, plan, parser)
        info.update(event=context['event'], provider_descriptors=context['descriptors'],
                    provider_source_kind=context['source_kind'])
        spec, signatures, named = input_spec(label, plan, template, context)
        info['input_descriptors'] = list(named.values())
        info['schema_alias'] = 'v09; the actual identity is in event and spec.identity'
        if mode == 'candidate':
            run = module.load_run('v09', spec)
            raw = {name: pinned(d) for name, d in signatures.items()}
            numeric = module.numeric(run, run, run)
            selected = module.selected_read(run, run)
            signed = module.retained_signature(run, run, raw)
            extra = candidate_gate(run, raw, context, plan, parser)
            admitted = all(x['admitted'] for x in (numeric, selected, signed, extra))
            info['source_binding_checks'] = run['binding_checks']
        else:
            raw = {d['path']: pinned(d) for d in named.values()}
            con = baseline_connection()
            try:
                run = module.inspect_run('v09', spec, raw, con)
                loaded = {'v09': run}
                scenario = {'id': label, 'numeric': 'v09', 'target': 'v09'}
                numeric = module.numeric(scenario, loaded, con)
                selected = module.retained_read_gate('v09', loaded)
                signed = module.retained_signature({'v09_retained_signature_files': signatures}, raw, loaded)
                extra = baseline_gate(run, raw, signatures, context, plan, parser)
                admitted = all(x['positive'] for x in (numeric, selected, signed, extra))
                info['source_binding_checks'] = 'Independent inspect_run completed without error.'
            finally:
                con.close()
        info.update(admitted=admitted, status='ADMITTED' if admitted else 'RETAINED_GATE_OR_BINDING_NOT_PASSED',
                    joint_key=run['key'], numeric=numeric, selected_read=selected,
                    retained_signature=signed, additional_admission=extra)
        for d in info['input_descriptors'] + info['provider_descriptors']:
            pinned(d)
        return info
    except Exception as error:
        info.update(status='PENDING_OR_FAILED_INPUT_NOT_ADMITTED',
                    error_type=type(error).__name__, error=str(error), admitted=False)
        return info


def semantic_rows(core, checker, plan, evidence, snapshot_sha):
    target = core.Target(core.TargetKind.ARTIFACT_VERSION, plan['common_target_id'])
    rows = []
    for request in plan['matrix']:
        records, facts, origins = [], {}, {}
        missing = []
        for index, label in enumerate(request['events']):
            event = evidence[label]['event']
            if event is None:
                missing.append({'reference': index, 'slot': label, 'reason': evidence[label]['status']})
                continue  # Missing identities do not become invented distinct events.
            unit = event_id(event)
            rid = request['id'] + ':reference:' + str(index)
            records.append(core.EvidenceRecord(rid, unit, 'shared-wine-code-data-design', target,
                                               'retained-prospective-event/' + label))
            ok = evidence[label]['admitted']
            facts[rid] = core.EvidenceFact('support' if ok else 'neutral', ok,
                                          core.EvidenceBasis.HASHED_ARTIFACT, 'reported')
            origins[unit] = {'run': frozenset([unit]),
                             'dataset': frozenset([plan['common_target']['data']['sha256']]),
                             'implementation': frozenset([plan['common_target']['author']['sha256']])}
        scope = core.Scope('wine-distinct-prospective-events', 'iteration311-v01', snapshot_sha,
                          ('One retained evidence projection; not an exhaustive physical history.',
                           'Actual provider event identities supply the run dimension.',
                           'Dataset and implementation are shared pinned artifacts.',
                           'Semantic checking does not authenticate adapter facts.',
                           'Missing identities are omitted, not invented as new events.'))
        world = core.World('retained-admitted-event-projection', facts, origins)
        study = core.Study(scope, tuple(records), (world,))
        claim = core.Claim(request['id'], target, tuple(request['dimensions']),
                           (core.EvidenceBasis.HASHED_ARTIFACT,), 'reported', False)
        cert = core.certify(study, claim, 'replication', replication_r=2, quantifier=core.Quantifier.FIXED)
        checked = checker.verify_certificate(study, claim, cert, predicate='replication',
                                              replication_r=2, quantifier=core.Quantifier.FIXED)
        need(checked.valid, 'INDEPENDENT_SEMANTIC_CHECK_FAILED:' + request['id'])
        distinct = len({event_id(evidence[x]['event']) for x in request['events']
                        if evidence[x]['admitted'] and evidence[x]['event'] is not None})
        rows.append({'id': request['id'], 'dimensions': request['dimensions'], 'status': cert.status.value,
                     'admitted_distinct_event_count': distinct, 'requested_references': len(request['events']),
                     'omitted_unidentified_references': missing,
                     'claim': json.loads(core.canonical_bytes(claim)),
                     'study': json.loads(core.canonical_bytes(study)),
                     'certificate': json.loads(core.canonical_bytes(cert)),
                     'checker': {'valid': checked.valid, 'errors': list(checked.errors)}})
    return rows


def sql_rows(plan, evidence):
    """Consume only baseline intake results, never candidate facts or certificates."""
    con = sqlite3.connect(':memory:')
    con.executescript('''
      CREATE TABLE refs(scenario TEXT,ref INTEGER,repository TEXT,run_id INTEGER,attempt INTEGER,
                        admitted INTEGER,dataset TEXT,implementation TEXT);
      CREATE TABLE requested(scenario TEXT,dimension TEXT);
    ''')
    for request in plan['matrix']:
        con.executemany('INSERT INTO requested VALUES (?,?)', [(request['id'], d) for d in request['dimensions']])
        for index, label in enumerate(request['events']):
            info = evidence[label]
            if info['event'] is not None:
                con.execute('INSERT INTO refs VALUES (?,?,?,?,?,?,?,?)',
                            (request['id'], index, *info['event'], int(info['admitted']),
                             plan['common_target']['data']['sha256'], plan['common_target']['author']['sha256']))
    pair_sql = '''SELECT a.ref,b.ref FROM refs a JOIN refs b ON a.scenario=b.scenario AND a.ref<b.ref
      WHERE a.scenario=? AND a.admitted=1 AND b.admitted=1
        AND (a.repository<>b.repository OR a.run_id<>b.run_id OR a.attempt<>b.attempt)
        AND NOT EXISTS (SELECT 1 FROM requested d WHERE d.scenario=a.scenario AND
          ((d.dimension='run' AND a.repository=b.repository AND a.run_id=b.run_id AND a.attempt=b.attempt)
           OR (d.dimension='dataset' AND a.dataset=b.dataset)
           OR (d.dimension='implementation' AND a.implementation=b.implementation)))
      ORDER BY a.ref,b.ref'''
    count_sql = '''SELECT COUNT(*) FROM (SELECT DISTINCT repository,run_id,attempt
      FROM refs WHERE scenario=? AND admitted=1)'''
    rows = []
    for request in plan['matrix']:
        pairs = [list(p) for p in con.execute(pair_sql, (request['id'],))]
        count = con.execute(count_sql, (request['id'],)).fetchone()[0]
        rows.append({'id': request['id'], 'dimensions': request['dimensions'],
                     'status': 'MET' if pairs else 'UNRESOLVED',
                     'admitted_distinct_event_count': count, 'valid_reference_pairs': pairs})
    con.close()
    return rows, {'pair_query': pair_sql, 'count_query': count_sql,
                  'source': 'Only independently extracted baseline admission and event identities.'}


def validate_guard(path):
    raw = read_bytes(path)
    g = parse(raw)
    age = (datetime.now(timezone.utc) - datetime.fromisoformat(g['checked_at_utc'])).total_seconds()
    need(g['status'] == 'PASS' and 0 <= age < 1800, 'FRESH_STORAGE_GUARD_REQUIRED')
    need(g['external_after']['volume_guid'] == '24e3d2ec-f154-46da-95c6-924f89aa02d0', 'WRONG_EXTERNAL_VOLUME')
    need(g['expected_external_write_bytes'] >= 2 * 1024 * 1024 and
         g['system_after']['available_bytes'] >= 10 * 1024**3 + g['expected_local_write_bytes'],
         'GUARD_OUTPUT_BUDGET_OR_C_RESERVE')
    return descriptor(path, raw)


def main():
    global HERE, PINS, INITIAL_PROVIDER_STATE, OLD_RELEASE_DIRECTORY, OLD_SIGNATURE_DIRECTORY
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--storage-guard', required=True, type=Path)
    parser.add_argument('--plan', type=Path, default=HERE / 'PLAN_V01.json')
    parser.add_argument('--new-artifacts', type=Path, default=HERE,
                        help='Contains new_run_release_gate, new_run_signature, identity, intent, and polls.')
    parser.add_argument('--v03-package', type=Path,
                        help='Optional extracted v03 root supplying all exact-pinned helper modules and protocol.')
    parser.add_argument('--old-release-directory', type=Path,
                        help='Optional same-byte old receipt/report directory; e.g. package/evidence/v09.')
    parser.add_argument('--old-signature-directory', type=Path,
                        help='Optional same-byte old signature directory; e.g. package/evidence/signature.')
    parser.add_argument('--initial-provider-state', type=Path,
                        help='Optional same-byte pre-dispatch state; defaults beside the selected plan.')
    args = parser.parse_args()
    HERE = args.new_artifacts.resolve()
    plan_path = args.plan.resolve()
    INITIAL_PROVIDER_STATE = (args.initial_provider_state.resolve() if args.initial_provider_state else
                              plan_path.parent / 'INITIAL_PROVIDER_STATE_V01.json')
    OLD_RELEASE_DIRECTORY = args.old_release_directory.resolve() if args.old_release_directory else None
    OLD_SIGNATURE_DIRECTORY = args.old_signature_directory.resolve() if args.old_signature_directory else None
    if args.v03_package:
        package = args.v03_package.resolve()
        relative = {'candidate': 'layer_candidate.py', 'baseline': 'sql_baseline_v02.py',
                    'protocol': 'protocol.json', 'core': 'semantic/rules_v2_core.py',
                    'checker': 'semantic/rules_v2_checker.py'}
        PINS = {name: (package / relative[name], value[1]) for name, value in PINS.items()}
    out = args.output.resolve()
    need(out.parent.is_dir() and not out.exists(), 'OUTPUT_MUST_BE_NEW_WITH_EXISTING_PARENT')
    protected = [HERE / 'new_run_release_gate', HERE / 'new_run_signature', HERE / 'polls',
                 *[path.parent for path, _ in PINS.values()]]
    protected += [p for p in (OLD_RELEASE_DIRECTORY, OLD_SIGNATURE_DIRECTORY) if p is not None]
    need(not any(out.is_relative_to(p.resolve()) for p in protected), 'OUTPUT_INSIDE_INPUT_BUNDLE')
    guard = validate_guard(args.storage_guard)
    out.mkdir()
    result = {'schema': 1, 'status': 'FAIL', 'started_utc': datetime.now(timezone.utc).isoformat(),
              'storage_guard': guard, 'script': descriptor(Path(__file__)), 'rows': [],
              'offline_only': True, 'new_author_execution_by_this_program': False,
              'fresh_cryptographic_verification_by_this_program': False,
              'semantic_checker_authenticates_external_truth': False,
              'historical_authentication': False, 'human_gold': False, 'advantage_claim': False}
    try:
        plan_raw = read_bytes(plan_path)
        need(sha(plan_raw) == PLAN_SHA, 'FROZEN_PLAN_CHANGED')
        plan = parse(plan_raw)
        result['plan'] = descriptor(plan_path, plan_raw)
        need(sha(json.dumps(plan['common_target'], sort_keys=True, separators=(',', ':')).encode()) ==
             plan['common_target_id'], 'COMMON_TARGET_DIGEST_MISMATCH')
        observed = [(x['id'], x['events'], x['dimensions'], x['expected_r2_if_new_admitted'],
                     x['expected_distinct_runs']) for x in plan['matrix']]
        need(observed == MATRIX, 'THREE_ROW_MATRIX_CHANGED')
        semantics = plan['semantics']
        need(semantics['predicate'] == 'replication' and semantics['r'] == 2 and
             semantics['closed_scope'] is False and semantics['quantifier'] == 'EXISTS_GROUP_FOR_ALL_WORLDS',
             'FROZEN_SEMANTIC_REQUEST_CHANGED')
        result['source_pin_scope'] = ('Frozen plan source paths are historical descriptions, not followed here. '
                                      'Both intake modules verify the native source/protocol bytes retained in each tar.')
        module_descriptors = {}
        for name, (path, expected) in PINS.items():
            raw = read_bytes(path)
            need(sha(raw) == expected, 'IMMUTABLE_MODULE_PIN:' + name)
            module_descriptors[name] = descriptor(path, raw)
        result['module_descriptors'] = module_descriptors
        template = parse(pinned(module_descriptors['protocol']))
        core = load_module('rules_v2_core', PINS['core'][0])
        checker = load_module('rules_v2_checker', PINS['checker'][0])
        candidate = load_module('iter311_candidate', PINS['candidate'][0])
        baseline = load_module('iter311_baseline', PINS['baseline'][0])
        # Independent reads/parses and existing implementation paths; no returned
        # candidate object is supplied to any baseline function.
        ce = {label: intake(label, 'candidate', candidate, plan, template) for label in ('old', 'new')}
        be = {label: intake(label, 'baseline', baseline, plan, template) for label in ('old', 'new')}
        result['candidate_events'], result['baseline_events'] = ce, be
        snapshot = {'plan': result['plan'], 'modules': module_descriptors,
                    'script': result['script'],
                    'candidate_inputs': {k: {'event': v['event'], 'files': v['input_descriptors'],
                                             'provider': v['provider_descriptors']} for k, v in ce.items()},
                    'baseline_inputs': {k: {'event': v['event'], 'files': v['input_descriptors'],
                                            'provider': v['provider_descriptors']} for k, v in be.items()}}
        result['snapshot'], result['snapshot_sha256'] = snapshot, sha(canonical(snapshot))
        candidate_rows = semantic_rows(core, checker, plan, ce, result['snapshot_sha256'])
        baseline_rows, queries = sql_rows(plan, be)
        result['candidate_rows'], result['baseline_rows'], result['sql'] = candidate_rows, baseline_rows, queries
        for c, b, expected in zip(candidate_rows, baseline_rows, plan['matrix']):
            result['rows'].append({'id': c['id'], 'candidate_status': c['status'], 'baseline_status': b['status'],
                                   'candidate_distinct': c['admitted_distinct_event_count'],
                                   'baseline_distinct': b['admitted_distinct_event_count'],
                                   'agree': c['status'] == b['status'] and c['admitted_distinct_event_count'] == b['admitted_distinct_event_count'],
                                   'frozen_success_branch_status': expected['expected_r2_if_new_admitted']})
        same = {label: ce[label]['event'] == be[label]['event'] and
                ce[label]['input_descriptors'] == be[label]['input_descriptors'] and
                ce[label]['provider_descriptors'] == be[label]['provider_descriptors'] for label in ce}
        result['same_information'] = same
        for info in list(ce.values()) + list(be.values()):
            for d in info['input_descriptors'] + info['provider_descriptors']:
                pinned(d)
        result['all_observed_inputs_unchanged'] = True
        need(all(same.values()), 'CANDIDATE_BASELINE_INPUT_DIFFERENCE')
        need(ce['old']['admitted'] and be['old']['admitted'], 'OLD_POSITIVE_CONTROL_NOT_ADMITTED')
        need(all(x['agree'] for x in result['rows']) and
             all(ce[k]['admitted'] == be[k]['admitted'] for k in ce), 'CANDIDATE_BASELINE_DISAGREEMENT')
        if ce['new']['admitted']:
            for row, expected in zip(candidate_rows, plan['matrix']):
                need(row['status'] == expected['expected_r2_if_new_admitted'] and
                     row['admitted_distinct_event_count'] == expected['expected_distinct_runs'],
                     'FROZEN_SUCCESS_MATRIX_MISMATCH:' + row['id'])
            result['status'] = 'PASS_THREE_FROZEN_ROWS_TWO_ACTUAL_ADMITTED_EVENTS'
        else:
            need(all(x['status'] == 'UNRESOLVED' for x in candidate_rows), 'FAILED_NEW_EVENT_YIELDED_MET')
            result['status'] = 'INCOMPLETE_NEW_EVENT_NOT_ADMITTED_ALL_R2_UNRESOLVED'
        result['limits'] = plan['limits'] + [
            'Provider selection and descriptor assembly are shared input-contract plumbing, not independent implementations.',
            'Candidate and baseline independently parse originals and compute their numerical/provenance predicates.',
            'Saved fresh-verification evidence is inspected offline; this comparison does not perform cryptography.',
            'Text is not a merge key. Run identities, not code/data/text similarity, determine run separation.',
            'No measurement/team dimension is certified; dataset means only the pinned raw artifact identity.']
    except Exception as error:
        result.update(status='FAIL_COMPARISON_NOT_CERTIFIED', error_type=type(error).__name__, error=str(error))
    result['completed_utc'] = datetime.now(timezone.utc).isoformat()
    raw = (json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
    need(len(raw) <= 2 * 1024 * 1024, 'RESULT_OUTPUT_CAP')
    path = out / 'RESULT_V01.json'
    with path.open('xb') as handle:
        handle.write(raw)
    print(json.dumps({'status': result['status'], 'result': descriptor(path, raw), 'rows': result['rows']}))
    return 0 if result['status'].startswith('PASS_') else 2


if __name__ == '__main__':
    raise SystemExit(main())
