"""Build this frozen authored-source release with explicit external dependencies."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time

HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--dependencies', required=True, help='Flat directory containing the six pinned external files')
parser.add_argument('--out', required=True, help='New absolute build directory outside this source directory')
parser.add_argument('--engine', default='pdflatex')
parser.add_argument('--miktex', action='store_true')
args = parser.parse_args()
out = Path(args.out).resolve()
deps = Path(args.dependencies).resolve()
assert Path(args.out).is_absolute() and not out.exists() and not out.is_relative_to(HERE)
assert deps.is_dir() and not deps.is_relative_to(out)


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


sources = json.loads((HERE / 'AUTHOR_SOURCE_MANIFEST.json').read_text(encoding='utf-8'))
external = json.loads((HERE / 'EXTERNAL_DEPENDENCIES.json').read_text(encoding='utf-8'))
for row in sources['files']:
    assert Path(row['name']).name == row['name']
    p = HERE / row['name']
    assert p.stat().st_size == row['bytes'] and sha(p) == row['sha256']
for row in external['files']:
    assert Path(row['name']).name == row['name']
    p = deps / row['name']
    assert p.is_file() and p.stat().st_size == row['bytes'] and sha(p) == row['sha256'], row['name']
engine = Path(shutil.which(args.engine) or args.engine).resolve()
bibtex = engine.with_name('bibtex.exe' if os.name == 'nt' else 'bibtex')
assert engine.is_file() and bibtex.is_file()
out.mkdir()
for row in sources['files']:
    shutil.copyfile(HERE / row['name'], out / row['name'])
for row in external['files']:
    shutil.copyfile(deps / row['name'], out / row['name'])


def save(name, value):
    with (out / name).open('x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')


stages = []


def run(name, command):
    command = list(map(str, command))
    begun = time.perf_counter()
    with (out / (name + '.stdout.txt')).open('xb') as stdout, (out / (name + '.stderr.txt')).open('xb') as stderr:
        child = subprocess.Popen(command, cwd=out, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
            env={**os.environ, 'TEMP': str(out), 'TMP': str(out), 'TMPDIR': str(out)},
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        save(name + '_START.json', {'pid': child.pid, 'command': command, 'retained_Popen': True,
             'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()})
        timed = False
        try:
            child.wait(timeout=90)
        except subprocess.TimeoutExpired:
            timed = True
            child.kill()
            child.wait()
        row = {'stage': name, 'pid': child.pid, 'actual_exit_code': child.returncode,
               'timed_out': timed, 'retained_Popen_wait': True, 'wall_seconds': time.perf_counter() - begun}
    save(name + '_TERMINAL.json', row)
    stages.append(row)
    print(json.dumps(row), flush=True)
    assert child.returncode == 0 and not timed


flags = ['--disable-installer', '--disable-write18'] if args.miktex else ['-no-shell-escape']
latex = [engine, *flags, '-interaction=nonstopmode', '-halt-on-error', 'paper.tex']
run('compile_1', latex)
run('bibtex', [bibtex, *(['--disable-installer'] if args.miktex else []), 'paper'])
raw = (out / 'paper.bbl').read_bytes()
clean = re.sub(rb',\s*\\blocation\{\?\?\?\}', b'', raw)
assert raw.count(b'\\bibitem') == clean.count(b'\\bibitem') == 27 and b'???' not in clean
(out / 'paper.bbl').write_bytes(clean)
run('compile_2', latex)
run('compile_3', latex)
for extra in (4, 5):
    log = (out / 'paper.log').read_text(errors='replace')
    if not any(t in log for t in ('Rerun to get cross-references right.', 'Rerun to get outlines right.')):
        break
    run('compile_' + str(extra), latex)
log = (out / 'paper.log').read_text(errors='replace')
issues = [line for line in log.splitlines() if any(t in line for t in (
    'Overfull', 'undefined references', 'undefined citations', 'Missing character:', 'LaTeX Error:',
    'Rerun to get cross-references right.', 'Rerun to get outlines right.'))]
assert not issues, issues
save('SOURCE_BUILD_RESULT.json', {
    'status': 'PASS_AUTHORED_SOURCE_WITH_EXPLICIT_PINNED_EXTERNAL_DEPENDENCIES',
    'stages': stages, 'issues': issues, 'references_settled': True,
    'PDF_sha256': sha(out / 'paper.pdf'),
    'authored_source_manifest_sha256': sha(HERE / 'AUTHOR_SOURCE_MANIFEST.json'),
    'external_dependency_manifest_sha256': sha(HERE / 'EXTERNAL_DEPENDENCIES.json'),
    'external_files_redistributed_in_source_release': False,
    'no_global_installation_or_shell_escape_or_model_calls': True,
    'bibliography_adapter': 'Only absent publisher-location placeholders removed; all27recordsretained',
})
