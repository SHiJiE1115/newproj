"""Exact additive-cost solver for the complete even alternating path source.

Standard library only. Arithmetic uses Fraction; input prices are integers or
exact rational/decimal strings, never binary floating-point approximations.
The all-source optimality premise is the separately reviewed envelope theorem.
"""
from fractions import Fraction
import argparse
import json


def solve(prices):
    if len(prices) < 2 or len(prices) % 2:
        raise ValueError('The source requires an even number of at least two records.')
    if any(isinstance(x, bool) or not isinstance(x, (int, str, Fraction)) for x in prices):
        raise ValueError('Prices must be integers, Fractions, or exact numeric strings.')
    costs = [Fraction(x) for x in prices]
    if any(x < 0 for x in costs):
        raise ValueError('Prices must be nonnegative.')
    n = len(costs)
    value = [[Fraction(0) for _ in range(n + 1)] for _ in range(n)]
    split = [[None for _ in range(n + 1)] for _ in range(n)]
    candidates = 0
    for length in range(2, n + 1):
        for start in range(n):
            best = None
            for left_length in range(1, length):
                q = (start + left_length) % n
                v = costs[q] + max(value[start][left_length], value[q][length - left_length])
                candidates += 1
                if best is None or v < best:
                    best = v
                    split[start][length] = left_length
            value[start][length] = best
    anchor_values = [costs[i] + value[i][n] for i in range(n)]
    anchor = min(range(n), key=lambda i: (anchor_values[i], i))
    order = [anchor]

    def build(start, length):
        if length == 1:
            return {'cut_edge': start, 'label': 'B' if start % 2 == 0 else 'A'}
        left_length = split[start][length]
        q = (start + left_length) % n
        order.append(q)
        left = build(start, left_length)
        right = build(q, length - left_length)
        return {'query': q, 'left': left, 'right': right}

    tree = build(anchor, n)
    assert sorted(order) == list(range(n))
    assert candidates == n * n * (n - 1) // 2
    return {
        'schema': 1, 'n': n, 'prices': [str(x) for x in costs],
        'optimal_worst_cost': str(anchor_values[anchor]),
        'anchor': anchor, 'anchor_values': [str(x) for x in anchor_values],
        'priority_order': order, 'tree': tree,
        'dp_states': n * n, 'split_candidates': candidates,
        'scope': 'Complete even alternating equivalence path; deterministic zero-error, additive nonnegative costs.'
    }


def execute(policy, acquire):
    """Execute by relative equality only.

    acquire(record, None) buys the first anchor; its return is ignored.
    acquire(record, anchor) buys a record and returns a bool: equal to anchor.
    Any additional free equality observations may be ignored by this policy.
    The caller must ensure the actual world satisfies the source promise.
    """
    anchor = policy['anchor']
    acquire(anchor, None)
    acquired = [anchor]
    ranks = {q: i for i, q in enumerate(policy['priority_order'])}
    node = policy['tree']
    while 'query' in node:
        q = node['query']
        assert ranks[q] > ranks[acquired[-1]]
        same = acquire(q, anchor)
        if type(same) is not bool:
            raise TypeError('Acquisition must return bool equality to the anchor.')
        acquired.append(q)
        g = int(not same) ^ int(q < anchor)
        node = node['left'] if g else node['right']
    return {
        'label': node['label'], 'cut_edge': node['cut_edge'],
        'acquired': acquired,
        'cost': str(sum((Fraction(policy['prices'][q]) for q in acquired), Fraction(0)))
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('prices', nargs='+', help='Exact nonnegative record prices in physical order.')
    args = parser.parse_args()
    print(json.dumps(solve(args.prices), indent=2))
