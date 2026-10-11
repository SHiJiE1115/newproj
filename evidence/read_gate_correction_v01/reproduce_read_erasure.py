"""Two-case offline admission control; derived report fixtures, no new physical run."""
import argparse
import copy
from datetime import datetime, timezone
import difflib
import hashlib
import importlib.util
import json
from pathlib import Path
import sqlite3
import sys

PINS = {'layer_candidate.py': '7d86bd4ede7e089a8325d7d57c89b7135f86f290eabd4b15bd149a64470e4918',
        'sql_baseline_v02.py': 'fed2570f8e59ee993e2b99dc9e6d24578ebb72c1b4383d81fd95302c50742488',
        'protocol.json': '3d5f542359cc385cd6edacc3612994fecb034dcedae4e3322602c1aea934641f'}
FIELD = 'trace_isolation_observed'
SCHEMA = '''CREATE TABLE tar_members(run TEXT,member TEXT,bytes INTEGER,sha TEXT,PRIMARY KEY(run,member));
CREATE TABLE run_identity(run TEXT PRIMARY KEY,repository TEXT,source_commit TEXT,run_id TEXT,attempt TEXT,protocol_sha256 TEXT,tar_sha256 TEXT);
CREATE TABLE csv_rows(scenario TEXT,draw INTEGER,seed INTEGER,test_accuracy TEXT,row_sha TEXT,PRIMARY KEY(scenario,draw));
CREATE TABLE output_edges(scenario TEXT,donor TEXT,actual_sha TEXT,summary_sha TEXT);
CREATE TABLE admissions(layer TEXT,ok INTEGER,repository TEXT,source_commit TEXT,run_id TEXT,attempt TEXT,protocol_sha256 TEXT,tar_sha256 TEXT);'''

def require(ok, message):
    if not ok:
        raise ValueError(message)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def desc(path):
    data = path.read_bytes()
    return {'path': path.as_posix(), 'bytes': len(data), 'sha256': sha(data)}

def checked(spec):
    data = Path(spec['path']).read_bytes()
    require(len(data) == spec['bytes'] and sha(data) == spec['sha256'], 'PIN: ' + spec['path'])
    return data

def write(path, obj):
    with path.open('xb') as handle:
        handle.write((json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode())

def load(name, path, expected):
    require(sha(path.read_bytes()) == expected, 'CODE_PIN: ' + path.name)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

def input_specs(p):
    return [d for r in p['runs'].values() for d in r['files'].values()] + list(p['v09_retained_signature_files'].values()) + list(p['existing_semantic_modules'].values())

def prepare():
    require(not OUT.exists(), 'OUTPUT_ALREADY_EXISTS')
    sources = []
    for name, pin in PINS.items():
        d = desc(PKG/name)
        require(d['sha256'] == pin, 'SOURCE_CHANGED')
        sources.append(d)
    p = json.loads((PKG/'protocol.json').read_bytes())
    original = (PKG/p['runs']['v09']['files']['CANDIDATE_REPORT.json']['path']).read_bytes()
    require(sha(original) == p['runs']['v09']['files']['CANDIDATE_REPORT.json']['sha256'], 'REPORT_PIN')
    line = b'      "trace_isolation_observed": true,\r\n'
    require(original.count(line) == 1, 'ONE_EXACT_LINE_REQUIRED')
    OUT.mkdir()
    (OUT/'fixtures').mkdir()
    fixtures = []
    for name, data in [('intact', original), ('isolation_erased', original.replace(line, b''))]:
        path = OUT/'fixtures'/(name + '.json')
        path.write_bytes(data)
        obj = json.loads(data)
        expected = json.loads(original)
        if name != 'intact':
            del expected['receipt_audit']['checks'][FIELD]
        require(obj == expected, 'ONLY_SPECIFIED_FIELD_MAY_CHANGE')
        fixtures.append({'id': name, 'descriptor': desc(path), 'expected_admission': name == 'intact'})
    plan = {'schema': 1, 'status': 'FROZEN_BEFORE_CONTROL_EXECUTION', 'created_utc': datetime.now(timezone.utc).isoformat(),
        'control_kind': 'One retained positive report and one synthetic single-field erasure',
        'required_contract': 'Selected-read support requires the explicitly required trace isolation flag to be present and true; retained summary PASS is not a substitute.',
        'pointer': '/receipt_audit/checks/trace_isolation_observed', 'sources': sources, 'harness': desc(Path(__file__)),
        'fixtures': fixtures,
        'prediction_not_result': {'candidate': [True, False], 'original_baseline': [True, True]},
        'conditional_repair': 'If the original baseline admits the erased fixture, add only trace_isolation_observed to its candidate required-field list; preserve all other source bytes.',
        'scope': {'original_frozen_cli_invoked': False, 'original_pin_bypassed': False,
            'new_physical_run': False, 'fresh_crypto_verification': False, 'human_gold': False,
            'same_input_bytes_for_both_adapters': True, 'derived_fixtures_have_new_pins': True,
            'not_general_adapter_equivalence_or_natural_error_rate': True},
        'stop_rule': 'Run each of the two fixtures once per original and corrected baseline mode. One full-package regression only if delivering corrected code. No additional mutations without a concrete new failure.'}
    write(OUT/'PLAN_V01.json', plan)
    print(json.dumps({'status': plan['status'], 'plan': desc(OUT/'PLAN_V01.json')}))

def probe(mode):
    plan = json.loads((OUT/'PLAN_V01.json').read_bytes())
    require(desc(Path(__file__)) == plan['harness'], 'FROZEN_HARNESS_CHANGED')
    for d in plan['sources']:
        checked(d)
    folder = OUT/(mode + '_probe')
    require(not folder.exists(), 'MODE_ALREADY_EXECUTED')
    candidate = load('erasure_candidate', PKG/'layer_candidate.py', PINS['layer_candidate.py'])
    if mode == 'original':
        baseline_path, baseline_pin = PKG/'sql_baseline_v02.py', PINS['sql_baseline_v02.py']
    else:
        patch = json.loads((OUT/'PATCH_V01.json').read_bytes())
        baseline_path = Path(patch['corrected']['path'])
        baseline_pin = patch['corrected']['sha256']
    baseline = load('erasure_baseline_' + mode, baseline_path, baseline_pin)
    p = baseline.resolve_inputs(json.loads((PKG/'protocol.json').read_bytes()), PKG)
    specs = input_specs(p)
    require(len(specs) == 17, 'INPUT_COUNT')
    original_blobs = {d['path']: checked(d) for d in specs}
    core, checker = candidate.load_semantics(p['existing_semantic_modules'])
    folder.mkdir()
    rows = []
    for fixture in plan['fixtures']:
        data = checked(fixture['descriptor'])
        pp = copy.deepcopy(p)
        pp['runs']['v09']['files']['CANDIDATE_REPORT.json'] = fixture['descriptor']
        blob = dict(original_blobs)
        blob[fixture['descriptor']['path']] = data
        # Freshly load both adapters from the same derived descriptor and unchanged tar/direct/gate bytes.
        run = candidate.load_run('v09', pp['runs']['v09'])
        con = sqlite3.connect(':memory:')
        con.executescript(SCHEMA)
        loaded = {'v09': baseline.inspect_run('v09', pp['runs']['v09'], blob, con)}
        require(loaded['v09']['key'] == run['key'], 'IDENTITY_DIFFERENCE')
        rd = candidate.selected_read(run, run)
        br = baseline.retained_read_gate('v09', loaded)
        cn = candidate.numeric(run, run, run)
        bn = baseline.numeric({'id': fixture['id'], 'numeric': 'v09', 'target': 'v09'}, loaded, con)
        raw = {k: blob[d['path']] for k, d in pp['v09_retained_signature_files'].items()}
        cs = candidate.retained_signature(run, run, raw)
        bs = baseline.retained_signature(pp, blob, loaded)
        require(cn['admitted'] and bn['positive'] and cs['admitted'] and bs['positive'], 'UNCHANGED_COMPONENT_CONTROL_FAILED')
        for layer, result in [('numeric', bn), ('read', br), ('signature', bs)]:
            con.execute('INSERT INTO admissions VALUES (?,?,?,?,?,?,?,?)', (layer, int(result['positive']), *(result['key'][k] for k in baseline.KEYS)))
        query = '''SELECT COUNT(*) FROM admissions n JOIN admissions r USING(repository,source_commit,run_id,attempt,protocol_sha256,tar_sha256)
        JOIN admissions s USING(repository,source_commit,run_id,attempt,protocol_sha256,tar_sha256)
        WHERE n.layer='numeric' AND r.layer='read' AND s.layer='signature' AND n.ok=1 AND r.ok=1 AND s.ok=1'''
        joint_rows = con.execute(query).fetchone()[0]
        require(joint_rows in (0, 1), 'SQL_JOIN_MULTIPLICITY')
        con.close()
        scope = core.digest({'plan_sha256': sha((OUT/'PLAN_V01.json').read_bytes()), 'fixture': fixture['descriptor'], 'baseline_sha256': baseline_pin})
        certs = {}
        for adapter, read_ok, joint_ok in [('candidate', rd['admitted'], rd['admitted'] and cn['admitted'] and cs['admitted']),
                                          ('baseline_fact_projection', br['positive'], joint_rows == 1)]:
            certs[adapter] = {layer: candidate.certify_layer(core, checker, {'id': fixture['id'], 'copies': 1}, layer, admitted, run['key'], scope)
                for layer, admitted in [('selected_read_gate', read_ok), ('joint_scoped_receipt', joint_ok)]}
        row = {'id': fixture['id'], 'input': fixture['descriptor'], 'expected_admission': fixture['expected_admission'],
            'candidate': rd, 'baseline': br, 'baseline_sql_joint_rows': joint_rows,
            'retained_numeric_and_signature_positive_both': True, 'scope_digest_input': scope, 'semantic_certificates': certs}
        rows.append(row)
    # Record observations even if a prediction is falsified. Validation is a separate field.
    observed = [[r['candidate']['admitted'], r['baseline']['positive']] for r in rows]
    prediction = [[True, True], [False, mode == 'original']]
    unchanged = [dict(d, unchanged=checked(d) == original_blobs[d['path']]) for d in specs]
    result = {'schema': 1, 'status': 'PASS_BOUNDED_CONTROL_OBSERVED' if observed == prediction else 'UNEXPECTED_CONTROL_RESULT',
        'mode': mode, 'plan': desc(OUT/'PLAN_V01.json'), 'harness': desc(Path(__file__)),
        'candidate_source': desc(PKG/'layer_candidate.py'), 'baseline_source': desc(baseline_path), 'cases': rows,
        'observed_candidate_baseline': observed, 'all_17_original_inputs_unchanged': unchanged,
        'scope': plan['scope'], 'completed_utc': datetime.now(timezone.utc).isoformat(),
        'certificate_scope_note': 'The existing semantic scope label is retained by the library; snapshot digest binds this new derived fixture and code scope. A valid checker verifies the admitted fact model, not the missing external fact.'}
    write(folder/'RESULT_V01.json', result)
    print(json.dumps({'status': result['status'], 'observed_candidate_baseline': observed, 'result': desc(folder/'RESULT_V01.json')}))
    require(observed == prediction, 'CONTROL_PREDICTION_FALSIFIED_INSPECT_RECORDED_RESULT')

def patch():
    result = json.loads((OUT/'original_probe/RESULT_V01.json').read_bytes())
    require(result['observed_candidate_baseline'] == [[True, True], [False, True]], 'NO_OBSERVED_DEFECT_TO_PATCH')
    old = (PKG/'sql_baseline_v02.py').read_bytes()
    require(sha(old) == PINS['sql_baseline_v02.py'], 'BASELINE_PIN')
    before = b"'wine_positive_read_observed', 'execve_wine_order'],"
    after = b"'wine_positive_read_observed', 'execve_wine_order', 'trace_isolation_observed'],"
    require(old.count(before) == 1, 'UNIQUE_PATCH_SITE')
    new = old.replace(before, after)
    require(new.replace(after, before) == old, 'PATCH_INVERSE')
    (OUT/'patched').mkdir()
    path = OUT/'patched/sql_baseline_v02.py'
    path.write_bytes(new)
    diff = ''.join(difflib.unified_diff(old.decode().splitlines(keepends=True), new.decode().splitlines(keepends=True), fromfile='wine_v02/sql_baseline_v02.py', tofile='wine_v03/sql_baseline_v02.py'))
    (OUT/'patched/trace_isolation.patch').write_bytes(diff.encode())
    write(OUT/'PATCH_V01.json', {'schema': 1, 'status': 'PATCH_PREPARED_NOT_YET_EXECUTED',
        'original': desc(PKG/'sql_baseline_v02.py'), 'corrected': desc(path), 'diff': desc(OUT/'patched/trace_isolation.patch'),
        'observed_failure': desc(OUT/'original_probe/RESULT_V01.json'), 'only_change': 'Add trace_isolation_observed to baseline required candidate flags.',
        'inverse_reconstruction_exact': True, 'scope': 'Bounded missing-field admission correction; no general equivalence claim.'})
    print(json.dumps({'status': 'PATCH_PREPARED_NOT_YET_EXECUTED', 'corrected': desc(path)}))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', required=True, type=Path, help='Extracted frozen Wine v02 directory')
    parser.add_argument('--output', required=True, type=Path, help='New output directory outside the bundle')
    args = parser.parse_args()
    PKG, OUT = args.bundle.resolve(), args.output.resolve()
    require(PKG.is_dir() and OUT.parent.is_dir(), 'BUNDLE_AND_OUTPUT_PARENT_REQUIRED')
    require(not OUT.exists() and not OUT.is_relative_to(PKG), 'OUTPUT_MUST_BE_NEW_AND_OUTSIDE_BUNDLE')
    import shutil
    require(shutil.disk_usage(OUT.parent).free >= 64*1024**2, 'OUTPUT_VOLUME_FREE_SPACE')
    prepare()
    probe('original')
    patch()
    probe('patched')
