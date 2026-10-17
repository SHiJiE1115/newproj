"""Full portable replay; Python standard library only. See README.txt."""
import sys
import os
from pathlib import Path
import json
import hashlib
import argparse
import time

ROOT=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('--out',required=True,help='New JSON output path; never overwrites')
args=parser.parse_args();OUT=Path(args.out).resolve()
assert not OUT.exists() and OUT.parent.is_dir() and not OUT.is_relative_to(ROOT)
assert not sys.flags.optimize,'Assertions must remain enabled; do not use -O.'
assert sys.dont_write_bytecode,'Use python -B verify.py --out <new-output.json>.'
runtime=Path(sys.base_prefix).resolve();reads=set();runtime_reads=set();denied=[]
def audit(event,a):
    if event=='open':
        raw=a[0]
        if isinstance(raw,int):return
        if not isinstance(raw,(str,bytes,os.PathLike)):raise RuntimeError('Unsupported open target')
        p=Path(os.fsdecode(raw)).resolve()
        mode=a[1];flags=a[2]
        writing=(isinstance(mode,str) and any(x in mode for x in 'wax+')) or bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC))
        if writing:
            if p==OUT:return
        elif p.is_relative_to(ROOT):reads.add(p.relative_to(ROOT).as_posix());return
        elif p.is_relative_to(runtime):runtime_reads.add(p.relative_to(runtime).as_posix());return
        denied.append({'event':event,'category':'write' if writing else 'read'})
        raise PermissionError('Read/write outside the portable input/output contract')
    if event.startswith(('socket.','subprocess.')) or event in ('os.system','os.exec','os.posix_spawn'):
        denied.append({'event':event});raise PermissionError('Network/process launch disabled during replay')
sys.addaudithook(audit)
sys.path.insert(0,str(ROOT))
start=time.perf_counter()
import proofio
import catalogue
import policies
import structures
import prices
import seven

files=proofio.check_static_files()
families=proofio.data('families')['rows'];groups=proofio.data('groups')['groups']
assert len(families)==1356
assigned=[i for g in groups for i in g['orbits']]
assert len(assigned)==len(set(assigned))==1356 and set(assigned)==set(range(1356))
science={
    'scope':'complete_binary_equivalence_partition_fibres_le4_all_nonnegative_real_additive_prices_private_zero_error_worst_input_randomization',
    'catalogue':catalogue.verify(families),
    'complete_policy_families':policies.verify(families),
    'threshold_and_subset':structures.threshold_and_subset(families,groups),
    'structural':structures.structural(families,groups),
    'additive_only':prices.verify(families),
    'old_positive_seven_witness':seven.verify(),
    'conclusion':{'le4_RA_equals_RP':True,'strict_randomized_additive_first_occurrence_interval':[5,7],
        'exact_first_occurrence_unknown':True,'arbitrary_partial_promises_included':False,
        'universal_known_prior_result_claimed':False,'literature_priority_established':False,
        'human_review':False,'formal_proof_kernel':False,'new_API_calls':0,'new_discovery_grid':False}}
canonical=json.dumps(science,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')
assert not denied
result={'schema':1,'status':'PASS_FULL_PORTABLE_REPLAY','science':science,
    'science_sha256':hashlib.sha256(canonical).hexdigest(),
    'execution':{'elapsed_seconds':time.perf_counter()-start,'python':sys.version.split()[0],
        'static_files_checked':files,'packet_relative_files_read':sorted(reads),
        'runtime_relative_files_read':sorted(runtime_reads),'denied':denied,
        'file_open_contract':'packetinputsandPythonstdlibruntimeonly;singlenewoutput;PythonaudithooknotOSsecuritysandbox',
        'network_and_child_processes_disabled_during_replay':True}}
with OUT.open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'status':result['status'],'science_sha256':result['science_sha256'],'elapsed_seconds':result['execution']['elapsed_seconds']}))
