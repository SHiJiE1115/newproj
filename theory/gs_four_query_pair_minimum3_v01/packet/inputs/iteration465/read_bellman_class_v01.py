"""Separate Fraction recurrence checker; no policy-family completeness input."""
from pathlib import Path
from fractions import Fraction as Q
from itertools import permutations,combinations
import hashlib
import json
import os
import sys

H=Path(__file__).resolve().parent
PROOF=H/'CAUSAL_SKIP_BELLMAN_PROOF_V01.json';SCOPE=H/'BELLMAN_CLASS_SCOPE_V01.json'
SOURCE=H/'SOURCE1209_ORIGINAL_FAMILIES_V01.json';CERT=H/'TRIANGLE3_STRICT_GS_GAP_CANDIDATE_CERTIFICATE_V01.json'
OUT=H/'SEPARATE_BELLMAN_CLASS_RESULT_V01.json';AUDIT=H/'SEPARATE_BELLMAN_INPUTS_V01.json'
allowed={p.resolve() for p in [PROOF,SCOPE,SOURCE,CERT]};reads=set();denied=[]
def hook(event,args):
    if event.startswith('socket.') or event in ('subprocess.Popen','os.system'):
        denied.append(event);raise PermissionError(event)
    if event!='open' or isinstance(args[0],int):return
    p=Path(os.fsdecode(args[0])).resolve();flags=args[2]
    if flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):
        if p not in {OUT.resolve(),AUDIT.resolve()}:denied.append(str(p));raise PermissionError(str(p))
    elif p not in allowed and not p.is_relative_to(Path(sys.base_prefix).resolve()):
        denied.append(str(p));raise PermissionError(str(p))
    else:reads.add(str(p))
sys.addaudithook(hook)
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def pin(p):
    b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
p=read(PROOF);cert=read(CERT);source=read(SOURCE);scope=read(SCOPE)
assert p['scope']==pin(SCOPE) and p['source']==pin(SOURCE) and p['certificate']==pin(CERT)
W=tuple(w for w in range(16) if (source['task'][0]|source['task'][1])>>w&1)
labels={w:int(bool(source['task'][1]>>w&1)) for w in W};pi={w:Q(x) for w,x in zip(W,cert['P_prior_all7'])}
assert sum(pi.values())==1 and min(pi.values())>=0
fees=[]
for s in range(16):
    f=sum(cert['charges'][q] for q in range(4) if s>>q&1)
    for (i,j),v in zip(cert['pair_order'],cert['pair_weights']):
        if s&(1<<i|1<<j):f+=v
    fees.append(Q(f))
assert fees==list(map(Q,p['all16_fees']))
assert all(fees[s]<=fees[t] for s in range(16) for t in range(16) if s&t==s)
visited=set();states=set();stats={'nodes':0,'mixed_choices':0,'pure':0,'infeasible_mixed_terminal':0,'zero_prior_mixed_states':0}


def parse(v):return None if v is None else Q(v)


def visit(nid,order,worlds,k,paid):
    record=p['nodes'][nid]
    assert record['order']==list(order) and record['worlds']==list(worlds)
    assert record['suffix_position']==k and record['paid_mask']==paid
    assert paid&sum(1<<q for q in order[:k])==paid
    key=(order,worlds,k,paid)
    if nid in visited:return parse(record['value'])
    assert key not in states;states.add(key);visited.add(nid);stats['nodes']+=1
    labs={labels[w] for w in worlds}
    if len(labs)<=1:
        assert record['kind']=='pure' and record['value']=='0';stats['pure']+=1;return Q(0)
    if not sum(pi[w] for w in worlds):stats['zero_prior_mixed_states']+=1
    if k==4:
        assert record['kind']=='infeasible_mixed_terminal' and record['value'] is None
        stats['infeasible_mixed_terminal']+=1;return None
    assert record['kind']=='choice' and record['query']==order[k]
    q=order[k];assert not(paid>>q&1)
    skip=visit(record['skip_child'],order,worlds,k+1,paid)
    zero=tuple(w for w in worlds if not(w>>q&1));one=tuple(w for w in worlds if w>>q&1)
    a=visit(record['take_children'][0],order,zero,k+1,paid|1<<q)
    b=visit(record['take_children'][1],order,one,k+1,paid|1<<q)
    extra=sum(pi[w] for w in worlds)*(fees[paid|1<<q]-fees[paid]);assert extra>=0
    take=None if a is None or b is None else a+b+extra
    candidates=[v for v in [skip,take] if v is not None];best=min(candidates) if candidates else None
    assert Q(record['weighted_increment'])==extra and parse(record['skip_value'])==skip
    assert parse(record['take_value'])==take and parse(record['value'])==best
    stats['mixed_choices']+=1;return best


assert [r['order'] for r in p['roots']]==[list(o) for o in permutations(range(4))]
roots=[]
for root in p['roots']:
    order=tuple(root['order']);v=visit(root['node'],order,W,0,0)
    assert v is not None and str(v)==root['Bayes_optimum'];roots.append(v)
assert visited==set(range(len(p['nodes']))) and len(visited)==1602
best=min(roots);assert best==Q(1025,47)==Q(p['P_Bayes_exact'])
ba=sum(pi[w]*fees[source['adaptive'][39]['sets'][w]] for w in W);assert ba==Q(1022,47)<best
result={'schema':1,'status':'PASS_FULL_CAUSAL_SKIP_BAYES_CLASS_BY_EXACT_BELLMAN_RECURRENCE',
    'scope':pin(SCOPE),'source':pin(SOURCE),'certificate':pin(CERT),'proof':pin(PROOF),
    'all24_globalorders_checked':True,'all1602states_checked':True,'counts':stats,
    'P_Bayes_exact':str(best),'A39_Bayes_upper':str(ba),'Bayes_gap_lower':str(best-ba),
    'original_zero_prior_worlds_remain_correctness_obligations':True,
    'full_policy_class_coverage':'Every fixed-order zero-error continuation either stops on a pure version space or makes the next causalSKIP/TAKE decision. Both branches are checked; mixedterminal is infeasible evenatzeroprior. State(V,k,S)containsallfutureinformationandfinal-setcostcontext. Monotonecost makespurestopoptimal. PrivateBayesrandomizationislinear andcannotbeatbestpureorder/policy.',
    'P_lower_no_longer_requires_cached32profile_exhaustiveness':True,
    'cached_source_policy_families_imported_or_compared':False,
    'exact_adaptive_minimax_or_priority_claimed':False,'producer_code_imported':False,
    'same_agent_internal_not_external_human_or_formal_review':True,'whole_project_complete':False}
with OUT.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2);f.write('\n')
with AUDIT.open('x',encoding='utf-8') as f:json.dump({'read_files':sorted(reads),'denied':denied,
    'producer_code_imported':False,'boundary':'Pythonafterbootstrap,notOSisolation'},f,indent=2);f.write('\n')
print({'status':result['status'],'orders':24,'states':len(visited),'P_Bayes':str(best),'A39_upper':str(ba),'stats':stats})
