"""Run the fixed-point certificate and separate DP using packet files only."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import sys

if not __debug__ or sys.flags.optimize:
    raise RuntimeError('Assertions must remain enabled; do not use -O.')
if not sys.flags.dont_write_bytecode:
    raise RuntimeError('Run with -B to avoid creating bytecode files in the packet.')

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--out',required=True)
args = parser.parse_args()
OUT = Path(args.out)
assert OUT.is_absolute() and OUT.parent.is_dir() and not OUT.exists()
OUT = OUT.resolve()
assert not OUT.is_relative_to(ROOT)
RUNTIME = Path(sys.base_prefix).resolve()
phase = 'manifest'
reads = {}
runtime_reads = set()
writes = []


def audit(event, args):
    if event in ('socket.connect','socket.getaddrinfo','subprocess.Popen','os.system'):
        raise RuntimeError('Network and subprocess use are outside this checker.')
    if event != 'open' or isinstance(args[0],int):
        return
    path = Path(os.fsdecode(args[0])).resolve()
    mode = args[1]
    flags = args[2]
    writing = (isinstance(mode,str) and any(c in mode for c in 'wax+')) or (
        isinstance(flags,int) and bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)))
    if writing:
        if path != OUT:
            raise RuntimeError('Unexpected write outside the requested new result.')
        writes.append('requested_result')
    elif path.is_relative_to(ROOT):
        reads.setdefault(phase,set()).add(path.relative_to(ROOT).as_posix())
    elif path.is_relative_to(RUNTIME):
        runtime_reads.add(path.relative_to(RUNTIME).as_posix())
    else:
        raise RuntimeError('Unexpected file read outside packet and Python runtime.')


sys.addaudithook(audit)


def load(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))


def canonical(obj):
    normalized = json.loads(json.dumps(obj,ensure_ascii=False))
    return json.dumps(normalized,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')


manifest = load(ROOT/'MANIFEST.json')
expected_names = {'MANIFEST.json'} | {r['name'] for r in manifest['files']}
assert {p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file()} == expected_names
for row in manifest['files']:
    p = ROOT/row['name']
    assert p.resolve().is_relative_to(ROOT) and not p.is_symlink()
    raw = p.read_bytes()
    assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
assert manifest['scope']=='Oneacceptedcoveragepoint_fullAandcausal-skipP_analyticconstantremoval_robustboxes'
expected = load(ROOT/'EXPECTED_SCIENCE.json')


def module(name):
    path = ROOT/name
    namespace = {'__file__':str(path),'__name__':'portable_'+path.stem}
    exec(compile(path.read_text(encoding='utf-8'),name,'exec'),namespace)
    return namespace['run']


phase = 'main'
main = module('main_check.py')()
assert reads['main'] == {'main_check.py','data/frozen_scope.json','data/source1209.json.gz'}
phase = 'separate'
other = module('bayes_check.py')()
assert reads['separate'] == {'bayes_check.py','data/frozen_scope.json'}
phase = 'derived'
derived = module('derive.py')(main,other)
assert reads['derived'] == {'derive.py'}
science = {'main':{k:v for k,v in main.items() if k not in ('scope','input_families')},
           'separate':other,'derived':derived}
assert canonical(science)==canonical(expected)
phase = 'transport'
payload = {
    'schema':1,'status':'PASS_ONE_RELOCATABLE_COVERAGE_PROOF_ALL_SCIENCE_FIELDS_MATCH_ACCEPTED_ORIGINALS',
    'science':science,
    'science_sha256':hashlib.sha256(canonical(science)).hexdigest(),
    'transport':{'scope':main['scope'],'input_families':main['input_families'],
                 'manifest_sha256':hashlib.sha256((ROOT/'MANIFEST.json').read_bytes()).hexdigest()},
    'execution':{'python_version':platform.python_version(),'assertions_enabled':__debug__,
        'no_network_or_subprocess_requested_by_checker':True,
        'separate_component_did_not_read_family_or_main_result':True,
        'file_open_audit_is_python_observation_not_OS_sandbox':True,
        'same_existing_algorithms_portability_not_new_independent_implementation_or_human_review':True,
        'three_query_lower_inherited_not_reexecuted':True},
}
phase = 'result'
with OUT.open('x',encoding='utf-8') as f:
    assert writes == ['requested_result']
    payload['execution']['packet_file_reads_by_component']={k:sorted(v) for k,v in reads.items()}
    payload['execution']['runtime_file_read_count']=len(runtime_reads)
    payload['execution']['actual_allowed_write_events']=writes.copy()
    json.dump(payload,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'status':payload['status'],'science_sha256':payload['science_sha256'],
    'R_A':derived['clean_exact_RA'],'R_P':derived['clean_exact_RP'],'gap':derived['gap'],
    'P_orders':len(other['all24_original_Porder_results']),
    'main_paths':504,'box_gap_lower':derived['box_gap_lower']}))
