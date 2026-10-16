"""Offline conditional check of retained provider snapshots and original generated archive; no science rerun."""
from pathlib import Path
import argparse,hashlib,json,zipfile
HERE=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args();out=Path(a.out)
assert out.is_absolute() and not out.exists()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(n):return json.loads((HERE/n).read_bytes())
run=read('RUN_PROVIDER_V01.json');jobs=read('JOBS_PROVIDER_V01.json');arts=read('ARTIFACTS_PROVIDER_V01.json')
assert run['id']==38844940996 and run['run_attempt']==1 and run['workflow_id']==386254520
assert run['head_sha']=='aade35dbb049f64f6a66e0db8fd79fc269fb0ba5'
assert run['event']=='workflow_dispatch' and run['status']=='completed' and run['conclusion']=='success'
assert len(jobs['jobs'])==1
job=jobs['jobs'][0];assert job['id']==116793229607 and job['name']=='verify-small-menu-ideal'
assert job['run_id']==run['id'] and job['head_sha']==run['head_sha'] and job['run_attempt']==1
assert job['status']=='completed' and job['conclusion']=='success'
step=[s for s in job['steps'] if s['name']=='Replay exact three-query ideal proof'];assert len(step)==1 and step[0]['conclusion']=='success'
assert len(arts['artifacts'])==1;art=arts['artifacts'][0]
assert art['id']==12023071120 and art['name']=='small-menu-38844940996-1'
assert art['workflow_run']['id']==run['id'] and art['workflow_run']['head_sha']==run['head_sha']
archive=HERE/'ORIGINAL_HOSTED_ARTIFACT_V01.zip'
assert sha(archive)==art['digest'].split(':')[1]=='d079ee21ba414964dd7c18b3eb4088ed211ee1c67de07259af458fb5eecdfed3'
assert archive.stat().st_size==art['size_in_bytes']==3928
freeze=read('FREEZE.json');assert sha(HERE/'FREEZE.json')=='403e0b3a7becab752a7f02eaaebcec3396fcee0a07db9b0185154a0dc9d953c7'
expected=read('EXPECTED_NON_TIMING_RESULT_V01.json');assert sha(HERE/'EXPECTED_NON_TIMING_RESULT_V01.json')==freeze['expected_non_timing_result_sha256']
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None and set(z.namelist())=={'PROCESS_START.json','PROCESS_TERMINAL.json','RUN_RECEIPT.json','checker-output/VERIFICATION_RESULT_V01.json','stdout.txt','stderr.txt'}
    start=json.loads(z.read('PROCESS_START.json'));terminal=json.loads(z.read('PROCESS_TERMINAL.json'));receipt=json.loads(z.read('RUN_RECEIPT.json'))
    result_raw=z.read('checker-output/VERIFICATION_RESULT_V01.json');result=json.loads(result_raw)
assert start['pid']==terminal['pid']==2403 and start['retained_Popen'] and terminal['retained_Popen_wait']
assert terminal['actual_exit_code']==0 and receipt['actual_child_exit_code']==0
assert start['checker_sha256']==receipt['checker_sha256']==freeze['checker_sha256']
assert receipt['source_packet_sha256']==freeze['packet_sha256'] and receipt['wrapper_sha256']==freeze['wrapper_sha256']
assert receipt['freeze_sha256']==sha(HERE/'FREEZE.json') and receipt['actual_result_sha256']==hashlib.sha256(result_raw).hexdigest()
assert receipt['status']=='PASS_FRESH_LE3_ACTUAL_EXIT_AND_ALL_NON_TIMING_FIELDS_EQUAL'
assert receipt['runtime']=={'python':'3.12.3','system':'Linux'}
assert receipt['claimed_workflow_identity']=={'GITHUB_REPOSITORY':'SHiJiE1115/newproj','GITHUB_SHA':run['head_sha'],
    'GITHUB_RUN_ID':str(run['id']),'GITHUB_RUN_ATTEMPT':'1','GITHUB_JOB':'verify-small-menu-ideal'}
assert receipt['excluded_fields']==['wall_seconds'] and receipt['no_mathematical_fields_excluded']
non_timing={k:v for k,v in result.items() if k!='wall_seconds'};assert non_timing==expected
canonical=(json.dumps(non_timing,sort_keys=True,separators=(',',':'),ensure_ascii=False)+'\n').encode('utf-8')
assert hashlib.sha256(canonical).hexdigest()==receipt['canonical_non_timing_result_sha256']=='462f25ce1dfaaaad671e061a8e90fe34fb65b0077a9abd366599b2dcab2169c3'
assert result['mathematics']==receipt['mathematical_output']
math=result['mathematics'];assert math['checked_source_ideal_pairs']==17810 and math['applicable_total_priority_tree_witnesses']==10974 and math['full_cube_paths_checked']==87308
assert result['four_query_reexecuted'] is False and receipt['four_query_reexecuted'] is False
report={'status':'PASS_ORIGINAL_ARTIFACT_PROVIDER_IDENTITY_REAL_EXIT_AND_FULL_NON_TIMING_RESULT_COMPARISON',
    'run_id':run['id'],'run_attempt':1,'source_commit':run['head_sha'],'workflow_id':run['workflow_id'],'job_id':job['id'],
    'artifact_id':art['id'],'artifact_bytes':3928,'artifact_sha256':sha(archive),'checker_pid':2403,'checker_actual_exit_code':0,
    'retained_Popen_wait':True,'runtime':receipt['runtime'],'all_non_timing_fields_equal':True,'excluded_fields':['wall_seconds'],
    'no_mathematical_fields_excluded':True,'mathematics':math,'canonical_non_timing_result_sha256':hashlib.sha256(canonical).hexdigest(),
    'four_query_reexecuted':False,'new_model_API_calls':0,'new_independent_implementation':False,'human_review':False,
    'literature_priority_established':False,'historical_scientific_authentication':False,
    'trust_limit':'Conditional on authentic GitHub provider snapshots, executed source binding and the original service-digest-matched artifact. Local copies/hashes do not self-authenticate the platform.'}
with out.open('x',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({k:report[k] for k in ['status','run_id','checker_pid','checker_actual_exit_code','all_non_timing_fields_equal']}))
