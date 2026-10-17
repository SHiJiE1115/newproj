"""Read the universal-cone proof using Fraction elimination, not its producer."""
from fractions import Fraction
from itertools import combinations, permutations
import gzip
import sys
import hashlib
import json
from math import gcd
from pathlib import Path

H = Path(__file__).resolve().parent
B = H.parent


def pin(path):
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


spec=read(Path(sys.argv[1]))
scopefile=Path(spec['scope']['path']);sourcefile=Path(spec['source']['path']);prooffile=Path(spec['proof']['path'])
for key,path in [('scope',scopefile),('source',sourcefile),('proof',prooffile)]:assert pin(path)==spec[key]
scope=read(scopefile);source=read(sourcefile);proof=json.loads(gzip.decompress(prooffile.read_bytes()))
assert proof['scope_sha256']==pin(scopefile)['sha256']==spec['scope']['sha256']
assert proof['source_sha256']==pin(sourcefile)['sha256']==scope['source_sha256']
assert source['task']==scope['source_task']
ACOUNT,PCOUNT=scope['A_P_counts'];NC=ACOUNT+PCOUNT
assert len(source['adaptive'])==ACOUNT and len(source['priority'])==PCOUNT
assert pin(H/'REMAINING_SOURCE_AUDIT_V01.json')['sha256']==scope['dependency_audit_sha256']
assert pin(H/'RESIDUAL_SOURCE_PROJECTIONS_V01.json')['sha256']==scope['source_projection_sha256']
projection=next(r for r in read(H/'RESIDUAL_SOURCE_PROJECTIONS_V01.json')['rows'] if r['source_id']==scope['source_orbit'])
assert projection['source']==source
physical=projection['physical_label_witnesses']
for target,witness in zip(source['task'],physical):
    pi=witness['same_partition'];pairs=witness['different_record_pairs'];support=0
    for word in range(16):
        components=[{i} for i in range(8)]
        def merge(a,b):
            x=next(c for c in components if a in c);y=next(c for c in components if b in c)
            if x is not y:x.update(y);components.remove(y)
        for i in range(8):
            for j in range(i):
                if pi[i]==pi[j]:merge(i,j)
        for q in range(4):
            if word>>q&1:merge(2*q,2*q+1)
        same=lambda a,b:any(a in c and b in c for c in components)
        if any(same(2*q,2*q+1)!=bool(word>>q&1) for q in range(4)):continue
        if any(same(a,b) for a,b in pairs):continue
        support|=1<<word
    assert support==target
W0=[w for w in range(16) if source['task'][0]>>w&1]
W1=[w for w in range(16) if source['task'][1]>>w&1]
W=sorted(W0+W1);WN=len(W)
assert W==scope['W']==proof['W']
labels={w:int(w in W1) for w in W}
profiles = []
path_checks = 0
for kind, expected in [('priority', PCOUNT), ('adaptive', ACOUNT)]:
    assert len(source[kind]) == expected
    for col in source[kind]:
        profile = []
        for word in W:
            node, path = col['tree'], []
            while isinstance(node, list):
                assert len(node) == 3
                q = node[0]
                assert type(q) is int and q in range(4) and q not in path
                path.append(q)
                node = node[1 + ((word >> q) & 1)]
            assert node == labels[word]
            mask = sum(1 << q for q in path)
            assert col['sets'][word] == mask
            if kind == 'priority':
                assert sorted(col['order']) == [0,1,2,3]
                positions = [col['order'].index(q) for q in path]
                assert positions == sorted(positions)
            profile.append(mask)
            path_checks += 1
        profiles.append(profile)
assert path_checks == NC*WN
assert len({tuple(p) for p in profiles[PCOUNT:]}) == ACOUNT
assert len({tuple(p) for p in profiles[:PCOUNT]}) == PCOUNT
assert all(p in profiles[PCOUNT:] for p in profiles[:PCOUNT])


def scalar(a, b):
    assert len(a) == len(b) == 5
    return sum(x*y for x,y in zip(a,b))


def rational_rank(vectors):
    """Gauss-Jordan over Q, independent of the producer's primitive integer rows."""
    matrix = [[Fraction(x) for x in vector] for vector in vectors]
    pivot = 0
    for column in range(5):
        found = next((i for i in range(pivot, len(matrix)) if matrix[i][column]), None)
        if found is None:
            continue
        matrix[pivot], matrix[found] = matrix[found], matrix[pivot]
        factor = matrix[pivot][column]
        matrix[pivot] = [x/factor for x in matrix[pivot]]
        for i in range(len(matrix)):
            if i != pivot:
                factor = matrix[i][column]
                matrix[i] = [x-factor*y for x,y in zip(matrix[i], matrix[pivot])]
        pivot += 1
        if pivot == len(matrix):
            break
    return pivot


def primitive(vector):
    divisor = gcd(*vector)
    assert divisor > 0
    return tuple(x//divisor for x in vector)


eye = [tuple(int(i == j) for i in range(5)) for j in range(5)]
visited = set()
counts = {'nodes': 0, 'splits': 0, 'closed_lifting_leaves': 0, 'pure_saddle_leaves': 0, 'fixed_rational_minimax_leaves':0, 'unclosed_leaves':0, 'not_started_roots':0,
          'column_deletions': 0, 'row_deletions': 0, 'full_original_row_P_lifts': 0,
          'scalar_inequalities': 0, 'exact_fraction_rank_calls': 0}


def checked_rank(vectors):
    counts['exact_fraction_rank_calls'] += 1
    return rational_rank(vectors)


def clipped_generators(rays, normals, form, sign):
    signed = tuple(sign*x for x in form)
    positive = [r for r in rays if scalar(signed,r) > 0]
    negative = [r for r in rays if scalar(signed,r) < 0]
    boundary = [r for r in rays if scalar(signed,r) == 0]
    assert positive and negative
    candidates = set(positive+boundary)
    for a in positive:
        for b in negative:
            aa, bb = scalar(signed,a), scalar(signed,b)
            candidates.add(primitive([-bb*x+aa*y for x,y in zip(a,b)]))
    constraints = normals+[signed]
    extreme = set()
    for ray in candidates:
        assert all(x >= 0 for x in ray)
        assert all(scalar(n,ray) >= 0 for n in constraints)
        rank = checked_rank([n for n in constraints if scalar(n,ray) == 0])
        assert rank <= 4
        if rank == 4:
            extreme.add(ray)
    assert checked_rank(extreme) == 5
    return extreme, constraints


def visit(index, rays, normals, rows, columns, fees):
    assert type(index) is int and 0 <= index < len(proof['nodes']) and index not in visited
    visited.add(index)
    counts['nodes'] += 1
    rec = proof['nodes'][index]
    actual_rays = [tuple(v) for v in rec['rays']]
    assert len(set(actual_rays)) == len(actual_rays)
    assert set(actual_rays) == set(rays)
    assert checked_rank(rays) == 5
    assert all(all(scalar(n,r) >= 0 for n in normals) for r in rays)

    def geq(s,t):
        difference = [a-b for a,b in zip(fees[s],fees[t])]
        for ray in rays:
            counts['scalar_inequalities'] += 1
            if scalar(difference,ray) < 0:
                return False
        return True

    if rec['kind'] == 'pure_saddle':
        assert rec['trace'] == []
        assert rec['terminal_rows'] == rows and rec['terminal_columns'] == columns
        word, p = rec['hard_word'], rec['original_P']
        assert {'word':word,'P':p} in scope['pure_saddle_templates']
        w = W.index(word)
        anchor = profiles[p][w]
        assert rec['anchor_mask'] == anchor
        assert all(geq(profiles[a][w],anchor) for a in range(PCOUNT,NC))
        assert all(geq(anchor,profiles[p][v]) for v in range(WN))
        counts['pure_saddle_leaves'] += 1
        return True

    if rec['kind']=='fixed_rational_minimax':
        assert rec['trace']==[] and rec['terminal_rows']==rows and rec['terminal_columns']==columns
        tid=rec['template'];assert type(tid) is int and tid in range(len(scope['fixed_mixed_templates']))
        template=scope['fixed_mixed_templates'][tid]
        prior=[Fraction(x) for x in template['prior']]
        mixture=[(r['policy_index'],Fraction(r['probability'])) for r in template['priority_mixture']]
        assert len(prior)==WN and sum(prior)==1 and all(x>=0 for x in prior)
        assert sum(x for _,x in mixture)==1 and all(p in range(PCOUNT) and x>=0 for p,x in mixture)
        for ray in rays:
            cost=[scalar(f,ray) for f in fees]
            upper=[sum(x*cost[profiles[p][w]] for p,x in mixture) for w in range(WN)]
            anchor=sum(x*y for x,y in zip(prior,upper))
            for c in range(PCOUNT,NC):
                assert sum(prior[w]*cost[profiles[c][w]] for w in range(WN))>=anchor
                counts['scalar_inequalities']+=1
            assert all(v<=anchor for v in upper);counts['scalar_inequalities']+=WN
        counts['fixed_rational_minimax_leaves']+=1
        return True

    rows, columns = list(rows), list(columns)
    for deletion in rec['trace']:
        victim, by = deletion['victim'], deletion['by']
        assert victim != by
        if deletion['kind'] == 'column':
            assert victim in columns and by in columns
            assert all(geq(profiles[victim][w],profiles[by][w]) for w in rows)
            columns.remove(victim)
            counts['column_deletions'] += 1
        else:
            assert deletion['kind'] == 'row' and victim in rows and by in rows
            assert all(geq(profiles[c][by],profiles[c][victim]) for c in columns)
            rows.remove(victim)
            counts['row_deletions'] += 1
        assert rows and columns
    assert rec['terminal_rows'] == rows and rec['terminal_columns'] == columns

    if rec['kind'] == 'closed':
        lifts = rec['P_lifts_on_all_original_rows']
        assert [p['column'] for p in lifts] == columns
        for lift in lifts:
            c, p = lift['column'], lift['original_P']
            assert p in range(PCOUNT)
            assert all(geq(profiles[c][w],profiles[p][w]) for w in range(WN))
            counts['full_original_row_P_lifts'] += 1
        counts['closed_lifting_leaves'] += 1
        return True

    if rec['kind']=='unclosed':
        assert rec['reason'] in ('COMPUTE_BUDGET','NODE_BUDGET','PURE_DOMINANCE_AND_FULL_ROW_LIFTING_INSUFFICIENT_ON_FIXED_FEE_ORDER_CELL')
        counts['unclosed_leaves']+=1
        return False
    assert rec['kind'] == 'split'
    assert len(rec['children']) == 2
    form = tuple(rec['form'])
    assert len(form) == 5 and any(form)
    assert min(scalar(form,r) for r in rays) < 0 < max(scalar(form,r) for r in rays)
    counts['splits'] += 1
    passed=True
    for sign, child in zip((1,-1), rec['children']):
        newrays, newnormals = clipped_generators(rays,normals,form,sign)
        passed &= visit(child,newrays,newnormals,rows,columns,fees)
    return passed


expected_roots = [(list(e),list(o)) for e in combinations(range(4),2) for o in permutations(range(4))]
assert len(proof['roots']) == 144
assert [(r['pair'],r['order']) for r in proof['roots']] == expected_roots
for root in proof['roots']:
    if root['node'] is None:
        assert root['closed'] is False and root['reason']=='NOT_STARTED_AFTER_GLOBAL_BUDGET'
        counts['not_started_roots']+=1;continue
    pair, order = root['pair'], root['order']
    positions = {q:order.index(q) for q in range(4)}
    fees = []
    for mask in range(16):
        # c_order[j] = d0+...+dj. d0,...,d3,lambda are nonnegative.
        coeff = [sum(1 for q in range(4) if mask & (1<<q) and positions[q] >= k) for k in range(4)]
        coeff.append(int(any(mask & (1<<q) for q in pair)))
        fees.append(coeff)
    before = len(visited)
    closed=visit(root['node'],eye,eye,list(range(WN)),list(range(NC)),fees)
    assert closed==root['closed']
    assert len(visited)-before == root['nodes']
assert visited == set(range(len(proof['nodes'])))
assert counts['nodes']==proof['stats']['cone_nodes']==len(proof['nodes'])
assert counts['splits']==proof['stats']['splits']
assert counts['pure_saddle_leaves']==proof['stats']['pure_saddle_leaves']
assert counts['fixed_rational_minimax_leaves']==proof['stats']['fixed_rational_minimax_leaves']
assert counts['column_deletions']==proof['stats']['column_deletions'] and counts['row_deletions']==proof['stats']['row_deletions']
assert counts['unclosed_leaves']==proof['stats']['unclosed_leaves']
closed_roots=sum(r['closed'] for r in proof['roots'])
closed_pairs=[list(p) for p in combinations(range(4),2) if all(r['closed'] for r in proof['roots'] if r['pair']==list(p))]
result={'schema':1,'status':'PASS_ALL6_ONE_PAIR_FAMILIES_ALL_CONTINUOUS_NONNEGATIVE_PARAMETERS' if closed_roots==144 else 'VALID_PARTIAL_PROOF_WITH_EXPLICIT_UNRESOLVED_REGIONS_NOT_A_GAP',
    'source_id':scope['source_orbit'],'source':pin(sourcefile),'scope':pin(scopefile),'proof':pin(prooffile),
    'physical_label_witnesses':physical,'W0':W0,'W1':W1,'original_paths_checked':path_checks,
    'original_A_P_counts':[ACOUNT,PCOUNT],'completeness_dependency':pin(H/'REMAINING_SOURCE_AUDIT_V01.json'),
    'parameter_root_cones_replayed':144,'parameter_root_cones_closed':closed_roots,'closed_pairs':closed_pairs,
    'full_source_one_pair_exclusion_accepted':closed_roots==144,'counts':counts,
    'unclosed_roots':[r for r in proof['roots'] if not r['closed']],
    'exact_rank_method':'FractionGaussJordan;producerusesprimitiveintegerelimination',
    'cover_argument':'Sorted-priceclosedorthantspluslambda>=0 coverallcontinuousnonnegativeparameters. Twoexactclosedhalfcones includezero/tie/splitboundaries;crossingrays andrank4activeconstraints preserveeach full5dimpointedcone.',
    'game_argument':'Everyweakdeletionpreserves the reduced finite game with a common originalrow map; fulloriginalrowprioritylifts recover RP<=RA;policyinclusion gives reverse. Pure and fixedrational leaves close thefulloriginal game directly. Fixedrationalchecks use Fraction expectation on eachgenerator,independentofproducerinteger coefficientcompilation.',
    'claim_scope':'This fixed source only. Partialproofisnotgap or universalexclusion. Globalall-complete-four-queryminimumstillOPEN1or2untilremainingcasesclose.',
    'no_all_prior_Bayes_equality_claim':True,'numeric_games_LP_price_prior_grid_API_hosted_humanlabels_or_PDF':False,
    'same_agent_separate_reader_not_external_human_or_formal_kernel':True,'whole_project_complete':False}
out=Path(spec['out']);assert out.parent.is_dir() and out.resolve().is_relative_to(H)
with out.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'status':result['status'],'source':scope['source_orbit'],'closed_roots':closed_roots,'closed_pairs':closed_pairs,'counts':counts}))
