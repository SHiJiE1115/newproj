"""Compose all fixed-source exclusions with the inherited complete-source cover and strict upper witness."""
from fractions import Fraction as Q
import gzip
import hashlib
import itertools
import json
from pathlib import Path

H=Path(__file__).resolve().parent
B=H.parent


def load(p):return json.loads(Path(p).read_text(encoding='utf-8'))


def pin(p):
    p=Path(p);raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def save(n,x):
    with (H/n).open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')


audit=load(H/'REMAINING_SOURCE_AUDIT_V01.json')
assert audit['status']=='PASS_FROZEN_1345_PLUS11_REDUCTION_PHYSICAL_RESIDUAL_SOURCES_FULL_POLICY_PREMISE_AND_PAIR_FEE_TRANSPORT'
assert audit['monotone_already_closed']==1345 and len(audit['residual_sources'])==11
assert audit['fee_coefficient_identities_checked']==2304 and not audit['literal_answer_complementation_used']
assert audit['original_full_policy_input_paths_checked']==6957 and audit['explicit_transported_policy_input_paths_checked']==48*6957
original=load(B/'iteration441/ACCEPTANCE_V01.json')
assert original['local']==pin(B/'iteration441/LOCAL_RESULT_V01.json')
old_science=load(B/'iteration441/LOCAL_RESULT_V01.json')['science']
assert old_science['catalogue']['orbits']==1356 and old_science['catalogue']['tasks']==42864
assert old_science['threshold_and_subset']['threshold_sources']==1300
assert old_science['threshold_and_subset']['pointwise_sources']==31 and old_science['structural']['structural_sources']==14
assert 1300+31+14==1345 and 1345+11==1356
projection=load(H/'RESIDUAL_SOURCE_PROJECTIONS_V01.json')
assert projection['source_order']==audit['residual_sources']
source1209=next(r['source'] for r in projection['rows'] if r['source_id']==1209)
old1209=load(B/'iteration449/ORIGINAL_SOURCE1209_FAMILIES_V01.json')
for key in ('task','adaptive','priority'):assert source1209[key]==old1209[key]
portable=load(B/'iteration455/PORTABLE_ACCEPTANCE_V01.json')
assert portable['actual_result']==pin(B/'iteration455/ACTUAL_REPLAY_RESULT_V03.json')
old_pair=load(B/'iteration455/ACTUAL_REPLAY_RESULT_V03.json')['science']['single_pair']
assert old_pair['parameter_root_cones_verified']==144 and old_pair['closed_single_pair_families']==6
assert old_pair['original_paths_checked']==504 and old_pair['original_A_P_counts']==[40,32]
old_terminal=load(B/'iteration455/CLOSE_PORTABLE.PROCESS_TERMINAL.json')
assert old_terminal['actual_exit_code']==0 and not old_terminal['timed_out']
all_results=[{'source_id':1209,'reader_result_origin':'Inheritedactual455whole-objectreplayof453separatechecker',
    'reader_result':pin(B/'iteration453/SINGLE_PAIR_SEPARATE_READER_RESULT_V01.json'),
    'portable_whole_science_result':pin(B/'iteration455/ACTUAL_REPLAY_RESULT_V03.json'),
    'roots':144,'counts':old_pair['counts']}]
names=['nodes','splits','closed_lifting_leaves','pure_saddle_leaves','column_deletions','row_deletions',
       'full_original_row_P_lifts','scalar_inequalities','exact_fraction_rank_calls']
totals={name:old_pair['counts'][name] for name in names}
new_paths=0;new_terminals=[]
for source_id in audit['residual_sources'][1:]:
    assert source_id!=1209
    if source_id==1217:
        resultfile=H/'SOURCE1217_READER_RESULT_V02.json';specfile=H/'SOURCE1217_READER_SPEC_V02.json'
    else:
        resultfile=H/('source'+str(source_id))/'SEPARATE_READER_RESULT_V02.json'
        specfile=H/('source'+str(source_id))/'READER_SPEC_V02.json'
    reader=load(resultfile);spec=load(specfile)
    assert reader['status']=='PASS_ALL6_ONE_PAIR_FAMILIES_ALL_CONTINUOUS_NONNEGATIVE_PARAMETERS'
    assert reader['source_id']==source_id and reader['full_source_one_pair_exclusion_accepted']
    assert reader['parameter_root_cones_replayed']==reader['parameter_root_cones_closed']==144
    assert reader['closed_pairs']==[list(p) for p in itertools.combinations(range(4),2)]
    assert not reader['unclosed_roots'] and reader['counts']['unclosed_leaves']==0 and reader['counts']['not_started_roots']==0
    assert reader['counts']['fixed_rational_minimax_leaves']==0
    old_resultfile=H/'SOURCE1217_READER_RESULT_V01.json' if source_id==1217 else H/('source'+str(source_id))/'SEPARATE_READER_RESULT_V01.json'
    old_reader=load(old_resultfile)
    assert reader['claim_scope']==old_reader['scope']
    assert {k:v for k,v in old_reader.items() if k!='scope'}=={k:v for k,v in reader.items() if k not in ('scope','claim_scope')}
    assert reader['scope']==spec['scope']
    assert reader['completeness_dependency']==pin(H/'REMAINING_SOURCE_AUDIT_V01.json')
    for key in ('source','scope','proof'):
        assert pin(spec[key]['path'])==spec[key]==reader[key]
    assert pin(spec['reader']['path'])==spec['reader']==pin(H/'read_source_pair_proof_v02.py')
    scope=load(Path(spec['scope']['path']));source=load(Path(spec['source']['path']))
    assert scope['source_orbit']==source_id and source['task']==scope['source_task']
    assert source==next(r['source'] for r in projection['rows'] if r['source_id']==source_id)
    assert scope['dependency_audit_sha256']==pin(H/'REMAINING_SOURCE_AUDIT_V01.json')['sha256']
    proof=json.loads(gzip.decompress(Path(spec['proof']['path']).read_bytes()))
    assert len(proof['roots'])==144 and all(r['closed'] for r in proof['roots'])
    assert len(proof['nodes'])==reader['counts']['nodes']
    assert len(proof['nodes'])==144+2*reader['counts']['splits']
    assert all(n['kind'] in ('pure_saddle','closed','split') for n in proof['nodes'])
    phases=[]
    for label in ('PROVE_SOURCE','REREAD_SOURCE'):
        phase=label+str(source_id)
        start=load(H/(phase+'.PROCESS_START.json'));end=load(H/(phase+'.PROCESS_TERMINAL.json'))
        assert start['pid']==end['pid'] and end['actual_exit_code']==0 and not end['timed_out']
        assert start['script_sha256']==pin(start['command'][5])['sha256']
        assert load(H/(phase+'.STORAGE.json'))['status']=='PASS'
        phases.append({'phase':phase,'pid':end['pid'],'actual_exit_code':0,
                       'terminal':pin(H/(phase+'.PROCESS_TERMINAL.json'))})
        new_terminals.append(phases[-1])
    new_paths+=reader['original_paths_checked']
    for name in names:totals[name]+=reader['counts'][name]
    all_results.append({'source_id':source_id,'reader_result':pin(resultfile),'reader_spec':pin(specfile),
        'roots':144,'counts':reader['counts'],'actual_phases':phases})
assert len(all_results)==11 and len(new_terminals)==20 and new_paths+504==6957
roots=11*144
assert roots==1584 and totals['nodes']==roots+2*totals['splits']
assert totals['closed_lifting_leaves']+totals['pure_saddle_leaves']==roots+totals['splits']
point=load(B/'iteration453/TWO_PAIR_FULL_CLASS_RESULT_V01.json')
dp=load(B/'iteration453/TWO_PAIR_SEPARATE_DP_RESULT_V01.json')
derived=load(B/'iteration453/DERIVED_PAIR_RESOURCE_MINIMUM_V01.json')
assert point['results']['A']['anchor']=='286/29' and point['results']['P']['anchor']=='79/8' and not point['failed_bounds']
assert Q(point['results']['P']['anchor'])-Q(point['results']['A']['anchor'])==Q(3,232)
assert dp['exact_gap']=='3/232' and len(dp['all24_original_Porder_results'])==24
assert derived['sparse_coverage_parameter_box']['coordinate_radius']=='1/1856'
assert derived['sparse_coverage_parameter_box']['gap_lower_bound']=='3/464'
charges=[4,3,2,3];groups=[([1,2],2),([2,3],2)]
assert all(c>0 for c in charges) and len({tuple(e) for e,w in groups if w>0})==2
fees=[sum(c for q,c in enumerate(charges) if mask>>q&1)+sum(w for e,w in groups if any(mask>>q&1 for q in e)) for mask in range(16)]
assert fees==[0,4,5,9,6,10,9,13,5,9,10,14,9,13,12,16]
assert all(fees[s]<fees[t] for s in range(16) for t in range(16) if s!=t and s&t==s)
result={'schema':1,'status':'PASS_INTERNAL_COMPUTER_ASSISTED_ALL_COMPLETE_FOUR_QUERY_ONE_PAIR_EQUALITY_AND_MINIMUM_POSITIVE_PAIR_SUPPORT2',
 'theorem_id':'G4_PAIR_SUPPORT_MINIMUM2','statement':
  'For every nonempty disjoint complete equivalence-partition promise on at most four indexed pair-equality queries, every finite c_i>=0 and any one distinct two-query group e with lambda>=0, F(S)=sum_{i in S}c_i+lambda*1{S intersects e} satisfies R_A=R_P in the private-seed zero-error worst-input expected final-set-cost model. Over all complete FOUR-query sources, the minimum number of positive distinct pair-setup weights permitting R_A<R_P is exactly2, also with strictly positive individual charges.',
 'proof_modules':{'inherited_complete_source_cover_and1345_monotone_equalities':pin(B/'iteration441/ACCEPTANCE_V01.json'),
   'fresh_residual_physical_completeness_and_pair_fee_transport':pin(H/'REMAINING_SOURCE_AUDIT_V01.json'),
   'all11_residual_sources_closed':all_results,
   'inherited_two_pair_fullclass_witness':pin(B/'iteration453/TWO_PAIR_FULL_CLASS_RESULT_V01.json'),
   'inherited_separate_physical_DP':pin(B/'iteration453/TWO_PAIR_SEPARATE_DP_RESULT_V01.json'),
   'inherited_robustness':pin(B/'iteration453/DERIVED_PAIR_RESOURCE_MINIMUM_V01.json')},
 'source_cover':{'all_canonical_orbits':1356,'inherited_monotone_closed_orbits':1345,'one_pair_residual_orbits':11,
   'original_ordered_tasks':42864,'fresh_residual_ordered_tasks':408,'physical_supports_rechecked':22},
 'residual_cones':roots,'residual_counts':totals,'original_residual_policy_input_paths':6957,
 'new_source_producers':10,'final_accepted_separate_readers':10,'actual_separate_reader_passes_including_metadata_repair':20,'retained_metadata_repair':pin(H/'READER_METADATA_REPAIR_V02.json'),'new_real_process_terminals':new_terminals,
 'source1209_original_proof_and1345cases_inherited_not_rerun':True,
 'one_pair_class_monotone_normalized':'Nonnegative individual charges plus nonnegative activation on intersection with a pair is finite,normalized and monotone; hence fits the1345older proofs.',
 'fewer_than4query_extension':'Pad with fresh query pairs forcedDIFFERENT under both labelpriors,eachdummyindividualcharge0and outside the shared pair. Every old physicalworld extends with fresh classes,so projected support is oldW times constantzero answers. Erasing these known-answer dummies preserves both fullAandcausal-skipPgames and every final fee. The four-query exclusion therefore implies all smaller menus.',
 'upper_witness':{'source1209':{'W0':[1,7,9],'W1':[0,4,11,15]},'individual_charges':charges,
   'positive_pair_groups':groups,'all_other_pair_weights':0,'separate_global_setup':False,
   'R_A':'286/29','R_P':'79/8','gap':'3/232','relative_saving_to_RP':'3/2291',
   'strictly_increasing_coverage_fee':True,'six_coordinate_robust_radius':'1/1856','robust_gap_at_least':'3/464'},
 'scope_limits':['Completeequivalencepromises,unrestrictedclasscount,disjointlabelprojections,atmost4indexedqueries',
   'Individualchargespluspairintersectionactivationcosts;notarbitrarylargerresourcegroups',
   'Minimum2isoverallcompleteFOUR-querysources;notalllargermenus,whereadditivegapsalreadyexist',
   'Existenceoftwo-pairgapdoesnotclaimeverytwo-pairfeeorsourcehasagap',
   'Privatezeroerrorminimaxwithfullcausalskippriority;notallevery-priorBayesequality',
   'No all-four-querygeneral-submodularclassification or practicalapplicationadvantage follows'],
 'bibliographic_priority':'OPEN','application_advantage':'NOT_ESTABLISHED',
 'internal_computer_assisted_proof_not_external_human_independent_or_formal_kernel_review':True,
 'new_numeric_fee_prior_grid_LP_API_hosted_humanlabels_PDF_or_publicupload':False,'whole_project_complete':False}
save('GLOBAL_PAIR_SUPPORT_MINIMUM2_RESULT_V01.json',result)
proof_text=f'''All-complete-four-query pair-setup support minimum: internal theorem and proof

THEOREM G4_PAIR_SUPPORT_MINIMUM2 (computer-assisted).
Use nonempty disjoint complete equivalence-partition promises, unrestricted
class count, reliable indexed pair-equality queries, private input-independent
seeds, zero error on every promised input, and worst-input expected final
purchased-set fee. P uses one global order per seed and permits causal
permanent SKIP; both classes see exactly the same query information.

On any source with at most four queries, for every finite c_i>=0,lambda>=0
and every pair e of distinct query indices,
  F(S)=sum(i in S)c_i + lambda*1[S intersects e] implies R_A=R_P.
Consequently, over all complete FOUR-query sources and pair-coverage fees,
the minimum number of positive distinct pair weights allowing R_A<R_P is2.
The same minimum holds with strictly positive individual charges.

Proof.
1. Complete source cover and inherited majority.
The accepted441proof reduces arbitrary hidden/repeated records to endpoint
SAME blocks and DIFFERENT filters, with fresh-class extension for sufficiency.
Its actual full replay covers42864ordered tasks in1356query-permutation/label
orbits. Literal-answer complementation is not used. The disjoint proof ledger
has1300certificate-threshold,31pointwise-subset and14structural cases whose
claims hold for EVERY finite normalized nonnegative monotone fee. A one-pair
fee is in this class. These1345cases inherit that accepted proof; they were
not freshly rerun or replaced by counts. The exact remaining sourceIDs are
{audit['residual_sources']}.

2. Exact transport and policy premise for the residual sources.
Fresh direct witness projection checks both physical label supports for all
11sources on all16answerwords. Fresh symbolic feasible-state recursion checks
full adaptive and all24causal-skip priority minima, against the retained full
policy families; original families are not assumed irredundant. The6957
original policy/input paths and333936permuted/label-swapped paths are legal.
For any query permutation sigma, rename query i and charge c_i to sigma(i),
and rename e to sigma(e). Every purchased mask has the same five fee
coefficients;2304coefficient identities check all24permutations,6pairs,16sets.
This is an algebraic identity for all real parameters, not evaluated minimax
games at sampled prices. The inverse maps strategies back, including the
shared order and all skips. Input-independent seed distributions, perinput
costs, maxima and positive-pair-support count are preserved.

3. Continuous one-pair certificates.
For each of the11sources and6pairs, all24closed individual-price order cones
are covered. In a cone c_order[j]=d0+...+dj with d>=0; lambda is a fifth
nonnegative coordinate. A path cost is a five-variable homogeneous linear
form. Splits use two CLOSED halfcones and exact crossing generators; active
rank-four constraints retain every extreme ray of each pointed full5Dcone.
Zero prices,lambda0,price ties and all split boundaries remain included.
The root orthants thus cover all continuous nonnegative parameters.

There are{roots}roots,{totals['nodes']}nodes,{totals['splits']}splits,
{totals['pure_saddle_leaves']}full-game pure-saddle leaves and
{totals['closed_lifting_leaves']}dominance/full-original-row lifting leaves.
All leaves close. The source1209proof is the accepted453/455proof; the other
10sources have10new producers and10final separate readers, all exit0.
Ten earlier reader passes are retained; a result metadata-key collision
was repaired without changing any mathematical checking code or output.
The compositionV01rejection and both reader versions remain on record.
Separate-reader Fraction elimination checks cone ranks instead of using the
producer's primitive-integer elimination. It replays every deletion, every
full-original-input priority lift and every full-game saddle inequality.
The full residual total is{totals['scalar_inequalities']}scalar inequalities,
with{totals['exact_fraction_rank_calls']}Fraction rank calls.

At a pure leaf, one legal Ppolicy has cost at most an anchor on ALL inputs;
every full adaptive policy costs at least that anchor on one original input.
This directly gives R_A>=anchor>=R_P. At a lifting leaf, weak row/column
deletions preserve the finite minimax value. Every removed row maps through
the retained row chains to a common no-cheaper terminal row for ALL terminal
columns. Each terminal adaptive column has a legal original Pcolumn whose
cost is no greater on ALL original inputs, not only the surviving rows.
Apply these replacements with the same private mixture weights. Then
R_P<=R_A; policy inclusion gives R_A<=R_P. Full-game legal witnesses and
the fresh completeness premise include zero-prior inputs. Thus every seedwise
zero-error policy is covered and all11residual sources have equality.
Together with steps1--2, all complete four-query sources have equality.

4. Smaller menus and exact support threshold.
For fewer queries, add fresh dummy record-pairs forcedDIFFERENT under each
label, with zero individual charges and no membership in e. Every old world
extends using fresh classes; dummy answers are constant0. Known-answer dummy
purchases may be removed. Deleting them from each seed's global order is a
legal permanent skip, so both minimax games and final fees are unchanged.
The four-query equality therefore also covers all smaller menus.

At four queries the accepted complete source1209hasW0={{1,7,9}} and
W1={{0,4,11,15}}. Setc=(4,3,2,3),w_{{1,2}}=w_{{2,3}}=2,otherpairweights0.
There is no global setup term. Its exact full-class and separate physical-DP
checks give R_A=286/29,R_P=79/8, gap3/232>0. All individual charges are
strictly positive and all proper set inclusions strictly increase the fee.
At most one positive pair is excluded above; two positive pairs suffice.
Therefore the over-source four-query support minimum is exactly2 in both
the nonnegative and positive individual-charge classes. The old six-parameter
box of radius1/1856 still has gap>=3/464 and stays in this two-pair class.

Limits.
This is an internal computer-assisted mathematical result, not human or
external independent implementation review, a formal proof kernel, historical
execution attestation, evidence of application advantage or a venue decision.
No new fee/prior grid,LP,model API,hosted run,human labels or PDF is used.
The result concerns pairwise activation at at most4queries; at larger menus
additive gaps exist, so minimum2is not a resource lower bound for all menus.
It does not classify every four-query submodular fee or every two-pair instance.
The primary-literature priority comparison and portable combined proof
delivery remain to be completed before strengthening the manuscript claim.
'''
with (H/'GLOBAL_PAIR_MINIMUM_THEOREM_AND_PROOF_V01.txt').open('x',encoding='utf-8') as f:f.write(proof_text)
print(json.dumps({'status':result['status'],'g4_pair_support_minimum':2,'all_source_orbits':1356,
    'newly_checked_sources':10,'residual_roots':roots,'counts':totals,'new_real_exit0_processes':20,
    'priority':'OPEN','application_advantage':'NOT_ESTABLISHED'}))
