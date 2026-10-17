"""Physical-source fixed-prior recurrences; reads no policy matrix or main result."""
from fractions import Fraction as Q
from functools import lru_cache
from itertools import permutations
import hashlib
import json
from pathlib import Path
import sys

H = Path(__file__).resolve().parent
B = H.parent
scopefile = H/'FROZEN_TWO_PAIR_CANDIDATE_V01.json'
project_reads = []


def audit(event, args):
    if event != 'open' or not isinstance(args[0],str):
        return
    mode = args[1]
    if mode is not None and any(s in mode for s in 'wax'):
        return
    path = Path(args[0]).resolve()
    if str(path).casefold().startswith(str(B).casefold()):
        assert path == scopefile
        project_reads.append(str(path))


sys.addaudithook(audit)
raw = scopefile.read_bytes()
assert hashlib.sha256(raw).hexdigest() == 'dbd1a77d661a0af9e369e27b22ee5523edf9f12a5c4f9bf0c3b24b400e715487'
scope = json.loads(raw)
partitions = []
for label, groups in enumerate([[(0,1,2,4,6),(3,5),(7,)], [(0,2,4,6),(1,3,7),(5,)]]):
    values = []
    for pattern in [(0,0,0),(0,0,1),(0,1,0),(0,1,1),(0,1,2)]:
        classes = [None]*8
        for index, group in enumerate(groups):
            for record in group:
                assert classes[record] is None
                classes[record] = pattern[index]
        if label == 0 and classes[3] == classes[7]:
            continue
        word = sum((classes[2*q] == classes[2*q+1]) << q for q in range(4))
        values.append({'partition':classes,'coarsening':list(pattern),'word':word})
    partitions.append(values)
assert [len(v) for v in partitions] == [3,5]
W0,W1 = [sorted({v['word'] for v in values}) for values in partitions]
assert W0 == [1,7,9] and W1 == [0,4,11,15]
W = sorted(W0+W1)
assert W == scope['W']
labels = {w:int(w in W1) for w in W}
features = [(1,4),(2,3),(4,2),(8,3),(6,2),(12,2)]
fees = [sum(v for resource,v in features if resource&s) for s in range(16)]
assert fees == scope['candidate_F_by_mask']
assert all(v>0 for _,v in features)
cert = scope['certificates']
u,v = [0,1,0],[1,1,0]
z = [3,u,0]
trees = {'a1':[1,u,[3,0,1]], 'a2':[3,u,[1,0,1]],
         'a3':[2,[1,z,1],[3,v,1]], 'p3':[2,[1,u,1],[3,v,1]],
         'p4':[2,[1,z,1],[3,u,1]]}
orders = {'a1':(1,0,2,3),'a2':(2,3,0,1),'p3':(2,3,1,0),'p4':(2,1,3,0)}


def array_path(tree, word):
    bought = []
    while isinstance(tree,list):
        q, low, high = tree
        assert q not in bought
        bought.append(q)
        tree = high if ((word>>q)&1) else low
    assert tree == labels[word]
    return bought


upper = {}
for kind in ('A','P'):
    mixed = {name:Q(weight) for name,weight in cert[kind+'_mix'].items()}
    assert all(v>=0 for v in mixed.values()) and sum(mixed.values()) == 1
    bound = Q(cert[kind+'_anchor'])
    values = []
    for index,word in enumerate(W):
        value = Q(0)
        for name,weight in mixed.items():
            path = array_path(trees[name],word)
            assert sum(1<<q for q in path) == scope['profiles_on_W'][name][index]
            if kind == 'P':
                positions = [orders[name].index(q) for q in path]
                assert positions == sorted(positions)
            value += weight * fees[sum(1<<q for q in path)]
        assert value <= bound
        values.append({'word':word,'fee':str(value)})
    assert max(Q(row['fee']) for row in values) == bound
    upper[kind] = values

root = (1<<len(W))-1
positive = sum(1<<i for i,w in enumerate(W) if labels[w])
highs = {q:sum(1<<i for i,w in enumerate(W) if (w>>q)&1) for q in range(4)}


def leaf_label(state):
    if not state or not state&positive:
        return 0
    if state&positive == state:
        return 1
    return None


def mass_function(prior):
    assert all(v>=0 for v in prior) and sum(prior) == 1
    @lru_cache(None)
    def mass(state):
        return sum(prior[i] for i in range(7) if state&(1<<i))
    return mass


massA = mass_function(list(map(Q,cert['A_dual_on_W'])))


@lru_cache(None)
def adaptive(state, paid):
    label = leaf_label(state)
    if label is not None:
        return massA(state)*fees[paid], {'leaf':label}
    best, witness = None, None
    for q in range(4):
        if paid&(1<<q):
            continue
        hi = state&highs[q]
        lo = state^hi
        a,left = adaptive(lo,paid|(1<<q))
        b,right = adaptive(hi,paid|(1<<q))
        if best is None or a+b<best:
            best, witness = a+b, {'q':q,'zero':left,'one':right}
    assert best is not None
    return best,witness


A_value,A_tree = adaptive(root,0)
massP = mass_function(list(map(Q,cert['P_dual_on_W'])))
allorders = []
bestP,P_tree,P_order = None,None,None
for order in permutations(range(4)):
    @lru_cache(None)
    def priority(index,state,paid):
        label = leaf_label(state)
        if label is not None:
            return massP(state)*fees[paid], {'leaf':label}
        if index == 4:
            return None,None  # Impure zero-mass states still cannot stop.
        q = order[index]
        skip,nextnode = priority(index+1,state,paid)
        best = skip
        witness = {'skip':q,'next':nextnode} if skip is not None else None
        hi = state&highs[q]
        lo = state^hi
        a,left = priority(index+1,lo,paid|(1<<q))
        b,right = priority(index+1,hi,paid|(1<<q))
        if a is not None and b is not None and (best is None or a+b<best):
            best,witness = a+b, {'q':q,'zero':left,'one':right}
        return best,witness
    value,tree = priority(0,root,0)
    assert value is not None
    allorders.append({'order':list(order),'fixed_prior_Bayes':str(value),'states':priority.cache_info().currsize})
    if bestP is None or value<bestP:
        bestP,P_tree,P_order = value,tree,order
assert len(allorders) == 24


def dictionary_path(tree,word):
    path = []
    while 'leaf' not in tree:
        if 'skip' in tree:
            tree = tree['next']
            continue
        q = tree['q']
        assert q not in path
        path.append(q)
        tree = tree['one'] if (word>>q)&1 else tree['zero']
    assert tree['leaf'] == labels[word]
    return path


for word in W:
    dictionary_path(A_tree,word)
    pos = [P_order.index(q) for q in dictionary_path(P_tree,word)]
    assert pos == sorted(pos)
bad = []
if A_value != Q(cert['A_anchor']):
    bad.append({'A_fixed_prior_value':str(A_value),'expected':cert['A_anchor']})
if bestP != Q(cert['P_anchor']):
    bad.append({'P_fixed_prior_value':str(bestP),'expected':cert['P_anchor']})
assert set(project_reads) == {str(scopefile)}
result = {
    'schema':1,'status':'PASS_SEPARATE_PHYSICAL_SOURCE_AND_FIXED_PRIOR_FULL_DP' if not bad else 'FAIL_FROZEN_POINT_NOT_RETUNED',
    'scope_sha256':hashlib.sha256(raw).hexdigest(), 'physical_partitions':partitions,
    'W0':W0,'W1':W1,'coverage_features':features,'fee':fees,
    'upper_on_all7':upper,'A_fixed_dual_Bayes_value':str(A_value),'A_DP_states':adaptive.cache_info().currsize,
    'A_DP_witness':A_tree,'P_fixed_dual_min_over24orders':str(bestP),'all24_original_Porder_results':allorders,
    'P_DP_witness':P_tree,'best_Porder':list(P_order),'failed_checks':bad,
    'exact_randomized_worst_input_A':str(A_value) if not bad else None,
    'exact_randomized_worst_input_P':str(bestP) if not bad else None,
    'exact_gap':str(bestP-A_value) if not bad else None,
    'all7correctness_worlds_retained_in_every_DP_state':True,
    'zero_mass_impure_states_cannot_stop':True,
    'one_global_order_per_seed_shared_branches_and_permanent_causal_skip':True,
    'DP_project_input_read_audit':{'unique_read_files':sorted(set(project_reads)),
                                'policy_catalogue_main_result_or_producer_read':False},
    'proof_bridge':'Fixed-prior Bayes lower bounds plus all-input upper mixtures; no all-prior equality claim',
    'same_agent_separate_algorithm_not_external_human_or_formal_kernel':True,
    'new_model_API_LP_price_prior_policy_grid':False,
}
with (H/'TWO_PAIR_SEPARATE_DP_RESULT_V01.json').open('x',encoding='utf-8') as f:
    json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'status':result['status'],'A':str(A_value),'P':str(bestP),'gap':str(bestP-A_value),'orders':24,'input_files':sorted(set(project_reads)),'bad':bad}))
if bad:
    raise SystemExit(1)
