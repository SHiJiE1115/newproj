"""Check fee-class compatibility and independently recalculate the inherited exact upper witness."""
from fractions import Fraction as Q
from itertools import combinations
import hashlib
import json
from pathlib import Path

H=Path(__file__).resolve().parent
B=H.parent


def load(p):return json.loads(Path(p).read_text(encoding='utf-8'))


def pin(p):
    p=Path(p);raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


g=load(H/'GLOBAL_PAIR_SUPPORT_MINIMUM2_RESULT_V01.json')
assert g['status']=='PASS_INTERNAL_COMPUTER_ASSISTED_ALL_COMPLETE_FOUR_QUERY_ONE_PAIR_EQUALITY_AND_MINIMUM_POSITIVE_PAIR_SUPPORT2'
assert load(H/'COMPOSE_GLOBAL_V03.PROCESS_TERMINAL.json')['actual_exit_code']==0
assert g['source_cover']['inherited_monotone_closed_orbits']+g['source_cover']['one_pair_residual_orbits']==1356
assert g['residual_cones']==1584 and g['residual_counts']['nodes']==1776
checks=0
for pair in combinations(range(4),2):
    edge=sum(1<<q for q in pair)
    coefficients=[[int(mask>>q&1) for q in range(4)]+[int(bool(mask&edge))] for mask in range(16)]
    assert coefficients[0]==[0]*5
    for smaller in range(16):
        for larger in range(16):
            if smaller!=larger and smaller&larger==smaller:
                assert all(x<=y for x,y in zip(coefficients[smaller],coefficients[larger]))
                checks+=1
assert checks==390
source=load(B/'iteration449/ORIGINAL_SOURCE1209_FAMILIES_V01.json')
assert source['task']==[642,34833]
W=sorted(w for w in range(16) if (source['task'][0]|source['task'][1])>>w&1)
assert W==[0,1,4,7,9,11,15]
c=(4,3,2,3);groups=(((1,2),2),((2,3),2))
fees={mask:sum(c[i] for i in range(4) if mask>>i&1)+sum(w for group,w in groups if any(mask>>i&1 for i in group)) for mask in range(16)}
A=[[fees[col['sets'][w]] for w in W] for col in source['adaptive']]
P=[[fees[col['sets'][w]] for w in W] for col in source['priority']]
assert len(A)==40 and len(P)==32
mixA={6:Q(13,29),21:Q(12,29),39:Q(3,29),20:Q(1,29)}
mixP={6:Q(7,16),19:Q(7,16),18:Q(1,16),30:Q(1,16)}
priorA=[Q(x,29) for x in (0,1,0,3,3,11,11)]
priorP=[Q(x,8) for x in (0,0,0,1,1,3,3)]
assert sum(mixA.values())==sum(mixP.values())==sum(priorA)==sum(priorP)==1
upperA=[sum(weight*A[col][w] for col,weight in mixA.items()) for w in range(7)]
upperP=[sum(weight*P[col][w] for col,weight in mixP.items()) for w in range(7)]
lowerA=[sum(x*y for x,y in zip(priorA,col)) for col in A]
lowerP=[sum(x*y for x,y in zip(priorP,col)) for col in P]
assert max(upperA)==min(lowerA)==Q(286,29)
assert max(upperP)==min(lowerP)==Q(79,8)
assert min(lowerP)-max(upperA)==Q(3,232)
assert upperA==[Q(x,29) for x in (286,286,273,286,286,286,286)]
assert upperP==[Q(x,16) for x in (155,155,151,158,158,158,158)]
assert all(v>=Q(286,29) for v in lowerA) and all(v>=Q(79,8) for v in lowerP)
assert len({tuple(group) for group,w in groups if w>0})==2 and all(x>0 for x in c)
r=Q(1,1856)
assert 6*r==Q(3,928) and Q(3,232)-12*r==Q(3,464)>0
assert min(c)-r>0 and 2-r>0
argument={
 'source_reduction':'Query-only observations and final paid-set fees depend only on the projected word and label. Physical sources with the same disjoint label supports induce the same two finite games.',
 'majority_fee_premise':'Each coefficient of F(T)-F(S) is nonnegative for S subset T,for all6pairs and65proper subset inclusions;F(empty)=0. Thus the1345inherited ALLmonotone proofs apply to the entire continuous one-pair fee family.',
 'symmetry':'The source audit maps the physical query labels,prices,activation pair,tree nodes,globalorder and terminal labels bijectively;support size and private seed independence preserved. No literal answer complement symmetry is assumed.',
 'normalization':'Known-answer/repeated/postpure purchases can be removed under monotone final-set fees. Source-specific symbolic antichain pruning remains valid under common previously purchased contexts. All old full columns remain legal and retained,including zero-prior correctness worlds.',
 'padding':'A fresh dummy query forcedDIFFERENT under both labels has constant answer0. Give it zero individual charge and no membership in any positive pair group. Fresh classes extend each old physical world under the unrestricted class-count model. Remove dummy purchases from each adaptive tree and per-seed priority order;cost and zero-error observations are unchanged. Thus every smaller-menu counterexample would yield a four-query counterexample.',
 'exact_minimum':'Universal support<=1exclusion plus the explicit support2positive-individual-charge witness gives g4(nonnegative)=g4(positive)=2. No perturbation lemma is needed to equate these two minima.',
 'not_implied':'No bound for all larger menus or arbitrary-size setup groups;no exact first additive gap between5and7;no general classification of every four-query submodular cost;no real academic-evaluation benefit or literature priority.'}
result={'schema':1,'status':'PASS_SEPARATE_GLOBAL_SCOPE_PREMISE_AND_EXACT_POSITIVE_TWO_PAIR_WITNESS_RECALCULATION',
 'global_result':pin(H/'GLOBAL_PAIR_SUPPORT_MINIMUM2_RESULT_V01.json'),
 'formal_monotone_coefficient_checks':checks,'sampled_minimax_games':0,'new_fee_or_prior_candidates':0,
 'original_upper_witness_source':pin(B/'iteration449/ORIGINAL_SOURCE1209_FAMILIES_V01.json'),
 'fixed_old_individual_charges':list(c),'fixed_old_pair_groups':[[list(e),w] for e,w in groups],
 'A_upper_costs':[str(x) for x in upperA],'P_upper_costs':[str(x) for x in upperP],
 'A_dual_slacks_all40':[str(x-Q(286,29)) for x in lowerA],
 'P_dual_slacks_all32':[str(x-Q(79,8)) for x in lowerP],
 'R_A':'286/29','R_P':'79/8','gap':'3/232','robust_sparse_radius':'1/1856','robust_gap_at_least':'3/464',
 'global_pair_support_minimum_nonnegative_and_positive':2,'scope_argument':argument,
 'same_agent_separate_arithmetic_and_scope_review_not_human_or_formal_kernel':True,
 'new_LP_price_prior_grid_API_hosted_humanlabels_or_PDF':False,'whole_project_complete':False}
with (H/'GLOBAL_SCOPE_AND_UPPER_QA_V01.json').open('x',encoding='utf-8') as f:
    json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'status':result['status'],'monotone_coefficient_checks':390,'old_fixed_upper_dual_inequalities':72,
 'g4_nonnegative':2,'g4_positive':2,'gap':'3/232','robust_gap':'3/464'}))
