"""Unchanged exact coverage-certificate mathematics from the 263 checker.

Repackaging is not a third independent mathematical implementation.
Only selected source definitions and explicit stdlib dependencies are retained.
No historical main, file writer, machine-specific path, or producer is loaded.
"""
from fractions import Fraction
import hashlib
import json

ADAPTIVE = ((3, 5), (11, 28, 57, 105, 120), (11, 57, 60, 105),
            (19, 20), (28, 43, 57, 120), (35, 49, 52), (67, 84, 113))


PRIORITY = ((3, 5), (11, 28, 121), (11, 57, 60, 105),
            (19, 20), (35, 49, 52), (67, 84, 113))


SPECIAL = (ADAPTIVE[1], ADAPTIVE[4])


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate JSON key')
        result[key] = value
    return result


def decode(raw):
    return json.loads(raw, object_pairs_hook=no_duplicates,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSON')))


def coordinates(mask):
    require(type(mask) is int and 0 <= mask < 128, 'invalid coordinate mask')
    # Literal coordinate sets, rather than the producer's bitwise incidence.
    return frozenset(q for q in range(7) if (mask // (2 ** q)) % 2 == 1)


RESOURCES = tuple(coordinates(mask) for mask in range(1, 128))


def rational(value):
    require(type(value) is str and len(value) <= 128, 'rational must be a bounded string')
    x = Fraction(value)
    require(x.numerator.bit_length() <= 512 and x.denominator.bit_length() <= 512,
            'rational size exceeds verification cap')
    return x


def sparse(entries, dimension):
    require(type(entries) is list and len(entries) <= dimension, 'invalid sparse vector')
    output = [Fraction(0)] * dimension
    used = set()
    for entry in entries:
        require(type(entry) is list and len(entry) == 2, 'invalid sparse entry')
        i, text = entry
        require(type(i) is int and 0 <= i < dimension and i not in used, 'duplicate/out-of-range index')
        used.add(i)
        value = rational(text)
        require(value > 0, 'sparse entries must be positive')
        output[i] = value
    return output


def charge(paid, weights):
    return sum((w for resource, w in zip(RESOURCES, weights)
                if not resource.isdisjoint(paid)), Fraction(0))


def envelope_costs(envelopes, weights):
    return tuple(max(charge(coordinates(p), weights) for p in env) for env in envelopes)


def choice_from_serial(serial):
    require(type(serial) is int and 0 <= serial < 432, 'invalid branch serial')
    residual = serial
    choices = []
    for envelope in reversed(PRIORITY):
        residual, position = divmod(residual, len(envelope))
        choices.append(envelope[position])
    require(residual == 0, 'mixed-radix overflow')
    return tuple(reversed(choices))


def verify_lp(envelope, selected, primal, dual, objective):
    """Reconstruct max t, C_E(w)<=1, t<=C_selected(w), w,t>=0.

    Dual u,v>=0: sum u_j I(R intersects E_j) >=
    sum v_k I(R intersects selected_k), sum v_k>=1; minimize sum u.
    No floating coefficients or approximate tolerances occur here.
    """
    x = sparse(primal, 128)
    y = sparse(dual, len(envelope) + len(selected))
    weights, t = x[:127], x[127]
    upper_paths = tuple(coordinates(s) for s in envelope)
    lower_paths = tuple(coordinates(s) for s in selected)
    for paid in upper_paths:
        require(charge(paid, weights) <= 1, 'primal adaptive normalization fails')
    for paid in lower_paths:
        require(t <= charge(paid, weights), 'primal selected-path bound fails')
    u, v = y[:len(envelope)], y[len(envelope):]
    for resource in RESOURCES:
        positive = sum((weight for paid, weight in zip(upper_paths, u)
                        if not resource.isdisjoint(paid)), Fraction(0))
        negative = sum((weight for paid, weight in zip(lower_paths, v)
                        if not resource.isdisjoint(paid)), Fraction(0))
        require(positive >= negative, 'dual resource column fails')
    require(sum(v) >= 1, 'dual t column fails for nonnegative t')
    dual_value = sum(u)
    require(t == dual_value == rational(objective), 'exact primal/dual objectives differ')
    return t, weights


def validate_record(row):
    require(type(row) is dict and set(row) == {
        'kind', 'serial', 'selected_priority_paths', 'primal', 'dual', 'objective'}, 'record schema differs')
    kind = row['kind']
    require(type(kind) is int and kind in (0, 1), 'invalid envelope kind')
    selected = choice_from_serial(row['serial'])
    require(type(row['selected_priority_paths']) is list and
            all(type(x) is int for x in row['selected_priority_paths']) and
            tuple(row['selected_priority_paths']) == selected, 'branch path/serial disagreement')
    value, weights = verify_lp(SPECIAL[kind], selected, row['primal'], row['dual'], row['objective'])
    return (kind, row['serial']), value, weights


def full_coverage(keys):
    require(len(keys) == 864 and len(set(keys)) == 864, 'missing or duplicate LP records')
    require(set(keys) == {(kind, serial) for kind in (0, 1) for serial in range(432)},
            'LP branch coverage differs')
    # Distinct serials must cover exactly the Cartesian path choices.
    expected = {()}
    for envelope in PRIORITY:
        expected = {prefix + (path,) for prefix in expected for path in envelope}
    require(len(expected) == 432 and {choice_from_serial(i) for i in range(432)} == expected,
            'mixed-radix path enumeration is incomplete')


def controls():
    passed = []
    primal = [[0, '1'], [127, '1']]
    dual = [[0, '1'], [1, '1']]
    require(verify_lp((1,), (1,), primal, dual, '1')[0] == 1, 'valid exact toy rejected')
    passed.append('valid_exact_one_resource_LP')
    invalid = [
        ('negative_primal', [[0, '-1']], dual, '1'),
        ('duplicate_sparse_index', [[0, '1'], [0, '1']], dual, '1'),
        ('primal_normalization', [[0, '2'], [127, '2']], [[0, '2'], [1, '2']], '2'),
        ('primal_selected_path', [[0, '1/2'], [127, '1']], dual, '1'),
        ('negative_dual', primal, [[0, '-1'], [1, '1']], '1'),
        ('dual_resource', primal, [[0, '1/2'], [1, '1']], '1'),
        ('dual_t_column', primal, [[0, '1/2'], [1, '1/2']], '1'),
        ('objective_mismatch', primal, dual, '2'),
    ]
    for name, p, d, objective in invalid:
        try:
            verify_lp((1,), (1,), p, d, objective)
        except (ValueError, ZeroDivisionError):
            passed.append(name + '_rejected')
        else:
            raise ValueError('invalid control accepted: ' + name)
    keys = [(k, s) for k in (0, 1) for s in range(432)]
    full_coverage(keys)
    passed.append('complete_cartesian_branch_map')
    for name, bad in [('missing_branch', keys[:-1]), ('duplicate_branch', keys[:-1] + [keys[0]])]:
        try:
            full_coverage(bad)
        except ValueError:
            passed.append(name + '_rejected')
        else:
            raise ValueError('invalid branch coverage accepted')
    return passed

