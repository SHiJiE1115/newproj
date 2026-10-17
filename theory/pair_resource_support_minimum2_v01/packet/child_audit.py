"""Execute one byte-exact original checker under a scoped Python file-open audit."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import runpy
import sys

if not __debug__ or sys.flags.optimize or not sys.flags.dont_write_bytecode:
    raise RuntimeError('Use assertions enabled and -B.')
ROOT=Path(__file__).resolve().parent
ns=runpy.run_path(str(ROOT/'science.py'))
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--work',required=True)
parser.add_argument('--component',required=True,choices=[c['id'] for c in ns['COMPONENTS']])
args=parser.parse_args()
WORK=Path(args.work).resolve()
component=next(c for c in ns['COMPONENTS'] if c['id']==args.component)
script=WORK/component['script'];target=WORK/component['output']
allowed={script.resolve(),*[(WORK/p).resolve() for p in component['inputs']]}
AUDIT=WORK/(component['id']+'.READ_AUDIT.json')
RUNTIME=Path(sys.base_prefix).resolve()
script_sha=hashlib.sha256(script.read_bytes()).hexdigest()
reads=set();runtime_reads=set();writes=set();denied=[]


def audit(event,values):
    if event in ('socket.connect','socket.getaddrinfo','socket.__new__','subprocess.Popen','os.system'):
        raise RuntimeError('Network and nested process creation are outside this component.')
    if event!='open' or isinstance(values[0],int):return
    path=Path(os.fsdecode(values[0])).resolve()
    mode,flags=values[1:3]
    writing=(isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)))
    if writing:
        if path not in {target.resolve(),AUDIT.resolve()}:
            denied.append({'operation':'write','path':str(path)});raise PermissionError('Unexpected component write.')
        writes.add(path.relative_to(WORK).as_posix())
    elif path in allowed:
        reads.add(path.relative_to(WORK).as_posix())
    elif path.is_relative_to(RUNTIME):
        runtime_reads.add(path.relative_to(RUNTIME).as_posix())
    else:
        denied.append({'operation':'read','path':str(path)});raise PermissionError('Unexpected component read.')


sys.addaudithook(audit)
status='FAIL';error=None
try:
    runpy.run_path(str(script),run_name='__main__')
    expected={p.relative_to(WORK).as_posix() for p in allowed}
    assert reads==expected,(reads,expected)
    assert target.is_file()
    status='PASS_EXACT_COMPONENT_READ_SCOPE'
except BaseException as exc:
    error=type(exc).__name__
    raise
finally:
    receipt={'schema':1,'status':status,'component':component['id'],'script_sha256':script_sha,
             'exact_work_read_files':sorted(reads),'allowed_work_read_files':sorted(p.relative_to(WORK).as_posix() for p in allowed),
             'runtime_read_files':sorted(runtime_reads),'work_writes_before_audit_receipt':sorted(writes),
             'denied':denied,'error_type':error,'monitor_scope':'Original scientific checker execution and later imports; bootstrap/config imports occur before monitor',
             'not_an_OS_sandbox_or_external_review':True}
    with AUDIT.open('x',encoding='utf-8') as f:json.dump(receipt,f,indent=2);f.write('\n')
