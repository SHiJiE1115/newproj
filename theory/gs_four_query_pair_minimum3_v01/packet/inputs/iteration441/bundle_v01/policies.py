"""Replay the complete OLD normal-form A/P vector families, not a cost grid."""
from functools import lru_cache
import itertools
from proofio import words, trace


ONES = [sum(1<<w for w in range(16) if w>>q & 1) for q in range(4)]


def packed(sets): return sum(mask<<(4*w) for w,mask in enumerate(sets))


def regenerate(task):
    initial = task[0] | task[1]; label1 = task[1]
    def pure(state): return not (state & label1) or not (state & task[0])
    @lru_cache(None)
    def purchase(state,q): return sum(1<<(4*w+q) for w in range(16) if state>>w & 1)
    @lru_cache(None)
    def adaptive(state,left):
        if pure(state): return frozenset([0])
        answers = set()
        for q in range(4):
            if not left>>q & 1: continue
            yes = state & ONES[q]; no = state & ~ONES[q]
            if not yes or not no: continue
            for a in adaptive(no,left^(1<<q)):
                for b in adaptive(yes,left^(1<<q)): answers.add(a | b | purchase(state,q))
        return frozenset(answers)
    @lru_cache(None)
    def priority(state,suffix):
        if pure(state): return frozenset([0])
        if not suffix: return frozenset()
        q = suffix[0]; rest = suffix[1:]
        answers = set(priority(state,rest)) # causal permanentSKIP; state still contains all words
        yes = state & ONES[q]; no = state & ~ONES[q]
        if yes and no:
            for a in priority(no,rest):
                for b in priority(yes,rest): answers.add(a | b | purchase(state,q))
        return frozenset(answers)
    A = adaptive(initial,15); P = set()
    for order in itertools.permutations(range(4)): P.update(priority(initial,order))
    return A,P,adaptive.cache_info().currsize,priority.cache_info().currsize


def verify(families):
    paths=0; Acount=0; Pcount=0; Astates=0; Pstates=0
    for source in families:
        task=source['task']; ww=words(task)
        assert task[0] and task[1] and not (task[0]&task[1])
        stored=[]
        for field in ('adaptive','priority'):
            vectors=set()
            for column in source[field]:
                for w in ww:
                    label,mask,seen=trace(column['tree'],w)
                    assert type(label) is int and label==int(bool(task[1]>>w&1)) and mask==column['sets'][w]
                    if field=='priority':
                        assert sorted(column['order'])==[0,1,2,3]
                        assert seen==sorted(seen,key=column['order'].index)
                    paths+=1
                assert all(column['sets'][w]==0 for w in range(16) if w not in ww)
                signature=packed(column['sets']); assert signature not in vectors; vectors.add(signature)
            stored.append(vectors)
        A,P,sa,sp=regenerate(task)
        assert A==stored[0] and P==stored[1]
        assert P <= A
        Acount+=len(A);Pcount+=len(P);Astates+=sa;Pstates+=sp
    assert Acount==39113 and Pcount==33781 and paths==629694
    return {'A_vectors':Acount,'P_vectors':Pcount,'policy_input_paths':paths,
        'all1356_original_families_regenerated':True,'adaptive_states':Astates,'priority_suffix_states':Pstates}
