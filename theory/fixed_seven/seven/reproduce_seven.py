"""Portable verification using extracted, byte-identical mathematical definitions.
Archived drivers and main functions are absent from the adjacent pure kernels.
Mathematical scope, data checks and execution logic match the prior portable adapter.
This extraction is code reuse, not another independent mathematical implementation.
"""
import sys
sys.dont_write_bytecode = True

import argparse
from collections import Counter
from fractions import Fraction
import gzip
import hashlib
import importlib.util
from itertools import permutations, product
import json
from pathlib import Path
import time

HERE = Path(__file__).resolve().parent
FILES = {
    'seven_qa_kernel_v01.py': '05b2e429b138e33d970e94c6a3e7a8b0b80d19798c4d41855a35f9c11c40e0af',
    'ALL_ORDER_FRONTIERS_V01.jsonl.gz': '33ed0bb404f1da86eb57004e79e96593c6b20995587615da234722e9a7f0d6b2',
    'ENVELOPE_WITNESSES_V01.json': '03f29180ea65939b1861661cd3b965bfccc81252e932fe3e76f18032e432cb0c',
    'PRICE_CONE_CERTIFICATES_V01.jsonl.gz': '2e558b36fd1a97d02a624fdbaf13459dda651749c34c996258f9d4bed8d93e68',
}
A = ['a', 1, 'a', 'b', 'a', 'c', 'c']
B = ['u', 'u', 0, 'v', 'w', 'w', 'v']
EXPECTED_AD = [[3, 5], [11, 28, 57, 105, 120], [11, 57, 60, 105],
               [19, 20], [28, 43, 57, 120], [35, 49, 52], [67, 84, 113]]
EXPECTED_PRIORITY = [[3, 5], [11, 28, 121], [11, 57, 60, 105],
                     [19, 20], [35, 49, 52], [67, 84, 113]]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def explicit_worlds(template):
    names = sorted({x for x in template if isinstance(x, str)})
    worlds = []
    for bits in product((0, 1), repeat=len(names)):
        assignment = dict(zip(names, bits))
        worlds.append([assignment[x] if isinstance(x, str) else x for x in template])
    return worlds


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seconds', type=float, default=120.0,
                        help='cooperatively observed computation time limit; default 120')
    args = parser.parse_args()
    started = time.monotonic()
    result = {'schema': 1, 'status': 'INCOMPLETE_OR_FAILED',
              'query_count': 7, 'orders_checked': 0, 'LP_certificates_checked': 0,
              'files_written': 0, 'API_calls': 0, 'P1_access': False,
              'six_query_catalogue_verified': False,
              'six_query_minimality_verified': False,
              'unique_maximizing_ray_mechanically_verified': False,
              'new_independent_mathematical_implementation': False,
              'checker_provenance': 'Byte-identical selected iteration251 definitions; archived driver and main excluded.',
              'script_sha256': sha(Path(__file__))}
    try:
        # The archived checker uses assertions as executable proof obligations.
        require(not sys.flags.optimize, 'Run without -O or -OO; assertions are required')
        require(sys.version_info >= (3, 9), 'Python 3.9 or newer is required')
        require(0 < args.seconds <= 3600, 'seconds must be in (0, 3600]')
        deadline = started + args.seconds
        bindings = []
        for name, expected in FILES.items():
            path = HERE / name
            digest = sha(path)
            require(digest == expected, 'Bundle hash mismatch: ' + name)
            bindings.append({'file': name, 'bytes': path.stat().st_size, 'sha256': digest})
        result['input_files'] = bindings
        spec = importlib.util.spec_from_file_location('archived_seven_qa', HERE / 'seven_qa_kernel_v01.py')
        kernel = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(kernel)

        left, right = explicit_worlds(A), explicit_worlds(B)
        require(len(left) == len(right) == 8 and not set(map(tuple, left)) & set(map(tuple, right)),
                'Source must be the complete disjoint 8+8 assignments')
        data = kernel.cube(A, B)
        require(data['world_counts'] == [8, 8], 'Independent literal source expansion mismatch')
        solver = kernel.Frontiers(data, deadline, 250000, 10000000, 20000)
        adaptive = kernel.masks(solver.ad(0))
        seen = []
        order_digest = hashlib.sha256()
        with gzip.open(HERE / 'ALL_ORDER_FRONTIERS_V01.jsonl.gz', 'rt', encoding='utf-8') as stream:
            for index, order in enumerate(permutations(range(7))):
                if time.monotonic() > deadline:
                    raise TimeoutError('TIME_CAP')
                row = json.loads(next(stream))
                require(row['index'] == index and row['order'] == list(order), 'Order missing, repeated, or reordered')
                front = solver.ordered(0, order)
                actual = kernel.masks(front)
                require(actual == row['frontier'], 'Per-order causal TAKE/SKIP frontier mismatch')
                seen.extend(front)
                order_digest.update(json.dumps([list(order), actual], separators=(',', ':')).encode())
                result['orders_checked'] += 1
            require(stream.read() == '', 'Extra order records')
        priority = kernel.masks(kernel.prune(seen))
        require(adaptive == EXPECTED_AD and priority == EXPECTED_PRIORITY, 'Complete frontier table mismatch')
        shared = [E for E in adaptive if E in priority]
        unique = [E for E in adaptive if E not in priority]
        require([len(adaptive), len(priority), len(shared), len(unique)] == [7, 6, 5, 2], 'Frontier counts')
        # This ensures normalization bounds every price coordinate; no artificial
        # upper bounds are silently imposed on absent query coordinates.
        require(all({q for q in range(7) if any(mask >> q & 1 for mask in E)} == set(range(7))
                    for E in unique), 'Adaptive unique envelope does not cover all coordinates')
        witnesses = json.loads((HERE / 'ENVELOPE_WITNESSES_V01.json').read_bytes())
        witness_count = 0
        for kind, expected in [('adaptive', adaptive), ('priority', priority)]:
            require([w['envelope'] for w in witnesses[kind]] == expected, 'Witness list mismatch')
            for witness in witnesses[kind]:
                actual, _, _ = kernel.replay(data, witness['tree'], witness.get('order') if kind == 'priority' else None)
                require(list(actual) == witness['envelope'], 'Witness replay mismatch')
                witness_count += 1

        best, winner = Fraction(1), None
        histogram = Counter()
        per_unique = [Fraction(0)] * len(unique)
        with gzip.open(HERE / 'PRICE_CONE_CERTIFICATES_V01.jsonl.gz', 'rt', encoding='utf-8') as stream:
            for ei, E in enumerate(unique):
                for selected in product(*priority):
                    if time.monotonic() > deadline:
                        raise TimeoutError('TIME_CAP')
                    row = json.loads(next(stream))
                    require(row['index'] == result['LP_certificates_checked'], 'Certificate sequence mismatch')
                    require(row['unique_envelope_index'] == ei and row['envelope'] == E
                            and row['selected_paths'] == list(selected), 'Price-cone branch missing or changed')
                    optimum, prices = kernel.verify_certificate(E, selected, row['certificate'])
                    histogram[str(optimum)] += 1
                    per_unique[ei] = max(per_unique[ei], optimum)
                    if optimum > best:
                        best, winner = optimum, prices
                    result['LP_certificates_checked'] += 1
            require(stream.read() == '', 'Extra price certificates')
        require(result['orders_checked'] == 5040 and result['LP_certificates_checked'] == 864,
                'Incomplete exhaustive verification')
        require(best == Fraction(5, 4) and winner is not None, 'Exact maximum differs from claimed result')
        av = min(kernel.cost(E, winner) for E in adaptive)
        pv = min(kernel.cost(E, winner) for E in priority)
        require(av > 0 and pv / av == best, 'Upper bound lacks matching full-frontier lower witness')
        checks = []
        for label, prices, expected in [
                ('positive_probe', [2, 2, 3, Fraction(1, 2), 1, 1, 1], (Fraction(9, 2), Fraction(5))),
                ('zero_probe', [2, 2, 3, 0, 1, 1, 1], (Fraction(4), Fraction(5)))]:
            values = (min(kernel.cost(E, prices) for E in adaptive),
                      min(kernel.cost(E, prices) for E in priority))
            require(values == expected, 'Exact price check mismatch: ' + label)
            checks.append({'case': label, 'prices': list(map(str, prices)),
                           'adaptive': str(values[0]), 'priority': str(values[1])})
        result.update(status='PASS_FIXED_SEVEN_FULL_FRONTIERS_AND_ALL_RATIONAL_CERTIFICATES',
                      A=A, B=B, world_counts=[8, 8], cube_states=len(data['digits']),
                      adaptive_frontier=adaptive, priority_frontier=priority,
                      order_frontier_sequence_sha256=order_digest.hexdigest(),
                      witness_trees_replayed=witness_count, price_checks=checks,
                      nonnegative_price_ratio_maximum=str(best),
                      per_unique_cone_maxima=list(map(str, per_unique)),
                      certificate_objective_histogram=dict(histogram),
                      maximizing_prices=list(map(str, winner)),
                      maximizing_AD=str(av), maximizing_priority=str(pv),
                      recursive_states=solver.states, envelope_products=solver.pairs,
                      LP_solver_used=False,
                      scope='Only this fixed seven-query complete-copy/pin source; deterministic zero error, worst additive cost, one global order with causal permanent SKIP.')
    except Exception as exc:
        result['failure'] = {'type': type(exc).__name__, 'message': str(exc)}
    result['wall_seconds'] = time.monotonic() - started
    print(json.dumps(result, separators=(',', ':'), allow_nan=False))
    return 0 if result['status'].startswith('PASS_') else 1


if __name__ == '__main__':
    raise SystemExit(main())
