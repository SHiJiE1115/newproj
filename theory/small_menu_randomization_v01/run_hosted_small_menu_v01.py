"""Exact <=3 ideal-proof replay; the four-query leg is inherited, never executed here."""
from pathlib import Path
import argparse,datetime,hashlib,json,os,platform,re,subprocess,sys,time,zipfile
HERE=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--expect-freeze-sha256',required=True)
p.add_argument('--output-dir',required=True);p.add_argument('--execution-kind',choices=['local','github-actions'],required=True)
a=p.parse_args();out=Path(a.output_dir).resolve();assert not out.exists();out.mkdir(parents=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,x):
    with (out/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
receipt={'schema':1,'status':'PRECHECK_PENDING','at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'execution_kind':a.execution_kind,'runtime':{'python':platform.python_version(),'system':platform.system()},
    'new_model_API_calls':0,'human_review':False,'four_query_reexecuted':False}
started=time.monotonic()
try:
    freeze_path=HERE/'FREEZE.json';assert sha(freeze_path)==a.expect_freeze_sha256
    frozen=json.loads(freeze_path.read_bytes());assert sha(Path(__file__).resolve())==frozen['wrapper_sha256']
    packet=HERE/'small_menu_le3_v01.zip';assert sha(packet)==frozen['packet_sha256']
    expected=HERE/'EXPECTED_NON_TIMING_RESULT_V01.json';assert sha(expected)==frozen['expected_non_timing_result_sha256']
    if a.execution_kind=='github-actions':
        assert os.environ.get('GITHUB_ACTIONS')=='true' and os.environ.get('GITHUB_REPOSITORY')=='SHiJiE1115/newproj'
        assert re.fullmatch('[0-9a-f]{40}',os.environ.get('GITHUB_SHA',''))
        assert os.environ.get('GITHUB_RUN_ID','').isdigit() and os.environ.get('GITHUB_RUN_ATTEMPT','').isdigit()
        receipt['claimed_workflow_identity']={k:os.environ[k] for k in ['GITHUB_REPOSITORY','GITHUB_SHA','GITHUB_RUN_ID','GITHUB_RUN_ATTEMPT','GITHUB_JOB']}
    work=out/'extracted';work.mkdir()
    with zipfile.ZipFile(packet) as z:
        names=z.namelist();assert len(names)==len(set(names))==10 and z.testzip() is None
        assert all('/' not in n and '\\' not in n for n in names)
        assert sum(i.file_size for i in z.infolist())<8388608
        for n in names:
            with (work/n).open('xb') as f:f.write(z.read(n))
    manifest=work/'REPLAY_MANIFEST_V01.json';assert sha(manifest)==frozen['manifest_sha256']
    m=json.loads(manifest.read_bytes());assert set(names)=={r['name'] for r in m['files']}|{'REPLAY_MANIFEST_V01.json'}
    for r in m['files']:
        assert (work/r['name']).stat().st_size==r['bytes'] and sha(work/r['name'])==r['sha256']
    checker=work/'verify_small_menu_portable_v01.py';assert sha(checker)==frozen['checker_sha256']
    result_dir=out/'checker-output'
    argv=[sys.executable,'-I','-X','utf8','-B',str(checker),'--expected-manifest-sha256',frozen['manifest_sha256'],'--out',str(result_dir)]
    with (out/'stdout.txt').open('xb') as stdout,(out/'stderr.txt').open('xb') as stderr:
        child=subprocess.Popen(argv,cwd=work,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,
            creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        save('PROCESS_START.json',{'pid':child.pid,'argv':argv,'retained_Popen':True,'checker_sha256':sha(checker)})
        code=child.wait()
    save('PROCESS_TERMINAL.json',{'pid':child.pid,'actual_exit_code':code,'retained_Popen_wait':True})
    assert type(code) is int and code==0
    actual=result_dir/'VERIFICATION_RESULT_V01.json';result=json.loads(actual.read_bytes())
    assert type(result['wall_seconds']) in [int,float] and result['wall_seconds']>=0
    scientific={k:v for k,v in result.items() if k!='wall_seconds'}
    assert scientific==json.loads(expected.read_bytes())
    canonical=(json.dumps(scientific,sort_keys=True,separators=(',',':'),ensure_ascii=False)+'\n').encode('utf-8')
    receipt.update(status='PASS_FRESH_LE3_ACTUAL_EXIT_AND_ALL_NON_TIMING_FIELDS_EQUAL',actual_child_exit_code=code,
        all_non_timing_fields_equal_expected=True,excluded_fields=['wall_seconds'],no_mathematical_fields_excluded=True,
        mathematical_output=result['mathematics'],canonical_non_timing_result_sha256=hashlib.sha256(canonical).hexdigest(),
        actual_result_sha256=sha(actual),source_packet_sha256=sha(packet),checker_sha256=sha(checker),
        wrapper_sha256=sha(Path(__file__).resolve()),freeze_sha256=sha(freeze_path),
        same_checker_across_systems_not_a_new_independent_implementation=True,
        trust_limit='Claimed GitHub environment identity must be compared with separate provider metadata; this receipt is not self-authenticating.')
except BaseException as exc:
    receipt.update(status='FAILED_REPLAY_PRESERVED',error=type(exc).__name__+': '+str(exc))
receipt['wall_seconds']=time.monotonic()-started
save('RUN_RECEIPT.json',receipt)
print(json.dumps({k:receipt.get(k) for k in ['status','runtime','actual_child_exit_code','four_query_reexecuted']}),flush=True)
raise SystemExit(0 if receipt['status']=='PASS_FRESH_LE3_ACTUAL_EXIT_AND_ALL_NON_TIMING_FIELDS_EQUAL' else 1)
