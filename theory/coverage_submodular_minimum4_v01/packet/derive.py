"""Pure analytic consequences of the single checked point; no new optimization."""
from fractions import Fraction as Q


def run(main, other):
    assert main['both_exact_values_certified'] and main['primary_strict_gap_certified']
    assert main['fee'] == other['fee']
    features = [tuple(row) for row in other['coverage_features'] if row[0] != 15]
    assert len(features) == 10 and all(group.bit_count() <= 2 and weight > 0 for group, weight in features)
    clean = [sum(weight for group, weight in features if group & s) for s in range(16)]
    assert clean == [0] + [v - 9 for v in main['fee'][1:]]
    assert clean == [0,8,11,17,10,17,17,22,11,17,18,22,17,22,20,23]
    proper = [clean[s | (1 << q)] - clean[s] for s in range(16) for q in range(4) if not s & (1 << q)]
    pairweights = {tuple(sorted((i,j))):weight for group,weight in features if group.bit_count()==2
                   for i in range(4) for j in range(i+1,4) if group == ((1<<i)|(1<<j))}
    assert len(pairweights) == 6
    incomparable = []
    slacks = []
    for s in range(16):
        for t in range(16):
            slack = clean[s] + clean[t] - clean[s|t] - clean[s&t]
            cross = sum(pairweights[tuple(sorted((i,j)))] for i in range(4) if (s & ~t) & (1<<i)
                        for j in range(4) if (t & ~s) & (1<<j))
            assert slack == cross
            slacks.append(slack)
            if s & ~t and t & ~s:
                incomparable.append({'S':s,'T':t,'slack':slack})
    assert min(slacks) == 0 and len(incomparable) == 110
    assert min(r['slack'] for r in incomparable) == min(proper) == 1
    assert min(clean[1:]) == 8
    assert main['task'][0] and main['task'][1]  # Both labels occur.
    # Every correct deterministic seed must query before a label can be known.
    # Thus removing a charge on every nonempty set shifts every input by nine.
    A = Q(main['A_anchor']) - 9
    P = Q(main['P_anchor']) - 9
    assert A == Q(other['A_fixed_dual_Bayes_value']) - 9 == Q(125,7)
    assert P == Q(other['P_fixed_dual_Bayes_min_over24orders']) - 9 == Q(161,9)
    assert P-A == Q(2,63) and P/A == Q(1127,1125)
    uppers = {kind:[{'word':r['word'],'cost':str(Q(r['cost'])-9),'anchor_slack':r['anchor_slack']}
                   for r in main['mixture_input_costs'][kind]] for kind in ('A','P')}
    radius = Q(1,126)
    delta = Q(1,1260)
    assert 10*delta == radius and P-A-2*radius == Q(1,63)
    assert 8-radius > 0 and 1-2*radius > 0 and 1-4*radius > 0 and 1-delta > 0
    return {
        'status':'ANALYTIC_COROLLARIES_OF_ONE_CHECKED_POINT_NO_SECOND_GAME_OR_FEE_SEARCH',
        'nonconstant_source_forces_nonempty_purchase_every_correct_seed_every_input':True,
        'removing_global9_shifts_all_policy_input_costs_uniformly':True,
        'pairwise_only_features':features,'clean_fee':clean,
        'clean_exact_RA':str(A),'clean_exact_RP':str(P),'gap':str(P-A),'ratio':str(P/A),
        'clean_upper_mixture_input_costs':uppers,
        'minimum_nonempty_fee':8,'minimum_proper_increment':1,
        'incomparable_submodular_slacks':incomparable,'strict_incomparable_slack_min':1,
        'strict_submodular_definition':'StrictforallincomparableS,T;comparablesetsnecessarilygiveidentity',
        'full15dim_normalized_fee_box_radius':str(radius),'box_gap_lower':str(P-A-2*radius),
        'box_nonempty_fee_lower':str(8-radius),'box_proper_increment_lower':str(1-2*radius),
        'box_incomparable_submodular_slack_lower':str(1-4*radius),
        'ten_positive_coverage_parameter_box_radius':str(delta),
        'coverage_box_per_set_fee_change_bound':str(10*delta),
        'largest_ratio_or_radius_or_region_claimed':False,
    }
