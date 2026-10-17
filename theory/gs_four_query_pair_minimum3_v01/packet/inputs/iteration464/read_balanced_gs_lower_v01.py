"""Separate Fraction reader; rebuild costs from merge blocks, not producer code."""
from pathlib import Path
from fractions import Fraction
from itertools import combinations,permutations
from functools import lru_cache
import gzip
import hashlib
import json
import math
import os
import sys

OUTROOT=Path(__file__).resolve().parent
H=Path(sys.argv[2]).resolve()
SELECTED={2,5,8,10,13,15}
SID=int(sys.argv[1]);out=OUTROOT/f'SOURCE{SID}_BALANCED_LOWER_RESULT_V01.json';auditout=OUTROOT/f'SOURCE{SID}_BALANCED_LOWER_INPUTS_V01.json'
scopefile=H/'GS_SCOPE_V01.json';sourcefile=H/f'SOURCE{SID}_ORIGINAL_FAMILIES_V01.json';prooffile=H/f'SOURCE{SID}_GS_PROOF_V01.json.gz'
projectionfile=H/'RESIDUAL_SOURCE_PROJECTIONS_V01.json';dependencyfile=H/'REMAINING_SOURCE_AUDIT_V01.json'
allowed={p.resolve() for p in [scopefile,sourcefile,prooffile,projectionfile,dependencyfile]};reads=set();denied=[]


def audit(event,args):
    if event.startswith('socket.') or event in ('subprocess.Popen','os.system'):
        denied.append(event);raise PermissionError(event)
    if event!='open' or isinstance(args[0],int):return
    p=Path(os.fsdecode(args[0])).resolve();flags=args[2]
    write=bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
    if write:
        if p not in {out.resolve(),auditout.resolve()}:denied.append(str(p));raise PermissionError(str(p))
    elif p not in allowed and not p.is_relative_to(Path(sys.base_prefix).resolve()):
        denied.append(str(p));raise PermissionError(str(p))
    else:reads.add(str(p))


sys.addaudithook(audit)


def read(p):return json.loads(p.read_text(encoding='utf-8'))
def pin(p):
    b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}


scope=read(scopefile);source=read(sourcefile);proof=json.loads(gzip.decompress(prooffile.read_bytes()))
assert pin(scopefile)['sha256']=='787e74427596fee670d7b1828682c697984dff4c31f08f8feebf0b6064a808a9'==proof['scope_sha256']
sr=next(r for r in scope['sources'] if r['source_id']==SID)
assert sr['source']==pin(sourcefile) and sr['source']['sha256']==proof['source_sha256']
assert pin(projectionfile)==scope['inherited_classification']['source_projection']
assert pin(dependencyfile)==scope['inherited_classification']['dependency_audit']
projection=next(r for r in read(projectionfile)['rows'] if r['source_id']==SID)
assert source==projection['source'] and sr['physical_label_witnesses']==projection['physical_label_witnesses']
AC,PC=sr['original_A_P_counts'];NC=AC+PC
assert len(source['adaptive'])==AC and len(source['priority'])==PC
W0=[w for w in range(16) if source['task'][0]>>w&1];W1=[w for w in range(16) if source['task'][1]>>w&1]
assert not set(W0)&set(W1)
W=sorted(W0+W1);WN=len(W);assert W==sr['W']==proof['W']
labels={w:int(w in W1) for w in W};physical_checks=0
for target,wit in zip(source['task'],projection['physical_label_witnesses']):
    support=0;pi=wit['same_partition']
    for word in range(16):
        eq=[[pi[i]==pi[j] for j in range(8)] for i in range(8)]
        for q in range(4):
            if word>>q&1:eq[2*q][2*q+1]=eq[2*q+1][2*q]=True
        for k in range(8):
            for i in range(8):
                for j in range(8):eq[i][j]=eq[i][j] or (eq[i][k] and eq[k][j])
        physical_checks+=1
        if any(eq[2*q][2*q+1]!=bool(word>>q&1) for q in range(4)):continue
        if any(eq[i][j] for i,j in wit['different_record_pairs']):continue
        support|=1<<word
    assert support==target
profiles=[];pathchecks=0
for kind in ['priority','adaptive']:
    for col in source[kind]:
        profile=[]
        for word in W:
            t=col['tree'];path=[]
            while isinstance(t,list):
                assert len(t)==3;q=t[0];assert type(q) is int and q in range(4) and q not in path
                path.append(q);t=t[1+((word>>q)&1)]
            assert t==labels[word]
            mask=sum(1<<q for q in path);assert mask==col['sets'][word]
            if kind=='priority':
                assert sorted(col['order'])==list(range(4))
                positions=[col['order'].index(q) for q in path];assert positions==sorted(positions)
            profile.append(mask);pathchecks+=1
        profiles.append(profile)
assert len({tuple(x) for x in profiles[:PC]})==PC and len({tuple(x) for x in profiles[PC:]})==AC
assert all(p in profiles[PC:] for p in profiles[:PC])


def merge_histories(blocks,prior=()):
    if len(blocks)==1:yield prior;return
    for a,b in combinations(range(len(blocks)),2):
        merged=tuple(sorted(blocks[a]+blocks[b]))
        nextblocks=tuple(sorted([x for i,x in enumerate(blocks) if i not in (a,b)]+[merged]))
        yield from merge_histories(nextblocks,prior+((blocks[a],blocks[b],merged),))


histories=list(merge_histories(((0,),(1,),(2,),(3,))))
assert len(histories)==18
DIM=7;eye=[tuple(int(i==j) for i in range(DIM)) for j in range(DIM)]
counts={'nodes':0,'splits':0,'closed_lifting_leaves':0,'pure_saddle_leaves':0,'fixed_rational_minimax_leaves':0,
    'unclosed_leaves':0,'not_started_roots':0,'column_deletions':0,'row_deletions':0,'full_original_row_P_lifts':0,
    'scalar_inequalities':0,'exact_fraction_rank_calls':0}


def scalar(a,b):
    assert len(a)==len(b)==DIM
    return sum(x*y for x,y in zip(a,b))


@lru_cache(maxsize=100000)
def rational_rank(vectors):
    m=[[Fraction(x) for x in v] for v in vectors];pivot=0
    for j in range(DIM):
        k=next((i for i in range(pivot,len(m)) if m[i][j]),None)
        if k is None:continue
        m[pivot],m[k]=m[k],m[pivot];a=m[pivot][j];m[pivot]=[x/a for x in m[pivot]]
        for i in range(len(m)):
            if i!=pivot:
                a=m[i][j];m[i]=[x-a*y for x,y in zip(m[i],m[pivot])]
        pivot+=1
        if pivot==len(m):break
    return pivot


def checked_rank(rows):
    counts['exact_fraction_rank_calls']+=1;return rational_rank(tuple(rows))


def primitive(v):
    d=math.gcd(*v);assert d>0;return tuple(x//d for x in v)


def clip(rays,normals,form,sign):
    n=tuple(sign*x for x in form);pos=[r for r in rays if scalar(n,r)>0];neg=[r for r in rays if scalar(n,r)<0]
    zero=[r for r in rays if scalar(n,r)==0];assert pos and neg
    candidates=set(pos+zero)
    for a in pos:
        for b in neg:
            va,vb=scalar(n,a),scalar(n,b);candidates.add(primitive(tuple(-vb*x+va*y for x,y in zip(a,b))))
    constraints=normals+[n];extreme=[]
    for r in sorted(candidates):
        assert all(x>=0 for x in r) and all(scalar(c,r)>=0 for c in constraints)
        rank=checked_rank(c for c in constraints if scalar(c,r)==0);assert rank<DIM
        if rank==DIM-1:extreme.append(r)
    assert checked_rank(extreme)==DIM
    return extreme,constraints


visited=set()
def visit(nid,rays,normals,rows,columns,fees):
    assert nid not in visited;visited.add(nid);counts['nodes']+=1;rec=proof['nodes'][nid]
    assert set(map(tuple,rec['rays']))==set(rays) and len(rec['rays'])==len(rays)
    def geq(a,b):
        for ray in rays:
            counts['scalar_inequalities']+=1
            if scalar(fees[a],ray)<scalar(fees[b],ray):return False
        return True
    kind=rec['kind']
    if kind in ('pure_saddle','fixed_rational_minimax'):
        assert rec['trace']==[] and rec['terminal_rows']==rows and rec['terminal_columns']==columns
        if kind=='pure_saddle':
            p=rec['original_P'];w=W.index(rec['hard_word']);anchor=profiles[p][w]
            assert p in range(PC) and anchor==rec['anchor_mask']
            assert all(geq(profiles[c][w],anchor) for c in range(PC,NC))
            assert all(geq(anchor,profiles[p][v]) for v in range(WN))
            counts['pure_saddle_leaves']+=1;return True
        t=sr['fixed_rational_templates'][rec['template']]
        pi=[Fraction(x) for x in t['prior']];mix=[(p['policy_index'],Fraction(p['probability'])) for p in t['priority_mixture']]
        assert len(pi)==WN and sum(pi)==1 and min(pi)>=0
        assert sum(x for _,x in mix)==1 and all(p in range(PC) and x>=0 for p,x in mix)
        for ray in rays:
            cost=[scalar(f,ray) for f in fees]
            upper=[sum(x*cost[profiles[p][w]] for p,x in mix) for w in range(WN)]
            value=sum(x*y for x,y in zip(pi,upper))
            assert all(sum(pi[w]*cost[profiles[c][w]] for w in range(WN))>=value for c in range(PC,NC))
            assert all(x<=value for x in upper);counts['scalar_inequalities']+=AC+WN
        counts['fixed_rational_minimax_leaves']+=1;return True
    rows=list(rows);columns=list(columns)
    for deletion in rec['trace']:
        a,b=deletion['victim'],deletion['by'];assert a!=b
        if deletion['kind']=='column':
            assert a in columns and b in columns and all(geq(profiles[a][w],profiles[b][w]) for w in rows)
            columns.remove(a);counts['column_deletions']+=1
        else:
            assert deletion['kind']=='row' and a in rows and b in rows and all(geq(profiles[c][b],profiles[c][a]) for c in columns)
            rows.remove(a);counts['row_deletions']+=1
        assert rows and columns
    assert rec['terminal_rows']==rows and rec['terminal_columns']==columns
    if kind=='closed':
        lifts=rec['P_lifts_on_all_original_rows'];assert [l['column'] for l in lifts]==columns
        for lift in lifts:
            p,c=lift['original_P'],lift['column'];assert p in range(PC)
            assert all(geq(profiles[c][w],profiles[p][w]) for w in range(WN));counts['full_original_row_P_lifts']+=1
        counts['closed_lifting_leaves']+=1;return True
    if kind=='unclosed':
        assert rec['reason'] in ['COMPUTE_BUDGET','RAY_BUDGET','NODE_BUDGET','DOMINANCE_AND_FIXED_TEMPLATES_INSUFFICIENT_ON_FEE_ORDER_CELL']
        counts['unclosed_leaves']+=1;return False
    assert kind=='split' and len(rec['children'])==2
    form=tuple(rec['form']);assert len(form)==DIM and min(scalar(form,r) for r in rays)<0<max(scalar(form,r) for r in rays)
    counts['splits']+=1;passed=True
    for sign,child in zip((1,-1),rec['children']):
        newrays,newnormals=clip(rays,normals,form,sign)
        passed&=visit(child,newrays,newnormals,rows,columns,fees)
    return passed


expected=[(i,list(order)) for i in range(18) for order in permutations(range(4))]
assert [(r['hierarchy'],r['individual_order']) for r in proof['roots']]==expected
for root in proof['roots']:
    if root['hierarchy'] not in SELECTED:continue
    if root['node'] is None:
        assert root['closed'] is False and root['reason']=='NOT_STARTED_AFTER_GLOBAL_BUDGET';counts['not_started_roots']+=1;continue
    history=histories[root['hierarchy']];order=root['individual_order'];fees=[]
    for mask in range(16):
        vector=[sum(int(bool(mask>>q&1)) for q in range(4) if order.index(q)>=k) for k in range(4)]+[0,0,0]
        for i,j in combinations(range(4),2):
            if not(mask&(1<<i|1<<j)):continue
            first=next(t for t,(_,_,block) in enumerate(history) if i in block and j in block)
            for k in range(first,3):vector[4+k]+=1
        fees.append(tuple(vector))
    before=len(visited);closed=visit(root['node'],eye,eye,list(range(WN)),list(range(NC)),fees)
    assert closed==root['closed'] and len(visited)-before==root['nodes']
selectedroots=[r for r in proof['roots'] if r['hierarchy'] in SELECTED]
assert len(selectedroots)==144 and counts['nodes']==len(visited)==sum(r['nodes'] for r in selectedroots)
assert counts['unclosed_leaves']==counts['not_started_roots']==0
closed=sum(r['closed'] for r in selectedroots)
assert closed==144
result={'schema':1,'status':'PASS_ALL144_BALANCED_HIERARCHY_GS_SUPPORT2_COVER_THIS_SOURCE' if closed==144 else 'VALID_PARTIAL_CONTINUOUS_GS_COVER_EXPLICIT_OPEN_REGIONS_NOT_A_GAP',
    'source_id':SID,'scope':pin(scopefile),'source':pin(sourcefile),'proof':pin(prooffile),
    'counts':counts,'roots':144,'original_full_GS_roots':432,'selected_balanced_hierarchy_ids':sorted(SELECTED),'closed_roots':closed,'unclosed_roots':[r for r in selectedroots if not r['closed']],
    'source_balanced_hierarchy_equality_accepted':closed==144,'source_full_GS_equality_claimed':False,'physical_support_word_checks':physical_checks,
    'original_policy_paths_checked':pathchecks,'original_A_P_counts':[AC,PC],
    'inherited_global_source_policy_completeness':scope['inherited_classification'],
    'costs_rebuilt_from_binary_merges_not_producer_or_geometry_coefficients':True,
    'whole_cone_rank_method':'FractionGaussJordan; producer uses primitive integer elimination',
    'game_argument':'Common reduced row/column game followed by full-original-row P lifts; pure and fixed-rational leaves close original game directly; P inclusion gives reverse inequality.',
    'cover_argument':'All24closedindividualorders times6balancedGSmergehistories;targetall2disjointpaircostsareh3=0faces;closedhalfconesincludeties/zeros.',
    'producer_code_or_summary_read':False,'no_numerical_games_LP_fee_prior_grid_global_catalogue_API_PDF_or_publication':True,
    'same_agent_not_external_human_independent_or_formal_kernel':True,'priority':'OPEN','whole_project_complete':False}
with out.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
with auditout.open('x',encoding='utf-8') as f:json.dump({'read_files':sorted(reads),'denied':denied,'producer_code_or_summary_read':False,'audit_boundary':'Pythonafterbootstrap,notOSisolation'},f,indent=2);f.write('\n')
print({'status':result['status'],'source_id':SID,'closed_roots':closed,'roots':144,'counts':counts,'paths':pathchecks})
