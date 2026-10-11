"""Pure mathematical extraction; selected original definitions are byte-identical.
No archived driver or main is included. See the extraction provenance receipt.
This is code reuse, not a new independent mathematical implementation.
"""
from functools import lru_cache
from itertools import product
from fractions import Fraction as F
import re
import time
ZERO = frozenset()
PURE = (frozenset((ZERO,)),)
VOID = (frozenset(),)

def fraction(x):
    assert isinstance(x,str) and re.fullmatch(r'-?\d+(?:/[1-9]\d*)?',x)
    return F(x)


def paths_key(E):return tuple(sorted(sum(1<<q for q in s) for s in E))


def masks(front):return sorted([list(paths_key(E)) for E in front])


def maximize_sets(paths):
    paths=frozenset(paths)
    return frozenset(s for s in paths if not any(s<t for t in paths))


def cheaper(Fenv,Eenv):return all(any(s<=t for t in Eenv) for s in Fenv)


def prune(options):
    kept=[]
    for candidate in set(options):
        if any(cheaper(old,candidate) for old in kept):continue
        kept=[old for old in kept if not cheaper(candidate,old)]
        kept.append(candidate)
    return tuple(sorted(kept,key=paths_key))


def clauses(template):
    result=[];groups={}
    for q,x in enumerate(template):
        if type(x) is int:assert x in (0,1);result.append(((q,x),))
        else:assert isinstance(x,str);groups.setdefault(x,[]).append(q)
    for group in groups.values():
        for i,q in enumerate(group):
            for r in group[:i]:result.extend([((q,0),(r,1)),((q,1),(r,0))])
    return result


def cube(A,B):
    m=len(A);assert len(B)==m
    powers=tuple(3**q for q in range(m))
    digits=tuple(tuple((s//p)%3 for p in powers) for s in range(3**m))
    formulas=[clauses(A),clauses(B)];flags=[]
    for ds in digits:
        flags.append(sum((1<<label) for label,formula in enumerate(formulas)
                         if all(not all(ds[q] and ds[q]-1!=b for q,b in clause) for clause in formula)))
    # Independently enumerate every literal copy assignment, then check all
    # existential projections. This validates source clauses, not policy search.
    sources=[]
    for template in (A,B):
        groups=sorted({x for x in template if isinstance(x,str)})
        sources.append(tuple(tuple(v[x] if isinstance(x,str) else x for x in template)
                             for bits in product((0,1),repeat=len(groups))
                             for v in [dict(zip(groups,bits))]))
    assert set(sources[0]).isdisjoint(sources[1])
    for s,ds in enumerate(digits):
        exact=sum(1<<label for label,W in enumerate(sources)
                  if any(all(d==0 or d-1==w[q] for q,d in enumerate(ds)) for w in W))
        assert exact==flags[s]
    return {'m':m,'powers':powers,'digits':digits,'flags':tuple(flags),'world_counts':list(map(len,sources))}


class Frontiers:
    def __init__(self,data,deadline,state_cap,pair_cap,front_cap):
        self.data=data;self.deadline=deadline;self.state_cap=state_cap
        self.pair_cap=pair_cap;self.front_cap=front_cap;self.states=0;self.pairs=0
        self.ad=lru_cache(None)(self._ad);self.ordered=lru_cache(None)(self._ordered)

    def tick(self):
        self.states+=1
        if self.states>self.state_cap:raise MemoryError('STATE_CAP')
        if self.states%256==0 and time.monotonic()>self.deadline:raise TimeoutError('TIME_CAP')

    def base(self,s):
        f=self.data['flags'][s]
        return VOID if f==0 else PURE if f!=3 else None

    def join(self,q,left,right):
        result=[]
        for E in left:
            for G in right:
                self.pairs+=1
                if self.pairs>self.pair_cap:raise MemoryError('ENVELOPE_PRODUCT_CAP')
                result.append(maximize_sets(s|{q} for s in E|G))
        return result

    def checked_prune(self,options):
        result=prune(options)
        if len(result)>self.front_cap:raise MemoryError('FRONTIER_CAP')
        return result

    def _ad(self,s):
        self.tick();base=self.base(s)
        if base is not None:return base
        options=[]
        for q,d in enumerate(self.data['digits'][s]):
            if d:continue
            p=self.data['powers'][q]
            options.extend(self.join(q,self.ad(s+p),self.ad(s+2*p)))
        assert options
        return self.checked_prune(options)

    def _ordered(self,s,remaining):
        self.tick();base=self.base(s)
        if base is not None:return base
        if not remaining:return ()
        q=remaining[0];tail=remaining[1:];assert self.data['digits'][s][q]==0
        p=self.data['powers'][q]
        options=list(self.ordered(s,tail))
        options.extend(self.join(q,self.ordered(s+p,tail),self.ordered(s+2*p,tail)))
        return self.checked_prune(options)


def replay(data,tree,order=None):
    position=None if order is None else {q:i for i,q in enumerate(order)}
    if position is not None:assert sorted(order)==list(range(data['m']))
    leaves=[];nodes=0
    def visit(node,s,paid,last):
        nonlocal nodes
        flags=data['flags'][s]
        if flags==0:return
        nodes+=1
        if type(node) is int:
            assert node in (0,1) and flags==1<<node
            leaves.append(paid);return
        assert isinstance(node,list) and len(node)==3
        q=node[0];assert type(q) is int and 0<=q<data['m'] and data['digits'][s][q]==0
        loc=last
        if position is not None:loc=position[q];assert loc>last
        p=data['powers'][q]
        visit(node[1],s+p,paid|{q},loc);visit(node[2],s+2*p,paid|{q},loc)
    visit(tree,0,ZERO,-1)
    return paths_key(maximize_sets(leaves)),nodes,len(leaves)


def verify_certificate(E,chosen,cert,m=7):
    x=list(map(fraction,cert['primal']));assert len(x)==m+1
    # Reconstruct rows directly from mathematical constraints, not the producer matrix.
    rows=[([-int(q==j) for q in range(m+1)],0) for j in range(m+1)]
    rows += [([int(mask>>q&1) for q in range(m)]+[0],1) for mask in E]
    rows += [([-int(mask>>q&1) for q in range(m)]+[1],0) for mask in chosen]
    dual=[F(0)]*len(rows);seen=set()
    for index,value in cert['dual_sparse']:
        assert type(index) is int and 0<=index<len(rows) and index not in seen
        seen.add(index);dual[index]=fraction(value);assert dual[index]>=0
    assert all(sum(a*v for a,v in zip(row,x))<=rhs for row,rhs in rows)
    assert all(sum(y*row[q] for y,(row,rhs) in zip(dual,rows))==int(q==m) for q in range(m+1))
    objective=fraction(cert['objective'])
    assert x[-1]==objective==sum(y*rhs for y,(row,rhs) in zip(dual,rows))
    return objective,x[:m]


def cost(E,c):return max(sum(c[q] for q in range(len(c)) if mask>>q&1) for mask in E)

