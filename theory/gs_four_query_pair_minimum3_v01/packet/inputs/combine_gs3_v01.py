"""Compose current relocated proof values; standard-library exact arithmetic."""
from pathlib import Path
from fractions import Fraction as F
from itertools import combinations,permutations
from collections import Counter
import gzip
import json
import sys

C=Path(sys.argv[1]).resolve();OUT=Path(sys.argv[2]).resolve()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
audit=read(C/'iteration458/REMAINING_SOURCE_AUDIT_V01.json')
majority=read(C/'MAJORITY_RESULT_V01.json')
cached=read(C/'iteration441/LOCAL_RESULT_V01.json')
families=json.loads(gzip.decompress((C/'iteration441/bundle_v01/data/families.json.gz').read_bytes()))['rows']
assert len(families)==1356 and sum(len(x['orbit_members']) for x in families)==42864
assert audit['monotone_already_closed']==1345
assert majority['threshold_and_subset']['threshold_sources']+majority['threshold_and_subset']['pointwise_sources']+majority['structural']['structural_sources']==1345
ids=[1209,1217,1221,1258,1265,1292,1312,1322,1328,1343,1344]
assert audit['residual_sources']==ids and sum(x['source_count'] for x in audit['source_classification'])==1356
counts=Counter();lower_rows=[]
for n in ids:
    row=read(C/f'iteration464/SOURCE{n}_BALANCED_LOWER_RESULT_V01.json')
    assert row['source_id']==n and row['roots']==row['closed_roots']==144
    assert row['source_balanced_hierarchy_equality_accepted'] and not row['source_full_GS_equality_claimed']
    assert row['selected_balanced_hierarchy_ids']==[2,5,8,10,13,15] and row['unclosed_roots']==[]
    for k,v in row['counts'].items():counts[k]+=v
    counts['roots']+=144;counts['paths']+=row['original_policy_paths_checked'];counts['physical_words']+=row['physical_support_word_checks']
    lower_rows.append({'source_id':n,'roots':144,'closed':144})
assert counts['roots']==1584 and counts['nodes']==2074 and counts['scalar_inequalities']==4330508
assert counts['unclosed_leaves']==counts['not_started_roots']==0

pairs=list(combinations(range(4),2));graphs=0;small=0
for mask in range(64):
    edges={pairs[i] for i in range(6) if mask>>i&1}
    if any(sum(e in edges for e in combinations(t,2))==2 for t in combinations(range(4),3)):continue
    graphs+=1
    if len(edges)<=2:
        if len(edges)==2:
            a,b=list(edges);assert not(set(a)&set(b))
        small+=1
assert graphs==15 and small==10
transport=0
for p in permutations(range(4)):
    for S in range(16):
        T=sum(1<<p[i] for i in range(4) if S>>i&1)
        assert [int(bool(S>>i&1)) for i in range(4)]+[int(bool(S&((1<<i)|(1<<j)))) for i,j in pairs]==[int(bool(T>>p[i]&1)) for i in range(4)]+[int(bool(T&((1<<p[i])|(1<<p[j])))) for i,j in pairs]
        transport+=1

upper=read(C/'iteration464/TRIANGLE3_INDEPENDENT_STRICT_GS_GAP_CHECK_V01.json')
bell=read(C/'iteration465/SEPARATE_BELLMAN_CLASS_RESULT_V01.json')
cert=read(C/'iteration464/TRIANGLE3_STRICT_GS_GAP_CANDIDATE_CERTIFICATE_V01.json')
source=read(C/'iteration464/SOURCE1209_ORIGINAL_FAMILIES_V01.json')
assert source==families[1209]
assert bell['all24_globalorders_checked'] and bell['all1602states_checked']
assert bell['P_lower_no_longer_requires_cached32profile_exhaustiveness']
vp=F(bell['P_Bayes_exact']);va=F(upper['adaptive_minimax_upper']);gap=vp-va
assert vp==F(1025,47)==F(upper['P_exact_minimax']) and va==F(324871,14899) and gap==F(54,14899)>0
assert upper['GS_discrete_exchange_tests']==256 and upper['original_paths_checked']==504
assert cert['charges']==[7,4,3,6] and cert['pair_weights']==[0,0,0,4,4,4]
W=[0,1,4,7,9,11,15];pi=list(map(F,cert['P_prior_all7']))
assert sum(pi)==1 and min(pi)>=0
coeff=[]
for mask in range(16):
    coeff.append([F(int(bool(mask>>i&1))) for i in range(4)]+[F(sum(bool(mask&((1<<i)|(1<<j))) for i,j in combinations((1,2,3),2)))])
center=list(map(F,[7,4,3,6,4]));radius=gap/28
fees=[sum(x*y for x,y in zip(v,center)) for v in coeff]
assert fees==list(map(F,cert['all16_fees'])) and max(sum(x) for x in coeff)==7
assert min(center)>radius>0

# Full-class robustness: EVERY final set has sensitivity <=7, hence every
# policy (and its expectation) does. min_T E_pi F_z(S_T) >= B_P(center)-7r,
# while the fixed adaptive witness costs <= Aupper(center)+7r. This removes
# cached-P-profile exhaustiveness from the robustness premise as well.
uniform_gap=vp-va-14*radius
assert radius==F(27,208586) and uniform_gap==F(27,14899)>0
box=read(C/'iteration464/RELATIVE_GS_ROBUST_BOX_V01.json')
pc=[]
for col in source['priority']:
    pc.append([sum(pi[j]*coeff[col['sets'][w]][k] for j,w in enumerate(W)) for k in range(5)])
ac=[]
for w in W:
    ac.append([sum(F(m['probability'])*coeff[source[m['kind']][m['index']]['sets'][w]][k] for m in cert['adaptive_mixture']) for k in range(5)])
lookup={(r['P'],r['world']):r for r in box['inequalities']}
bounds=[]
for j,p in enumerate(pc):
    for i,a in enumerate(ac):
        d=[x-y for x,y in zip(p,a)]
        bound=sum(x*(c-radius if x>=0 else c+radius) for x,c in zip(d,center))
        assert bound>=uniform_gap
        r=lookup[j,W[i]]
        assert list(map(F,r['difference_coefficients']))==d and F(r['box_lower_bound'])==bound
        bounds.append(bound)
assert len(bounds)==224
science={'schema':1,'claim':'exact_GS_restricted_positive_pair_support_minimum3_complete_FOUR_query_sources',
    'scope':'Unrestrictedclasscountcompleteequivalencefibres;privateinputindependentzeroerrorworstinputexpectation;fullglobalordercausalpermanentSKIPandstop',
    'source_cover':{'canonical_orbits':len(families),'ordered_tasks':sum(len(x['orbit_members']) for x in families),
        'inherited_catalogue_and_full_global_policy_enumeration':True,'fresh_monotone_sources':1345,'fresh_residual_sources':ids},
    'fresh_monotone_certificates':majority,'fresh_residual_audit':{'physical_labels':audit['physical_label_supports_checked'],
        'original_paths':audit['original_full_policy_input_paths_checked'],'transported_paths':audit['explicit_transported_policy_input_paths_checked'],
        'ordered_tasks':audit['residual_ordered_tasks_covered'],'classification':audit['source_classification']},
    'lower':{'positive_support_patterns':64,'GS_clique_patterns':graphs,'atmost2patterns':small,
        'balanced_histories':[2,5,8,10,13,15],'price_orders_each':24,'sources':lower_rows,'counts':dict(counts),'ten_coefficient_transport_checks':transport},
    'upper':{'individual_charges':cert['charges'],'pair_order':cert['pair_order'],'pair_weights':cert['pair_weights'],
        'all16_fees':cert['all16_fees'],'P_exact':str(vp),'A_upper':str(va),'gap_at_least':str(gap),'A_exact_claimed':False,
        'all7P_upper':upper['all7P_upper_verified'],'all7A_upper':upper['all7adaptive_upper_verified'],
        'P_full_class_Bellman_counts':bell['counts'],'P_full_class_orders':24,'P_Bayes':bell['P_Bayes_exact'],
        'Bayes_A39':bell['A39_Bayes_upper'],'Bayes_gap':bell['Bayes_gap_lower'],
        'point_P_lower_requires_cached_profile_exhaustiveness':False,'A39_profile_used_for_Bayes_upper_only':True},
    'robust':{'relative_dimension':5,'center':list(map(str,center)),'Linf_radius':str(radius),'uniform_gap_at_least':str(uniform_gap),
        'all16_finalset_sensitivity_max':7,'uniform_full_class_P_lower_requires_cached_profile_exhaustiveness':False,
        'cached224_affine_crosschecks':224,'minimum_affine_box_bound':str(min(bounds)),'arbitrary_independent10parameter_GS_perturbations_claimed':False},
    'GS_restricted_minimum':3,'older_unrestricted_minimum_unchanged':2,'universal_GS_equality_hypothesis':'REFUTED',
    'priority':'OPEN','application_advantage':'NOT_ESTABLISHED','external_human_or_formal_review':False,'whole_project_complete':False}
with OUT.open('x',encoding='utf-8',newline='\n') as f:json.dump(science,f,ensure_ascii=False,indent=2);f.write('\n')
print({'status':'PASS_COMBINED_RELOCATED_GS_MINIMUM3_SCIENCE','lower_roots':1584,'Bellman_states':1602,
    'all16_full_class_robust_sensitivity':7,'uniform_gap':str(uniform_gap),'priority':'OPEN'})
