"""Capture one fixed-seven verifier run; never perform a network request.

GitHub context is selected runner metadata, not a cryptographic attestation.
Local validation is explicitly distinct from a hosted Actions execution.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / 'theory/fixed_seven'
ENTRY_SHA256 = '9d3d05354b1a89bfb8a63fd1bd890bf8c093fb9d070d0de9b950e5ab2d91a380'

def require(ok, message):
    if not ok:
        raise ValueError(message)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def decode(raw):
    def unique(items):
        result = {}
        for key, value in items:
            require(key not in result, 'Duplicate JSON key')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execution-kind', required=True, choices=['local-validation', 'github-actions'])
    parser.add_argument('--expect-manifest-sha256', required=True)
    parser.add_argument('--output-dir', required=True)
    args = parser.parse_args()
    out = Path(args.output_dir).resolve()
    require(not out.is_relative_to(PACKAGE), 'Outputs must be outside the verifier package')
    require(not out.exists(), 'Output directory already exists; do not overwrite a run')
    out.mkdir(parents=True)
    started = time.monotonic()
    receipt = {
        'schema': 1, 'execution_kind': args.execution_kind,
        'started_utc': datetime.now(timezone.utc).isoformat(),
        'status': 'FAIL_OR_INCOMPLETE', 'child_launched': False,
        'actual_child_exit_code': None, 'github_context': None,
        'python': {'version': platform.python_version(), 'implementation': platform.python_implementation()},
        'platform': {'system': platform.system(), 'release': platform.release(), 'machine': platform.machine()},
        'wrapper_sha256': sha(Path(__file__)),
        'six_query_boundary_reverified': False, 'general_submodular_upper_bound_machine_proved': False,
        'historical_research_authenticated': False, 'human_review_obtained': False,
        'new_independent_mathematical_implementation': False,
        'model_API_calls': 0, 'network_requests_by_wrapper': 0,
        'scope': 'One fixed-seven source; exact frontier/additive and coverage checks. Written arguments remain necessary.',
        'attestation': 'None. Runner metadata and hashes are not a signed execution certificate.'
    }
    exit_code = 2
    try:
        require(sys.version_info >= (3, 10), 'Python 3.10+ required')
        require(not sys.flags.optimize, 'Do not use -O or -OO')
        require(re.fullmatch(r'[0-9a-f]{64}', args.expect_manifest_sha256), 'Invalid manifest hash')
        # Read only these public CI context fields. Never dump the environment.
        if args.execution_kind == 'github-actions':
            require(os.environ.get('GITHUB_ACTIONS') == 'true', 'Not in a declared GitHub Actions context')
            fields = ('GITHUB_REPOSITORY', 'GITHUB_SHA', 'GITHUB_RUN_ID', 'GITHUB_RUN_ATTEMPT', 'GITHUB_EVENT_NAME')
            context = {key: os.environ.get(key, '') for key in fields}
            require(context['GITHUB_REPOSITORY'].lower() == 'shijie1115/newproj', 'Wrong repository context')
            require(re.fullmatch(r'[0-9a-f]{40}', context['GITHUB_SHA']), 'Invalid commit context')
            require(all(re.fullmatch(r'[1-9][0-9]*', context[key]) for key in ('GITHUB_RUN_ID', 'GITHUB_RUN_ATTEMPT')), 'Invalid run context')
            require(context['GITHUB_EVENT_NAME'] == 'workflow_dispatch', 'Manual dispatch required')
            receipt['github_context'] = context
        else:
            require(os.environ.get('GITHUB_ACTIONS') != 'true', 'Use github-actions mode on the hosted runner')
        receipt['manifest_sha256'] = sha(PACKAGE / 'MANIFEST.json')
        require(receipt['manifest_sha256'] == args.expect_manifest_sha256, 'Manifest differs from the reviewed pin')
        receipt['entry_sha256'] = sha(PACKAGE / 'verify.py')
        require(receipt['entry_sha256'] == ENTRY_SHA256, 'Verifier entry changed')
        command = [sys.executable, '-I', '-X', 'utf8', '-B', str(PACKAGE / 'verify.py'), '--mode', 'all', '--seconds', '120']
        receipt['logical_command'] = 'python -I -X utf8 -B theory/fixed_seven/verify.py --mode all --seconds 120'
        with (out / 'verifier.stdout.json').open('xb') as stdout, (out / 'verifier.stderr.txt').open('xb') as stderr:
            child = subprocess.Popen(command, cwd=ROOT, stdout=stdout, stderr=stderr, stdin=subprocess.DEVNULL,
                                     creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            receipt.update(child_launched=True, child_pid=child.pid)
            try:
                receipt['actual_child_exit_code'] = child.wait(timeout=300)
            except subprocess.TimeoutExpired:
                child.kill()
                receipt['actual_child_exit_code'] = child.wait()
                receipt['outer_timeout'] = True
                receipt['descendant_termination_not_established'] = True
                raise RuntimeError('Outer timeout; do not retry without checking for unfinished descendants')
        require(receipt['actual_child_exit_code'] == 0, 'Verifier returned nonzero')
        result = decode((out / 'verifier.stdout.json').read_bytes())
        require(result['status'] == 'PASS_FIXED_SEVEN_SUPPLEMENT_ALL' and result['mode'] == 'all', 'Incomplete verifier result')
        require(result['inventory']['manifest_sha256'] == args.expect_manifest_sha256, 'Result manifest mismatch')
        require(result['complete_fixed_source_frontiers_rebuilt'] is True and
                result['coverage_certificates_reverified'] is True and
                result['coverage_frontier_premise_rebuilt_in_same_invocation'] is True, 'Incomplete mathematical layers')
        require(result['six_query_boundary_reverified'] is False and
                result['all_submodular_upper_bound_mechanically_proved'] is False, 'Result exceeds the package scope')
        seven = result['results']['seven']; coverage = result['results']['coverage']
        require(seven['orders_checked'] == 5040 and seven['witness_trees_replayed'] == 13 and
                seven['LP_certificates_checked'] == 864 and coverage['records_verified'] == 864, 'Incomplete certificate counts')
        receipt['counts'] = {'orders': 5040, 'policy_witnesses': 13, 'additive_certificates': 864, 'coverage_certificates': 864}
        receipt['status'] = 'PASS_SCOPED_FIXED_SEVEN_RUN'
        exit_code = 0
    except Exception as exc:
        receipt['error'] = type(exc).__name__ + ': ' + str(exc)
    finally:
        for name in ('verifier.stdout.json', 'verifier.stderr.txt'):
            path = out / name
            if path.exists():
                receipt[name] = {'bytes': path.stat().st_size, 'sha256': sha(path)}
        receipt.update(finished_utc=datetime.now(timezone.utc).isoformat(), elapsed_seconds=time.monotonic() - started)
        with (out / 'receipt.json').open('x', encoding='utf8', newline='\n') as stream:
            json.dump(receipt, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print(json.dumps({'status': receipt['status'], 'execution_kind': args.execution_kind,
                      'child_launched': receipt['child_launched'],
                      'actual_child_exit_code': receipt['actual_child_exit_code'], 'receipt_sha256': sha(out / 'receipt.json')}))
    return exit_code

if __name__ == '__main__':
    raise SystemExit(main())
