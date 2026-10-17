"""Threshold, full-policy domination and fixed structural-lemma replay."""
from proofio import data, words, transform, trace
from algebra import verify_386, verify_393, verify_399


def threshold_and_subset(families,groups):
    idealdata=data('ideals'); ideals=[]
    for I in range(1,1<<16):
        if not I&1:continue
        if all(not(I>>s&1) or all(not(s>>q&1) or I>>(s^(1<<q))&1 for q in range(4)) for s in range(16)):ideals.append(I)
    assert ideals==idealdata['nonempty_ideals'] and len(ideals)==167
    old=data('threshold'); byid={r['orbit_index']:r for r in old['rows']}
    group=next(g for g in groups if g['kind']=='THRESHOLD_IDEAL_385')
    assert group['orbits']==old['certificate_optimal_orbits'] and len(byid)==1300
    cells=0;subset_checks=0
    for i in group['orbits']:
        source=families[i];saved=byid[i];ww=words(source['task'])
        assert saved['task']==source['task'] and saved['all_monotone_certificate_optimal'] is True
        certs={w:[s for s in range(16) if all((w^u)&s for u in ww if bool(source['task'][1]>>u&1)!=bool(source['task'][1]>>w&1))] for w in ww}
        assert {str(w):v for w,v in certs.items()}==saved['certificates_by_input']
        relevant={I for I in ideals if all(any(I>>s&1 for s in certs[w]) for w in ww)}
        decisions=dict(saved['relevant_ideal_priority_decisions'])
        assert set(decisions)==relevant and len(decisions)==len(saved['relevant_ideal_priority_decisions'])
        for I,j in decisions.items():
            assert 0<=j<len(source['priority']) and all(I>>source['priority'][j]['sets'][w]&1 for w in ww)
            cells+=1
    assert cells==155995
    group=next(g for g in groups if g['kind']=='POINTWISE_SUBSET_378')
    assert len(group['orbits'])==31
    for i in group['orbits']:
        source=families[i];choices=source['pointwise_subset_priority_indices']
        assert not source['uncovered_adaptive_indices'] and len(choices)==len(source['adaptive'])
        for A,j in zip(source['adaptive'],choices):
            for w in words(source['task']):
                assert source['priority'][j]['sets'][w]&~A['sets'][w]==0;subset_checks+=1
    return {'nonempty_ideals':167,'threshold_sources':1300,'threshold_cells':cells,
        'pointwise_sources':31,'pointwise_input_checks':subset_checks}


def structural(families,groups):
    algebra={'386':verify_386(data('struct386')),'393':verify_393(data('struct393')),'399':verify_399(data('struct399'))}
    checks=0;sources=0
    for group in groups:
        if not group['kind'].startswith('STRUCTURAL_'):continue
        n=int(group['kind'].split('_')[1]);cert=data('struct'+str(n))
        if n==386:
            byid={v['orbit_index']:v for v in cert['physical_targets']}
            L=[{1,7},{0,3,4,15}];U=[{1,5,7,9},{0,2,3,4,8,10,11,12,14,15}]
            hard=[1,7];lower=[[3,14],[7,13]]
            trees=[[1,[0,1,0],[2,1,[3,0,1]]],[2,[1,[0,1,0],1],[0,1,[3,0,1]]]]
            upperrows=[[3,7],[14,13],[6,6],[3,13]]
        else:
            byid={v['orbit_index']:v for v in cert['physical_source_eligibility']}
            if n in (393,394):
                L=[{0,3,7},{1,15}];U=[{0,2,3,4,6,7,8},{1,9,13,14,15}]
                hard=[1,3,7];lower=[[3,10,10],[3,6,14],[7,6,12]]
                trees=[[1,[0,0,1],[3,0,1]],[1,[0,0,1],[2,0,[3,0,1]]],[2,[1,[0,0,1],0],[3,0,1]]]
                upperrows=[[3,3,7],[10,6,6],[10,14,12],[3,3,12]]
            elif n==399:
                L=[{1,7},{0,5,15}];U=[{1,3,6,7,9},{0,4,5,8,10,12,13,14,15}]
                hard=[1,5,7];lower=[[5,6,14],[7,6,10]]
                trees=[[2,[0,1,0],[1,1,[3,0,1]]],[1,[2,[0,1,0],1],[3,0,1]]]
                upperrows=[[5,7],[6,6],[14,10],[5,10]]
        if n in (386,393,394,399):
            for label in (0,1):
                for w in U[label]:
                    actual=[]
                    for tree in trees:
                        leaf,mask,_=trace(tree,w);assert leaf==label;actual.append(mask)
                    assert any(all(a&~b==0 for a,b in zip(actual,ref)) for ref in upperrows)
        for i in group['orbits']:
            source=families[i];target=byid[i];assert target['task']==source['task']
            ww=words(source['task']);sources+=1
            if n in (395,397,398):
                tau={int(w):t for w,t in target['source_retraction'].items()}
                assert set(tau)==set(ww) and set(tau.values())<=set(ww)
                bindings=target['adaptive_priority_bindings']
                assert [v['adaptive_index'] for v in bindings]==list(range(len(source['adaptive'])))
                for bind in bindings:
                    A=source['adaptive'][bind['adaptive_index']];P=source['priority'][bind['physical_priority_index']]
                    for w in ww:assert P['sets'][w]&~A['sets'][tau[w]]==0;checks+=1
            elif n==396:
                regions=target['source_regions'];assert len(regions)==2
                assert regions[0]['actual_cost_edge']==regions[1]['actual_cost_edge'][::-1]
                for region in regions:
                    small,large=region['actual_cost_edge']
                    reach=[[(a&~b)==0 for b in range(16)] for a in range(16)];reach[small][large]=True
                    for k in range(16):
                        for a in range(16):
                            for b in range(16):reach[a][b]=reach[a][b] or(reach[a][k] and reach[k][b])
                    tau={int(w):t for w,t in region['source_retraction'].items()}
                    assert set(tau)==set(ww) and set(tau.values())<=set(ww)
                    assert [v['adaptive_index'] for v in region['adaptive_priority_bindings']]==list(range(len(source['adaptive'])))
                    for bind in region['adaptive_priority_bindings']:
                        A=source['adaptive'][bind['adaptive_index']];P=source['priority'][bind['physical_priority_index']]
                        for w in ww:assert reach[P['sets'][w]][A['sets'][tau[w]]];checks+=1
            else:
                if n==386:
                    m=target['eligibility_witness'];perm=m['permutation_new_to_template']
                    assert perm==[0,1,2,3] and m['swap_labels'] is False
                    xor=0;swap=False
                else:
                    m=target['mapping'];assert m is not None
                    perm=m['coordinate_map'];xor=m.get('response_xor',0);swap=bool(m['swap_labels'])
                def T(w):return transform(w,perm,xor)
                inverse={T(w):w for w in range(16)}
                for label in (0,1):
                    actual={w for w in ww if bool(source['task'][1]>>w&1)==bool(label^swap)}
                    assert {T(w) for w in L[label]}<=actual<={T(w) for w in U[label]}
                for A in source['adaptive']:
                    actual=[A['sets'][T(w)] for w in hard]
                    assert any(all(transform(mask,perm)&~paid==0 for mask,paid in zip(col,actual)) for col in lower)
                    if n==386:assert transform(6,perm)&~A['sets'][T(3)]==0
                    checks+=len(hard)
                for tree in trees:
                    wanted={w:transform(trace(tree,inverse[w])[1],perm) for w in ww}
                    assert all((trace(tree,inverse[w])[0]^int(swap))==int(bool(source['task'][1]>>w&1)) for w in ww)
                    assert any(all(P['sets'][w]&~wanted[w]==0 for w in ww) for P in source['priority'])
                    checks+=len(ww)
    assert sources==14 and checks==2336
    return {'structural_sources':sources,'actual_binding_checks':checks,'scalar_lemma_algebra':algebra,
        'ordered_case_exhaustion_and_generator_signs': 'analyticargumentsincluded;polynomialidentitiesandpositiveproductcertificatesreplayed'}
