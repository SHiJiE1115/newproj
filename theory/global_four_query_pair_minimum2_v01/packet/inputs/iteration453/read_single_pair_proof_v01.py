"""Read the universal-cone proof using Fraction elimination, not its producer."""
from fractions import Fraction
from itertools import combinations, permutations
import gzip
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


scopefile = H/'SYMBOLIC_PROOF_SCOPE_V02.json'
assert pin(scopefile)['sha256'] == '2e7dcd9050b4f13ed6908d991225c120b25aaab51d1dd4ad1dc5608b84d11082'
sourcefile = B/'iteration449/ORIGINAL_SOURCE1209_FAMILIES_V01.json'
assert pin(sourcefile)['sha256'] == '03d5f73f832bf7888a61c75ddd761704dab14ed3fbafe99f65dc6347d9f706ad'
prooffile = H/'SYMBOLIC_SINGLE_PAIR_PROOF_V02.json.gz'
assert pin(prooffile)['sha256'] == '1c7d1631191a6f466506f3b1cf437af2a41d2330ade909e028a0220f729099f0'
scope = read(scopefile)
source = read(sourcefile)
proof = json.loads(gzip.decompress(prooffile.read_bytes()))
assert proof['scope_sha256'] == pin(scopefile)['sha256']
assert proof['source_sha256'] == pin(sourcefile)['sha256']
assert source['task'] == [642, 34833]

# Reconstruct the physical task from all coarsenings of its three prior blocks.
patterns = [(0, 0, 0), (0, 0, 1), (0, 1, 0), (0, 1, 1), (0, 1, 2)]
physical = []
for label, groups in enumerate([[(0,1,2,4,6),(3,5),(7,)], [(0,2,4,6),(1,3,7),(5,)]]):
    partitions = []
    for pattern in patterns:
        classes = [None]*8
        for i, block in enumerate(groups):
            for record in block:
                assert classes[record] is None
                classes[record] = pattern[i]
        if label == 0 and classes[3] == classes[7]:
            continue
        word = sum((classes[2*q] == classes[2*q+1]) << q for q in range(4))
        partitions.append({'coarsening': list(pattern), 'word': word})
    physical.append(partitions)
W0, W1 = [sorted({p['word'] for p in part}) for part in physical]
assert [len(p) for p in physical] == [3, 5]
assert W0 == [1,7,9] and W1 == [0,4,11,15]
W = sorted(W0+W1)
assert W == scope['W'] == proof['W']
labels = {w: int(w in W1) for w in W}
profiles = []
path_checks = 0
for kind, expected in [('priority', 32), ('adaptive', 40)]:
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
assert path_checks == 504
assert len({tuple(p) for p in profiles[32:]}) == 40
assert len({tuple(p) for p in profiles[:32]}) == 32
assert all(p in profiles[32:] for p in profiles[:32])


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
counts = {'nodes': 0, 'splits': 0, 'closed_lifting_leaves': 0, 'pure_saddle_leaves': 0,
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
        assert all(geq(profiles[a][w],anchor) for a in range(32,72))
        assert all(geq(anchor,profiles[p][v]) for v in range(7))
        counts['pure_saddle_leaves'] += 1
        return

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
            assert p in range(32)
            assert all(geq(profiles[c][w],profiles[p][w]) for w in range(7))
            counts['full_original_row_P_lifts'] += 1
        counts['closed_lifting_leaves'] += 1
        return

    assert rec['kind'] == 'split'
    assert len(rec['children']) == 2
    form = tuple(rec['form'])
    assert len(form) == 5 and any(form)
    assert min(scalar(form,r) for r in rays) < 0 < max(scalar(form,r) for r in rays)
    counts['splits'] += 1
    for sign, child in zip((1,-1), rec['children']):
        newrays, newnormals = clipped_generators(rays,normals,form,sign)
        visit(child,newrays,newnormals,rows,columns,fees)


expected_roots = [(list(e),list(o)) for e in combinations(range(4),2) for o in permutations(range(4))]
assert len(proof['roots']) == 144
assert [(r['pair'],r['order']) for r in proof['roots']] == expected_roots
for root in proof['roots']:
    assert root['closed'] is True and root['node'] is not None
    pair, order = root['pair'], root['order']
    positions = {q:order.index(q) for q in range(4)}
    fees = []
    for mask in range(16):
        # c_order[j] = d0+...+dj. d0,...,d3,lambda are nonnegative.
        coeff = [sum(1 for q in range(4) if mask & (1<<q) and positions[q] >= k) for k in range(4)]
        coeff.append(int(any(mask & (1<<q) for q in pair)))
        fees.append(coeff)
    before = len(visited)
    visit(root['node'],eye,eye,list(range(7)),list(range(72)),fees)
    assert len(visited)-before == root['nodes']
assert visited == set(range(len(proof['nodes'])))
assert counts['nodes'] == 164 and counts['splits'] == 10
assert counts['pure_saddle_leaves'] == 73 and counts['closed_lifting_leaves'] == 81
assert counts['column_deletions'] == 5533 and counts['row_deletions'] == 342
result = {
    'schema':1, 'status':'PASS_ALL_SIX_SINGLE_PAIR_FAMILIES_ALL_CONTINUOUS_NONNEGATIVE_PARAMETERS',
    'source':pin(sourcefile), 'scope':pin(scopefile), 'proof':pin(prooffile),
    'physical_partitions':physical, 'W0':W0, 'W1':W1,
    'original_paths_checked':path_checks, 'original_A_P_counts':[40,32],
    'full_policy_completeness':'Inherited unchanged original source1209 monotone-cost catalogue and its earlier completeness proof; no new catalogue generated',
    'parameter_root_cones_verified':144, 'closed_single_pair_families':6,
    'counts':counts,
    'exact_rank_method':'Independent Fraction Gauss-Jordan, not producer integer primitive elimination',
    'continuous_cover_lemma':'Sorted-price orthants cover c>=0; exact half-cone crossing generators and active rank-four extreme-ray pruning preserve full five-dimensional pointed cones and closed boundaries',
    'game_bridge':'Every deletion preserves reduced finite minimax; removed row inequalities remain on terminal columns. All-original-row P-lifts give RP<=RA, while P subset A gives reverse. Full-game saddle leaves directly prove equality.',
    'claim':'For this fixed source only, RA=RP for F(S)=sum(c_i over i in S)+lambda*1{S intersects e}, all c_i,lambda>=0 and all six physical pairs e',
    'no_all_prior_Bayes_equality_claim':True,
    'numeric_games_LP_price_or_prior_grids_new_model_API_or_human_review':False,
    'same_agent_separate_reader_not_external_human_or_formal_kernel':True,
    'whole_project_complete':False,
}
with (H/'SINGLE_PAIR_SEPARATE_READER_RESULT_V01.json').open('x',encoding='utf-8') as f:
    json.dump(result,f,ensure_ascii=False,indent=2); f.write('\n')
print(json.dumps({'status':result['status'],'roots':144,'paths':path_checks,'counts':counts}))
