"""Transport adaptation of the accepted full-column checker; math core unchanged."""

def run():
    """One fixed coverage fee and already-derived exact rational certificates."""
    from fractions import Fraction as Q
    import gzip
    import hashlib
    import itertools
    import json
    from pathlib import Path
    H = Path(__file__).resolve().parent


    def load(p):
        return json.loads(Path(p).read_text(encoding='utf-8'))


    def pin(p):
        p = Path(p)
        raw = p.read_bytes()
        return {'path': p.relative_to(H).as_posix(), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


    scope = load(H / 'data/frozen_scope.json')
    data = H / 'data/source1209.json.gz'
    assert pin(data)['sha256'] == 'de2f8a28f9efdf058f6b775ec6d7a8e95a14c1de3fedb1619594452af087029d'
    raw = gzip.decompress(data.read_bytes())
    assert hashlib.sha256(raw).hexdigest() == '03d5f73f832bf7888a61c75ddd761704dab14ed3fbafe99f65dc6347d9f706ad'
    record = json.loads(raw)
    assert record['task'] == scope['source']['task_masks'] == [642, 34833]
    assert len(record['adaptive']) == 40 and len(record['priority']) == 32
    W = scope['source']['input_order']
    labels = {w: int((record['task'][1] >> w) & 1) for w in W}
    assert {w for w in W if labels[w] == 0} == set(scope['source']['W0'])
    assert {w for w in W if labels[w] == 1} == set(scope['source']['W1'])
    F = []
    for mask in range(16):
        value = sum(scope['individual_costs'][i] for i in range(4) if mask & (1 << i))
        value += scope['global_setup'] * int(mask != 0)
        for pair, weight in scope['pair_setup_weights'].items():
            i, j = map(int, pair.split(','))
            value += weight * int(bool(mask & ((1 << i) | (1 << j))))
        F.append(value)
    assert F == scope['candidate_F_by_mask']
    assert F[0] == 0 and all(v >= 0 for v in F)
    submod = [{'S': s, 'T': t, 'slack': F[s] + F[t] - F[s | t] - F[s & t]}
              for s in range(16) for t in range(16)]
    mono = [{'S': s, 'q': q, 'increment': F[s | (1 << q)] - F[s], 'proper': not bool(s & (1 << q))}
            for s in range(16) for q in range(4)]
    badfee = [r for r in submod if r['slack'] < 0] + [r for r in mono if r['increment'] < 0]
    strict = min(r['increment'] for r in mono if r['proper'])
    transfer = []
    for mask in range(16):
        if mask.bit_count() >= 2:
            assert F[mask] == 24 + scope['old_F0'][mask] + mask.bit_count()
            transfer.append(mask)


    def trace(tree, word):
        path = []
        while isinstance(tree, list):
            assert len(tree) == 3
            q, low, high = tree
            assert q in range(4) and q not in path
            path.append(q)
            tree = high if (word >> q) & 1 else low
        return int(tree), path


    traced = 0
    for kind, count in [('adaptive', 40), ('priority', 32)]:
        assert len(record[kind]) == count
        for col in record[kind]:
            assert len(col['sets']) == 16
            if kind == 'priority':
                assert sorted(col['order']) == list(range(4))
            for w in W:
                label, path = trace(col['tree'], w)
                assert label == labels[w]
                paid = sum(1 << q for q in path)
                assert paid == col['sets'][w]
                if kind == 'priority':
                    pos = {q: k for k, q in enumerate(col['order'])}
                    assert all(pos[a] < pos[b] for a, b in zip(path, path[1:]))
                traced += 1
    assert traced == 504
    bindings = {}
    for name, profile in scope['profiles_on_input_order'].items():
        matched = {}
        for kind in ('adaptive', 'priority'):
            matches = [i for i, col in enumerate(record[kind]) if [col['sets'][w] for w in W] == profile]
            if matches:
                assert len(matches) == 1
                matched[kind] = matches[0]
        assert 'adaptive' in matched
        if name != 'a3':
            assert 'priority' in matched
        bindings[name] = matched
    coeff = scope['candidate_certificates']
    A_value = Q(coeff['A_anchor'])
    P_value = Q(coeff['P_anchor'])
    hard = (7, 9, 11, 15)
    priors = {}
    for kind in ('A', 'P'):
        priors[kind] = {w: Q(0) for w in W}
        priors[kind].update(zip(hard, map(Q, coeff[kind + '_dual_on_7_9_11_15'])))
        assert sum(priors[kind].values()) == 1
    for w in hard:
        # Every possible one-query transcript at w has an opposite-label input.
        for q in range(4):
            assert any(labels[v] != labels[w] and ((v >> q) & 1) == ((w >> q) & 1) for v in W)
    mixes = {}
    for kind, family, anchor in [('A', 'adaptive', A_value), ('P', 'priority', P_value)]:
        mixture = coeff[kind + '_mix']
        assert sum(map(Q, mixture.values())) == 1
        perinput = []
        for w in W:
            value = sum(Q(weight) * F[record[family][bindings[name][family]]['sets'][w]] for name, weight in mixture.items())
            perinput.append({'word': w, 'cost': str(value), 'anchor_slack': str(anchor - value)})
        mixes[kind] = perinput
    duals = {}
    for kind, family, anchor in [('A', 'adaptive', A_value), ('P', 'priority', P_value)]:
        columns = []
        for i, col in enumerate(record[family]):
            value = sum(priors[kind][w] * F[col['sets'][w]] for w in W)
            columns.append({'column': i, 'expected_cost': str(value), 'anchor_slack': str(value - anchor)})
        duals[kind] = columns
    A_upper = all(Q(r['anchor_slack']) >= 0 for r in mixes['A'])
    P_upper = all(Q(r['anchor_slack']) >= 0 for r in mixes['P'])
    A_lower = all(Q(r['anchor_slack']) >= 0 for r in duals['A'])
    P_lower = all(Q(r['anchor_slack']) >= 0 for r in duals['P'])
    primary = not badfee and strict > 0 and A_upper and P_lower and P_value > A_value
    exact = primary and A_lower and P_upper
    selected = {}
    for name, binding in bindings.items():
        selected[name] = {kind: {'index': i, **record[kind][i]} for kind, i in binding.items()}
    result = {
        'schema': 2, 'status': 'PASS_EXACT_COVERAGE_COUNTEREXAMPLE_ALL_ORIGINAL_FULL_CLASSES' if exact else 'COMPLETED_FIXED_CANDIDATE_CHECK_WITH_UNPASSED_OBLIGATIONS',
        'scope': pin(H / 'data/frozen_scope.json'), 'input_families': pin(data),
        'task': record['task'], 'W': W, 'labels': labels, 'full_class_counts': [40,32], 'physical_orbit_members': len(record['orbit_members']),
        'fee': F, 'fee_class': 'Weightedcoveragewithstrictlypositiveindividualquerychargesandnonnegativepair/globalsetupweights',
        'all256_submodular_slacks': submod, 'all64_query_addition_checks': mono,
        'strict_proper_increment_min': strict, 'positive_nonempty_fee_min': min(F[1:]),
        'fee_failures': badfee, 'transfer_identity_on_masks': transfer,
        'some_zero_prior_worlds_may_have_one_query_certificates': True,
        'hard_prior_support_has_no_one_query_certificate': True,
        'all504_original_policy_input_paths_correct_and_P_orders_legal': True,
        'selected_profiles': selected, 'mixture_input_costs': mixes, 'dual_all_original_columns': duals,
        'A_upper_valid': A_upper, 'P_lower_valid': P_lower, 'A_lower_valid': A_lower, 'P_upper_valid': P_upper,
        'primary_strict_gap_certified': primary, 'both_exact_values_certified': exact,
        'A_anchor': str(A_value), 'P_anchor': str(P_value), 'gap': str(P_value - A_value),
        'complete_full_family_scope': 'Inheritedaccepted378/441normalform/pointwise-monotonecoverage;thisfixedrowpaths/fees/dual/primalfreshlychecked',
        'new_grid_LP_model_hosted_or_human_review': False,
        'literature_priority_or_natural_gain_established': False,
        'unexecuted_V01_curvature_point_not_used_for_result_selection': True,
    }

    return result
