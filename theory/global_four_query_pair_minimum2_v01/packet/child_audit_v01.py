"""Python audit contract, not an OS sandbox. Installs before target import."""
import json
import os
from pathlib import Path
import runpy
import sys

packet, work, target, auditfile, writes, *args = sys.argv[1:]
packet, work, target, auditfile = map(lambda p: Path(p).resolve(), (packet, work, target, auditfile))
allowed_writes = {str(Path(p).resolve()).casefold() for p in json.loads(writes)} | {str(auditfile).casefold()}
roots = [packet, work, Path(sys.base_prefix).resolve()]
reads = set()
written = set()
denied = []


def under(p, root):
    return p == root or p.is_relative_to(root)


def audit(event, vals):
    if event.startswith('socket.') or event in ('subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.spawn', 'os.fork'):
        denied.append(event)
        raise PermissionError('Scientific child has no network or subprocess authority: ' + event)
    if event in ('os.remove', 'os.rmdir', 'os.rename', 'os.link', 'os.symlink', 'os.mkdir'):
        denied.append(event)
        raise PermissionError('Scientific child cannot mutate filesystem structure: ' + event)
    if event != 'open' or isinstance(vals[0], int): return
    p = Path(os.fsdecode(vals[0])).resolve()
    mode, flags = vals[1:3]
    write = bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
    if write:
        if str(p).casefold() not in allowed_writes:
            denied.append(str(p)); raise PermissionError('Undeclared scientific output: ' + str(p))
        written.add(str(p))
    else:
        if not any(under(p, r) for r in roots):
            denied.append(str(p)); raise PermissionError('Read outside packet/work/runtime: ' + str(p))
        reads.add(str(p))


sys.addaudithook(audit)
sys.argv = [str(target), *args]
ok = False
try:
    runpy.run_path(str(target), run_name='__main__')
    ok = True
finally:
    with auditfile.open('x', encoding='utf-8') as f:
        json.dump({'schema': 1, 'target': str(target), 'normal_return': ok,
                   'read_files': sorted(reads), 'written_files': sorted(written),
                   'denied': denied, 'no_network_or_nested_child': not denied,
                   'boundary': 'Python audit events after bootstrap, not OS isolation'}, f, indent=2)
        f.write('\n')
