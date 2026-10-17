"""Public metadata-derived GS proof replay, using actual paths and retained child handles.

Original scientific files are byte exact. Only provenance pin path labels are
explicitly bound by packet_child_v01.py. One inherited acceptance fingerprint
uses a declared origin bridge after checking actual derived bytes. No filesystem remapping.
"""
from pathlib import Path
import argparse
import ctypes
import datetime
import hashlib
import json
import os
import subprocess
import shutil
import sys
import time

P=Path(__file__).resolve().parent
ap=argparse.ArgumentParser()
ap.add_argument('--work',required=True)
ap.add_argument('--out',required=True)
ap.add_argument('--host-storage-guard',help='Optional original host environment guard; not a mathematical input')
a=ap.parse_args()
W=Path(a.work).resolve();O=Path(a.out).resolve();GUARD=Path(a.host_storage_guard).resolve() if a.host_storage_guard else None
assert sys.dont_write_bytecode and sys.flags.isolated and not sys.flags.optimize
assert os.name=='nt','Only the stated Windows host integration is tested'
assert Path(a.work).is_absolute() and Path(a.out).is_absolute()
assert not W.exists() and not O.exists() and W!=O
assert not W.is_relative_to(P) and not O.is_relative_to(P)

def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
def save(p,x):
    with Path(p).open('x',encoding='utf-8',newline='\n') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
def pin(p):
    p=Path(p);b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':sha(b)}
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def verify(p,row):
    b=Path(p).read_bytes();assert len(b)==row['bytes'] and sha(b)==row['sha256'],str(p)
def safe(root,rel):
    assert isinstance(rel,str) and '\\' not in rel
    q=Path(rel);assert not q.is_absolute() and ':' not in rel and '..' not in q.parts
    p=(root/q).resolve();assert p.is_relative_to(root);return p
def cpu(proc):
    x=ctypes.c_ulonglong;v=[x() for _ in range(4)]
    fn=ctypes.WinDLL('kernel32',use_last_error=True).GetProcessTimes
    fn.argtypes=[ctypes.c_void_p]+[ctypes.POINTER(x)]*4;fn.restype=ctypes.c_int
    assert fn(int(proc._handle),*(ctypes.byref(t) for t in v))
    return {'seconds':(v[2].value+v[3].value)/10000000,'method':'GetProcessTimes on retained child Process.Handle'}

manifest=read(P/'MANIFEST_V01.json')
assert manifest['expected_children']==17 and len(manifest['outputs'])==18
files=manifest['files'];roles={r['role']:r for r in files}
assert len(roles)==len(files)
assert len({r['file'].casefold() for r in files})==len(files)
assert {p.relative_to(P).as_posix() for p in P.rglob('*') if p.is_file()}=={r['file'] for r in files}|{'MANIFEST_V01.json'}
for row in files:verify(safe(P,row['file']),row)
config=None
if GUARD:
    assert W.drive.casefold()==O.drive.casefold()=='d:'
    assert pin(GUARD)['sha256']==manifest['host_guard_sha256']
    config=GUARD.parent/'STORAGE_GUARD_CONFIG_V01.json'
    assert pin(config)['sha256']==manifest['host_config_sha256']

# Host guard is an explicit environment input. It is never an original
# scientific-path fallback. Every scientific subprocess gets a new snapshot.
def storage(phase):
    if GUARD is None:
        for root in (W.parent,O.parent):assert root.is_dir() and shutil.disk_usage(root).free>=268435456
        g={'status':'PASS','method':'Public reviewer disk snapshot,notoriginalhostguard','required_bytes':268435456}
        if O.exists():save(O/(phase+'.STORAGE.json'),g)
        return g
    r=subprocess.run([sys.executable,'-I','-X','utf8','-B',str(GUARD),
        '--expected-local-bytes','1048576','--expected-external-bytes','67108864'],
        capture_output=True,encoding='utf-8',timeout=45)
    if r.returncode:
        if O.exists():save(O/(phase+'.STORAGE_FAILURE.json'),{'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
        raise RuntimeError('Original storage preflight failed')
    g=json.loads(r.stdout)
    assert g['status']=='PASS' and g['config_sha256']==manifest['host_config_sha256']
    assert g['script_sha256']==manifest['host_guard_sha256']
    assert g['external_after']['volume_guid']=='24e3d2ec-f154-46da-95c6-924f89aa02d0'
    assert g['external_after']['filesystem']=='NTFS'
    assert g['system_after']['available_bytes']>=10737418240+1048576
    if O.exists():save(O/(phase+'.STORAGE.json'),g)
    return g

initial=storage('BOOTSTRAP')
W.mkdir();O.mkdir();C=W/'core';C.mkdir();(W/'tmp').mkdir()
save(O/'BOOTSTRAP.STORAGE.json',initial)
for row in files:
    if row.get('stage'):
        dest=safe(C,row['stage']);dest.parent.mkdir(parents=True,exist_ok=True)
        with dest.open('xb') as f:f.write(safe(P,row['file']).read_bytes())
        verify(dest,row)
for out in manifest['outputs']:
    p=safe(C,out['stage']);p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists()
for rel in manifest['legacy_audits']:
    safe(C,rel).parent.mkdir(parents=True,exist_ok=True)
bindings=[]
for row in files:
    if row.get('stage'):bindings.append({'actual_path':str(safe(C,row['stage'])),'origin_path':row['origin_path'],'role':row['role'],**({'origin_metadata_derivative':row['origin_metadata_derivative']} if row.get('origin_metadata_derivative') else {})})
for row in manifest['outputs']:
    bindings.append({'actual_path':str(safe(C,row['stage'])),'origin_path':row['origin_path'],'role':'output/'+row['stage']})
assert len({r['actual_path'].casefold() for r in bindings})==len(bindings)
save(W/'BINDINGS_V01.json',{'schema':1,'origin_paths_are_opaque_metadata_only':True,'rows':bindings})

parent_reads=set();parent_writes=set();parent_denied=[]
readroots=[P,W,O,Path(sys.base_prefix).resolve()]
def parent_hook(event,args):
    if event.startswith('socket.') or event in ('os.system','os.posix_spawn','os.spawn','os.fork'):
        parent_denied.append(event);raise PermissionError(event)
    if event in ('os.remove','os.rmdir','os.rename','os.link','os.symlink'):
        parent_denied.append(event);raise PermissionError(event)
    if event!='open' or isinstance(args[0],int):return
    p=Path(os.fsdecode(args[0])).resolve();flags=args[2]
    write=bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
    if write:
        if not(p.is_relative_to(W) or p.is_relative_to(O)):
            parent_denied.append(str(p));raise PermissionError(str(p))
        parent_writes.add(str(p))
    else:
        if not(any(p==root or p.is_relative_to(root) for root in readroots) or p in (GUARD,config)):
            parent_denied.append(str(p));raise PermissionError(str(p))
        parent_reads.add(str(p))
sys.addaudithook(parent_hook)

children=[];comparisons=[];bridge=None
expected_by_stage={r['stage']:r for r in manifest['outputs']}
def compare(rel,phase):
    row=expected_by_stage[rel];actual=safe(C,rel);expected=safe(P,row['expected_file'])
    av=read(actual);ev=read(expected)
    assert av==ev,('Whole JSON mismatch',rel)
    if row.get('raw_byte_exact'):assert actual.read_bytes()==expected.read_bytes(),('Raw mismatch',rel)
    item={'phase':phase,'stage':rel,'entire_JSON_equal_no_fields_omitted':True,
        'whole_canonical_sha256':sha(canonical(av)),'actual':pin(actual),'expected':pin(expected),
        'raw_byte_exact_required':row.get('raw_byte_exact',False),'actual_raw_equal':actual.read_bytes()==expected.read_bytes()}
    comparisons.append(item)

def run(phase,target,anchor,outputs,tail=(),legacy=None):
    assert phase not in [x['phase'] for x in children]
    storage(phase)
    target=safe(C,target)
    source=target.read_bytes();astrow=next(r for r in files if r.get('stage')==target.relative_to(C).as_posix())
    verify(target,astrow)
    for r in outputs:assert not safe(C,r).exists()
    audit=O/(phase+'.PHYSICAL_IO.json')
    writes=[str(safe(C,r)) for r in outputs]
    if legacy:writes.append(str(safe(C,legacy)));assert not safe(C,legacy).exists()
    command=[sys.executable,'-I','-X','utf8','-B',str(P/'packet_child_v01.py'),str(P),str(W),str(target),
        str(W/'BINDINGS_V01.json'),str(audit),json.dumps(writes),'%s'%anchor,*map(str,tail)]
    env=os.environ.copy();env.update({'TMP':str(W/'tmp'),'TEMP':str(W/'tmp'),'PYTHONDONTWRITEBYTECODE':'1'})
    started=time.perf_counter()
    with (O/(phase+'.stdout.txt')).open('xb') as out,(O/(phase+'.stderr.txt')).open('xb') as err:
        p=subprocess.Popen(command,cwd=W,stdout=out,stderr=err,env=env)
        save(O/(phase+'.PROCESS_START.json'),{'phase':phase,'pid':p.pid,'command':command,'started_utc':now(),
            'actual_target':pin(target),'wrapper':pin(P/'packet_child_v01.py'),'raw_source_equals_frozen_scientific_file':True})
        timeout=False
        try:p.wait(timeout=120)
        except subprocess.TimeoutExpired:timeout=True;p.kill();p.wait()
        terminal={'phase':phase,'pid':p.pid,'actual_exit_code':p.returncode,'timed_out':timeout,
            'completed_utc':now(),'wall_seconds':time.perf_counter()-started,'full_process_CPU':cpu(p)}
    save(O/(phase+'.PROCESS_TERMINAL.json'),terminal)
    assert p.returncode==0 and not timeout,('Child failed, no automatic rerun',phase,p.returncode)
    io=read(audit);assert io['normal_return'] and not io['denied']
    assert io['actual_source_sha256']==sha(source) and io['exact_source_prefix_body_reconcatenation']
    assert io['only_global_provenance_pin_rebound']==(anchor!='none')
    assert set(io['written_files'])==set(writes+[str(audit)])
    for s in io['read_files']:
        x=Path(s).resolve()
        assert x.is_relative_to(W) or x.is_relative_to(Path(sys.base_prefix).resolve()),('Read outside scientific work/runtime',s)
    for call in io['origin_pin_calls']:
        assert Path(call['actual_path']).is_relative_to(C)
        actual=pin(Path(call['actual_path']))
        assert actual['sha256']==call['actual_sha256'] and actual['bytes']==call['actual_bytes']
        returned=call['returned_reference']
        if call['inherited_origin_commitment_bridge_used']:
            assert phase=='RESIDUAL_COVER' and call['role']=='iteration441/ACCEPTANCE_V01.json'
            bridge=roles[call['role']]['origin_metadata_derivative']
            assert returned=={'path':roles[call['role']]['origin_path'],'bytes':bridge['origin_bytes'],'sha256':bridge['origin_sha256']}
            assert actual['sha256']==bridge['derived_sha256'] and actual['bytes']==bridge['derived_bytes']
        else:assert returned=={'path':call['origin_path_label'],'bytes':actual['bytes'],'sha256':actual['sha256']}
    if legacy:
        li=read(safe(C,legacy));assert li['denied']==[]
        assert all(Path(s).is_relative_to(C) or Path(s).is_relative_to(Path(sys.base_prefix).resolve()) for s in li['read_files'])
    for rel in outputs:compare(rel,phase)
    children.append({'phase':phase,'pid':p.pid,'actual_exit_code':p.returncode,'terminal':pin(O/(phase+'.PROCESS_TERMINAL.json')),
        'physical_IO':pin(audit),'target':pin(target),'source_file_role':astrow['role']})
    print(json.dumps({'phase':phase,'pid':p.pid,'exit':p.returncode,'whole_objects':len(outputs)}),flush=True)

run('RESIDUAL_COVER','iteration458/audit_remaining_sources_v02.py','residual',[
    'iteration458/RESIDUAL_SOURCE_PROJECTIONS_V01.json','iteration458/REMAINING_SOURCE_AUDIT_V01.json'])
bridges=[]
for n in (463,464):
    for name in ['RESIDUAL_SOURCE_PROJECTIONS_V01.json','REMAINING_SOURCE_AUDIT_V01.json']:
        fresh=C/'iteration458'/name;snapshot=C/f'iteration{n}'/name
        assert fresh.read_bytes()==snapshot.read_bytes() and read(fresh)==read(snapshot)
        bridges.append({'fresh':pin(fresh),'immutable_dependency_snapshot':pin(snapshot),'raw_and_entire_JSON_equal':True})
bridge={'schema':1,'status':'PASS_FRESH_RESIDUAL_COVER_ADMITS_IMMUTABLE_DEPENDENCY_SNAPSHOTS_BEFORE_LOWER_OR_UPPER_READERS','pairs':bridges}
save(O/'DEPENDENCY_BRIDGE_V01.json',bridge)
run('MONOTONE_1345','majority_v01.py','none',['MAJORITY_RESULT_V01.json'])
for sid in manifest['residual_ids']:
    run('LOWER_'+str(sid),'iteration464/read_balanced_gs_lower_v01.py','balanced',
        [f'iteration464/SOURCE{sid}_BALANCED_LOWER_RESULT_V01.json'],[sid,C/'iteration463'],
        f'iteration464/SOURCE{sid}_BALANCED_LOWER_INPUTS_V01.json')
run('TRIANGLE_UPPER','iteration464/verify_triangle3_gs_gap_v01.py','upper',
    ['iteration464/TRIANGLE3_INDEPENDENT_STRICT_GS_GAP_CHECK_V01.json'],legacy='iteration464/TRIANGLE3_INDEPENDENT_STRICT_GS_INPUTS_V01.json')
run('BELLMAN_PRODUCE','iteration465/produce_bellman_class_v01.py','bellman_producer',
    ['iteration465/CAUSAL_SKIP_BELLMAN_PROOF_V01.json'])
run('BELLMAN_READ','iteration465/read_bellman_class_v01.py','bellman_reader',
    ['iteration465/SEPARATE_BELLMAN_CLASS_RESULT_V01.json'],legacy='iteration465/SEPARATE_BELLMAN_INPUTS_V01.json')
run('COMBINE_GS3','combine_gs3_v01.py','none',['GS_COMBINED_SCIENCE_V01.json'],[C,C/'GS_COMBINED_SCIENCE_V01.json'])
assert len(children)==17 and len(comparisons)==18
for row in files:
    verify(safe(P,row['file']),row)
    if row.get('stage'):verify(safe(C,row['stage']),row)
assert not parent_denied
save(O/'WHOLE_OBJECT_CORRESPONDENCE_V01.json',{'schema':1,'whole_objects':18,'no_fields_omitted':True,'comparisons':comparisons})
save(O/'ORIGIN_AND_CURRENT_SCOPE_V01.json',{'schema':1,
    'origin_context_immutable':'Old441receiptsand463hypothesis/464candidate/465readerlabelsareorigincontext;notcurrentPIDorverdict.',
    'current_verdict':'GS_restricted_minimum3;universalGS_equalityREFUTED;oldunrestrictedminimum2unchanged',
    'origin_pin_label_binding':'Originpathlabels;allactualbytes/SHAchecked;ONEdeclaredderivedacceptancerecordreturnsinheritedorigincommitmentafteractualderivedhashcheck;separatephysicalIOandcurrentprocessreceipts;nooriginfilesystemfallback',
    'inherited_global_source_and_full_policy_enumeration':True,'fresh_finite_monotone_source_kernels':1345,
    'fresh_residual_source_and_minimal_policy_audits':11,'fresh_balanced_lower_roots':1584,
    'full_class_P_lower_does_not_use_cached32profile_exhaustiveness':True,
    'A39_profile_read_only_for_Bayes_upper_comparison_in_separate_Bellman_reader':True,
    'combined_proof_also_reads_cached_profiles_for_feasible_mixtures_and_affine_crosschecks':True,
    'relative_box_full_class_lower_by_all16set_Lipschitz_bound':True,'arbitrary10parameter_GS_box_claimed':False,
    'same_agent_internal_not_human_external_or_formal_review':True,'priority':'OPEN','whole_project_complete':False})
save(O/'PARENT_PHYSICAL_IO_V01.json',{'schema':1,'read_files':sorted(parent_reads),'written_files':sorted(parent_writes),
    'denied':parent_denied,'boundary':'Python after initial verification/staging;subprocess receipts separate;not OS isolation'})
result={'schema':1,'status':'PASS_ACTUAL_EXTRACTED_COMBINED_GS_MINIMUM3_ALL17CHILDREN18WHOLEOBJECTS',
    'created_utc':now(),'actual_controller_pid':os.getpid(),'packet':str(P),'work':str(W),'out':str(O),
    'manifest':pin(P/'MANIFEST_V01.json'),'actual_science':pin(C/'GS_COMBINED_SCIENCE_V01.json'),
    'children':children,'mathematical_children':17,'whole_objects':18,
    'dependency_bridge':pin(O/'DEPENDENCY_BRIDGE_V01.json'),'whole_correspondence':pin(O/'WHOLE_OBJECT_CORRESPONDENCE_V01.json'),
    'current_scope':pin(O/'ORIGIN_AND_CURRENT_SCOPE_V01.json'),'parent_IO':pin(O/'PARENT_PHYSICAL_IO_V01.json'),
    'all_frozen_and_staged_immutable_files_rehashed_after':True,'raw_Bellman_proof_regenerated_byte_exact':True,
    'full_source_catalogue_and_global_policy_enumeration_regenerated':False,
    'all_scientific_target_sources_byte_exact':True,'relocation_tested_platform':'Windows',
    'public_metadata_derivative_uses_one_declared_origin_fingerprint_bridge':True,
    'priority':'OPEN','application_advantage':'NOT_ESTABLISHED','same_agent_internal_not_external_human_or_formal_review':True,
    'no_model_API_LP_newpricepriorgrid_globalenumeration_publication_or_submission':True,'whole_project_complete':False}
save(O/'ACTUAL_COMBINED_REPLAY_V01.json',result)
print(json.dumps({'status':result['status'],'children':17,'whole_objects':18,'GS_minimum':3,'priority':'OPEN'}),flush=True)
