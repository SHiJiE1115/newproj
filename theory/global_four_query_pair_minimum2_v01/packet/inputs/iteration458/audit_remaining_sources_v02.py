"""Audit frozen residual sources, physical supports, normal forms and pair-fee transports."""
from functools import lru_cache
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import time

H=Path(__file__).resolve().parent
B=H.parent
D=B/'iteration441/bundle_v01'
started=time.monotonic()
data_manifest=json.loads((D/'DATA_MANIFEST.json').read_text(encoding='utf-8'))


def pin(p):
    p=Path(p);raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def load(name):
    row=data_manifest['datasets'][name];p=D/row['file'];raw=p.read_bytes()
    assert len(raw)==row['compressed_bytes'] and hashlib.sha256(raw).hexdigest()==row['compressed_sha256']
    decoded=gzip.decompress(raw)
    assert len(decoded)==row['canonical_bytes'] and hashlib.sha256(decoded).hexdigest()==row['canonical_sha256']
    return json.loads(decoded)


def save(name,value):
    with (H/name).open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')


static=json.loads((D/'MANIFEST.json').read_text(encoding='utf-8'))
for row in static['files']:
    p=D/row['file'];assert p.resolve().is_relative_to(D)
    assert p.stat().st_size==row['bytes'] and pin(p)['sha256']==row['sha256']
families=load('families')['rows'];groups=load('groups')['groups'];cat=load('catalogue')
old_result=json.loads((B/'iteration441/LOCAL_RESULT_V01.json').read_text(encoding='utf-8'))
old_accept=json.loads((B/'iteration441/ACCEPTANCE_V01.json').read_text(encoding='utf-8'))
assert old_result['status']=='PASS_FULL_PORTABLE_REPLAY'
assert old_accept['local']['sha256']==pin(B/'iteration441/LOCAL_RESULT_V01.json')['sha256']
assert len(families)==1356 and old_result['science']['catalogue']['orbits']==1356
membership=[];monotone=[];additive=[];classification=[]
for group in groups:
    ids=group['orbits'];assert len(set(ids))==len(ids)
    membership.extend(ids)
    if group['fee_scope']=='all_finite_normalized_nonnegative_monotone':monotone.extend(ids)
    else:
        assert group['fee_scope']=='all_finite_nonnegative_additive';additive.extend(ids)
    classification.append({'proof_kind':group['kind'],'fee_scope':group['fee_scope'],'source_count':len(ids),'source_ids_sha256':hashlib.sha256(json.dumps(ids,separators=(',',':')).encode()).hexdigest()})
assert sorted(membership)==list(range(1356)) and len(set(membership))==1356
assert len(monotone)==1345 and len(additive)==11
residual=sorted(additive)
assert residual==[1209,1217,1221,1258,1265,1292,1312,1322,1328,1343,1344]
assert set(residual)==set(range(1356))-set(monotone)


def transform(mask,perm):return sum(((mask>>q)&1)<<perm[q] for q in range(4))


def physical_support(witness):
    pi=witness['same_partition'];different=witness['different_record_pairs']
    assert len(pi)==8
    result=0
    for w in range(16):
        parents=list(range(8))
        def find(i):
            while parents[i]!=i:i=parents[i]
            return i
        def join(i,j):parents[find(i)]=find(j)
        for i in range(8):
            for j in range(i):
                if pi[i]==pi[j]:join(i,j)
        for q in range(4):
            if w>>q&1:join(2*q,2*q+1)
        if any((find(2*q)==find(2*q+1))!=bool(w>>q&1) for q in range(4)):continue
        if any(find(a)==find(b) for a,b in different):continue
        result|=1<<w
    return result


def trace(tree,word):
    seen=[]
    while isinstance(tree,list):
        assert len(tree)==3
        q=tree[0];assert type(q) is int and q in range(4) and q not in seen
        seen.append(q);tree=tree[1+((word>>q)&1)]
    assert type(tree) is int and tree in (0,1)
    return tree,sum(1<<q for q in seen),seen


def transport_tree(tree,perm,swap):
    if not isinstance(tree,list):return tree^swap
    return [perm[tree[0]],transport_tree(tree[1],perm,swap),transport_tree(tree[2],perm,swap)]


def completeness(src):
    W=[w for w in range(16) if (src['task'][0]|src['task'][1])>>w&1]
    W1={w for w in W if src['task'][1]>>w&1};root=(1<<len(W))-1
    positive=sum(1<<i for i,w in enumerate(W) if w in W1)
    high={q:sum(1<<i for i,w in enumerate(W) if w>>q&1) for q in range(4)}
    zero=(0,)*len(W);deadline=time.monotonic()+20
    stats={'candidate_profiles':0,'subset_comparisons':0,'max_frontier':0}
    def pure(state):return not state or not state&positive or state&positive==state
    def subset(a,b):return all((x&y)==x for x,y in zip(a,b))
    def prune(vectors):
        values=sorted(set(vectors),key=lambda v:(sum(x.bit_count() for x in v),v))
        stats['candidate_profiles']+=len(values)
        assert stats['candidate_profiles']<=200000 and time.monotonic()<deadline
        keep=[]
        for vector in values:
            dominated=False
            for by in keep:
                stats['subset_comparisons']+=1;assert stats['subset_comparisons']<=5000000
                if subset(by,vector):dominated=True;break
            if not dominated:keep.append(vector)
        stats['max_frontier']=max(stats['max_frontier'],len(keep))
        return tuple(sorted(keep))
    def combine(q,state,left,right):return tuple((left[i]|right[i]|(1<<q)) if state>>i&1 else 0 for i in range(len(W)))
    @lru_cache(None)
    def adaptive(state,remaining):
        if pure(state):return (zero,)
        values=[]
        for q in range(4):
            if not remaining>>q&1:continue
            hi=state&high[q];lo=state^hi
            if not hi or not lo:continue
            values.extend(combine(q,state,a,b) for a in adaptive(lo,remaining^(1<<q)) for b in adaptive(hi,remaining^(1<<q)))
        assert values
        return prune(values)
    @lru_cache(None)
    def priority(order,index,state):
        if pure(state):return (zero,)
        if index==4:return ()
        q=order[index];values=list(priority(order,index+1,state));hi=state&high[q];lo=state^hi
        if hi and lo:values.extend(combine(q,state,a,b) for a in priority(order,index+1,lo) for b in priority(order,index+1,hi))
        return prune(values)
    A=adaptive(root,15);allP=[];orders=[]
    for order in itertools.permutations(range(4)):
        vectors=priority(order,0,root);assert vectors
        orders.append({'order':list(order),'minimal_profile_count':len(vectors)});allP.extend(vectors)
    P=prune(allP)
    originalA=[tuple(row['sets'][w] for w in W) for row in src['adaptive']]
    originalP=[tuple(row['sets'][w] for w in W) for row in src['priority']]
    assert len(set(originalA))==len(originalA) and len(set(originalP))==len(originalP)
    assert A==prune(originalA) and P==prune(originalP)
    assert all(v in originalA for v in A) and all(v in originalP for v in P)
    assert all(any(subset(a,v) for a in A) for v in originalA)
    assert all(any(subset(p,v) for p in P) for v in originalP)
    assert set(originalP)<=set(originalA)
    return {'A_minimal':[list(v) for v in A],'P_minimal':[list(v) for v in P],
        'full_counts':[len(originalA),len(originalP)],'minimal_counts':[len(A),len(P)],
        'original_A_to_minimal':[next(i for i,a in enumerate(A) if subset(a,v)) for v in originalA],
        'original_P_to_minimal':[next(i for i,p in enumerate(P) if subset(p,v)) for v in originalP],
        'all24_priority_orders':orders,'A_states':adaptive.cache_info().currsize,'P_states':priority.cache_info().currsize,'stats':stats}


fee_coefficient_checks=0
for perm in itertools.permutations(range(4)):
    assert sorted(perm)==list(range(4))
    for pair in itertools.combinations(range(4),2):
        edge=sum(1<<q for q in pair);newedge=transform(edge,perm)
        assert newedge.bit_count()==2
        for mask in range(16):
            newmask=transform(mask,perm)
            old_coeff=[int(mask>>q&1) for q in range(4)]+[int(bool(mask&edge))]
            new_coeff=[int(newmask>>perm[q]&1) for q in range(4)]+[int(bool(newmask&newedge))]
            assert old_coeff==new_coeff;fee_coefficient_checks+=1
results=[];projections=[];original_paths=0;transported_paths=0;orbit_members=set()
for source_id in residual:
    assert time.monotonic()-started<180
    src=families[source_id];task=src['task']
    assert task[0] and task[1] and not(task[0]&task[1])
    binding=load('source'+str(source_id))
    if 'task' in binding:
        assert source_id==1217 and binding['task']==task
    elif 'orbit_index' in binding:
        assert binding['orbit_index']==source_id
    else:
        assert source_id==1322 and task==[2457,32770]
        assert binding['old_A_P']==[len(src['adaptive']),len(src['priority'])]
        assert binding['transport']['query_permutation']==[0,1,3,2]
    witnesses=[cat['support_witnesses'][str(mask)] for mask in task]
    assert all(physical_support(w)==mask for mask,w in zip(task,witnesses))
    W=[w for w in range(16) if (task[0]|task[1])>>w&1]
    labels={w:int(bool(task[1]>>w&1)) for w in W}
    for field in ('adaptive','priority'):
        for col in src[field]:
            assert len(col['sets'])==16 and all(col['sets'][w]==0 for w in range(16) if w not in W)
            for word in W:
                label,mask,seen=trace(col['tree'],word)
                assert label==labels[word] and mask==col['sets'][word]
                if field=='priority':
                    assert sorted(col['order'])==list(range(4))
                    assert seen==sorted(seen,key=col['order'].index)
                original_paths+=1
    members=set()
    for perm in itertools.permutations(range(4)):
        image=tuple(sum(1<<transform(w,perm) for w in range(16) if mask>>w&1) for mask in task)
        members.update((image,image[::-1]))
        for swap in (0,1):
            for field in ('adaptive','priority'):
                for col in src[field]:
                    tree=transport_tree(col['tree'],perm,swap)
                    order=[perm[q] for q in col['order']] if field=='priority' else None
                    for word in W:
                        label,mask,seen=trace(tree,transform(word,perm))
                        assert label==(labels[word]^swap) and mask==transform(col['sets'][word],perm)
                        if order is not None:assert seen==sorted(seen,key=order.index)
                        transported_paths+=1
    assert members==set(map(tuple,src['orbit_members'])) and not(members&orbit_members)
    orbit_members|=members
    proof=completeness(src)
    results.append({'source_id':source_id,'task':task,'W':W,'orbit_members':len(members),
        'physical_label_witnesses':witnesses,'completeness':proof})
    projections.append({'source_id':source_id,'source':src,'physical_label_witnesses':witnesses})
    print(json.dumps({'source':source_id,'full':proof['full_counts'],'minimal':proof['minimal_counts'],'orbit_members':len(members)}),flush=True)
save('RESIDUAL_SOURCE_PROJECTIONS_V01.json',{'schema':1,'frozen441family_projection':pin(D/'data/families.json.gz'),
    'source_order':residual,'pair_order':[list(p) for p in itertools.combinations(range(4),2)],
    'price_order':'Lexicographicpermutations of0,1,2,3','rows':projections,
    'original_full_families_retained_not_assumed_irredundant':True})
result={'schema':1,'status':'PASS_FROZEN_1345_PLUS11_REDUCTION_PHYSICAL_RESIDUAL_SOURCES_FULL_POLICY_PREMISE_AND_PAIR_FEE_TRANSPORT',
    'original441acceptance':pin(B/'iteration441/ACCEPTANCE_V01.json'),'original441actual_full_replay':pin(B/'iteration441/LOCAL_RESULT_V01.json'),
    'frozen_data_manifest':pin(D/'DATA_MANIFEST.json'),'static_packet_files_rehashed':len(static['files']),
    'source_classification':classification,'monotone_already_closed':1345,'residual_sources':residual,
    'inherited1345_and_full_catalogue_proofs_not_reexecuted':True,'new_global_source_catalogue_regenerated':False,
    'source_projections':pin(H/'RESIDUAL_SOURCE_PROJECTIONS_V01.json'),'residual_results':results,
    'physical_label_supports_checked':22,'all16_possible_words_checked_per_physical_label':True,
    'original_full_policy_input_paths_checked':original_paths,'explicit_transported_policy_input_paths_checked':transported_paths,
    'residual_ordered_tasks_covered':len(orbit_members),'query_permutations':24,'label_swaps':2,'literal_answer_complementation_used':False,
    'fee_coefficient_identities_checked':fee_coefficient_checks,'cost_values_sampled':0,
    'transport_argument':'Rename oldqueryi toperm[i],individualprice likewise,andpair e toperm(e). Thefivelinear fee coefficients agree on every purchased mask,so everycontinuous parameter vector transports exactly. Rename treequeries and globalorders,swap leaflabels if needed;the inversepermutation gives a bijection,including causal SKIP. Private seed distributions remain input-independent,all perinput costs and their maximum identical. Positivepair-support count preserved. Label exchange does not alter queries or fees.',
    'completeness_argument':'At mixed feasible states exhaust informativefirstqueries/both continuations; at fixed orders exhaust SKIP and TAKE with common suffix. Stop atpurestates. Under monotone finalsetfees,repeated/knownanswer/postpurepurchases can be erased and pointwise subsetpruning is valid under every common paid context. Reconstructed minimal roots equal reducedcachedroots,and every minimal root is retained;every original cached vector has a reconstructed subset. Every frozen fullcolumn has a legal original tree/order witness. Private mixtures inherit the pointwise domination.',
    'new_one_pair_fee_equality_or_gap_proved':False,'g4_support_minimum':'OPEN_1_OR2',
    'next_source_in_frozen_order_not_already_accepted':1217,'source1209_all6pairfamilies_already_accepted_in453455':True,
    'new_fee_prior_grid_LP_API_hosted_human_labels_or_PDF':False,
    'same_agent_dependency_audit_not_external_human_or_formal_kernel':True,'whole_project_complete':False}
save('REMAINING_SOURCE_AUDIT_V01.json',result)
print(json.dumps({'status':result['status'],'residual_sources':11,'ordered_residual_tasks':len(orbit_members),
    'original_paths':original_paths,'transported_paths':transported_paths,'symbolic_fee_coefficient_identities':fee_coefficient_checks,
    'next_source':1217,'g4':'OPEN_1_OR2'}))
