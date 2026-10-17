"""One fixed source completeness dependency, using symbolic paid-set profiles only."""
from functools import lru_cache
import hashlib
from itertools import permutations
import json
from pathlib import Path
import time

H=Path(__file__).resolve().parent
source=H.parent/'iteration449/ORIGINAL_SOURCE1209_FAMILIES_V01.json'
raw=source.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='03d5f73f832bf7888a61c75ddd761704dab14ed3fbafe99f65dc6347d9f706ad'
src=json.loads(raw)
assert src['task']==[642,34833]
W0=[w for w in range(16) if src['task'][0]&(1<<w)]
W1=[w for w in range(16) if src['task'][1]&(1<<w)]
assert W0==[1,7,9] and W1==[0,4,11,15]
W=sorted(W0+W1)
root=(1<<len(W))-1
positive=sum(1<<i for i,w in enumerate(W) if w in W1)
highs={q:sum(1<<i for i,w in enumerate(W) if (w>>q)&1) for q in range(4)}
zero=(0,)*len(W)
stats={'candidate_profiles':0,'subset_pair_checks':0,'max_frontier':0}
deadline=time.monotonic()+20


def pure(state):
    return not state or not state&positive or state&positive==state


def prune(profiles):
    candidates=sorted(set(profiles),key=lambda v:(sum(x.bit_count() for x in v),v))
    stats['candidate_profiles']+=len(candidates)
    assert stats['candidate_profiles']<=100000 and time.monotonic()<=deadline
    kept=[]
    for vector in candidates:
        redundant=False
        for by in kept:
            stats['subset_pair_checks']+=1
            assert stats['subset_pair_checks']<=2000000
            if all((a&b)==a for a,b in zip(by,vector)):
                redundant=True;break
        if not redundant:kept.append(vector)
    stats['max_frontier']=max(stats['max_frontier'],len(kept))
    return tuple(sorted(kept))


def joined(q,state,left,right):
    return tuple((left[i]|right[i]|(1<<q)) if state&(1<<i) else 0 for i in range(7))


@lru_cache(None)
def adaptive(state,available):
    if pure(state):return (zero,)
    generated=[]
    for q in range(4):
        if not available&(1<<q):continue
        hi=state&highs[q];lo=state^hi
        if not hi or not lo:continue # A known-answer purchase is subset-dominated.
        for left in adaptive(lo,available^(1<<q)):
            for right in adaptive(hi,available^(1<<q)):
                generated.append(joined(q,state,left,right))
    assert generated
    return prune(generated)


@lru_cache(None)
def priority(order,index,state):
    if pure(state):return (zero,)
    if index==4:return ()
    q=order[index]
    generated=list(priority(order,index+1,state)) # Causal permanent SKIP.
    hi=state&highs[q];lo=state^hi
    if hi and lo:
        for left in priority(order,index+1,lo):
            for right in priority(order,index+1,hi):
                generated.append(joined(q,state,left,right))
    return prune(generated)


A=adaptive(root,15)
orders=[];allP=[]
for order in permutations(range(4)):
    profiles=priority(order,0,root)
    assert profiles
    orders.append({'order':list(order),'minimal_profiles':[list(v) for v in profiles]})
    allP.extend(profiles)
P=prune(allP)
expectedA=tuple(sorted(tuple(row['sets'][w] for w in W) for row in src['adaptive']))
expectedP=tuple(sorted(tuple(row['sets'][w] for w in W) for row in src['priority']))
assert len(expectedA)==40 and len(expectedP)==32
assert A==prune(expectedA) and P==prune(expectedP)
assert all(v in expectedA for v in A) and all(v in expectedP for v in P)
def subset(a,b):return all((x&y)==x for x,y in zip(a,b))
assert all(any(subset(a,v) for a in A) for v in expectedA)
assert all(any(subset(p,v) for p in P) for v in expectedP)
checked_paths=0
for kind in ('adaptive','priority'):
    for column in src[kind]:
        for word in W:
            node=column['tree'];path=[]
            while isinstance(node,list):
                q,low,high=node
                assert q in range(4) and q not in path
                path.append(q);node=high if (word>>q)&1 else low
            assert node==int(word in W1)
            assert sum(1<<q for q in path)==column['sets'][word]
            if kind=='priority':
                positions=[column['order'].index(q) for q in path]
                assert sorted(column['order'])==[0,1,2,3] and positions==sorted(positions)
            checked_paths+=1
assert checked_paths==504
assert all(p in A for p in P)
result={'schema':1,'status':'PASS_ONE_FIXED_SOURCE_FULL_ADAPTIVE_AND_ALL24_CAUSAL_SKIP_PRIORITY_PROFILE_COMPLETENESS',
        'source_sha256':hashlib.sha256(raw).hexdigest(),'W0':W0,'W1':W1,'W':W,
        'A_profiles':[list(v) for v in A],'P_profiles':[list(v) for v in P],
        'A_count':40,'P_count':32,'A_minimal_count':len(A),'P_minimal_count':len(P),'all24_order_profile_sets':orders,
        'original_A_to_minimal_subset_index':[next(i for i,a in enumerate(A) if subset(a,v)) for v in expectedA],
        'original_P_to_minimal_subset_index':[next(i for i,p in enumerate(P) if subset(p,v)) for v in expectedP],
        'all_original_paths_checked':checked_paths,
        'adaptive_feasible_state_count':adaptive.cache_info().currsize,'priority_feasible_state_count':priority.cache_info().currsize,
        'stats':stats,'all_reconstructed_minimal_profiles_and_reduced_original_profile_cells_match':True,
        'every_original_profile_has_reconstructed_subset':True,
        'original_families_are_complete_but_not_claimed_minimal':True,
        'completeness_argument':'Induct on remaining queries/order positions. Pure states stop; repeated/known-answer purchases are subset-dominated. At each adaptive mixed state exhaust every informative first query and both independently legal continuations. At each fixed-order state exhaust SKIP and TAKE with the same suffix in both branches. Pointwise subset-antichain pruning is valid under every common paid context and monotone final-set fee. Union all24orders, then prune. Every zero-error deterministic seed is dominated by one retained profile; each frozen retained profile has its original legal tree/order witness. Private mixtures inherit the pointwise domination.',
        'scope':'Only the fixed seven-word source1209; no global catalogue or fee/prior optimization',
        'new_scientific_fee_or_prior_candidates':0,'same_agent_dependency_check_not_human_or_formal_kernel':True}
with (H/'SOURCE_COMPLETENESS_RESULT.json').open('x',encoding='utf-8') as f:
    json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'status':result['status'],'original_A':40,'original_P':32,'minimal_A':len(A),'minimal_P':len(P),'orders':24,'stats':stats}))
