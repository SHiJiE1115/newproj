"""Offline four-case software regression, not a new scientific replication.

Use the original frozen Wine v01 directory and corrected v02 directory.
Output must be new and outside both directories. No network or crypto verifier.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path

def sha(b):
    return hashlib.sha256(b).hexdigest()

def checked(path, expected):
    data = path.read_bytes()
    if sha(data) != expected:
        raise ValueError('Source pin mismatch: ' + path.name)
    return data

def load(name, path, expected):
    checked(path, expected)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original', required=True, type=Path)
    parser.add_argument('--corrected', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    original, corrected, output = (p.resolve() for p in (args.original, args.corrected, args.output))
    if output.exists() or any(output.is_relative_to(p) for p in (original, corrected)):
        raise ValueError('Output must be new and outside both bundles')
    if not output.parent.is_dir() or shutil.disk_usage(output.parent).free < 64*1024**2:
        raise ValueError('Output parent missing or insufficient free space')
    candidate = load('old_candidate', original/'layer_candidate.py', '3597ee62fd7f9aae4b61e9d49fa2db16d5e0750573e05d5376b5064bfec5815b')
    fixed = load('corrected_candidate', corrected/'layer_candidate.py', '7d86bd4ede7e089a8325d7d57c89b7135f86f290eabd4b15bd149a64470e4918')
    baseline = load('signature_baseline', original/'sql_baseline_v02.py', 'fed2570f8e59ee993e2b99dc9e6d24578ebb72c1b4383d81fd95302c50742488')
    protocol_bytes = checked(original/'protocol.json', '3d5f542359cc385cd6edacc3612994fecb034dcedae4e3322602c1aea934641f')
    protocol = baseline.resolve_inputs(json.loads(protocol_bytes), original)
    run = candidate.load_run('v09', protocol['runs']['v09'])
    raw = {k: candidate.pinned(d) for k, d in protocol['v09_retained_signature_files'].items()}
    baseline_run = {'v09': {'key': baseline.key_for(protocol['runs']['v09']),
        'gate': baseline.parse(candidate.pinned(protocol['runs']['v09']['files']['POSTRUN_RELEASE_GATE.json']))}}
    if baseline_run['v09']['key'] != run['key']:
        raise ValueError('Identity disagreement')
    core, checker = candidate.load_semantics(protocol['existing_semantic_modules'])
    number = candidate.numeric(run, run, run)
    read = candidate.selected_read(run, run)
    if not number['admitted'] or not read['admitted']:
        raise ValueError('Retained positive control failed')
    output.mkdir()
    rows = []
    before = raw['ACCEPTANCE.json']
    if before.count(b'"verify_exit": 0') != 1:
        raise ValueError('Unexpected fixture template')
    for name, value in [('integer_zero', b'0'), ('boolean_false', b'false'), ('floating_zero', b'0.0'), ('integer_one', b'1')]:
        data = before.replace(b'"verify_exit": 0', b'"verify_exit": ' + value)
        fixture = output/(name + '.json')
        fixture.write_bytes(data)
        spec = {'path': str(fixture), 'bytes': len(data), 'sha256': sha(data)}
        if candidate.pinned(spec) != data:
            raise ValueError('Derived input verification failed')
        p = copy.deepcopy(protocol)
        p['v09_retained_signature_files']['ACCEPTANCE.json'] = spec
        altered = dict(raw, **{'ACCEPTANCE.json': data})
        blobs = {d['path']: altered[k] for k, d in p['v09_retained_signature_files'].items()}
        direct = baseline.retained_signature(p, blobs, baseline_run)
        row = {'id': name, 'input_sha256': sha(data), 'parsed_type': type(json.loads(data)['verify_exit']).__name__,
               'baseline_admitted': direct['positive']}
        for label, module in [('original', candidate), ('corrected', fixed)]:
            result = module.retained_signature(run, run, altered)
            scope = core.digest({'input_sha256': sha(data), 'harness_sha256': sha(Path(__file__).read_bytes()), 'mode': label})
            cert = module.certify_layer(core, checker, {'id': name, 'copies': 1}, 'retained_signed_identity', result['admitted'], run['key'], scope)
            joint = module.certify_layer(core, checker, {'id': name, 'copies': 1}, 'joint_scoped_receipt', result['admitted'] and number['admitted'] and read['admitted'], run['key'], scope)
            row[label] = {'admitted': result['admitted'], 'signature_status': cert['status'],
                          'joint_status': joint['status'], 'signature_checker': cert['checker'], 'joint_checker': joint['checker']}
        expected_old = name != 'integer_one'
        expected_fixed = name == 'integer_zero'
        if row['original']['admitted'] != expected_old or row['corrected']['admitted'] != expected_fixed or row['baseline_admitted'] != expected_fixed:
            raise ValueError('Expected bounded differential not reproduced: ' + name)
        rows.append(row)
    result = {'schema': 1, 'status': 'PASS_FOUR_CASE_DIFFERENTIAL_AND_CORRECTION_REPRODUCED', 'cases': rows,
              'four_unique_interface_interventions': True, 'fresh_crypto_verification': False,
              'new_author_execution': False, 'original_cli_invoked': False, 'old_pin_bypassed': False,
              'scope': 'Helper-level synthetic regression; valid semantic certificates do not authenticate adapter facts. No natural-material accuracy or theoretical novelty claim.'}
    (output/'RESULT.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result))

if __name__ == '__main__':
    main()
