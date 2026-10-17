"""Complete physical support and coordinate/label orbit replay."""
import itertools
from proofio import data, transform


def verify(families):
    cat = data('catalogue'); rows = cat['partition_rows']
    assert cat['query_pairs'] == [[0,1],[2,3],[4,5],[6,7]]
    partitions = [tuple(r['partition']) for r in rows]
    for pi in partitions:
        assert len(pi) == 8 and pi[0] == 0
        assert all(0 <= pi[k] <= max(pi[:k])+1 for k in range(1,8))
    stirling = [1]+[0]*8
    for _ in range(8): stirling = [0]+[stirling[k-1]+k*stirling[k] for k in range(1,9)]
    assert len(partitions) == len(set(partitions)) == sum(stirling) == 4140
    union = set(); projections = []; transitions = 0
    for row in rows:
        pi = row['partition']; allowed = {}
        for w in range(16):
            parent = list(range(8))
            def find(a):
                while parent[a] != a: a = parent[a]
                return a
            def join(a,b): parent[find(a)] = find(b)
            for a in range(8):
                for b in range(a):
                    if pi[a] == pi[b]: join(a,b)
            for q in range(4):
                if w>>q & 1: join(2*q,2*q+1)
            cc = [find(i) for i in range(8)]
            if sum((cc[2*q] == cc[2*q+1])<<q for q in range(4)) == w: allowed[w] = cc
        base = sum(1<<w for w in allowed); assert base == row['base_support']
        representatives = [pi.index(k) for k in sorted(set(pi))]
        filters = [[a,b,sum(1<<w for w,cc in allowed.items() if cc[a] != cc[b])] for a,b in itertools.combinations(representatives,2)]
        assert filters == row['different_generators']
        closure = {base}
        for _,_,filt in filters:
            transitions += len(closure); closure |= {x & filt for x in closure}
        assert 0 not in closure and sorted(closure) == row['closure_supports']
        union.update(closure); projections.append(allowed)
    assert union == set(map(int,cat['support_witnesses'])) and len(union) == 465
    for support,witness in cat['support_witnesses'].items():
        i = witness['partition_index']; assert witness['same_partition'] == rows[i]['partition']
        actual = sum(1<<w for w,cc in projections[i].items() if all(cc[a] != cc[b] for a,b in witness['different_record_pairs']))
        assert actual == int(support)
    tasks = {(a,b) for a in union for b in union if not (a & b)}
    assert len(tasks) == 42864 and len(families) == 1356
    covered = set(); members = []
    for source in families:
        actual = set()
        for perm in itertools.permutations(range(4)):
            image = tuple(sum(1<<transform(w,perm) for w in range(16) if mask>>w & 1) for mask in source['task'])
            actual.update((image,image[::-1]))
        assert actual == set(map(tuple,source['orbit_members'])) and not (actual & covered)
        covered.update(actual); members.append(len(actual))
    assert covered == tasks
    return {'partitions':4140,'supports':465,'tasks':42864,'orbits':1356,
        'intersection_transition_checks':transitions,'orbit_members':members}
