"""Replay the fixed-source support-two proof with byte-exact original programs."""
import argparse
import ctypes
import datetime
from fractions import Fraction as Q
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import shutil
import subprocess
import sys
import time

if not __debug__ or sys.flags.optimize or not sys.flags.dont_write_bytecode:
    raise RuntimeError('Run with -B and assertions enabled; do not use -O.')
ROOT=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--work',required=True,help='Fresh absolute staging directory outside the packet.')
parser.add_argument('--out',required=True,help='Fresh absolute result path outside both packet and staging directory.')
args=parser.parse_args()
WORK=Path(args.work);OUT=Path(args.out)
assert WORK.is_absolute() and OUT.is_absolute() and WORK.parent.is_dir() and OUT.parent.is_dir()
WORK=WORK.resolve();OUT=OUT.resolve()
assert not WORK.exists() and not OUT.exists()
assert not WORK.is_relative_to(ROOT) and not ROOT.is_relative_to(WORK)
assert not OUT.is_relative_to(ROOT) and not OUT.is_relative_to(WORK)
RUNTIME=Path(sys.base_prefix).resolve()
reads=set();writes=set();runtime_reads=set();denied=[];active_command=None;spawns=[]


def audit(event,values):
    if event in ('socket.connect','socket.getaddrinfo','socket.__new__','os.system'):
        raise RuntimeError('Network and shell use are outside this replay.')
    if event=='subprocess.Popen':
        actual=values[1]
        if active_command is None or actual not in (active_command,subprocess.list2cmdline(active_command)) or Path(values[2]).resolve()!=WORK:
            raise RuntimeError('Unexpected child command.')
        spawns.append(list(active_command));return
    if event!='open' or isinstance(values[0],int):return
    path=Path(os.fsdecode(values[0])).resolve()
    mode,flags=values[1:3]
    writing=(isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)))
    if writing:
        if path!=OUT and not path.is_relative_to(WORK):
            denied.append({'operation':'write','path':str(path)});raise PermissionError('Unexpected replay write.')
        writes.add('$RESULT' if path==OUT else '$WORK/'+path.relative_to(WORK).as_posix())
    elif path.is_relative_to(ROOT):reads.add('$PACKET/'+path.relative_to(ROOT).as_posix())
    elif path.is_relative_to(WORK):reads.add('$WORK/'+path.relative_to(WORK).as_posix())
    elif path.is_relative_to(RUNTIME):runtime_reads.add(path.relative_to(RUNTIME).as_posix())
    else:
        denied.append({'operation':'read','path':str(path)});raise PermissionError('Unexpected replay read.')


sys.addaudithook(audit)


def load(p):return json.loads(p.read_text(encoding='utf-8'))


def pin(p):
    raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def save(p,value):
    with p.open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')


manifest=load(ROOT/'MANIFEST.json')
expected_names={'MANIFEST.json'}|{r['name'] for r in manifest['files']}
assert {p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file()}==expected_names
for p in ROOT.rglob('*'):assert not p.is_symlink()
before={}
for row in manifest['files']:
    p=ROOT/row['name']
    assert p.resolve().is_relative_to(ROOT) and '\\' not in row['name'] and '..' not in Path(row['name']).parts
    current=pin(p);assert current['bytes']==row['bytes'] and current['sha256']==row['sha256']
    before[row['name']]=current['sha256']
manifest_pin=pin(ROOT/'MANIFEST.json')
ns=runpy.run_path(str(ROOT/'science.py'))
expected=load(ROOT/'EXPECTED_SCIENCE.json')
origins=load(ROOT/'SOURCE_ORIGINS.json')
assert manifest['scope']=='source1209_exact_pair_support2_original_four_cores_and_fixed_source_completeness'
WORK.mkdir()
staged=[]
for source,target in ns['STAGED'].items():
    dest=WORK/target;dest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(ROOT/source,dest)
    assert (ROOT/source).read_bytes()==dest.read_bytes()
    staged.append({'packet_name':source,'work_name':target,**{k:v for k,v in pin(dest).items() if k!='path'}})
assert all(not (WORK/c['output']).exists() for c in ns['COMPONENTS'])
save(WORK/'INPUT_STAGE_MANIFEST.json',{'files':staged,'original_outputs_prefilled':False})


def cpu(process):
    if os.name!='nt':return {'seconds':None,'method':'Retained Popen wait; per-process CPU unavailable here'}
    count=ctypes.c_ulonglong
    fn=ctypes.WinDLL('kernel32',use_last_error=True).GetProcessTimes
    fn.argtypes=[ctypes.c_void_p]+[ctypes.POINTER(count)]*4;fn.restype=ctypes.c_int
    values=[count() for _ in range(4)]
    assert fn(int(process._handle),*(ctypes.byref(v) for v in values))
    return {'seconds':(values[2].value+values[3].value)/10000000,'method':'GetProcessTimes on retained child handle'}


stages=[];raw_results={};audits=[]
for component in ns['COMPONENTS']:
    name=component['id']
    command=[sys.executable,'-I','-X','utf8','-B',str(ROOT/'child_audit.py'),'--work',str(WORK),'--component',name]
    active_command=command
    started=time.perf_counter()
    with (WORK/(name+'.stdout.txt')).open('xb') as stdout,(WORK/(name+'.stderr.txt')).open('xb') as stderr:
        child=subprocess.Popen(command,cwd=WORK,stdout=stdout,stderr=stderr,stdin=subprocess.PIPE,
            env={**os.environ,'TEMP':str(WORK),'TMP':str(WORK),'TMPDIR':str(WORK)},creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        child.stdin.close()
        save(WORK/(name+'.PROCESS_START.json'),{'pid':child.pid,'command':command,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
             'compiled_original_script_sha256':pin(WORK/component['script'])['sha256'],'retained_Popen':True})
        timeout=False
        try:child.wait(timeout=45)
        except subprocess.TimeoutExpired:timeout=True;child.kill();child.wait()
        terminal={'pid':child.pid,'actual_exit_code':child.returncode,'timed_out':timeout,'retained_Popen_wait':True,
                  'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'wall_seconds':time.perf_counter()-started,'whole_process_CPU':cpu(child)}
        save(WORK/(name+'.PROCESS_TERMINAL.json'),terminal)
    active_command=None
    stages.append({'component':name,**terminal,'start':pin(WORK/(name+'.PROCESS_START.json')),'terminal':pin(WORK/(name+'.PROCESS_TERMINAL.json'))})
    assert child.returncode==0 and not timeout,(name,child.returncode)
    assert (WORK/(name+'.stderr.txt')).stat().st_size==0
    check=load(WORK/(name+'.READ_AUDIT.json'))
    assert check['status']=='PASS_EXACT_COMPONENT_READ_SCOPE' and check['denied']==[]
    assert check['script_sha256']==pin(WORK/component['script'])['sha256']
    audits.append(check)
    raw_results[name]=load(WORK/component['output'])
assert len(spawns)==len(stages)==5
for row in staged:
    p=pin(WORK/row['work_name'])
    assert p['bytes']==row['bytes'] and p['sha256']==row['sha256']
paths={c['id']:WORK/c['output'] for c in ns['COMPONENTS']}
science=ns['normalize_all']({k:raw_results[k] for k in ('single_pair','full_class','separate_dp','derived')},
    WORK/'iteration449/ORIGINAL_SOURCE1209_FAMILIES_V01.json',WORK/'iteration453/SYMBOLIC_PROOF_SCOPE_V02.json',
    WORK/'iteration453/SYMBOLIC_SINGLE_PAIR_PROOF_V02.json.gz',WORK/'iteration453/FROZEN_TWO_PAIR_CANDIDATE_V01.json',
    WORK/'iteration453/PAIR_RESOURCE_MINIMUM_THEOREM_AND_PROOF_V01.txt',paths)
assert ns['canonical_bytes'](science)==ns['canonical_bytes'](expected)
assert raw_results['source_completeness']['A_count']==40 and raw_results['source_completeness']['P_count']==32
assert raw_results['source_completeness']['all_reconstructed_minimal_profiles_and_reduced_original_profile_cells_match']
binding=load(ROOT/'CLAIM_BINDING_V23.json')
excerpt=(ROOT/'data/pair_resource_support_v23.tex').read_text(encoding='utf-8')
statements=[]
for m in re.finditer(r'\\begin\{(theorem|corollary)\}.*?\\end\{\1\}',excerpt,re.S):
    label=re.search(r'\\label\{([^}]+)\}',m.group(0)).group(1)
    statements.append({'label':label,'body_sha256':hashlib.sha256(m.group(0).encode()).hexdigest()})
assert len(statements)==2
for actual,expected_row in zip(statements,binding['statements']):
    assert all(actual[k]==expected_row[k] for k in ('label','body_sha256'))
assert [r['number'] for r in binding['statements']]==['28','29']
arrays=re.findall(r'\\begin\{array\}\{r+\}(.*?)\\end\{array\}',excerpt,re.S)
assert len(arrays)==2
for kind,scale,body in zip(('A','P'),(29,8),arrays):
    assert list(map(int,re.findall(r'\d+',body)))==[int(scale*Q(r['slack'])) for r in science['full_class']['results'][kind]['dual_lower_on_all_columns']]
for literal in ('(c_0,c_1,c_2,c_3)=(4,3,2,3)','w_{12}=w_{23}=2',r'\frac{286}{29}',r'\frac{79}{8}',r'\frac{3}{232}','1/1856',r'\frac{3}{464}'):
    assert literal in excerpt,literal
assert science['derived']['claim_scope']['minimum_positive_pair_support']==2
assert science['derived']['sparse_coverage_parameter_box']['coordinate_radius']=='1/1856'
assert science['derived']['sparse_coverage_parameter_box']['gap_lower_bound']=='3/464'
for row in manifest['files']:assert pin(ROOT/row['name'])['sha256']==before[row['name']]
assert pin(ROOT/'MANIFEST.json')==manifest_pin
assert denied==[]
raw_byte_flags={name:pin(paths[name])['sha256']==origins['original_result_hashes'][name]['sha256'] for name in science}
result={'schema':1,'status':'PASS_ACTUAL_PORTABLE_FIXED_SOURCE_COMPLETENESS_AND_ALL_ORIGINAL_PAIR_RESOURCE_SCIENCE',
        'science':science,'whole_science_sha256':ns['science_sha'](science),
        'science_top_level_key_counts':{k:len(v) for k,v in science.items()},'whole_nested_value_counts':ns['leaf_counts'](science),
        'fixed_source_completeness':raw_results['source_completeness'],
        'current_V23_statement_binding':binding,'all72_current_TeX_slacks_match_computed_values':True,
        'transport':{'python_version':sys.version.split()[0],'implementation':sys.implementation.name,'os_name':os.name,
                     'work_directory':str(WORK),'staged_inputs':staged,'staged_inputs_unchanged_after_all_checks':True,
                     'packet_manifest':manifest_pin,'packet_all_file_hashes_unchanged':True,
                     'actual_five_child_processes':stages,'exact_child_read_audits':audits,
                     'original_four_core_scripts_byte_exact':True,'entire_original_result_objects_compared':True,
                     'mathematical_field_exclusions':[], 'provenance_normalization':'See README.txt and SOURCE_ORIGINS.json; every raw referenced file pin is validated before normalization',
                     'raw_original_result_byte_equal_flags':raw_byte_flags,'parent_read_files':sorted(reads),
                     'runtime_read_files':sorted(runtime_reads),'denied':denied,
                     'monitor_is_not_OS_sandbox_or_external_human_review':True},
        'replay_of_same_four_implementations_not_a_new_independent_implementation':True,
        'new_fee_or_prior_candidates_model_calls_or_human_labels_or_hosted_execution':0,
        'query_menu_global_resource_minimum_or_application_advantage_claimed':False,
        'bibliographic_priority':'OPEN','whole_project_complete':False}
with OUT.open('x',encoding='utf-8') as f:
    result['transport']['parent_write_files']=sorted(writes)
    json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'status':result['status'],'science_sha256':result['whole_science_sha256'],
    'source_counts':[40,32],'single_pair_roots':144,'A':science['derived']['exact_RA'],'P':science['derived']['exact_RP'],
    'gap':science['derived']['exact_gap'],'actual_children':len(stages),'mathematical_fields_excluded':0}))
