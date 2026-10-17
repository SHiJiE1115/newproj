"""Derive only algebraic consequences of the two already checked results."""
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path

H = Path(__file__).resolve().parent


def read(name):
    return json.loads((H/name).read_text(encoding='utf-8'))


def pin(name):
    raw = (H/name).read_bytes()
    return {'path':str(H/name),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


one = read('SINGLE_PAIR_SEPARATE_READER_RESULT_V01.json')
main = read('TWO_PAIR_FULL_CLASS_RESULT_V01.json')
separate = read('TWO_PAIR_SEPARATE_DP_RESULT_V01.json')
assert one['status'] == 'PASS_ALL_SIX_SINGLE_PAIR_FAMILIES_ALL_CONTINUOUS_NONNEGATIVE_PARAMETERS'
assert main['failed_bounds'] == [] and separate['failed_checks'] == []
assert main['status'] == 'PASS_FULL_ORIGINAL_CLASS_RATIONAL_PRIMAL_DUAL_CERTIFICATES'
assert separate['status'] == 'PASS_SEPARATE_PHYSICAL_SOURCE_AND_FIXED_PRIOR_FULL_DP'
A,P = Q(286,29),Q(79,8)
assert separate['exact_randomized_worst_input_A'] == main['results']['A']['anchor'] == str(A)
assert separate['exact_randomized_worst_input_P'] == main['results']['P']['anchor'] == str(P)
gap = P-A
radius = Q(3,928)
delta = Q(1,1856)
assert gap == Q(3,232) and gap-2*radius == Q(3,464)
assert delta*6 == radius and Q(2)-delta>0
assert main['positive_individual_costs'] == [4,3,2,3]
assert len(main['positive_pair_groups']) == 2 and main['minimum_proper_marginal'] == 2
result = {
    'schema':1,'status':'PASS_SOURCEWISE_PAIR_SUPPORT_MINIMUM_EXACTLY2_WITH_SPARSE_ROBUSTNESS',
    'claim_scope':{'source_orbit':1209,'W0':[1,7,9],'W1':[0,4,11,15],
                   'fee_family':'nonnegative additive individual costs plus nonnegative distinct two-query coverage groups; no global setup',
                   'minimum_positive_pair_support':2,
                   'minimum_also_with_strictly_positive_individual_costs':2,
                   'not_an_all_four_query_sources_lower_bound':True,
                   'not_arbitrary_resource_group_sizes':True},
    'one_pair_proof':pin('SINGLE_PAIR_SEPARATE_READER_RESULT_V01.json'),
    'two_pair_full_class_proof':pin('TWO_PAIR_FULL_CLASS_RESULT_V01.json'),
    'two_pair_catalogue_free_DP':pin('TWO_PAIR_SEPARATE_DP_RESULT_V01.json'),
    'theorem_and_proof':pin('PAIR_RESOURCE_MINIMUM_THEOREM_AND_PROOF_V01.txt'),
    'exact_RA':str(A),'exact_RP':str(P),'exact_gap':str(gap),
    'RP_over_RA':str(P/A),'relative_cost_reduction_versus_P':str(gap/P),
    'uniform_fee_lipschitz':{'per_class_constant':1,'gap_loss_constant':2,
                           'fee_sup_radius':str(radius),'gap_lower_bound':str(gap-2*radius),
                           'scope':'Valid fixed-task fees only; an arbitrary fee-vector box is not asserted to be submodular'},
    'sparse_coverage_parameter_box':{'dimensions':6,'parameters':'c0,c1,c2,c3,w12,w23',
                                    'coordinate_radius':str(delta),'sup_fee_deviation_bound':str(6*delta),
                                    'smallest_resource_weight_lower_bound':str(Q(2)-delta),
                                    'gap_lower_bound':str(gap-12*delta),
                                    'positive_exactly2_pair_groups_preserved':True,
                                    'strictly_increasing_coverage_submodular':True,
                                    'strict_on_all_incomparable_pairs':False},
    'prior_sourcewise_support_interval':[1,6],'new_exact_sourcewise_support':2,
    'old_query_menu_minimum_coverage_submodular':4,
    'old_global_additive_menu_interval':[5,7],
    'new_point_evaluations':1,'new_price_prior_grid_LP_model_hosted_human_calls':0,
    'not_in_public_V22_yet':True,'bibliographic_priority':'OPEN',
    'real_application_advantage':'NOT_ESTABLISHED','CCF_acceptance_guaranteed':False,
    'independent_external_human_or_formal_review':False,'whole_project_complete':False,
}
with (H/'DERIVED_PAIR_RESOURCE_MINIMUM_V01.json').open('x',encoding='utf-8') as f:
    json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'status':result['status'],'minimum':2,'gap':str(gap),'sparse_box_radius':str(delta),'robust_gap':str(gap-12*delta)}))
