"""Replay one OLD strictly positive seven-query witness and its full-P dual.

Zero-prior worlds are always retained for correctness/purity. The dynamic
program evaluates only the fixed supplied prior, price and all5040 orders.
It does not choose or optimize a prior/price and is not a new gap search.
"""
from fractions import Fraction as F
from functools import lru_cache
import itertools
from proofio import data


def projection(same,different,queries):
    projected=set()
    for bits in itertools.product((0,1),repeat=7):
        parent=list(range(14))
        def root(x):
            while parent[x]!=x:x=parent[x]
            return x
        def merge(a,b):parent[root(b)]=root(a)
        for a,b in same:merge(a,b)
        for bit,(a,b) in zip(bits,queries):
            if bit:merge(a,b)
        if any(root(a)==root(b) for a,b in different):continue
        if any(not bit and root(a)==root(b) for bit,(a,b) in zip(bits,queries)):continue
        # Assign fresh distinct classes to the remaining components. This
        # realizes every accepted word and all SAME/DIFFERENT constraints.
        projected.add(bits)
    return projected


def verify():
    old=data('seven');eps=F(old['old_epsilon']);assert eps==F(1,3)
    prices=list(map(F,old['prices']));assert prices==list(map(F,old['expected']['prices']))
    assert prices==[F(2),F(2),F(3),F(1,3),F(1),F(1),F(1)] and all(v>0 for v in prices)
    worlds=old['worlds'];assert len(worlds)==16
    expectedA={(a,1,a,b,a,c,c) for a,b,c in itertools.product((0,1),repeat=3)}
    expectedB={(u,u,0,v,w,w,v) for u,v,w in itertools.product((0,1),repeat=3)}
    assert {tuple(w['bits']) for w in worlds if w['label']=='A'}==expectedA
    assert {tuple(w['bits']) for w in worlds if w['label']=='B'}==expectedB
    assert not expectedA&expectedB
    physical=old['complete14record_realization'];queries=[[2*q,2*q+1] for q in range(7)]
    assert physical['query_pairs']==queries
    for label,expected in [('A',expectedA),('B',expectedB)]:
        assert projection(physical[label+'_SAME'],physical[label+'_DIFFERENT'],queries)==expected
    def evalpoly(coeff):return sum((F(c)*eps**i for i,c in enumerate(coeff)),F(0))
    den=evalpoly(old['denominator_polynomial']);assert den>0
    prior=[F(0)]*16
    for w,coeff in old['prior_numerator_polynomials'].items():prior[int(w)]=evalpoly(coeff)/den
    expectedprior=[F(0)]*16
    for w,num in zip([0,4,5,13,15],[9,1,1,1,5]):expectedprior[w]=F(num,17)
    assert prior==expectedprior and sum(prior)==1 and all(p>=0 for p in prior)
    def traces(column,priority):
        result=[]
        if priority:assert sorted(column['order'])==list(range(7))
        for w in worlds:
            tree=column['tree'];seen=[]
            while isinstance(tree,list):
                assert len(tree)==3;q=tree[0]
                assert type(q) is int and q in range(7) and q not in seen
                seen.append(q);tree=tree[1+w['bits'][q]]
            assert tree==w['label']
            if priority:assert seen==sorted(seen,key=column['order'].index)
            result.append(sum((prices[q] for q in seen),F(0)))
        return result
    def mixed_upper(columns,priority):
        weights=[evalpoly(c['probability_numerator'])/den if priority else F(c['probability']) for c in columns]
        assert sum(weights)==1 and all(w>=0 for w in weights)
        costs=[traces(c,priority) for c in columns]
        return max(sum((p*c[w] for p,c in zip(weights,costs)),F(0)) for w in range(16)),weights
    Aupper,_=mixed_upper(old['adaptive_upper'],False)
    Pupper,mix=mixed_upper(old['priority_upper'],True)
    assert Aupper==F(13,3) and Pupper==F(227,51) and mix==[F(n,17) for n in [4,5,6,2]]
    full=(1<<16)-1;labelA=sum(1<<i for i,w in enumerate(worlds) if w['label']=='A')
    labelB=full^labelA;one=[sum(1<<i for i,w in enumerate(worlds) if w['bits'][q]) for q in range(7)]
    pn=[int(p*17) for p in prior];cp=[int(c*3) for c in prices]
    assert all(F(n,17)==p for n,p in zip(pn,prior)) and all(F(n,3)==c for n,c in zip(cp,prices))
    @lru_cache(None)
    def mass(state):return sum(pn[i] for i in range(16) if state>>i&1)
    @lru_cache(None)
    def fixed(suffix,state):
        # A zero prior must never be mistaken for an empty correctness set.
        if not state&labelA or not state&labelB:return 0
        if not suffix:return 10**9
        q=suffix[0];rest=suffix[1:]
        skip=fixed(rest,state)
        take=mass(state)*cp[q]+fixed(rest,state&~one[q])+fixed(rest,state&one[q])
        return min(skip,take)
    values=[fixed(order,full) for order in itertools.permutations(range(7))]
    assert len(values)==5040 and min(values)==227
    Plower=F(min(values),51);assert Plower==Pupper and Plower-Aupper==F(2,17)
    assert old['expected']['A_feasible_upper']==str(Aupper) and old['expected']['P_exact_minimax']==str(Pupper)
    return {'worlds':16,'complete_record_endpoints':14,'strict_positive_prices':[str(c) for c in prices],
        'fixed_prior':[str(p) for p in prior],'orders_checked':5040,'fixed_prior_suffix_states':fixed.cache_info().currsize,
        'A_feasible_upper':str(Aupper),'P_exact_minimax':str(Pupper),'gap_at_least':str(Plower-Aupper),
        'fresh_exact_full_A_optimum_claimed':False,'zero_prior_worlds_kept_for_correctness':True}
