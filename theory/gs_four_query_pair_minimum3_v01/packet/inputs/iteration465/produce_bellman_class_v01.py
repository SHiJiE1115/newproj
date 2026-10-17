"""Exact whole causal-SKIP class proof for one frozen source/fee/prior."""
from pathlib import Path
from fractions import Fraction as Q
from itertools import permutations
from functools import lru_cache
import sys

H=Path(__file__).resolve().parent
sys.path.insert(0,str(H))
from common_v01 import read,pin,save

source=read(H/'SOURCE1209_ORIGINAL_FAMILIES_V01.json')
cert=read(H/'TRIANGLE3_STRICT_GS_GAP_CANDIDATE_CERTIFICATE_V01.json')
assert read(H/'BELLMAN_CLASS_SCOPE_V01.json')['status']=='FROZEN_FIXED_SOURCE_CAUSAL_SKIP_BELLMAN_READER_BEFORE_EXECUTION'
W=[0,1,4,7,9,11,15];labels={w:int(bool(source['task'][1]>>w&1)) for w in W}
pi={w:Q(p) for w,p in zip(W,cert['P_prior_all7'])};fees=cert['all16_fees'];nodes=[];roots=[]
def value(x):return None if x is None else str(x)

for order in permutations(range(4)):
    @lru_cache(None)
    def visit(worlds,k,paid):
        state={'order':list(order),'worlds':list(worlds),'suffix_position':k,'paid_mask':paid}
        if not worlds or len({labels[w] for w in worlds})==1:
            idx=len(nodes);nodes.append(dict(state,kind='pure',value='0'));return Q(0),idx
        if k==4:
            idx=len(nodes);nodes.append(dict(state,kind='infeasible_mixed_terminal',value=None));return None,idx
        q=order[k];assert not(paid>>q&1)
        skip,skipid=visit(worlds,k+1,paid)
        branch=[];values=[]
        for bit in (0,1):
            v,i=visit(tuple(w for w in worlds if (w>>q&1)==bit),k+1,paid|1<<q)
            values.append(v);branch.append(i)
        increment=sum(pi[w] for w in worlds)*(fees[paid|1<<q]-fees[paid])
        assert increment>=0
        take=None if any(v is None for v in values) else increment+sum(values)
        options=[v for v in (skip,take) if v is not None]
        best=min(options) if options else None
        idx=len(nodes);nodes.append(dict(state,kind='choice',query=q,skip_child=skipid,take_children=branch,
            skip_value=value(skip),take_value=value(take),weighted_increment=str(increment),value=value(best)))
        return best,idx
    best,node=visit(tuple(W),0,0);assert best is not None
    roots.append({'order':list(order),'node':node,'Bayes_optimum':str(best)})
best=min(Q(r['Bayes_optimum']) for r in roots)
assert best==Q(1025,47)
save(H/'CAUSAL_SKIP_BELLMAN_PROOF_V01.json',{'schema':1,'status':'CANDIDATE_FULL24ORDER_CAUSAL_SKIP_BAYES_PROOF',
    'scope':pin(H/'BELLMAN_CLASS_SCOPE_V01.json'),'source':pin(H/'SOURCE1209_ORIGINAL_FAMILIES_V01.json'),
    'certificate':pin(H/'TRIANGLE3_STRICT_GS_GAP_CANDIDATE_CERTIFICATE_V01.json'),
    'prior_all7':cert['P_prior_all7'],'all16_fees':fees,'roots':roots,'nodes':nodes,'P_Bayes_exact':str(best),
    'zero_mass_worlds_correctness_not_removed':True,'cached_policy_families_not_used_by_recurrence':True,
    'no_new_fee_prior_point_or_grid_LP_globalcatalogue_model_API':True,'reader_required':True,'whole_project_complete':False})
print({'status':'CANDIDATE_FULL24ORDER_CAUSAL_SKIP_BAYES_PROOF','orders':24,'nodes':len(nodes),'P_Bayes_exact':str(best),
    'cached_policy_completeness_needed':False})
