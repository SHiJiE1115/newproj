"""Execute the unchanged frozen full proof and retain real child receipts."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path,PurePosixPath
import platform
import subprocess
import sys
import time
import zipfile

HERE=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('--execution-kind',choices=['local-control','github-actions'],required=True)
parser.add_argument('--expect-freeze-sha256',required=True)
parser.add_argument('--output-dir',required=True)
args=parser.parse_args()
OUT=Path(args.output_dir).resolve();assert not OUT.exists() and not OUT.is_relative_to(HERE)
assert sys.dont_write_bytecode and not sys.flags.optimize
def digest(raw):return hashlib.sha256(raw).hexdigest()
def pin(p):
    p=Path(p);b=p.read_bytes();return {'file':p.name,'bytes':len(b),'sha256':digest(b)}
def save(name,value):
    with (OUT/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def whole_child_cpu(p):
    if os.name=='nt':
        import ctypes
        u=ctypes.c_ulonglong;v=[u() for _ in range(4)];fn=ctypes.WinDLL('kernel32',use_last_error=True).GetProcessTimes
        fn.argtypes=[ctypes.c_void_p]+[ctypes.POINTER(u)]*4;fn.restype=ctypes.c_int
        assert fn(int(p._handle),*(ctypes.byref(x) for x in v))
        return {'seconds':(v[2].value+v[3].value)/10_000_000,'method':'GetProcessTimesonretainedchildhandle'}
    import resource
    r=resource.getrusage(resource.RUSAGE_CHILDREN)
    return {'seconds':r.ru_utime+r.ru_stime,'method':'getrusageRUSAGE_CHILDRENafteronlycheckerchildwait'}
OUT.mkdir(parents=True)
environment={'execution_kind':args.execution_kind,'python':platform.python_version(),'platform':platform.platform()}
if args.execution_kind=='github-actions':
    assert os.environ.get('GITHUB_ACTIONS')=='true' and os.environ.get('GITHUB_REPOSITORY')=='SHiJiE1115/newproj'
    assert os.environ.get('GITHUB_EVENT_NAME')=='workflow_dispatch'
    for key in ('GITHUB_SHA','GITHUB_RUN_ID','GITHUB_RUN_ATTEMPT','GITHUB_WORKFLOW_REF'):
        environment[key]=os.environ[key]
    assert len(environment['GITHUB_SHA'])==40 and environment['GITHUB_RUN_ATTEMPT']=='1'
save('ENVIRONMENT_V01.json',environment)
frozen=(HERE/'PUBLIC_SOURCE_FREEZE_V01.json').read_bytes()
assert digest(frozen)==args.expect_freeze_sha256
freeze=json.loads(frozen);assert freeze['fixed_old_science_only'] is True
for record in freeze['files']:
    p=(HERE/record['file']).resolve();assert p.is_relative_to(HERE) and p.is_file()
    raw=p.read_bytes();assert len(raw)==record['bytes'] and digest(raw)==record['sha256'],record['file']
archive=HERE/'PORTABLE_PROOF_V01.zip';raw=archive.read_bytes()
assert digest(raw)=='a264fe664e9408d2c99cd1850e559620136155bee838a5dfaee140ca0348df14'
packet=OUT/'extracted-packet';packet.mkdir();different=OUT/'different-cwd';different.mkdir()
with zipfile.ZipFile(archive) as z:
    names=z.namelist();assert len(names)==len(set(names))==52
    assert sum(i.file_size for i in z.infolist())<32*1024*1024 and z.testzip() is None
    for name in names:
        rel=PurePosixPath(name);assert not rel.is_absolute() and '..' not in rel.parts and '\\' not in name and ':' not in name
        destination=(packet/name).resolve();assert destination.is_relative_to(packet)
        content=z.read(name);assert content==(HERE/'packet'/name).read_bytes()
        destination.parent.mkdir(parents=True,exist_ok=True)
        with destination.open('xb') as f:f.write(content)
save('SOURCE_VALIDATION_V01.json',{'status':'PASS_FROZEN_SOURCE_AND_ALL52_ARCHIVE_MEMBERS',
    'freeze_sha256':digest(frozen),'packet':pin(archive),'member_count':52,'all_public_extracted_members_equal_archive':True,
    'new_model_API_calls':0,'expected_science_not_read_by_checker':True})
command=[sys.executable,'-I','-X','utf8','-B',str(packet/'verify.py'),'--out',str(OUT/'ACTUAL_RESULT_V01.json')]
start=time.perf_counter()
with (OUT/'checker.stdout.txt').open('xb') as stdout,(OUT/'checker.stderr.txt').open('xb') as stderr:
    child=subprocess.Popen(command,cwd=different,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr)
    save('PROCESS_START_V01.json',{'pid':child.pid,'started_utc':now(),'retained_Popen':True,
        'checker_sha256':pin(packet/'verify.py')['sha256'],'packet_zip_sha256':pin(archive)['sha256'],
        'expected_science_sha256':'9603869d50d3ef3605200dd4fff86476cd8ea35688d17d223f48d86ab6b9fc4f',
        'execution_kind':args.execution_kind,'actual_fixed_full_replay':True})
    timed=False
    try:child.wait(timeout=230)
    except subprocess.TimeoutExpired:timed=True;child.kill();child.wait()
    terminal={'pid':child.pid,'actual_exit_code':child.returncode,'timed_out':timed,
        'retained_Popen_wait':True,'completed_utc':now(),'wall_seconds':time.perf_counter()-start,
        'full_process_CPU':whole_child_cpu(child)}
    save('PROCESS_TERMINAL_V01.json',terminal)
print(json.dumps(terminal),flush=True)
assert child.returncode==0 and not timed,'Actualcheckerfailure;receiptsretained;noretry'
actual=json.loads((OUT/'ACTUAL_RESULT_V01.json').read_text(encoding='utf-8'))
reference=json.loads((HERE/'EXPECTED_SCIENCE_V01.json').read_text(encoding='utf-8'))
science=json.dumps(actual['science'],sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')
assert actual['status']=='PASS_FULL_PORTABLE_REPLAY' and digest(science)==actual['science_sha256']==reference['science_sha256']
assert actual['science']==reference['science'] and not actual['execution']['denied']
assert set(names)<=set(actual['execution']['packet_relative_files_read'])
save('HOSTED_COMPARISON_V01.json',{'status':'PASS_ENTIRE_SCIENCE_OBJECT_EQUALS_FROZEN_WINDOWS_CONTROL',
    'execution_kind':args.execution_kind,'science_sha256':digest(science),'all_scientific_fields_compared':True,
    'excluded_scientific_fields':[],'runtime_metadata_kept_separate':True,
    'actual_result':pin(OUT/'ACTUAL_RESULT_V01.json'),'terminal':pin(OUT/'PROCESS_TERMINAL_V01.json'),
    'freeze_sha256':digest(frozen),'same_checker_across_environments':True,'new_independent_implementation':False,
    'human_review_formal_kernel_historical_science_authentication_or_priority_clearance':False,
    'new_API_model_calls':0,'new_price_prior_or_LP_game_search':False})
print(json.dumps({'status':'PASS_FIXED_FULL_FOUR_ADDITIVE_REPLAY','science_sha256':digest(science),
    'pid':child.pid,'actual_exit_code':child.returncode,'execution_kind':args.execution_kind}),flush=True)
