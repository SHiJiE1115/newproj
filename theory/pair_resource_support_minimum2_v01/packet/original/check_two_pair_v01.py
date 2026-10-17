"""Check one frozen rational certificate against every retained original column."""
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path

H = Path(__file__).resolve().parent
B = H.parent
scopefile = H/'FROZEN_TWO_PAIR_CANDIDATE_V01.json'
raw = scopefile.read_bytes()
scope = json.loads(raw)
sourcefile = B/'iteration449/ORIGINAL_SOURCE1209_FAMILIES_V01.json'
assert hashlib.sha256(sourcefile.read_bytes()).hexdigest() == scope['source_sha256']
src = json.loads(sourcefile.read_text(encoding='utf-8'))
W = scope['W']
labels = {w: int(w in scope['W1']) for w in W}
assert src['task'] == [642,34833] and scope['A_P_counts'] == [40,32]
c = scope['individual_costs']
pairs = [(tuple(map(int,k.split(','))),v) for k,v in scope['pair_setup_weights'].items()]
assert len(pairs) == 2 and all(v > 0 for _,v in pairs)
F = [sum(c[q] for q in range(4) if s & (1<<q)) + sum(v for e,v in pairs if any(s & (1<<q) for q in e)) for s in range(16)]
assert F == scope['candidate_F_by_mask']
submod = [F[s]+F[t]-F[s|t]-F[s&t] for s in range(16) for t in range(16)]
marginals = [F[s|(1<<q)]-F[s] for s in range(16) for q in range(4) if not s & (1<<q)]
assert min(submod) == 0 and min(marginals) == 2 and F[0] == 0
assert min(F[1:]) > 0
profiles = {}
costs = {}
pathchecks = 0
for kind, count in [('A',40),('P',32)]:
    records = src['adaptive' if kind == 'A' else 'priority']
    assert len(records) == count
    profiles[kind] = []
    costs[kind] = []
    for col in records:
        profile = []
        for w in W:
            node, path = col['tree'], []
            while isinstance(node,list):
                q, low, high = node
                assert q in range(4) and q not in path
                path.append(q)
                node = high if (w>>q)&1 else low
            assert node == labels[w]
            paid = sum(1<<q for q in path)
            assert paid == col['sets'][w]
            if kind == 'P':
                assert sorted(col['order']) == [0,1,2,3]
                sequence = [col['order'].index(q) for q in path]
                assert sequence == sorted(sequence)
            profile.append(paid)
            pathchecks += 1
        profiles[kind].append(profile)
        costs[kind].append([F[s] for s in profile])
assert pathchecks == 504
assert all(p in profiles['A'] for p in profiles['P'])
for name, binding in scope['original_index_bindings'].items():
    for kind, index in binding.items():
        assert profiles[kind][index] == scope['profiles_on_W'][name]

certs = scope['certificates']
bad = []
results = {}
for kind in ('A','P'):
    anchor = Q(certs[kind+'_anchor'])
    mixture = {name:Q(v) for name,v in certs[kind+'_mix'].items()}
    prior = list(map(Q,certs[kind+'_dual_on_W']))
    assert all(v>=0 for v in mixture.values()) and sum(mixture.values()) == 1
    assert all(v>=0 for v in prior) and sum(prior) == 1
    upper = []
    for index,w in enumerate(W):
        value = sum(weight * costs[kind][scope['original_index_bindings'][name][kind]][index] for name,weight in mixture.items())
        upper.append({'word':w,'expected_fee':str(value),'slack':str(anchor-value)})
        if value > anchor:
            bad.append({'kind':kind,'upper_word':w,'value':str(value),'anchor':str(anchor)})
    lower = []
    for index,col in enumerate(costs[kind]):
        value = sum(prior[j]*fee for j,fee in enumerate(col))
        lower.append({'column':index,'prior_expected_fee':str(value),'slack':str(value-anchor)})
        if value < anchor:
            bad.append({'kind':kind,'lower_column':index,'value':str(value),'anchor':str(anchor)})
    results[kind] = {'anchor':str(anchor),'upper_on_all7':upper,'dual_lower_on_all_columns':lower,
                     'minimum_dual_slack':str(min(Q(r['slack']) for r in lower)),
                     'binding_columns':[r['column'] for r in lower if Q(r['slack']) == 0]}
gap = Q(certs['P_anchor'])-Q(certs['A_anchor'])
assert gap == Q(certs['gap']) == Q(3,232)
result = {
    'schema':1,'status':'PASS_FULL_ORIGINAL_CLASS_RATIONAL_PRIMAL_DUAL_CERTIFICATES' if not bad else 'FAIL_FROZEN_POINT_NOT_RETUNED',
    'scope_sha256':hashlib.sha256(raw).hexdigest(), 'source_sha256':scope['source_sha256'],
    'fee_by_mask':F,'positive_individual_costs':c,'positive_pair_groups':[[list(e),v] for e,v in pairs],
    'minimum_submodularity_slack':min(submod), 'minimum_proper_marginal':min(marginals),
    'strict_on_all_incomparable_pairs':False,
    'full_A_P_counts':[40,32],'all_correct_original_paths_checked':pathchecks,
    'results':results,'exact_gap':str(gap),'failed_bounds':bad,
    'completeness':'Same unchanged previously certified source1209 full monotone-cost families; no new policy catalogue',
    'number_of_candidate_fee_points':1,'new_LP_or_numeric_parameter_or_prior_grid':False,
    'zero_prior_worlds_retained_for_correctness':True,
    'separate_physical_source_DP_required':True,
    'not_global_all_source_lower_bound_or_external_human_review':True,
}
with (H/'TWO_PAIR_FULL_CLASS_RESULT_V01.json').open('x',encoding='utf-8') as f:
    json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'status':result['status'],'A':results['A']['anchor'],'P':results['P']['anchor'],'gap':str(gap),'bad':bad,'paths':pathchecks}))
if bad:
    raise SystemExit(1)
