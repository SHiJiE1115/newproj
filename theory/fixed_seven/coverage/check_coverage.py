"""Portable exact replay of all 864 fixed-seven coverage LP certificates.

Python standard library only. Writes no result files or bytecode; one JSON
report is emitted on stdout. Defaults are relative to this script's directory.
This reuses the independent 263 mathematics, not a third implementation.
It neither enumerates the inherited frontiers nor proves the general
submodular-cost theorem. No producer, old main, or LP solver is imported.
"""
import sys
sys.dont_write_bytecode = True
import argparse
from datetime import datetime, timezone
from fractions import Fraction
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import time
import types

HERE = Path(__file__).resolve().parent
KERNEL_SHA256 = '975f8beb8d069042286d320499ae62e8e685ba3b2e55d2910929948959bd1704'
INPUTS = {
    'certificate': {'filename': 'RATIONAL_BRANCH_CERTIFICATES_V01.jsonl.gz', 'bytes': 6417,
                    'sha256': '95cb3a19aee9584301b02ddda2ab57f0d21c0edec7858be72e64a75f08d9f07a'},
    'frontiers': {'filename': 'ENVELOPE_WITNESSES_V01.json', 'bytes': 1160,
                  'sha256': '03f29180ea65939b1861661cd3b965bfccc81252e932fe3e76f18032e432cb0c'},
}


def bound_read(path, spec):
    if path.stat().st_size != spec['bytes']:
        raise ValueError('Input size differs: ' + path.name)
    raw = path.read_bytes()
    if len(raw) != spec['bytes'] or hashlib.sha256(raw).hexdigest() != spec['sha256']:
        raise ValueError('Input SHA256 differs: ' + path.name)
    return raw


def load_kernel():
    raw = (HERE / 'coverage_math_kernel.py').read_bytes()
    if hashlib.sha256(raw).hexdigest() != KERNEL_SHA256:
        raise ValueError('Pure mathematical kernel differs from the pinned bytes')
    module = types.ModuleType('coverage_math_kernel')
    exec(compile(raw, 'coverage_math_kernel.py', 'exec'), module.__dict__)
    return module


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--certificate', type=Path, default=HERE / 'data' / INPUTS['certificate']['filename'])
    parser.add_argument('--frontiers', type=Path, default=HERE / 'data' / INPUTS['frontiers']['filename'])
    parser.add_argument('--seconds', type=float, default=90.0,
                        help='Positive finite cooperative computation limit; default 90 seconds, not an OS wall-time limit.')
    args = parser.parse_args(argv)
    start = time.monotonic()
    report = {
        'schema': 1, 'status': 'NOT_COMPLETED', 'phase': 'input_binding', 'context': None,
        'failure': None, 'records_verified': 0, 'kernel_sha256': KERNEL_SHA256,
        'input_bindings': INPUTS, 'computation_seconds_limit': args.seconds if math.isfinite(args.seconds) else None,
        'time_limit_scope': 'Cooperative checks; no hard OS bound on file I/O, scheduling, or output serialization.',
        'writes_result_files': False, 'writes_bytecode': False,
        'producer_imported': False, 'LP_solver_imported': False,
        'third_party_modules_imported': False, 'API_calls': 0,
        'new_source_or_frontier_enumeration': False,
        'inherited_complete_frontiers_not_recomputed': True,
        'general_submodular_upper_bound': False,
        'third_independent_mathematical_implementation': False,
        'strict_monotone_nonattainment_mechanically_verified': False,
        'literary_priority_established': False,
    }
    try:
        if not math.isfinite(args.seconds) or args.seconds <= 0:
            raise ValueError('--seconds must be finite and strictly positive')
        k = load_kernel()

        def deadline():
            k.require(time.monotonic() - start <= args.seconds, 'Cooperative computation deadline')

        source_raw = bound_read(args.frontiers, INPUTS['frontiers'])
        certificate_raw = bound_read(args.certificate, INPUTS['certificate'])
        source = k.decode(source_raw)
        k.require(tuple(tuple(row['envelope']) for row in source['adaptive']) == k.ADAPTIVE, 'Adaptive premise differs')
        k.require(tuple(tuple(row['envelope']) for row in source['priority']) == k.PRIORITY, 'Priority premise differs')
        k.require(tuple(e for e in k.ADAPTIVE if e not in k.PRIORITY) == k.SPECIAL,
                  'Adaptive-only decomposition differs')
        k.require(len(set(k.ADAPTIVE) & set(k.PRIORITY)) == 5, 'Shared envelope count differs')
        for envelope in k.SPECIAL:
            k.require(frozenset().union(*(k.coordinates(p) for p in envelope)) == frozenset(range(7)),
                      'Adaptive-only envelope does not cover all coordinates')
        deadline()
        report['phase'] = 'controls'
        report['controls'] = k.controls()
        k.require(len(report['controls']) == 12, 'Control count differs')
        deadline()
        report['phase'] = 'all_branch_certificates'
        keys, seen, counts = [], set(), [0, 0]
        maxima, winners = [Fraction(-1), Fraction(-1)], [None, None]
        event_hash = hashlib.sha256()
        decompressed = 0
        with gzip.GzipFile(fileobj=io.BytesIO(certificate_raw), mode='rb') as stream:
            line_number = 0
            while True:
                raw = stream.readline(65537)
                if not raw:
                    break
                deadline()
                line_number += 1
                k.require(len(raw) <= 65536, 'Certificate line cap')
                decompressed += len(raw)
                k.require(decompressed <= 4194304 and line_number <= 864, 'Certificate expansion/count cap')
                row = k.decode(raw)
                report['context'] = {'line': line_number, 'kind': row.get('kind'), 'serial': row.get('serial')}
                key, value, weights = k.validate_record(row)
                k.require(key not in seen, 'Duplicate LP branch')
                seen.add(key)
                keys.append(key)
                counts[key[0]] += 1
                event_hash.update((str(key) + ':' + str(value) + '\n').encode('ascii'))
                if value > maxima[key[0]]:
                    maxima[key[0]] = value
                    ac = k.envelope_costs(k.ADAPTIVE, weights)
                    pc = k.envelope_costs(k.PRIORITY, weights)
                    winners[key[0]] = {
                        'kind': key[0], 'serial': key[1], 'LP_objective': str(value),
                        'adaptive_envelope_costs': list(map(str, ac)),
                        'priority_envelope_costs': list(map(str, pc)),
                        'actual_AD': str(min(ac)), 'actual_P': str(min(pc)),
                        'actual_ratio': str(min(pc) / min(ac)) if min(ac) else None,
                    }
                report['records_verified'] += 1
        k.full_coverage(keys)
        k.require(counts == [432, 432], 'Per-envelope branch count differs')
        k.require(maxima == [Fraction(4, 3), Fraction(4, 3)], 'Advertised 4/3 coverage bound not established')
        k.require(all(w['actual_AD'] == '1' and w['actual_P'] == '4/3' and w['actual_ratio'] == '4/3'
                      for w in winners), 'LP maxima are not actual priority/adaptive ratios')
        report['phase'] = 'literal_shared_setup_witness'
        weights = [Fraction(0)] * 127
        for q in (0, 1, 4, 6):
            weights[k.RESOURCES.index(frozenset([q]))] += 1
        weights[k.RESOURCES.index(frozenset([2]))] += 2
        weights[k.RESOURCES.index(frozenset([0, 5]))] += 1
        ac = k.envelope_costs(k.ADAPTIVE, weights)
        pc = k.envelope_costs(k.PRIORITY, weights)
        k.require(ac == tuple(map(Fraction, [4, 3, 4, 4, 3, 4, 4])) and pc == (Fraction(4),) * 6,
                  'Literal manual coverage witness differs')
        k.require(min(ac) == 3 and min(pc) == 4, 'Manual optima differ')
        deadline()
        report.update(
            status='PASS_ALL_864_EXACT_COVERAGE_LPS_AND_MANUAL_RATIO', phase='complete', context=None,
            branch_counts=counts, exact_maxima=list(map(str, maxima)),
            branches_event_sha256=event_hash.hexdigest(), decompressed_certificate_bytes=decompressed,
            LP_primal_rows_checked=432 * (5 + 6) + 432 * (4 + 6), LP_dual_columns_checked=864 * 128,
            maximizing_actual_ratio_checks=winners,
            hand_witness={'adaptive_costs': list(map(str, ac)), 'priority_costs': list(map(str, pc)),
                          'AD': '3', 'P': '4', 'ratio': '4/3'},
            proof_scope='Exact coverage bound for the fixed seven source, conditional on inherited complete frontiers; not all submodular functions.',
        )
    except (Exception, KeyboardInterrupt) as exc:
        report.update(status='FAIL_OR_INCOMPLETE_NO_NEW_BOUND',
                      failure={'type': type(exc).__name__, 'message': str(exc)})
    report['elapsed_seconds'] = time.monotonic() - start
    report['finished_utc'] = datetime.now(timezone.utc).isoformat()
    print(json.dumps(report, ensure_ascii=False, allow_nan=False), flush=True)
    return 0 if report['status'] == 'PASS_ALL_864_EXACT_COVERAGE_LPS_AND_MANUAL_RATIO' else 2


if __name__ == '__main__':
    sys.exit(main())
