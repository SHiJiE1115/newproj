"""Replay only the five frozen even-path fixtures. Python 3.10+, stdlib."""
from pathlib import Path
from datetime import datetime, timezone
from fractions import Fraction
import argparse
import hashlib
import importlib.util
import json
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
MEMBERS = {'alternating_path.py', 'verify.py', 'fixtures.json', 'README.md', 'MANIFEST.json'}
SOLVER_SHA256 = 'f9127ebd2c8386f5a338dab5b462490e6ff58cefe113816fab7b54b123ea4b3b'
FIXTURES_SHA256 = 'c802923f6d6cbec39f801f29f94cf2391c9ef5d0251161cdfe6d1fc94df632eb'
FROZEN = [
    ('n6_unit', ['1'] * 6, '4', {'A': 5, 'B': 10}, 203),
    ('n6_asymmetric', ['1', '7', '2', '3', '5', '1'], '11', {'A': 5, 'B': 10}, 203),
    ('n8_unit', ['1'] * 8, '4', {'A': 15, 'B': 37}, 4140),
    ('n2_zero', ['0', '0'], '0', {'A': 1, 'B': 1}, 2),
    ('n2_rational', ['0', '3/2'], '3/2', {'A': 1, 'B': 1}, 2),
]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def inventory():
    entries = list(HERE.iterdir())
    require({p.name for p in entries} == MEMBERS, 'Package member inventory differs.')
    require(all(p.is_file() and not p.is_symlink() for p in entries), 'Package must contain only regular member files.')
    blobs = {p.name: p.read_bytes() for p in entries}
    require(sum(map(len, blobs.values())) <= 102400, 'Package exceeds the 100 KiB fixed-fixture limit.')
    manifest = json.loads(blobs['MANIFEST.json'])
    require(manifest['schema'] == 1 and manifest['manifest_excludes_itself'] is True, 'Unsupported manifest schema.')
    files = manifest['files']
    require(len(files) == 4 and {r['path'] for r in files} == MEMBERS - {'MANIFEST.json'}, 'Manifest must name the other four members exactly once.')
    for row in files:
        blob = blobs[row['path']]
        require(row['bytes'] == len(blob) and row['sha256'] == digest(blob), 'Manifest member digest or byte count differs.')
    require(digest(blobs['alternating_path.py']) == SOLVER_SHA256, 'Frozen solver digest differs.')
    require(digest(blobs['fixtures.json']) == FIXTURES_SHA256, 'Frozen fixture digest differs.')
    fixtures = json.loads(blobs['fixtures.json'])
    cases = fixtures['cases']
    contract = [(c['id'], c['prices'], c['expected_worst_cost'], c['world_counts'], c['all_partitions']) for c in cases]
    require(contract == FROZEN, 'Fixed fixture contracts differ.')
    return blobs, cases


def partitions(n):
    """All set partitions: choose the block containing the least unused bit."""
    def visit(remaining, blocks):
        if not remaining:
            colours = [None] * n
            for colour, block in enumerate(blocks):
                for q in range(n):
                    if block & (1 << q):
                        colours[q] = colour
            yield tuple(colours)
            return
        first = remaining & -remaining
        rest = remaining ^ first
        subset = rest
        while True:
            yield from visit(rest ^ subset, blocks + (first | subset,))
            if subset == 0:
                break
            subset = (subset - 1) & rest
    yield from visit((1 << n) - 1, ())


def legal_worlds(n):
    legal = []
    total = 0
    for world in partitions(n):
        total += 1
        a = all(world[q] == world[q + 1] for q in range(0, n, 2))
        b = world[0] != world[n - 1] and all(world[q] == world[q + 1] for q in range(1, n - 1, 2))
        require(not (a and b), 'Source labels overlap.')
        if a or b:
            legal.append((world, 'A' if a else 'B'))
    return total, legal


def check_structure(policy, n):
    anchor = policy['anchor']
    require(type(anchor) is int and 0 <= anchor < n, 'Invalid anchor.')
    order = policy['priority_order']
    require(all(type(q) is int for q in order) and sorted(order) == list(range(n)), 'Order is not a physical record permutation.')
    require(order[0] == anchor, 'Anchor is not first in the fixed order.')
    seen = set()
    leaves = []
    preorder = []
    def walk(node):
        if 'query' not in node:
            require(set(node) == {'cut_edge', 'label'}, 'Invalid tree leaf schema.')
            j = node['cut_edge']
            require(type(j) is int and 0 <= j < n, 'Invalid leaf cut.')
            require(node['label'] == ('B' if j % 2 == 0 else 'A'), 'Leaf label differs from cut parity.')
            leaves.append(j)
            return
        require(set(node) == {'query', 'left', 'right'}, 'Invalid internal node schema.')
        q = node['query']
        require(type(q) is int and 0 <= q < n and q != anchor and q not in seen, 'Internal physical query repeats or is invalid.')
        seen.add(q)
        preorder.append(q)
        walk(node['left'])
        walk(node['right'])
    walk(policy['tree'])
    require(seen == set(range(n)) - {anchor}, 'Tree does not contain each nonanchor exactly once.')
    require(sorted(leaves) == list(range(n)), 'Tree does not have one leaf per cut.')
    require(order == [anchor] + preorder, 'Order differs from anchor plus preorder.')


def replay(module, case):
    prices = [Fraction(x) for x in case['prices']]
    expected = Fraction(case['expected_worst_cost'])
    n = len(prices)
    policy = module.solve(case['prices'])
    require(policy['n'] == n and policy['prices'] == [str(x) for x in prices], 'Solver prices or size differ.')
    require(Fraction(policy['optimal_worst_cost']) == expected, 'Solver value differs from fixed expected value.')
    require(policy['dp_states'] == n * n and policy['split_candidates'] == n * n * (n - 1) // 2, 'DP table accounting differs.')
    check_structure(policy, n)
    ranks = {q: i for i, q in enumerate(policy['priority_order'])}
    total, worlds = legal_worlds(n)
    require(total == case['all_partitions'], 'Complete partition count differs.')
    counts = {'A': 0, 'B': 0}
    costs = []
    traces = []
    for world, label in worlds:
        calls = []
        def acquire(q, anchor):
            require(type(q) is int and 0 <= q < n and q not in calls, 'Acquisition invalid or repeated.')
            if not calls:
                require(anchor is None and q == policy['anchor'], 'First acquisition must be the paid uninformative anchor.')
            else:
                require(anchor == calls[0] and ranks[q] > ranks[calls[-1]], 'Acquisition violates anchor reference or fixed order.')
            calls.append(q)
            return None if anchor is None else world[q] == world[anchor]
        trace = module.execute(policy, acquire)
        require(trace['acquired'] == calls and calls and calls[0] == policy['anchor'], 'Trace omits or alters an actual purchase.')
        require(trace['label'] == label, 'Incorrect full-source classification.')
        j = trace['cut_edge']
        require(type(j) is int and 0 <= j < n, 'Invalid executed cut.')
        right = (j + 1) % n
        require(j in calls and right in calls, 'Leaf certificate endpoints were not both acquired.')
        if j == n - 1:
            require(world[j] == world[right] == world[policy['anchor']], 'Seam certificate fails.')
        else:
            require(world[j] != world[right], 'Ordinary-edge certificate fails.')
        require(trace['label'] == ('B' if j % 2 == 0 else 'A'), 'Executed leaf label differs from its certificate.')
        # Count the first anchor exactly once, even when its price is zero.
        cost = sum((prices[q] for q in calls), Fraction(0))
        require(cost == Fraction(trace['cost']), 'Reported cost omits or misprices a purchase.')
        counts[label] += 1
        costs.append(cost)
        traces.append({'world': list(world), 'label': label, 'cut_edge': j, 'acquired': calls, 'cost': str(cost)})
    require(counts == case['world_counts'], 'Full legal fibre counts differ.')
    require(max(costs) == expected, 'Observed maximum differs from fixed expected value.')
    return {'id': case['id'], 'prices': case['prices'], 'expected_worst_cost': str(expected), 'observed_worst_cost': str(max(costs)), 'world_counts': counts, 'all_partitions': total, 'expected_value_basis': case['expected_value_basis'], 'kind': case['kind'], 'policy': policy, 'traces': traces}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='A new JSON file outside the extracted package; parent must exist.')
    args = parser.parse_args()
    output = args.output.resolve()
    if output == HERE or HERE in output.parents:
        parser.error('Output must be outside the package.')
    if output.exists() or not output.parent.is_dir():
        parser.error('Output must be new and its parent must already exist.')
    result = {'schema': 1, 'status': 'FAIL_FIXED_FIXTURE_REPLAY', 'human_review': False, 'new_price_or_size_search': False, 'adaptive_frontier_recomputed': False}
    try:
        require(sys.version_info >= (3, 10), 'Python 3.10 or later is required.')
        before, cases = inventory()
        spec = importlib.util.spec_from_file_location('packaged_even_path_solver', HERE / 'alternating_path.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        rows = [replay(module, c) for c in cases]
        after, _ = inventory()
        require(before == after, 'Package bytes changed during replay.')
        scientific = sum(sum(r['world_counts'].values()) for r in rows if r['kind'] == 'existing_scientific_fixture')
        software = sum(sum(r['world_counts'].values()) for r in rows if r['kind'] == 'software_edge_fixture')
        require((scientific, software) == (82, 4), 'Fixed replay trace totals differ.')
        result.update({'status': 'PASS_FIXED_FIXTURE_REPLAY', 'cases': rows, 'existing_scientific_fixture_world_traces': scientific, 'software_edge_case_world_traces': software, 'all_full_world_classifications_correct': True, 'first_anchor_paid_and_acquired': True, 'all_priority_orders_causal': True, 'all_leaf_certificates_checked': True, 'package_unchanged_during_replay': True, 'members': [{'path': name, 'bytes': len(before[name]), 'sha256': digest(before[name])} for name in sorted(before)], 'scope': 'The exact mathematical optimum for arbitrary even size follows from the analytic containment and minimax-DP proofs in journal V08 Appendix E.2; these finite fixture replays do not prove the all-size theorem or recompute adaptive lower bounds.'})
    except Exception as exc:
        result['error_type'] = type(exc).__name__
        result['error'] = str(exc)
    result['completed_at_utc'] = datetime.now(timezone.utc).isoformat()
    with output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'status': result['status'], 'existing_scientific_fixture_world_traces': result.get('existing_scientific_fixture_world_traces', 0), 'software_edge_case_world_traces': result.get('software_edge_case_world_traces', 0)}))
    return 0 if result['status'] == 'PASS_FIXED_FIXTURE_REPLAY' else 1


if __name__ == '__main__':
    raise SystemExit(main())
