"""Separate certificate reader: direct fees, partition coarsenings, exchange axiom."""
from pathlib import Path
from fractions import Fraction
from itertools import combinations
import hashlib
import json
import os
import sys

H=Path(__file__).resolve().parent
SCOPE=H/'TRIANGLE3_CANDIDATE_SCOPE_V01.json';SOURCE=H/'SOURCE1209_ORIGINAL_FAMILIES_V01.json'
CERT=H/'TRIANGLE3_STRICT_GS_GAP_CANDIDATE_CERTIFICATE_V01.json';DEP=H/'REMAINING_SOURCE_AUDIT_V01.json';PROJ=H/'RESIDUAL_SOURCE_PROJECTIONS_V01.json'
OUT=H/'TRIANGLE3_INDEPENDENT_STRICT_GS_GAP_CHECK_V01.json';AUDIT=H/'TRIANGLE3_INDEPENDENT_STRICT_GS_INPUTS_V01.json'
allowed={p.resolve() for p in [SCOPE,SOURCE,CERT,DEP,PROJ]};reads=set();denied=[]


def audit(event,args):
    if event.startswith('socket.') or event in ('subprocess.Popen','os.system'):
        denied.append(event);raise PermissionError(event)
    if event!='open' or isinstance(args[0],int):return
    p=Path(os.fsdecode(args[0])).resolve();flags=args[2]
    if flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):
        if p not in {OUT.resolve(),AUDIT.resolve()}:denied.append(str(p));raise PermissionError(str(p))
    elif p not in allowed and not p.is_relative_to(Path(sys.base_prefix).resolve()):
        denied.append(str(p));raise PermissionError(str(p))
    else:reads.add(str(p))


sys.addaudithook(audit)
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def pin(p):
    b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}

scope=read(SCOPE);source=read(SOURCE);cert=read(CERT)
assert scope['source']==pin(SOURCE)==cert['source'] and cert['scope']==pin(SCOPE)
assert scope['inherited_monotone_policy_completeness']==pin(DEP)
assert scope['original_projection']==pin(PROJ)
proj=next(r for r in read(PROJ)['rows'] if r['source_id']==1209)
assert proj['source']==source
dep=read(DEP);assert dep['status'].startswith('PASS_FROZEN_1345_PLUS11') and 1209 in dep['residual_sources']
W=scope['W'];assert W==[w for w in range(16) if (source['task'][0]|source['task'][1])>>w&1]
ys={w:int(bool(source['task'][1]>>w&1)) for w in W}

# Enumerate ALL coarsenings of the three prior blocks in each label, rather
# than the union/find answer-word check of earlier producer workflows.
def partitions(n):
    def visit(seq):
        if len(seq)==n:yield seq;return
        for j in range(max(seq)+2):yield from visit(seq+[j])
    yield from visit([0])

physical=[];coarsenings=0
for label,wit in enumerate(proj['physical_label_witnesses']):
    pi=wit['same_partition'];support=set();valid=0
    assert max(pi)==2
    for rho in partitions(3):
        coarsenings+=1;eq=[rho[i] for i in pi]
        if any(eq[i]==eq[j] for i,j in wit['different_record_pairs']):continue
        valid+=1
        support.add(sum(int(eq[2*q]==eq[2*q+1])<<q for q in range(4)))
    assert sorted(support)==[w for w in W if ys[w]==label]
    physical.append({'label':label,'words':sorted(support),'valid_partitions':valid})

charges=cert['charges'];pairweights={tuple(k):v for k,v in zip(cert['pair_order'],cert['pair_weights'])}
assert charges==scope['fixed_analytic_candidate']['individual_charges'] and len(pairweights)==6
fees=[]
for s in range(16):
    fee=sum(charges[i] for i in range(4) if s&(1<<i))
    for i in range(4):
        for j in range(i+1,4):
            if s&(1<<i|1<<j):fee+=pairweights[i,j]
    fees.append(fee)
assert fees==cert['all16_fees'] and min(charges)>0 and min(pairweights.values())>=0
assert sum(v>0 for v in pairweights.values())==3 and pairweights[1,2]==pairweights[1,3]==pairweights[2,3]==4
submod=0;exchange=0
for x in range(16):
    for y in range(16):
        assert fees[x]+fees[y]>=fees[x&y]+fees[x|y];submod+=1
        for i in range(4):
            if not(x>>i&1) or y>>i&1:continue
            options=[fees[x&~(1<<i)]+fees[y|(1<<i)]]
            for j in range(4):
                if (y>>j&1) and not(x>>j&1):
                    options.append(fees[(x&~(1<<i))|(1<<j)]+fees[(y&~(1<<j))|(1<<i)])
            assert fees[x]+fees[y]<=max(options);exchange+=1
for triple in combinations(range(4),3):
    w=[pairweights[p] for p in combinations(triple,2)];assert w.count(min(w))>=2

costs={};paths=0
for kind,n in [('priority',32),('adaptive',40)]:
    assert len(source[kind])==n;costs[kind]=[]
    for col in source[kind]:
        c=[]
        for word in W:
            t=col['tree'];queries=[]
            while isinstance(t,list):
                assert len(t)==3;q=t[0];assert q in range(4) and q not in queries
                queries.append(q);t=t[1+((word>>q)&1)]
            assert t==ys[word]
            mask=sum(1<<q for q in queries);assert mask==col['sets'][word]
            if kind=='priority':
                assert sorted(col['order'])==list(range(4))
                positions=[col['order'].index(q) for q in queries];assert positions==sorted(positions)
            c.append(Fraction(fees[mask]));paths+=1
        costs[kind].append(c)
assert paths==504
prior=list(map(Fraction,cert['P_prior_all7']));assert len(prior)==7 and sum(prior)==1 and min(prior)>=0
vp=Fraction(cert['P_exact_value'])
lower=[sum(p*c for p,c in zip(prior,col)) for col in costs['priority']]
assert min(lower)==vp and list(map(str,lower))==cert['all32P_prior_expectations']
pmix=[(r['P_index'],Fraction(r['probability'])) for r in cert['P_primal_mixture']]
assert sum(p for _,p in pmix)==1 and all(0<=j<32 and p>=0 for j,p in pmix)
upper=[sum(p*costs['priority'][j][w] for j,p in pmix) for w in range(7)]
assert max(upper)==vp and list(map(str,upper))==cert['all7P_primal_costs']

amix=[]
for r in cert['adaptive_mixture']:
    p=Fraction(r['probability']);assert p>=0
    kind=r['kind'];j=r['index'];assert kind in costs and 0<=j<len(costs[kind])
    amix.append((kind,j,p))
assert sum(p for _,_,p in amix)==1
aupper=[sum(p*costs[k][j][w] for k,j,p in amix) for w in range(7)]
va=Fraction(cert['adaptive_upper']);gap=Fraction(cert['strict_gap_lower_bound'])
assert max(aupper)==va<vp and vp-va==gap>0
assert list(map(str,aupper))==cert['all7adaptive_mixture_costs']
ai=scope['fixed_analytic_candidate']['candidate_A_index']
bayesA=sum(p*c for p,c in zip(prior,costs['adaptive'][ai]))
assert bayesA<vp
result={'schema':1,'status':'PASS_STRICT_QUADRATIC_GS_GAP_FULL_ORIGINAL32P40A7WORLDS',
    'scope':pin(SCOPE),'source':pin(SOURCE),'certificate':pin(CERT),
    'costs_directly_reconstructed':fees,'GS_submodular_set_inequalities':submod,'GS_discrete_exchange_tests':exchange,
    'GS_all_triangle_minimum_tests':4,'physical_prior_coarsenings':coarsenings,'physical_supports':physical,
    'original_paths_checked':paths,'inherited_exhaustive_policy_completeness':pin(DEP),
    'P_exact_minimax':str(vp),'adaptive_minimax_upper':str(va),'strict_minimax_gap_lower_bound':str(gap),
    'exact_adaptive_minimax_claimed':False,'all32P_expectations_verified':[str(x) for x in lower],
    'all7P_upper_verified':[str(x) for x in upper],'all7adaptive_upper_verified':[str(x) for x in aupper],
    'fixed_prior_consequence':{'same_prior_as_P_lower':True,'A_index':ai,'A_expectation':str(bayesA),
        'P_Bayes_exact':str(vp),'Bayes_gap_lower_bound':str(vp-bayesA),
        'not_the_same_as_worst_input_gain':True,'zero_prior_worlds_still_zero_error_correctness_obligations':True},
    'one_analytic_candidate_not_numerical_cost_prior_grid_or_LP':True,
    'producer_code_or_diagnostic_read':False,'same_agent_internal_not_external_human_or_formal_review':True,
    'priority':'OPEN','application_advantage':'NOT_ESTABLISHED','whole_project_complete':False}
with OUT.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2);f.write('\n')
with AUDIT.open('x',encoding='utf-8') as f:json.dump({'read_files':sorted(reads),'denied':denied,
    'producer_code_or_diagnostic_read':False,'audit_boundary':'Pythonafterbootstrap,notOSisolation'},f,indent=2);f.write('\n')
print({'status':result['status'],'P_exact':str(vp),'A_upper':str(va),'strict_gap_lower':str(gap),
    'GS_exchange_checks':exchange,'full_paths':paths,'fixed_prior_A39_cost':str(bayesA),'external_review':False})
