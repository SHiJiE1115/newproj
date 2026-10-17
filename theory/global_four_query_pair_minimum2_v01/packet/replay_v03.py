"""Actual relocation, unchanged mathematical programs, whole-output comparison."""
import argparse
import copy
import ctypes
import datetime
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

P = Path(__file__).resolve().parent
sys.path.insert(0, str(P))
from portable_common_v01 import Canon, diff, encoded, pathkey, pin, raw_hash, read, save, shape

ap = argparse.ArgumentParser()
ap.add_argument('--work', type=Path, required=True)
ap.add_argument('--out', type=Path, required=True)
ap.add_argument('--host-storage-guard', type=Path)
args = ap.parse_args()
W, O = args.work.resolve(), args.out.resolve()
assert args.work.is_absolute() and args.out.is_absolute()
assert W != O and not W.is_relative_to(O) and not O.is_relative_to(W)
assert not W.is_relative_to(P) and not O.is_relative_to(P)
assert not W.exists() and not O.exists()
M = read(P/'MANIFEST_V01.json')
E = read(P/'EXPECTED_WHOLE_OBJECTS_V01.json')
for row in M['files'] + M['runtime_files']:
    f = (P/row['file']).resolve()
    assert f.is_relative_to(P)
    assert {k: pin(f)[k] for k in ('bytes', 'sha256')} == {k: row[k] for k in ('bytes', 'sha256')}
W.mkdir(parents=True)
O.mkdir(parents=True)
C = W/'core'
A = W/'audit'
(C/'iteration458').mkdir(parents=True)
(A/'iteration458').mkdir(parents=True)
(W/'io_audits').mkdir()
(W/'temp').mkdir()
os.environ['TMP'] = os.environ['TEMP'] = str(W/'temp')
rows = {r['role']: r for r in M['files']}
actual, aliases = {}, {}


def input_path(role): return P/rows[role]['file']
def core_path(role): return C/role


output_roles = {'iteration453/SINGLE_PAIR_SEPARATE_READER_RESULT_V01.json',
                'iteration458/GLOBAL_PAIR_SUPPORT_MINIMUM2_RESULT_V01.json',
                'iteration458/GLOBAL_SCOPE_AND_UPPER_QA_V01.json',
                'iteration458/GLOBAL_PAIR_MINIMUM_THEOREM_AND_PROOF_V01.txt'}
custom_roles = {'iteration441/ACCEPTANCE_V01.json', 'iteration455/PORTABLE_ACCEPTANCE_V01.json'}
for c in M['cases']:
    output_roles.update(c[k] for k in ('proof', 'producer_result', 'reader_result'))
    custom_roles.update(c[k] for k in ('reader_spec', 'origin_v01_result'))
    if 'producer_spec' in c: custom_roles.add(c['producer_spec'])
for role, row in rows.items():
    if role.startswith('terminal/') or role in output_roles or role in custom_roles: continue
    f = core_path(role)
    f.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(input_path(role), f)
    aliases[str(f)] = role

# Explicitly transport just the two local content-pointer paths in old contexts.
for role, key in [('iteration441/ACCEPTANCE_V01.json', 'local'),
                  ('iteration455/PORTABLE_ACCEPTANCE_V01.json', 'actual_result')]:
    old = read(input_path(role))
    v = copy.deepcopy(old)
    target_role = ('iteration441/LOCAL_RESULT_V01.json' if key == 'local'
                   else 'iteration455/ACTUAL_REPLAY_RESULT_V03.json')
    v[key]['path'] = str(core_path(target_role))
    assert diff({**v[key], 'path': old[key]['path']}, old[key]) is None
    reverted = copy.deepcopy(v); reverted[key]['path'] = old[key]['path']
    assert reverted == old
    save(core_path(role), v)
    actual[role] = core_path(role)
shutil.copytree(C/'iteration441', A/'iteration441')
shutil.copyfile(C/'iteration458/audit_remaining_sources_v02.py', A/'iteration458/audit_remaining_sources_v02.py')
shutil.copyfile(P/'majority_v01.py', C/'majority_v01.py')
for f in (A/'iteration441').rglob('*'):
    if f.is_file(): aliases[str(f)] = f.relative_to(A).as_posix()
aliases[str(A/'iteration458/audit_remaining_sources_v02.py')] = 'iteration458/audit_remaining_sources_v02.py'


def transported_pin(role):
    r = rows[role]
    return {'path': str(core_path(role)), 'bytes': r['bytes'], 'sha256': r['sha256']}


for c in M['cases']:
    for k in ('reader_spec', 'producer_spec'):
        if k not in c: continue
        v = read(input_path(c[k]))
        for key in ('scope', 'source', 'proof'):
            if key in v: v[key] = transported_pin(c[key])
        if k == 'reader_spec':
            v['out'] = str(core_path(c['reader_result']))
            v['reader'] = transported_pin('iteration458/read_source_pair_proof_v02.py')
        else:
            v['proof_out'] = str(core_path(c['proof']))
            v['result_out'] = str(core_path(c['producer_result']))
            v['producer'] = transported_pin('iteration458/prove_source_pair_v01.py')
        # candidate_actual_terminal remains immutable ORIGIN context, not a current receipt.
        save(core_path(c[k]), v)
        actual[c[k]] = core_path(c[k])
    v = read(input_path(c['origin_v01_result']))
    for key in ('source', 'proof'):
        v[key] = transported_pin(c[key])
    v['completeness_dependency'] = pin(C/'iteration458/REMAINING_SOURCE_AUDIT_V01.json')
    save(core_path(c['origin_v01_result']), v)
    actual[c['origin_v01_result']] = core_path(c['origin_v01_result'])

# After staging, parent scientific I/O is limited to packet/work/out/runtime.
# The two optional host-gate files are explicit non-scientific environment inputs.
guard = args.host_storage_guard.resolve() if args.host_storage_guard else None
host_files = set()
if guard:
    config = guard.parent/'STORAGE_GUARD_CONFIG_V01.json'
    assert pin(guard)['sha256'] == M['host_guard_sha256']
    assert pin(config)['sha256'] == M['host_config_sha256']
    host_files = {str(guard).casefold(), str(config).casefold()}
parent_reads, parent_writes, parent_denied = set(), set(), []
launch = {'allowed': None}


def parent_audit(event, vals):
    if event.startswith('socket.') or event in ('os.system', 'os.posix_spawn', 'os.spawn', 'os.fork'):
        parent_denied.append(event); raise PermissionError(event)
    if event == 'subprocess.Popen':
        assert launch['allowed'] is not None
        expected = subprocess.list2cmdline(launch['allowed']) if os.name == 'nt' else launch['allowed']
        assert vals[1] == expected and Path(vals[0]).resolve() == Path(sys.executable).resolve(), vals[1]
        assert Path(vals[2]).resolve() == W
    if event != 'open' or isinstance(vals[0], int): return
    p = Path(os.fsdecode(vals[0])).resolve()
    flags = vals[2]
    wr = bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
    allowed = [W, O] if wr else [P, W, O, Path(sys.base_prefix).resolve()]
    if not any(p == r or p.is_relative_to(r) for r in allowed):
        if not wr and str(p).casefold() in host_files: return
        parent_denied.append(str(p)); raise PermissionError(str(p))
    (parent_writes if wr else parent_reads).add(str(p))


sys.addaudithook(parent_audit)


def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()


def cpu(pr):
    if os.name != 'nt': return {'seconds': None, 'reason': 'Windows handle metric unavailable'}
    T = ctypes.c_ulonglong
    fn = ctypes.WinDLL('kernel32', use_last_error=True).GetProcessTimes
    fn.argtypes = [ctypes.c_void_p] + [ctypes.POINTER(T)]*4
    fn.restype = ctypes.c_int
    v = [T() for _ in range(4)]
    assert fn(int(pr._handle), *(ctypes.byref(x) for x in v))
    return {'seconds': (v[2].value+v[3].value)/10_000_000,
            'method': 'GetProcessTimes on retained Popen handle'}


def process(command, prefix, target=None, timeout=120):
    start = time.perf_counter()
    with Path(str(prefix)+'.stdout.txt').open('xb') as out, Path(str(prefix)+'.stderr.txt').open('xb') as err:
        launch['allowed'] = command
        pr = subprocess.Popen(command, executable=sys.executable, cwd=W, stdin=subprocess.PIPE, stdout=out, stderr=err)
        launch['allowed'] = None
        pr.stdin.close()
        st = {'pid': pr.pid, 'command': command, 'started_utc': now(),
              'script_sha256': pin(command[5])['sha256']}
        if target: st['executed_mathematical_target'] = pin(target)
        save(str(prefix)+'.PROCESS_START.json', st)
        timed = False
        try: pr.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed = True; pr.kill(); pr.wait()
        end = {'pid': pr.pid, 'actual_exit_code': pr.returncode, 'timed_out': timed,
               'completed_utc': now(), 'wall_seconds': time.perf_counter()-start,
               'full_process_CPU': cpu(pr)}
    save(str(prefix)+'.PROCESS_TERMINAL.json', end)
    assert pr.returncode == 0 and not timed, (prefix.name, end, Path(str(prefix)+'.stderr.txt').read_text(encoding='utf-8')[-2500:])
    return end


receipts = []


def run(phase, target, outputs, argv=()):
    prefix = C/'iteration458'/phase
    if guard:
        command = [sys.executable, '-I', '-X', 'utf8', '-B', str(guard),
                   '--expected-local-bytes', '1048576', '--expected-external-bytes', '67108864']
        process(command, C/'iteration458'/(phase+'.HOST_GUARD'), timeout=45)
        gate = read(str(prefix)+'.HOST_GUARD.stdout.txt')
        assert gate['status'] == 'PASS'
        assert gate['external_after']['volume_guid'] == '24e3d2ec-f154-46da-95c6-924f89aa02d0'
    else:
        free = min(shutil.disk_usage(W).free, shutil.disk_usage(O).free)
        assert free >= 1024**3 + 67108864
        gate = {'status': 'PASS', 'kind': 'portable_disk_space_only', 'free_bytes': free,
                'original_host_guard_used': False}
    save(str(prefix)+'.STORAGE.json', gate)
    for f in outputs: assert not f.exists(), f
    auditfile = W/'io_audits'/(phase+'.json')
    import json
    command = [sys.executable, '-I', '-X', 'utf8', '-B', str(P/'child_audit_v01.py'),
               str(P), str(W), str(target), str(auditfile), json.dumps([str(f) for f in outputs]), *map(str, argv)]
    end = process(command, prefix, target)
    audit = read(auditfile)
    assert audit['normal_return'] and not audit['denied']
    assert all(f.is_file() for f in outputs)
    receipts.append({'phase': phase, 'pid': end['pid'], 'actual_exit_code': end['actual_exit_code'],
                     'target': pin(target), 'terminal': pin(str(prefix)+'.PROCESS_TERMINAL.json'),
                     'audit': pin(auditfile)})
    if 'terminal/'+phase in rows:
        actual['terminal/'+phase] = Path(str(prefix)+'.PROCESS_TERMINAL.json')
    print('PASS '+phase, flush=True)


comparisons = []


def compare(role, f):
    actual[role] = f
    v = Canon(P, M, actual, aliases).object(role)
    wanted = E[role]
    assert diff(wanted['object'], v) is None, (role, diff(wanted['object'], v))
    assert raw_hash(encoded(v)) == wanted['canonical_sha256']
    comparisons.append({'role': role, 'raw': pin(f), 'whole_canonical_sha256': raw_hash(encoded(v)),
                        'all_top_level_keys': list(v), 'all_nested_value_counts': shape(v),
                        'mathematical_field_exclusions': [], 'whole_object_equal': True})


# Fresh audit is required before the proof readers see immutable dependency snapshots.
ah = A/'iteration458'
run('AUDIT_RESIDUAL', ah/'audit_remaining_sources_v02.py',
    [ah/'REMAINING_SOURCE_AUDIT_V01.json', ah/'RESIDUAL_SOURCE_PROJECTIONS_V01.json'])
for n in ('RESIDUAL_SOURCE_PROJECTIONS_V01.json', 'REMAINING_SOURCE_AUDIT_V01.json'):
    compare('iteration458/'+n, ah/n)
run('MAJORITY_1345', C/'majority_v01.py', [C/'MAJORITY_RESULT_V01.json'])
v = read(C/'MAJORITY_RESULT_V01.json')
assert v == E['majority']['object'] and raw_hash(encoded(v)) == E['majority']['canonical_sha256']
comparisons.append({'role': 'majority', 'raw': pin(C/'MAJORITY_RESULT_V01.json'),
                    'whole_canonical_sha256': raw_hash(encoded(v)), 'all_top_level_keys': list(v),
                    'all_nested_value_counts': shape(v), 'mathematical_field_exclusions': [], 'whole_object_equal': True})
f = C/'iteration453/SINGLE_PAIR_SEPARATE_READER_RESULT_V01.json'
run('READ_SOURCE1209', C/'iteration453/read_single_pair_proof_v01.py', [f])
compare('iteration453/SINGLE_PAIR_SEPARATE_READER_RESULT_V01.json', f)

for c in M['cases']:
    sid = c['id']
    proof, result = core_path(c['proof']), core_path(c['producer_result'])
    target = C/'iteration458'/('prove_source1217_v01.py' if sid == 1217 else 'prove_source_pair_v01.py')
    argv = () if sid == 1217 else (core_path(c['producer_spec']),)
    run('PROVE_SOURCE'+str(sid), target, [proof, result], argv)
    row = rows[c['proof']]
    assert {k: pin(proof)[k] for k in ('bytes', 'sha256')} == {k: row[k] for k in ('bytes', 'sha256')}
    aliases[str(proof)] = c['proof']
    compare(c['producer_result'], result)
    f = core_path(c['reader_result'])
    run('REREAD_SOURCE'+str(sid), C/'iteration458/read_source_pair_proof_v02.py', [f], (core_path(c['reader_spec']),))
    compare(c['reader_result'], f)

gh = C/'iteration458'
g = gh/'GLOBAL_PAIR_SUPPORT_MINIMUM2_RESULT_V01.json'
theorem = gh/'GLOBAL_PAIR_MINIMUM_THEOREM_AND_PROOF_V01.txt'
run('COMPOSE_GLOBAL_V03', gh/'compose_global_pair_minimum_v03.py', [g, theorem])
compare('iteration458/GLOBAL_PAIR_SUPPORT_MINIMUM2_RESULT_V01.json', g)
assert theorem.read_bytes() == input_path('iteration458/GLOBAL_PAIR_MINIMUM_THEOREM_AND_PROOF_V01.txt').read_bytes()
q = gh/'GLOBAL_SCOPE_AND_UPPER_QA_V01.json'
run('CHECK_GLOBAL_SCOPE_UPPER', gh/'check_global_scope_and_upper_v01.py', [q])
compare('iteration458/GLOBAL_SCOPE_AND_UPPER_QA_V01.json', q)

# Current execution view: only these two origin-context facts are transported.
legacy = read(g)
current = copy.deepcopy(legacy)
assert legacy['actual_separate_reader_passes_including_metadata_repair'] == 20
assert legacy['source1209_original_proof_and1345cases_inherited_not_rerun'] is True
current['actual_separate_reader_passes_including_metadata_repair'] = 10
current['source1209_original_proof_and1345cases_inherited_not_rerun'] = False
changes = ['actual_separate_reader_passes_including_metadata_repair',
           'source1209_original_proof_and1345cases_inherited_not_rerun']
assert {k: v for k, v in current.items() if k not in changes} == {k: v for k, v in legacy.items() if k not in changes}
save(O/'CURRENT_GLOBAL_RESULT_V01.json', current)
assert len(receipts) == 25 and len(comparisons) == len(E) == 26
for row in M['files'] + M['runtime_files']:
    assert {k: pin(P/row['file'])[k] for k in ('bytes', 'sha256')} == {k: row[k] for k in ('bytes', 'sha256')}
save(O/'WHOLE_CORRESPONDENCE_V01.json', {'schema': 1, 'status': 'PASS', 'comparisons': comparisons,
     'mathematical_field_exclusions': [], 'origin_protocol_versus_current_metadata_fields': changes})
result = {'schema': 1, 'status': 'PASS_ACTUAL_RELOCATED_COMBINED_GLOBAL_FOUR_QUERY_PAIR_SUPPORT_MINIMUM2_PROOF',
          'whole_objects': len(comparisons), 'whole_object_correspondence': pin(O/'WHOLE_CORRESPONDENCE_V01.json'),
          'actual_mathematical_children': receipts, 'all_actual_mathematical_exit_codes': [r['actual_exit_code'] for r in receipts],
          'fresh_1345_finite_monotone_certificates': True, 'fresh_11_source_physical_policy_transport_audit': True,
          'fresh_producers': 10, 'fresh_fraction_readers': 11, 'fresh_global_composition': True,
          'fresh_fixed_upper_dual_inequalities': 72, 'byte_exact_candidate_gzip_proofs': 10,
          'inherited': M['rules']['inherited'],
          'current_global_result': pin(O/'CURRENT_GLOBAL_RESULT_V01.json'),
          'legacy_protocol_view': pin(g), 'host_storage_guard_used': bool(guard),
          'scientific_inputs_from_packet_or_staged_work_only': True,
          'audit_boundary': 'Python hooks after documented bootstrap, not OS isolation',
          'not_external_independent_human_or_formal_kernel_review': True,
          'bibliographic_priority': 'OPEN', 'application_advantage': 'NOT_ESTABLISHED',
          'new_model_calls_hosted_runs_numeric_grids_LP_human_labels_PDF_or_publicupload': False,
          'whole_project_complete': False}
save(O/'ACTUAL_REPLAY_RESULT_V01.json', result)
save(O/'PARENT_IO_AUDIT_V01.json', {'reads': sorted(parent_reads), 'writes': sorted(parent_writes),
     'denied': parent_denied, 'host_environment_guard_files_separate': sorted(host_files),
     'boundary': 'Python audit after packet staging/bootstrap, no network, allowlisted child commands'})
assert not parent_denied
print({'status': result['status'], 'actual_children': len(receipts), 'whole_objects': len(comparisons)}, flush=True)
