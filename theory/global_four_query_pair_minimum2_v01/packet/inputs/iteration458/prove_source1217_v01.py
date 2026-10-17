"""Exact parameter-cone proof search; never solves a numerical cost game."""
import gzip
from fractions import Fraction
from functools import lru_cache
import hashlib
import itertools
import json
import math
from pathlib import Path
import time
H=Path(__file__).resolve().parent
B=H.parent
SCOPE_SHA='6116b3c204eea8a6369a14965b1889c85024b06efb71a1efa55110ce31ee25ea'
assert hashlib.sha256((H/'SOURCE1217_SINGLE_PAIR_SCOPE_V01.json').read_bytes()).hexdigest()==SCOPE_SHA
scope=json.loads((H/'SOURCE1217_SINGLE_PAIR_SCOPE_V01.json').read_text(encoding='utf-8'))
sourcefile=H/'SOURCE1217_ORIGINAL_FAMILIES_V01.json'
assert hashlib.sha256(sourcefile.read_bytes()).hexdigest()==scope['source_sha256']
src=json.loads(sourcefile.read_text(encoding='utf-8'))
W=scope['W'];assert src['task']==[682,32769] and len(src['adaptive'])==30 and len(src['priority'])==28
policies=src['priority']+src['adaptive']
profiles=[[p['sets'][w] for w in W] for p in policies]
assert all(any(p==a for a in profiles[28:]) for p in profiles[:28])
DIM=5
EYE=[tuple(int(i==j) for i in range(DIM)) for j in range(DIM)]
deadline=time.monotonic()+scope['bounds']['compute_seconds']
MAXN=scope['bounds']['max_nodes_total'];MAXROOT=scope['bounds']['max_nodes_per_root']
nodes=[];roots=[]
stats={'cone_nodes':0,'column_deletions':0,'row_deletions':0,'splits':0,'closed_leaves':0,'unclosed_leaves':0,
       'whole_cone_generator_inequality_checks':0,'max_rays':5,'max_depth':0,'numerical_games_solved':0,'pure_saddle_leaves':0,'fixed_rational_minimax_leaves':0}


def dot(a,b):return sum(x*y for x,y in zip(a,b))


def primitive(v,canonical_sign=False):
    v=tuple(v);g=math.gcd(*v)
    assert g
    v=tuple(x//g for x in v)
    if canonical_sign and next(x for x in v if x)!=abs(next(x for x in v if x)):
        v=tuple(-x for x in v)
    return v


def rank(rows):
    pivots={}
    for vector in rows:
        v=list(vector)
        for p,b in sorted(pivots.items()):
            if v[p]:
                value=v[p];v=[b[p]*x-value*y for x,y in zip(v,b)]
                if any(v):v=list(primitive(v,True))
        if any(v):
            v=primitive(v,True);p=next(i for i,x in enumerate(v) if x);pivots[p]=v
    return len(pivots)


def halfcones(rays,constraints,form):
    positive=[r for r in rays if dot(form,r)>0]
    negative=[r for r in rays if dot(form,r)<0]
    zero=[r for r in rays if dot(form,r)==0]
    assert positive and negative
    crossings={primitive([dot(form,p)*n[i]-dot(form,n)*p[i] for i in range(DIM)])
               for p in positive for n in negative}
    out=[]
    for keep,normal in [(positive,form),(negative,tuple(-x for x in form))]:
        normals=constraints+[normal]
        candidates=set(keep+zero)|crossings
        selected=[]
        for r in sorted(candidates):
            assert all(x>=0 for x in r) and all(dot(a,r)>=0 for a in normals)
            if rank([a for a in normals if dot(a,r)==0])>=DIM-1:selected.append(r)
        assert rank(selected)==DIM
        out.append((selected,normals))
    return out


@lru_cache(None)
def mixed_forms(costs):
    out=[]
    for template in scope['fixed_mixed_templates']:
        prior=[Fraction(v) for v in template['prior']]
        mix=[(v['policy_index'],Fraction(v['probability'])) for v in template['priority_mixture']]
        assert len(prior)==7 and sum(prior)==1 and all(v>=0 for v in prior)
        assert sum(v for _,v in mix)==1 and all(0<=p<28 and v>=0 for p,v in mix)
        da=math.lcm(*(v.denominator for v in prior));dp=math.lcm(*(v.denominator for _,v in mix))
        a=[int(da*v) for v in prior];b=[(p,int(dp*v)) for p,v in mix]
        pm=[[sum(v*costs[profiles[p][w]][k] for p,v in b) for k in range(5)] for w in range(7)]
        anchor=[sum(a[w]*pm[w][k] for w in range(7)) for k in range(5)]
        lower=[tuple(dp*sum(a[w]*costs[profiles[c][w]][k] for w in range(7))-anchor[k] for k in range(5)) for c in range(28,58)]
        upper=[tuple(anchor[k]-da*pm[w][k] for k in range(5)) for w in range(7)]
        out.append((lower,upper))
    return out


def analyze(costs,rays,constraints,rows,cols,depth,root_counter,reserved=0):
    assert len(nodes)+reserved+1<=MAXN and root_counter[0]+reserved+1<=MAXROOT
    nid=len(nodes);record={'rays':[list(r) for r in rays],'trace':[]};nodes.append(record)
    stats['cone_nodes']+=1;root_counter[0]+=1
    stats['max_rays']=max(stats['max_rays'],len(rays));stats['max_depth']=max(stats['max_depth'],depth)
    values=[[dot(cost,r) for r in rays] for cost in costs]
    geq=[[all(a>=b for a,b in zip(values[s],values[t])) for t in range(16)] for s in range(16)]
    stats['whole_cone_generator_inequality_checks']+=256*len(rays)
    for template in scope['pure_saddle_templates']:
        w=W.index(template['word']);p=template['P'];anchor=profiles[p][w]
        if all(geq[profiles[c][w]][anchor] for c in range(28,58)) and all(geq[anchor][profiles[p][v]] for v in range(7)):
            record.update(kind='pure_saddle',hard_word=template['word'],original_P=p,anchor_mask=anchor,
                          terminal_rows=rows[:],terminal_columns=cols[:])
            stats['closed_leaves']+=1;stats['pure_saddle_leaves']+=1
            return nid,True
    for tid,(lower,upper) in enumerate(mixed_forms(tuple(costs))):
        if all(dot(form,r)>=0 for form in lower+upper for r in rays):
            record.update(kind='fixed_rational_minimax',template=tid,terminal_rows=rows[:],terminal_columns=cols[:])
            stats['closed_leaves']+=1;stats['fixed_rational_minimax_leaves']+=1
            return nid,True
    rr=rows[:];cc=cols[:]
    while True:
        if time.monotonic()>deadline:
            record.update(kind='unclosed',reason='COMPUTE_BUDGET',terminal_rows=rr,terminal_columns=cc)
            stats['unclosed_leaves']+=1;return nid,False
        event=None
        for victim in reversed(cc):
            for by in cc:
                if victim==by:continue
                if all(geq[profiles[victim][w]][profiles[by][w]] for w in rr):
                    same=all(geq[profiles[by][w]][profiles[victim][w]] for w in rr)
                    if same and by>victim:continue
                    event={'kind':'column','victim':victim,'by':by};break
            if event:break
        if event:
            cc.remove(event['victim']);record['trace'].append(event);stats['column_deletions']+=1;continue
        for victim in rr:
            for by in rr:
                if victim==by:continue
                if all(geq[profiles[c][by]][profiles[c][victim]] for c in cc):
                    same=all(geq[profiles[c][victim]][profiles[c][by]] for c in cc)
                    if same and by>victim:continue
                    event={'kind':'row','victim':victim,'by':by};break
            if event:break
        if event:
            rr.remove(event['victim']);record['trace'].append(event);stats['row_deletions']+=1;continue
        break
    record['terminal_rows']=rr;record['terminal_columns']=cc
    lifts=[];missing=[]
    for c in cc:
        match=next((p for p in range(28) if all(geq[profiles[c][w]][profiles[p][w]] for w in range(7))),None)
        if match is None:missing.append(c)
        else:lifts.append({'column':c,'original_P':match})
    if not missing:
        record.update(kind='closed',P_lifts_on_all_original_rows=lifts)
        stats['closed_leaves']+=1;return nid,True
    record['unlifted_columns']=missing
    if len(nodes)+reserved+2>MAXN or root_counter[0]+reserved+2>MAXROOT:
        record.update(kind='unclosed',reason='NODE_BUDGET');stats['unclosed_leaves']+=1;return nid,False
    split=None
    for c in missing:
        for p in range(28):
            for w in range(7):
                form=tuple(x-y for x,y in zip(costs[profiles[c][w]],costs[profiles[p][w]]))
                if any(x>0 for x in [dot(form,r) for r in rays]) and any(x<0 for x in [dot(form,r) for r in rays]):
                    split=primitive(form,True);break
            if split:break
        if split:break
    if split is None:
        for lower,upper in mixed_forms(tuple(costs)):
            for form in lower+upper:
                signs=[dot(form,r) for r in rays]
                if min(signs)<0<max(signs):split=primitive(form,True);break
            if split:break
    if split is None:
        active_masks=sorted({profiles[c][w] for c in cc for w in rr})
        for s,t in itertools.combinations(active_masks,2):
            form=tuple(x-y for x,y in zip(costs[s],costs[t]));vs=[dot(form,r) for r in rays]
            if min(vs)<0<max(vs):split=primitive(form,True);break
    if split is None:
        record.update(kind='unclosed',reason='PURE_DOMINANCE_AND_FULL_ROW_LIFTING_INSUFFICIENT_ON_FIXED_FEE_ORDER_CELL')
        stats['unclosed_leaves']+=1;return nid,False
    children=halfcones(rays,constraints,split)
    record.update(kind='split',form=list(split),children=[])
    stats['splits']+=1
    passed=True
    for child_index,(newrays,newconstraints) in enumerate(children):
        child,ok=analyze(costs,newrays,newconstraints,rr,cc,depth+1,root_counter,reserved+(1 if child_index==0 else 0))
        record['children'].append(child);passed &= ok
    return nid,passed


for pair in itertools.combinations(range(4),2):
    edge=sum(1<<q for q in pair)
    for order in itertools.permutations(range(4)):
        record={'pair':list(pair),'order':list(order)}
        if time.monotonic()>deadline or len(nodes)+1>MAXN:
            record.update(closed=False,reason='NOT_STARTED_AFTER_GLOBAL_BUDGET',node=None);roots.append(record);continue
        M=[[int(order.index(q)>=k) for k in range(4)] for q in range(4)]
        costs=[tuple([sum(M[q][k] for q in range(4) if mask&(1<<q)) for k in range(4)]+[int(bool(mask&edge))]) for mask in range(16)]
        counter=[0]
        root,closed=analyze(costs,EYE,EYE,list(range(7)),list(range(58)),0,counter)
        record.update(node=root,closed=closed,nodes=counter[0]);roots.append(record)
assert len(roots)==144
assert all(r['node'] is None or 0<=r['node']<len(nodes) for r in roots)
closed_pairs=[list(pair) for pair in itertools.combinations(range(4),2) if all(r['closed'] for r in roots if r['pair']==list(pair))]
blob={'schema':1,'status':'PRODUCER_CANDIDATE_ALL144_PARAMETER_CONES_CLOSED' if len(closed_pairs)==6 else 'PRODUCER_PARTIAL_CERTIFICATES_WITH_EXPLICIT_RESIDUALS',
    'scope_sha256':SCOPE_SHA,'source_sha256':scope['source_sha256'],'W':W,'source_task':src['task'],
    'policy_column_indexing':'P0..27thenA0..29;uniondoesnotchangeadaptivegame',
    'roots':roots,'nodes':nodes,'candidate_closed_pairs':closed_pairs,'stats':stats,
    'no_numerical_price_or_prior_game_or_policy_catalogue_solved':True,
    'generator_checks_are_linear_universal_cone_inequalities_not_sampled_game_results':True,
    'producer_alone_not_theorem_acceptance':True}
raw=(json.dumps(blob,ensure_ascii=False,separators=(',',':'))+'\n').encode('utf-8')
packed=gzip.compress(raw,compresslevel=9,mtime=0)
target=H/'SOURCE1217_SINGLE_PAIR_PROOF_V01.json.gz'
with target.open('xb') as f:f.write(packed)
summary={'schema':1,'status':blob['status'],'proof':{'path':str(target),'bytes':len(packed),'sha256':hashlib.sha256(packed).hexdigest(),
    'decoded_bytes':len(raw),'decoded_sha256':hashlib.sha256(raw).hexdigest()},
    'candidate_closed_pairs':closed_pairs,'closed_roots':sum(r['closed'] for r in roots),'roots':144,
    'unclosed_roots':[{'pair':r['pair'],'order':r['order'],'node':r['node'],'reason':r.get('reason','DESCENDANT_RESIDUAL')} for r in roots if not r['closed']],
    'stats':stats,'independent_reader_required':True,'new_numeric_games_LP_model_hosted_or_human_review':False}
with (H/'SOURCE1217_SINGLE_PAIR_RESULT_V01.json').open('x',encoding='utf-8') as f:json.dump(summary,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'status':blob['status'],'closed_pairs':closed_pairs,'closed_roots':summary['closed_roots'],'roots':144,
    'nodes':len(nodes),'stats':stats,'proof_bytes':len(packed),'decoded_bytes':len(raw)}))
