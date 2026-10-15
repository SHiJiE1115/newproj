"""Exact functions retained from research iteration336; see DERIVATION.json."""
from fractions import Fraction as F
import itertools, math

def q(x):return [x.numerator,x.denominator]
def dot(a,x):return sum(u*v for u,v in zip(a,x))
def solve3(rows):
 a=[[F(c) for c in v]+[F(b)] for v,b in rows]
 for col in range(3):
  pivot=next((r for r in range(col,3) if a[r][col]),None)
  if pivot is None:return None
  a[col],a[pivot]=a[pivot],a[col]
  divisor=a[col][col];a[col]=[v/divisor for v in a[col]]
  for r in range(3):
   if r!=col:
    multiplier=a[r][col];a[r]=[u-multiplier*v for u,v in zip(a[r],a[col])]
 return tuple(a[i][3] for i in range(3))
def constraints(values):
 # Each inequality is a.x <= b, x=(TP,FP,FN), TN=1-TP-FP-FN.
 cons=[('TP>=0',(-1,0,0),0),('FP>=0',(0,-1,0),0),('FN>=0',(0,0,-1),0),('TN>=0',(1,1,1),1)]
 intervals={k:(F(v)-F(1,200),F(v)+F(1,200)) for k,v in values.items()}
 lo,hi=intervals['accuracy'];cons += [('A_lower',(0,1,1),1-lo),('A_upper',(0,-1,-1),hi-1)]
 lo,hi=intervals['precision'];cons += [('P_lower',(lo-1,lo,0),0),('P_upper',(1-hi,-hi,0),0)]
 lo,hi=intervals['recall'];cons += [('R_lower',(lo-1,0,lo),0),('R_upper',(1-hi,0,-hi),0)]
 lo,hi=intervals['f1'];cons += [('F1_lower',(2*lo-2,lo,lo),0),('F1_upper',(2-2*hi,-hi,-hi),0)]
 return [(n,tuple(map(F,a)),F(b)) for n,a,b in cons],intervals
def vertices(cons,equality=None):
 points=set();tested=0;singular=0
 for indices in itertools.combinations(range(len(cons)),3 if equality is None else 2):
  tested+=1;rows=[(cons[i][1],cons[i][2]) for i in indices]
  if equality is not None:rows.append(equality)
  x=solve3(rows)
  if x is None:singular+=1;continue
  if all(dot(a,x)<=b for _,a,b in cons):points.add(x)
 return sorted(points),{'plane_combinations':tested,'singular_combinations':singular,'distinct_feasible_vertices':len(points)}
def metrics(x):
 tp,fp,fn=x;tn=1-tp-fp-fn
 assert min(tp,fp,fn,tn)>=0
 assert tp+fp>0 and tp+fn>0 and 2*tp+fp+fn>0 and fp+tn>0
 return {'accuracy':tp+tn,'precision':tp/(tp+fp),'recall':tp/(tp+fn),'f1':2*tp/(2*tp+fp+fn),'fpr':fp/(fp+tn)}
def mean(points):return tuple(sum(x[i] for x in points)/len(points) for i in range(3))
def witness(x,intervals):
 vals=metrics(x);dist=(*x,1-sum(x))
 denominator=math.lcm(*(v.denominator for v in dist))
 counts=[int(v*denominator) for v in dist]
 strict=all(lo<vals[k]<hi for k,(lo,hi) in intervals.items())
 return {'proportions_TP_FP_FN_TN':[q(v) for v in dist],
         'constructed_integer_counts_TP_FP_FN_TN':counts,'constructed_total':denominator,
         'actual_dataset_counts':False,'metrics':{k:q(v) for k,v in vals.items()},
         'strictly_inside_all_rounding_intervals':strict}
def identify(values,target):
 cons,intervals=constraints(values);vs,stats=vertices(cons);assert vs
 denominators=[1-x[0]-x[2] for x in vs];assert min(denominators)>0
 low=min(vs,key=lambda x:metrics(x)['fpr']);high=max(vs,key=lambda x:metrics(x)['fpr'])
 centroid=mean(vs)
 # Two strict-interior distributions prove non-uniqueness without endpoint ties.
 inside=[tuple((a+b)/2 for a,b in zip(edge,centroid)) for edge in (low,high)]
 witnesses=[witness(x,intervals) for x in inside]
 assert all(w['strictly_inside_all_rounding_intervals'] for w in witnesses)
 assert metrics(inside[0])['fpr']!=metrics(inside[1])['fpr']
 target=F(target)
 sliced,slice_stats=vertices(cons,((target,F(1),target),target))
 target_witness=witness(mean(sliced),intervals) if sliced else None
 if target_witness is not None:assert metrics(mean(sliced))['fpr']==target
 return {'printed_metrics':values,'assumed_rounding_closed_intervals':{k:[q(lo),q(hi)] for k,(lo,hi) in intervals.items()},
  'inequalities':[{'name':n,'coefficients':[q(v) for v in a],'upper_bound':q(b)} for n,a,b in cons],
  'enumeration':stats,'minimum_FPR_denominator_over_vertices':q(min(denominators)),
  'fpr_closed_bounds':[q(metrics(low)['fpr']),q(metrics(high)['fpr'])],
  'fpr_closed_bounds_decimal':[float(metrics(low)['fpr']),float(metrics(high)['fpr'])],
  'lower_vertex':witness(low,intervals),'upper_vertex':witness(high,intervals),
  'all_vertices':[[q(v) for v in x] for x in vs],
  'strict_interior_nonuniqueness_witnesses':witnesses,
  'specific_fpr_target':q(target),'target_slice_enumeration':slice_stats,
  'target_feasible_in_closed_polytope':bool(sliced),'target_witness':target_witness,
  'interpretation':'Conditional identification interval, not a confidence interval or a verified population/data result.'}
