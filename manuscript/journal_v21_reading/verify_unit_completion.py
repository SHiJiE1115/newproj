"""Check fixed obligations supporting Proposition25; the universal proof is in the paper.

No enumeration of total functions or policy search is performed. Passing these
fixtures is not a formal derivation of the arbitrary-algorithm lower bound.
"""
import argparse
from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--out', required=True)
args = parser.parse_args()
out = Path(args.out).resolve()
assert Path(args.out).is_absolute() and not out.exists()
assert not out.is_relative_to(Path(__file__).resolve().parent)
W0 = (0, 3, 4, 7, 8, 11)
W1 = (1, 15)
W = tuple(sorted(W0 + W1))
known = {w: int(w in W1) for w in W}
steps = []


def force(w):
    value = known[w]
    opposite = [w ^ (1 << q) for q in range(4) if (w ^ (1 << q)) in known and known[w ^ (1 << q)] != value]
    assert len(opposite) == 2
    added = {}
    for q in range(4):
        n = w ^ (1 << q)
        if n not in opposite:
            if n in known:
                assert known[n] == value
            else:
                known[n] = value
                added[str(n)] = value
    steps.append({'word': w, 'opposite_neighbours': opposite, 'forced': added})


for w in (1, 15, 7, 11):
    force(w)
assert 2 not in known and all(known[2 ^ (1 << q)] == 0 for q in range(4))
known[2] = 0
steps.append({'word': 2, 'all_neighbours_zero': True, 'forced': {'2': 0}})
force(14)
assert len(known) == 16


def bit(w, q):
    return (w >> q) & 1


def g(w):
    return int((bit(w, 0) and not bit(w, 1)) or (bit(w, 2) and bit(w, 3)))


assert all(known[w] == g(w) for w in range(16))
assert max(sum(g(w) != g(w ^ (1 << q)) for q in range(4)) for w in range(16)) == 2


def trace(tree, w):
    path = []
    while isinstance(tree, list):
        q, zero, one = tree
        assert q not in path
        path.append(q)
        tree = one if bit(w, q) else zero
    return tree, path


promise_rows = []
for tree, order in (([1, [0, 0, 1], [2, 0, [3, 0, 1]]], (1, 0, 2, 3)),
                    ([2, [1, [0, 0, 1], 0], [3, 0, 1]], (2, 1, 0, 3))):
    costs = []
    for w in W:
        result, path = trace(tree, w)
        assert result == int(w in W1)
        assert all(order.index(a) < order.index(b) for a, b in zip(path, path[1:]))
        costs.append(len(path))
    promise_rows.append(costs)
promise_expected = [Fraction(a + b, 2) for a, b in zip(*promise_rows)]
assert max(promise_expected) == Fraction(5, 2)
for w, pair in ((1, (0, 1)), (15, (2, 3))):
    assert all((w ^ (1 << q)) in W0 for q in pair)
for first in range(4):
    assert Fraction(sum(2 + int(first not in pair) for pair in ((0, 1), (2, 3))), 2) == Fraction(5, 2)
total_rows = []
for childorder, left, right in itertools.product(((0, 1), (1, 0)), ((0, 1), (1, 0)), ((2, 3), (3, 2))):
    leaforders = (left, right)
    order = tuple(q for child in childorder for q in leaforders[child])
    costs = []
    for w in range(16):
        literal = (bit(w, 0), 1 - bit(w, 1), bit(w, 2), bit(w, 3))
        paid = []
        result = 0
        for child in childorder:
            value = 1
            for q in leaforders[child]:
                paid.append(q)
                if literal[q] == 0:
                    value = 0
                    break
            if value:
                result = 1
                break
        assert result == g(w)
        assert all(order.index(a) < order.index(b) for a, b in zip(paid, paid[1:]))
        costs.append(len(paid))
    total_rows.append(costs)
total_expected = [sum(Fraction(row[w], 8) for row in total_rows) for w in range(16)]
assert max(total_expected) == 3
hard = (4, 7, 8, 11)
literal_hard = {(bit(w, 0), 1 - bit(w, 1), bit(w, 2), bit(w, 3)) for w in hard}
assert literal_hard == {(a, 1-a, b, 1-b) for a, b in itertools.product((0, 1), repeat=2)}
assert all(total_expected[w] == 3 for w in hard)
science = {
    'source_W0': list(W0), 'source_W1': list(W1), 'fixed_implications': steps,
    'forced_all16_values': [known[w] for w in range(16)],
    'promise_expected_costs': [str(c) for c in promise_expected],
    'eight_fixed_total_priority_seed_costs': total_rows,
    'total_expected_costs': [str(c) for c in total_expected],
    'hard_prior_words': list(hard), 'hard_prior_weights': ['1/4'] * 4,
}
canonical = json.dumps(science, sort_keys=True, separators=(',', ':')).encode()
result = {
    'status': 'PASS_FIXED_LOCAL_IMPLICATIONS_AND_EXPLICIT_UNIT_POLICY_WITNESSES',
    'science': science, 'science_sha256': hashlib.sha256(canonical).hexdigest(),
    'analytic_claim_supported': 'Onthisfixedcomplete4sourceatunitcosts,promiseRA=RP5/2whileminoverALLcompatiblefullcubetotalfunctionsRA=RP3',
    'written_proof_required': 'Sensitivity bounds every seed; the six implications cover every total completion; independent hard zero positions force expected3forg. These analytic arguments are in Proposition25,not inferred from fixture passing.',
    'no_function_or_policy_search_LP_model_API_network_human_or_formal_review': True,
}
out.parent.mkdir(parents=True, exist_ok=True)
with out.open('x', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
    f.write('\n')
print(json.dumps({'status': result['status'], 'science_sha256': result['science_sha256']}))
