"""Offline consistency checks for the retained ORIGINAL GitHub artifact.

Conditional on genuine provider metadata and the named executed source.
Copies/hashes alone do not authenticate GitHub or an original scientific study.
This verifies receipts, not a new execution of the mathematical checker.
"""
import hashlib
import io
import json
from pathlib import Path
import zipfile
H=Path(__file__).resolve().parent
def load(name):return json.loads((H/name).read_text(encoding='utf-8'))
manifest=load('CONTENT_MANIFEST_V01.json')
for r in manifest['files']:
    p=(H/r['file']).resolve();assert p.is_relative_to(H) and p.is_file()
    raw=p.read_bytes();assert len(raw)==r['bytes'] and hashlib.sha256(raw).hexdigest()==r['sha256']
run=load('RUN_METADATA_V01.json');jobs=load('JOBS_METADATA_V01.json');arts=load('ARTIFACTS_METADATA_V01.json');binding=load('EXECUTED_SOURCE_V01.json')
assert run['id']==binding['run_id']==39003766001 and run['run_attempt']==1
assert run['head_sha']==binding['executed_source_commit']=='837498553f02739d60d3c53f79b8141ac4f5e105'
assert run['status']=='completed' and run['conclusion']=='success' and run['event']=='workflow_dispatch'
assert run['workflow_id']==binding['workflow_id'] and jobs['total_count']==len(jobs['jobs'])==1
assert jobs['jobs'][0]['conclusion']=='success'
assert any(s['name']=='Replay all original source families and exact price certificates' and s['conclusion']=='success' for s in jobs['jobs'][0]['steps'])
assert arts['total_count']==len(arts['artifacts'])==1;artifact=arts['artifacts'][0]
assert artifact['name']=='four-additive-39003766001-1' and artifact['workflow_run']['id']==run['id'] and artifact['workflow_run']['head_sha']==run['head_sha']
raw=(H/'ORIGINAL_HOSTED_ARTIFACT_V01.zip').read_bytes()
assert len(raw)==artifact['size_in_bytes']==5710
assert hashlib.sha256(raw).hexdigest()==artifact['digest'][7:]==binding['original_archive_sha256']=='83ec1668ffaef243acced0dfe4407088d42be07095f7d9b181a4998058531700'
with zipfile.ZipFile(io.BytesIO(raw)) as z:
    assert len(z.namelist())==len(set(z.namelist()))==8 and z.testzip() is None
    assert all(Path(n).name==n for n in z.namelist())
    def member(n):return json.loads(z.read(n))
    actual=member('ACTUAL_RESULT_V01.json');start=member('PROCESS_START_V01.json');terminal=member('PROCESS_TERMINAL_V01.json')
    env=member('ENVIRONMENT_V01.json');source=member('SOURCE_VALIDATION_V01.json');comparison=member('HOSTED_COMPARISON_V01.json')
    assert start['pid']==terminal['pid']==2401 and start['retained_Popen'] and terminal['retained_Popen_wait']
    assert terminal['actual_exit_code']==0 and terminal['timed_out'] is False
    assert terminal['full_process_CPU']['seconds']>0
    assert env['GITHUB_SHA']==run['head_sha'] and env['GITHUB_RUN_ID']==str(run['id']) and env['GITHUB_RUN_ATTEMPT']=='1'
    assert env['execution_kind']=='github-actions' and actual['status']=='PASS_FULL_PORTABLE_REPLAY'
    assert source['freeze_sha256']==binding['freeze_sha256'] and source['member_count']==52
    reference=load('EXPECTED_SCIENCE_V01.json');assert actual['science']==reference['science']
    science=json.dumps(actual['science'],sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')
    assert hashlib.sha256(science).hexdigest()==actual['science_sha256']==reference['science_sha256']==binding['science_sha256']
    assert not actual['execution']['denied'] and comparison['all_scientific_fields_compared'] is True and comparison['excluded_scientific_fields']==[]
    assert comparison['actual_result']['sha256']==hashlib.sha256(z.read('ACTUAL_RESULT_V01.json')).hexdigest()
    assert comparison['terminal']['sha256']==hashlib.sha256(z.read('PROCESS_TERMINAL_V01.json')).hexdigest()
    assert z.read('checker.stderr.txt')==b''
print(json.dumps({'status':'PASS_CONDITIONAL_OFFLINE_PROVIDER_RECEIPT_AND_FULL_SCIENCE_CONSISTENCY',
    'run_id':run['id'],'source_commit':run['head_sha'],'actual_checker_pid':terminal['pid'],'actual_exit_code':0,
    'science_sha256':actual['science_sha256'],'excluded_scientific_fields':[],
    'new_science_execution':False,'platform_authentication_from_copies_alone':False,'human_review':False}))
