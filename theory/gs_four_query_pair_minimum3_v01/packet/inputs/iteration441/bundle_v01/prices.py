"""Exact replay of the eleven additive-only source certificates.

Cones are closed, and their nonnegative generators include all zero/tie faces.
No price sampling, LP optimization, or new certificate search is performed.
"""
from fractions import Fraction as F
import itertools
import math
from algebra import P, variables, parse
from proofio import data, words, transform

ORDERS=list(itertools.permutations(range(4)))
def sub(a,b):return [x-y for x,y in zip(a,b)]
def nn(v):return all(x>=0 for x in v)
def basis(order):return [[int(order.index(q)>=k) for k in range(4)] for q in range(4)]
def pay(mask,M):return [sum(M[q][k] for q in range(4) if mask>>q&1) for k in range(4)]
def normalized(v):
    if nn(v):return None
    scale=math.lcm(*(x.denominator for x in v));ints=[int(x*scale) for x in v];g=math.gcd(*ints)
    return tuple(x//g for x in ints)


def library1217(families):
    saved=data('source1217');src=families[1217];ww=words(src['task'])
    assert saved['task']==src['task']==[682,32769]
    retained={c['serial']:c for c in saved['old_realizing_certificates']}
    assert len(retained)==len(saved['cones'])==29
    inequalities=0;leaf_checks=0
    for cone in saved['cones']:
        case=retained[cone['realizing_case_serial']]
        assert case['orbit_index']==1217 and case['task']==src['task'] and case['domain']==ww
        prior=list(map(F,case['adaptive_prior']))
        mix=[(v['policy_index'],F(v['probability'])) for v in case['priority_upper']]
        assert len(prior)==len(ww) and sum(prior)==1 and nn(prior)
        assert sum(p for j,p in mix)==1 and all(p>=0 and 0<=j<len(src['priority']) for j,p in mix)
        def lower(A):return [sum(p*int(A['sets'][w]>>q&1) for w,p in zip(ww,prior)) for q in range(4)]
        L=lower(src['adaptive'][cone['anchor_adaptive_index']]);assert L==list(map(F,cone['lower_linear_form']))
        normals=set()
        for A in src['adaptive']:
            v=normalized(sub(lower(A),L))
            if v is not None:normals.add(v)
            inequalities+=1
        for w in ww:
            upper=[sum(p*int(src['priority'][j]['sets'][w]>>q&1) for j,p in mix) for q in range(4)]
            v=normalized(sub(L,upper))
            if v is not None:normals.add(v)
            inequalities+=1
        assert sorted(normals)==list(map(tuple,cone['effective_rows']))
    assert [tuple(r['price_order']) for r in saved['cover_roots']]==ORDERS
    assert len(saved['proof_nodes'])==24
    for root in saved['cover_roots']:
        node=saved['proof_nodes'][root['proof_node']];assert node['kind']=='leaf'
        M=basis(root['price_order']);rays=set(zip(*M))
        assert len(rays)==4 and rays==set(map(tuple,node['rays']))
        for normal in saved['cones'][node['cone_index']]['effective_rows']:
            for ray in rays:assert sum(a*b for a,b in zip(normal,ray))>=0;leaf_checks+=1
    return {'cones':29,'order_roots':24,'rational_inequalities':inequalities,'leaf_inequalities':leaf_checks}


def fan(src,cones,old436=False,allow_two_open=False):
    ww=words(src['task']);hard=[w for w in ww if w!=0] if old436 else ww[:]
    cols={f'P{k}':v for k,v in enumerate(src['priority'])}
    cols.update({f'A{k}':v for k,v in enumerate(src['adaptive'])})
    if old436:
        assert src['task']==[642,34833] and ww==[0,1,4,7,9,11,15]
        assert all(v['sets'][0]&~v['sets'][1]==0 for v in cols.values())
    assert [tuple(c['order']) for c in cones]==ORDERS
    steps=signs=pure=closed=0;open_orders=[]
    for cone in cones:
        if not cone['closed']:
            assert allow_two_open and cone['order'] in ([0,1,2,3],[0,1,3,2])
            open_orders.append(cone['order']);continue
        closed+=1;M=basis(cone['order']);assert cone['price_matrix']==M
        costs={(cid,w):pay(v['sets'][w],M) for cid,v in cols.items() for w in ww}
        def cost(cid,w):return costs[cid,w]
        cert=cone['certificate']
        if old436 and cone['method']=='pure_saddle':
            t=cert['template'];L=[sum(M[q][k]*t['value_coefficients'][q] for q in range(4)) for k in range(4)]
            checks=[]
            for j in range(len(src['adaptive'])):
                gap=sub(cost(f'A{j}',t['word']),L);assert nn(gap)
                checks.append({'kind':'lower','A':j,'gap':gap});pure+=4
            for w in ww:
                gap=sub(L,cost(f"P{t['P']}",w));assert nn(gap)
                checks.append({'kind':'upper','word':w,'gap':gap});pure+=4
            assert checks==cert['all47_linear_checks'];continue
        rr=hard[:];cc=list(cols);parent={}
        assert cert['initial_rows']==rr and cert['initial_columns']==cc and cert['closed'] is True
        for event in cert['trace']:
            assert event['active_rows']==rr and event['active_columns']==cc
            v,by=event['victim'],event['by'];assert v!=by
            if event['kind']=='column':
                assert v in cc and by in cc;gaps=[sub(cost(v,w),cost(by,w)) for w in rr];cc.remove(v)
            else:
                assert event['kind']=='row' and v in rr and by in rr
                gaps=[sub(cost(cid,by),cost(cid,v)) for cid in cc];rr.remove(v);parent[v]=by
            assert gaps==event['gap_polynomials'] and all(nn(g) for g in gaps) and rr and cc
            steps+=1;signs+=4*len(gaps)
        assert rr==cert['terminal_rows'] and cc==cert['terminal_columns']
        # One row map works simultaneously for every terminal column. This is
        # essential for mixtures and is stronger than separate column maxima.
        for w in ww:
            t=1 if old436 and w==0 else w;seen=set()
            while t not in rr:assert t not in seen;seen.add(t);t=parent[t]
            for cid in cc:assert nn(sub(cost(cid,t),cost(cid,w)));signs+=4
        lifts=cert['P_lifting_on_all_original_rows'] if old436 else cert['terminal_columnwise_P_replacements']
        assert [v['terminal_column'] for v in lifts]==cc
        for lift in lifts:
            cid=lift['terminal_column'];pj=f"P{lift['original_P']}";assert pj in cols
            gaps=[sub(cost(cid,w),cost(pj,w)) for w in hard]
            assert all(nn(g) for g in gaps)
            assert gaps==lift['gap_polynomials' if old436 else 'all_original_row_gap_polynomials']
            if old436:assert lift['all_original_rows']==hard
            signs+=4*len(gaps)
        assert cert['terminal_columns_without_P_lifting' if old436 else 'columns_without_columnwise_P_replacement']==[]
        if not old436:
            assert cert['certificate_kind']=='terminal_columnwise_original_row_P_lifting'
            assert cert['terminal_linear_value_P_upper'] is None
    assert closed==(22 if allow_two_open else 24)
    if allow_two_open:assert open_orders==[[0,1,2,3],[0,1,3,2]]
    return {'closed_order_cones':closed,'dominance_steps':steps,'scalar_sign_checks':signs,'pure_saddle_scalar_checks':pure}


def poly(terms):return parse(4,[(v['powers'],v['coefficient']) for v in terms])
def positive(poly):return nn(poly.t.values())


def last1322(families):
    saved=data('source1322');src=families[1322];ww=words(src['task'])
    assert src['task']==[2457,32770] and ww==[0,1,3,4,7,8,11,15]
    assert [len(src['adaptive']),len(src['priority'])]==saved['old_A_P']==[45,31]
    old=fan(src,saved['old_cones'],allow_two_open=True)
    cols={f'{p}{i}':v for field,p in [('adaptive','A'),('priority','P')] for i,v in enumerate(src[field])}
    perm=[0,1,3,2]
    for mask in src['task']:
        assert {transform(w,perm) for w in ww if mask>>w&1}=={w for w in ww if mask>>w&1}
    mapping={}
    for prefix in ('A','P'):
        available={tuple(v['sets'][w] for w in ww):cid for cid,v in cols.items() if cid[0]==prefix}
        for cid,v in cols.items():
            if cid[0]==prefix:
                signature=tuple(transform(v['sets'][transform(w,perm)],perm) for w in ww)
                assert signature in available;mapping[cid]=available[signature]
    assert mapping['P5']=='P6' and mapping['P14']=='P24'
    assert [cols[cid]['sets'][w] for cid,w in [('P5',1),('P5',15),('P14',1),('P14',15)]]==[3,14,7,12]
    a,b,c,d=variables(4);D=b+c;S=a+b-d;T=c+d-a;N=b*(a+b+c)+c*(c+d)
    assert S+T==D and N-(c+d)*D==b*S
    tau={0:1,1:1,3:15,4:15,7:15,8:1,11:15,15:15}
    assert {int(w):t for w,t in saved['mixed_domain']['common_row_map_for_both_upper_policies'].items()}==tau
    expectedM=[[[1,0,1,1],[1,1,1,1],[1,1,2,1],[1,1,2,2]],
        [[1,0,1,0],[1,1,1,0],[1,1,2,0],[2,1,2,1]],[[1,0,0,0],[1,1,0,0],[2,1,1,0],[2,1,1,1]]]
    expectedInv=[[[1,1,0,-1],[-1,1,0,0],[0,-1,1,0],[0,0,-1,1]],
        [[1,1,-1,0],[-1,1,0,0],[0,-1,1,0],[-1,-1,0,1]],[[1,0,0,0],[-1,1,0,0],[-1,-1,1,0],[0,0,-1,1]]]
    assert [r['name'] for r in saved['new_regions']]==['MIXED','PURE_LOW_C','PURE_HIGH_C']
    coefficient_checks=0
    for k,(spec,r) in enumerate(zip(saved['three_exact_closed_subcones'],saved['new_regions'])):
        M=expectedM[k];inv=expectedInv[k]
        assert spec['name']==r['name'] and spec['price_matrix']==r['price_matrix']==M
        assert spec['inverse_matrix']==r['inverse_matrix']==inv
        assert all(sum(inv[i][q]*M[q][j] for q in range(4))==int(i==j) for i in range(4) for j in range(4))
        xx=variables(4);a,b,c,d=[sum((M[q][j]*xx[j] for j in range(4)),P(4)) for q in range(4)]
        def cost(cid,w):return sum((p for q,p in enumerate((a,b,c,d)) if cols[cid]['sets'][w]>>q&1),P(4))
        S=a+b-d;D=b+c;T=c+d-a;N=b*(a+b+c)+c*(c+d);mixed=k==0
        forms=[a,b-a,c-b,d-c,S if mixed else -S]
        assert len(forms)==len(r['domain_linear_forms'])
        for v,encoded in zip(forms,r['domain_linear_forms']):assert positive(v) and poly(encoded)==v
        assert positive((a+b-c) if k==1 else (c-a-b)) if k else True
        if mixed:
            for key,v in [('D',D),('S',S),('N',N),('P5_weight_numerator',S),('P14_weight_numerator',T),('prior_word1_numerator',b),('prior_word15_numerator',c)]:assert poly(r[key])==v
            assert all(positive(v) for v in (D,S,T,b,c)) and S+T==D and b+c==D
            assert D==2*xx[0]+2*xx[1]+3*xx[2]+2*xx[3]
            assert r['zero_D_iff_parameter_origin'] is True and r['zero_face_legal_original_P']==14 and r['zero_face_value']==0
            # D=0 implies all nonnegative parameters zero; every paid set then costs0.
        else:
            V=c+d;assert poly(r['value'])==V and r['pure_original_P']==14
        lower=r['all_original_column_lower_gaps'];upper=r['all_original_row_upper_gaps']
        assert [v['column'] for v in lower]==list(cols) and [v['word'] for v in upper]==ww
        for v in lower:
            cid=v['column'];gap=b*cost(cid,1)+c*cost(cid,15)-N if mixed else cost(cid,15)-V
            assert positive(gap) and poly(v['Bayes_lower_numerator_gap' if mixed else 'word15_lower_gap'])==gap
            coefficient_checks+=10 if mixed else 4
        for v in upper:
            w=v['word'];gap=N-S*cost('P5',w)-T*cost('P14',w) if mixed else V-cost('P14',w)
            assert positive(gap) and poly(v['upper_numerator_gap' if mixed else 'P14_upper_gap'])==gap
            coefficient_checks+=10 if mixed else 4
            if mixed and w in (1,15):assert gap==0
        if mixed:
            rows=r['common_row_map_gaps'];assert {(v['word'],v['original_P']) for v in rows}=={(w,j) for w in ww for j in (5,14)} and len(rows)==16
            for v in rows:
                w=v['word'];cid=f"P{v['original_P']}";gap=cost(cid,tau[w])-cost(cid,w)
                assert v['mapped_word']==tau[w] and poly(v['linear_gap'])==gap and positive(gap);coefficient_checks+=4
    assert coefficient_checks==1576
    return {'old22cones':old,'new_closed_subcones':3,'new_coefficient_checks':coefficient_checks,
        'transported_full_columns':len(mapping),'all24_order_cones_covered':True,'zero_denominator_and_switch_faces':True}


def verify(families):
    out={'source1217':library1217(families),'source1209':fan(families[1209],data('source1209')['cones'],True)}
    batch=[1221,1258,1265,1292,1312,1328,1343,1344]
    for i in batch:out['source'+str(i)]=fan(families[i],data('source'+str(i))['cones'])
    nine=[out['source1209']]+[out['source'+str(i)] for i in batch]
    assert sum(v['dominance_steps'] for v in nine)==16634
    assert sum(v['scalar_sign_checks'] for v in nine)==556560
    assert sum(v['pure_saddle_scalar_checks'] for v in nine)==3008
    out['source1322']=last1322(families)
    return out
