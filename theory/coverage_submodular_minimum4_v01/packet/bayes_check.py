"""Transport adaptation of the accepted separate physical-source/Bayes checker."""

def run():
    """Separate fixed-prior recurrences; no retained family or candidate-result input."""
    from fractions import Fraction as Q
    from functools import lru_cache
    import hashlib
    import itertools
    import json
    from pathlib import Path
    H = Path(__file__).resolve().parent
    scope = json.loads((H / 'data/frozen_scope.json').read_text(encoding='utf-8'))
    coarsenings = [(0,0,0),(0,0,1),(0,1,0),(0,1,1),(0,1,2)]
    groups0 = [(0,1,2,4,6),(3,5),(7,)]
    groups1 = [(0,2,4,6),(1,3,7),(5,)]


    def source(groups, unequal):
        rows = []
        for pattern in coarsenings:
            classes = [None] * 8
            for i, group in enumerate(groups):
                for record in group:
                    assert classes[record] is None
                    classes[record] = pattern[i]
            if unequal and classes[3] == classes[7]:
                continue
            word = sum(int(classes[2*i] == classes[2*i+1]) << i for i in range(4))
            rows.append({'prior_block_coarsening': list(pattern), 'word': word})
        return rows


    physical0, physical1 = source(groups0, True), source(groups1, False)
    W0 = sorted({r['word'] for r in physical0})
    W1 = sorted({r['word'] for r in physical1})
    assert len(physical0) == 3 and len(physical1) == 5
    assert W0 == [1,7,9] and W1 == [0,4,11,15] and not set(W0) & set(W1)
    W = sorted(W0 + W1)
    labels = {w: int(w in W1) for w in W}
    # An independent direct resource representation, not the first checker's fee table.
    features = [(1,3),(2,1),(4,1),(8,1),(3,2),(5,1),(9,2),(6,4),(10,4),(12,4),(15,9)]
    fees = [sum(weight for group, weight in features if group & mask) for mask in range(16)]
    assert fees == scope['candidate_F_by_mask']
    assert all(weight > 0 for _, weight in features)
    submod_slacks = [fees[s] + fees[t] - fees[s | t] - fees[s & t] for s in range(16) for t in range(16)]
    assert min(submod_slacks) >= 0
    assert min(fees[s | (1 << q)] - fees[s] for s in range(16) for q in range(4) if not s & (1 << q)) == 1
    H1 = [v + i.bit_count() for i, v in enumerate(scope['old_F0'])]
    repair = [(7,5),(11,6),(13,5),(14,8)]
    assert all(fees[s] == H1[s] + sum(c for t, c in repair if t & s) for s in range(16))
    assert all(fees[s] == H1[s] + 24 for s in range(16) if s.bit_count() >= 2)
    onequery = {}
    for w in W:
        good = []
        for q in range(4):
            feasible = [v for v in W if ((v >> q) & 1) == ((w >> q) & 1)]
            if len({labels[v] for v in feasible}) == 1:
                good.append(q)
        onequery[w] = good
    assert onequery[0] == [0] and onequery[4] == [0]
    assert all(not onequery[w] for w in (7,9,11,15))

    u = [0,1,0]
    v = [1,1,0]
    z = [3,u,0]
    trees = {'a1':[1,u,[3,0,1]], 'a2':[3,u,[1,0,1]], 'a3':[2,[1,z,1],[3,v,1]],
             'p3':[2,[1,u,1],[3,v,1]], 'p4':[2,[1,z,1],[3,u,1]]}
    orders = {'a1':(1,0,2,3), 'a2':(2,3,0,1), 'p3':(2,3,1,0), 'p4':(2,1,3,0)}


    def trace_array(tree, w):
        path = []
        while isinstance(tree, list):
            q, low, high = tree
            assert q not in path
            path.append(q)
            tree = high if ((w >> q) & 1) else low
        return int(tree), path


    upper = {}
    for kind, target in [('A',Q(188,7)),('P',Q(242,9))]:
        records = []
        for w in W:
            value = Q(0)
            for name, weight in scope['candidate_certificates'][kind + '_mix'].items():
                output, path = trace_array(trees[name], w)
                assert output == labels[w] and len(path) >= 2
                if kind == 'P':
                    pos = {q:i for i,q in enumerate(orders[name])}
                    assert all(pos[a] < pos[b] for a,b in zip(path,path[1:]))
                paid = sum(1 << q for q in path)
                value += Q(weight) * fees[paid]
            assert value <= target
            records.append({'word':w,'cost':str(value)})
        assert max(Q(r['cost']) for r in records) == target
        upper[kind] = records

    root = (1 << len(W)) - 1
    positive = sum(1 << i for i,w in enumerate(W) if labels[w])
    one_answers = {q: sum(1 << i for i,w in enumerate(W) if (w >> q) & 1) for q in range(4)}


    def pure(state):
        if not state or not state & positive:
            return 0
        if state & positive == state:
            return 1
        return None


    def dual(kind):
        out = {w:Q(0) for w in W}
        out.update(zip((7,9,11,15), map(Q,scope['candidate_certificates'][kind + '_dual_on_7_9_11_15'])))
        assert sum(out.values()) == 1
        return out


    def masses(prior):
        @lru_cache(None)
        def mass(state):
            return sum(prior[w] for i,w in enumerate(W) if state & (1 << i))
        return mass


    priorA = dual('A')
    massA = masses(priorA)


    @lru_cache(None)
    def adaptive(state, paid):
        label = pure(state)
        if label is not None:
            return massA(state) * fees[paid], {'leaf':label}
        best, witness = None, None
        for q in range(4):
            if paid & (1 << q):
                continue
            high = state & one_answers[q]
            low = state ^ high
            a, left = adaptive(low, paid | (1 << q))
            b, right = adaptive(high, paid | (1 << q))
            value = a + b
            if best is None or value < best:
                best, witness = value, {'query':q,'zero':left,'one':right}
        assert best is not None
        return best, witness


    A_value, A_tree = adaptive(root, 0)
    assert A_value == Q(188,7)
    priorP = dual('P')
    massP = masses(priorP)
    P_orders = []
    bestP, P_tree, P_order = None, None, None
    for order in itertools.permutations(range(4)):
        @lru_cache(None)
        def priority(index, state, paid):
            label = pure(state)
            if label is not None:
                return massP(state) * fees[paid], {'leaf':label}
            if index == 4:
                return None, None  # Impure is illegal even when this state has zero mass.
            q = order[index]
            value, nextnode = priority(index + 1, state, paid)
            best = value
            witness = {'skip':q,'next':nextnode} if value is not None else None
            high = state & one_answers[q]
            low = state ^ high
            a, left = priority(index + 1, low, paid | (1 << q))
            b, right = priority(index + 1, high, paid | (1 << q))
            if a is not None and b is not None and (best is None or a+b < best):
                best, witness = a+b, {'query':q,'zero':left,'one':right}
            return best, witness
        value, tree = priority(0, root, 0)
        assert value is not None
        P_orders.append({'order':list(order),'Bayes_expected_cost':str(value),'states':priority.cache_info().currsize})
        if bestP is None or value < bestP:
            bestP, P_tree, P_order = value, tree, order
    assert len(P_orders) == 24 and bestP == Q(242,9)


    def trace_dict(tree, word):
        path = []
        while 'leaf' not in tree:
            if 'skip' in tree:
                tree = tree['next']
                continue
            q = tree['query']
            assert q not in path
            path.append(q)
            tree = tree['one'] if ((word >> q) & 1) else tree['zero']
        assert tree['leaf'] == labels[word]
        return path


    for w in W:
        trace_dict(A_tree,w)
        path = trace_dict(P_tree,w)
        position = {q:i for i,q in enumerate(P_order)}
        assert all(position[a] < position[b] for a,b in zip(path,path[1:]))
    result = {
        'schema':2,'status':'PASS_SEPARATE_PHYSICAL_SOURCE_AND_FIXED_PRIOR_FULL_ADAPTIVE_PRIORITY_DP',
        'scope_sha256':hashlib.sha256((H/'data/frozen_scope.json').read_bytes()).hexdigest(),
        'physical_negative_partitions':physical0,'physical_positive_partitions':physical1,
        'W0':W0,'W1':W1,'coverage_features':features,'fee':fees,
        'coverage_repair_triples':repair,'one_query_certificate_coordinates':onequery,
        'upper_mixture_costs_on_all7':upper,
        'A_fixed_dual_Bayes_value':str(A_value),'A_DP_states':adaptive.cache_info().currsize,'A_DP_witness':A_tree,
        'P_fixed_dual_Bayes_min_over24orders':str(bestP),'all24_original_Porder_results':P_orders,
        'best_Porder':list(P_order),'P_DP_witness':P_tree,
        'all7correctness_worlds_retained_in_every_DP_state':True,
        'zero_mass_impure_states_cannot_stop':True,
        'full_original_P_order_shared_across_both_branches_with_causal_permanent_skips':True,
        'exact_randomized_worst_input_A':'188/7','exact_randomized_worst_input_P':'242/9','exact_gap':'2/63',
        'proof_bridge':'Fixed-priorBayeslowerbounds+all-inputuppermixtures;noall-priorBayesequalityassumed',
        'retained_policy_matrix_or_main_candidate_result_read':False,
        'same_agent_separate_algorithm_not_external_human_review':True,
        'new_LP_model_calls_price_or_prior_or_policy_discovery_grid':False,
    }

    return result
