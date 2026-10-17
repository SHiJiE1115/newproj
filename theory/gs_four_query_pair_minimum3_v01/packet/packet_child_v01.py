"""Execute byte-exact legacy mathematical source with declared pin-label binding.

Only the global provenance pin function is rebound after its definition/import.
For byte-exact files it returns origin PATH LABEL plus actual bytes/SHA.
For the ONE declared inherited metadata derivative it checks actual derived
bytes/SHA, then returns the inherited origin commitment; both are audited. All
file reads remain at packet/work paths; no origin path is opened or resolved.
This Python audit contract is not an operating-system sandbox.
"""
from pathlib import Path
import hashlib
import json
import os
import sys

packet,work,target,bindingfile,auditfile,writes,anchor_key,*tail=sys.argv[1:]
packet,work,target,bindingfile,auditfile=map(lambda x:Path(x).resolve(),[packet,work,target,bindingfile,auditfile])
assert sys.dont_write_bytecode and not sys.flags.optimize and sys.flags.isolated
allowed_writes={str(Path(x).resolve()).casefold() for x in json.loads(writes)}|{str(auditfile).casefold()}
write_parents={str(Path(x).parent.resolve()).casefold() for x in allowed_writes}
roots=[packet,work,Path(sys.base_prefix).resolve()]
reads=set();written=set();denied=[];mkdir_existing=[];pin_calls=[]
def audit(event,args):
    if event.startswith('socket.') or event in ('subprocess.Popen','os.system','os.posix_spawn','os.spawn','os.fork'):
        denied.append(event);raise PermissionError(event)
    if event in ('os.remove','os.rmdir','os.rename','os.link','os.symlink'):
        denied.append(event);raise PermissionError(event)
    if event=='os.mkdir':
        p=Path(os.fsdecode(args[0])).resolve()
        if str(p).casefold() in write_parents and p.is_dir():mkdir_existing.append(str(p));return
        denied.append(str(p));raise PermissionError('No new child directories')
    if event!='open' or isinstance(args[0],int):return
    p=Path(os.fsdecode(args[0])).resolve();flags=args[2]
    if flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):
        if str(p).casefold() not in allowed_writes:denied.append(str(p));raise PermissionError(str(p))
        written.add(str(p))
    else:
        if not any(p==r or p.is_relative_to(r) for r in roots):denied.append(str(p));raise PermissionError(str(p))
        reads.add(str(p))
sys.addaudithook(audit)
bindings=json.loads(bindingfile.read_text(encoding='utf-8'))
mapping={str(Path(r['actual_path']).resolve()).casefold():r for r in bindings['rows']}
assert len(mapping)==len(bindings['rows'])
raw=target.read_bytes();source=raw.decode('utf-8')
anchors={'none':None,'residual':'\nstatic=json.loads','balanced':'\nscope=read(scopefile)',
    'upper':'\nscope=read(SCOPE)','bellman_producer':'\nsource=read(', 'bellman_reader':'\np=read(PROOF)'}
anchor=anchors[anchor_key]
if anchor:
    assert source.count(anchor)==1;cut=source.index(anchor)
else:cut=0
prefix,body=source[:cut],source[cut:]
assert prefix.encode('utf-8')+body.encode('utf-8')==raw
def origin_pin(p):
    p=Path(p).resolve();key=str(p).casefold()
    assert key in mapping,('Unbound metadata pin',str(p))
    row=mapping[key];b=p.read_bytes()
    observed={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
    bridge=row.get('origin_metadata_derivative')
    if bridge:
        assert row['role']=='iteration441/ACCEPTANCE_V01.json'
        assert observed=={'bytes':bridge['derived_bytes'],'sha256':bridge['derived_sha256']}
        assert bridge['only_one_path_string_literal_changed_all_other_raw_bytes_exact'] is True
        v={'path':row['origin_path'],'bytes':bridge['origin_bytes'],'sha256':bridge['origin_sha256']}
    else:v={'path':row['origin_path'],**observed}
    pin_calls.append({'actual_path':str(p),'role':row['role'],'origin_path_label':row['origin_path'],
        'actual_bytes':observed['bytes'],'actual_sha256':observed['sha256'],
        'returned_reference':v,'inherited_origin_commitment_bridge_used':bool(bridge)})
    return v
sys.argv=[str(target),*tail]
ns={'__name__':'__main__','__file__':str(target),'__package__':None}
# This one declared audit descriptor is opened before narrower legacy hooks.
# It is used only for the wrapper's actual physical I/O report after execution.
handle=auditfile.open('x',encoding='utf-8',newline='\n')
ok=False;error=None
try:
    if prefix:
        exec(compile(prefix,str(target),'exec'),ns,ns)
        assert 'pin' in ns and callable(ns['pin'])
        ns['pin']=origin_pin
    exec(compile('\n'*prefix.count('\n')+body,str(target),'exec'),ns,ns)
    ok=True
except BaseException as exc:
    error=type(exc).__name__;raise
finally:
    report={'schema':1,'normal_return':ok,'error_type':error,'actual_mathematical_target':str(target),
        'actual_source_sha256':hashlib.sha256(raw).hexdigest(),'anchor_key':anchor_key,
        'prefix_bytes':len(prefix.encode('utf-8')),'prefix_sha256':hashlib.sha256(prefix.encode('utf-8')).hexdigest(),
        'body_bytes':len(body.encode('utf-8')),'body_sha256':hashlib.sha256(body.encode('utf-8')).hexdigest(),
        'exact_source_prefix_body_reconcatenation':True,'only_global_provenance_pin_rebound':bool(prefix),
        'origin_labels_not_filesystem_read_authority':True,'origin_pin_calls':pin_calls,
        'read_files':sorted(reads),'written_files':sorted(written),'denied':denied,
        'idempotent_existing_output_parent_mkdir_attempts':mkdir_existing,
        'boundary':'Pythonauditafterbootstrap;predeclaredwrapperauditdescriptor;notOSisolation'}
    json.dump(report,handle,indent=2);handle.write('\n');handle.close()
