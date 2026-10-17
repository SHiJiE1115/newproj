"""Exact scalar certificate replay for the included fixed analytic lemmas.

Polynomial arithmetic and nonnegative-product identities are checked here.
The stated monotone/case generators and exhaustion of the ordered cases are
also given as complete analytic arguments in proofs/struct*.txt.
"""
from fractions import Fraction


class P:
    def __init__(self, n, terms=None):
        self.n = n
        self.t = {tuple(e): Fraction(v) for e, v in (terms or {}).items() if v}
        assert all(len(e) == n and all(type(k) is int and k >= 0 for k in e) for e in self.t)

    def cast(self, value):
        if isinstance(value, P):
            assert self.n == value.n
            return value
        return P(self.n, {(0,)*self.n: Fraction(value)})

    def __add__(self, other):
        other = self.cast(other); out = self.t.copy()
        for e, v in other.t.items(): out[e] = out.get(e, 0)+v
        return P(self.n, out)

    __radd__ = __add__

    def __neg__(self): return P(self.n, {e: -v for e, v in self.t.items()})
    def __sub__(self, other): return self + (-self.cast(other))
    def __rsub__(self, other): return self.cast(other) - self

    def __mul__(self, other):
        other = self.cast(other); out = {}
        for e, v in self.t.items():
            for f, w in other.t.items():
                q = tuple(a+b for a, b in zip(e, f)); out[q] = out.get(q, 0)+v*w
        return P(self.n, out)

    __rmul__ = __mul__

    def __eq__(self, other):
        other = self.cast(other)
        return self.t == other.t


def variables(n): return [P(n, {tuple(int(i == j) for i in range(n)): 1}) for j in range(n)]
def parse(n, value):
    terms = {}
    for exp, coefficient in value:
        exp = tuple(exp); assert exp not in terms
        terms[exp] = Fraction(coefficient)
    return P(n, terms)


def check_product_proof(expected, encoded, products, generators, strict):
    assert parse(expected.n, encoded) == expected
    total = expected.cast(0); positive_term = False
    for term in products:
        if isinstance(term, dict):
            coefficient = Fraction(term['coefficient']); factors = term['factors']
        else:
            coefficient = Fraction(1); factors = term
        assert coefficient >= 0
        value = expected.cast(coefficient); positive = coefficient > 0
        for name in factors:
            assert name in generators, name
            polynomial, is_strict = generators[name]
            value *= polynomial; positive = positive and is_strict
        total += value; positive_term = positive_term or positive
    assert total == expected
    if strict: assert positive_term


def verify_386(data):
    assert data['cost_variables'] == ['A', 'X', 'Y', 'B', 'Z']
    A, X, Y, B, Z = variables(5); zero = A.cast(0); one = A.cast(1)
    alpha = X-A; beta = B-Y; den = alpha+beta; num = beta*A+alpha*B
    names = ['B_le_A', 'B_gt_A_B_le_Y', 'B_gt_A_B_gt_Y_X_le_Y', 'interior_h_ge_Z', 'interior_Z_ge_h']
    models = [(one, A, [one, zero], [one, zero, zero]),
              (one, B, [one, zero], [zero, one, zero]),
              (one, Y, [zero, one], [zero, one, zero]),
              (den, num, [X-Y, B-A], [beta, alpha, zero]),
              (den, Z*den, [X-Y, B-A], [zero, zero, den])]
    matrix = [[A, X], [B, Y], [Z, Z]]; checks = 0; norms = 0
    assert len(data['saddle_cases']) == 5
    for k, (case, model) in enumerate(zip(data['saddle_cases'], models)):
        D, N, mu, prior = model
        assert case['id'] == names[k] and case['prior_inputs'] == [1, 7, 3]
        assert parse(5, case['denominator']) == D and parse(5, case['value_numerator']) == N
        assert [parse(5, v) for v in case['mu_numerators']] == mu
        assert [parse(5, v) for v in case['prior_numerators']] == prior
        assert sum(mu, zero) == D and sum(prior, zero) == D; norms += 2
        generators = {name: (poly, False) for name, poly in zip(['A','X','Y','B','Z'], [A,X,Y,B,Z])}
        generators.update({'XminusA': (X-A, False), 'XminusZ': (X-Z, False), 'BminusZ': (B-Z, False)})
        if k == 0: generators['AminusB'] = (A-B, False)
        if k >= 1: generators['BminusA'] = (B-A, True)
        if k == 1: generators['YminusB'] = (Y-B, False)
        if k >= 2: generators['BminusY'] = (B-Y, True)
        if k == 2: generators['YminusX'] = (Y-X, False)
        if k >= 3:
            generators.update({'XminusY': (X-Y, True), 'den': (den, True),
                'cap': ((num-Z*den) if k == 3 else (Z*den-num), False)})
        assert set(generators) == set(case['generators'])
        for name, (poly, strict) in generators.items():
            assert parse(5, case['generators'][name]['polynomial']) == poly
            assert case['generators'][name]['strict'] == strict
        targets = {'positive_denominator': D, 'mu_5': mu[0], 'mu_11': mu[1],
            'lambda_1': prior[0], 'lambda_7': prior[1], 'lambda_3': prior[2], 'value_nonnegative': N,
            'upper_row1': N-sum((m*x for m,x in zip(mu,matrix[0])),zero),
            'upper_row7': N-sum((m*x for m,x in zip(mu,matrix[1])),zero),
            'upper_row3': N-sum((m*x for m,x in zip(mu,matrix[2])),zero),
            'upper_special5': N-mu[0]*A-mu[1]*Y}
        if k == 4: targets['lower_point3'] = prior[2]*Z-N
        else:
            for j in range(2): targets['lower_pair_column_'+str(j)] = sum((prior[i]*matrix[i][j] for i in range(3)),zero)-N
        assert {v['name'] for v in case['conditions']} == set(targets)
        for condition in case['conditions']:
            check_product_proof(targets[condition['name']], condition['polynomial'], condition['nonnegative_product_sum'], generators, condition['strict'])
            checks += 1
    assert checks == data['sign_conditions'] == 64
    return {'identities': checks, 'normalizations': norms, 'cases': 5}


def verify_393(data):
    a,x,b,d,y,c = variables(6); z = a.cast(0); o = a.cast(1)
    D2 = x-a+b-c; N2 = a*(b-c)+b*(x-a)
    u = (x-a)*(y-d)+(y-c)*(a-d)
    D3 = (x-a)*(y-d)+(y-c)*(b-d)
    N3 = a*(y-c)*(b-d)+b*(x-a)*(y-d)
    names = ['B_LE_A','D_GE_B','C_GE_B','X_LE_C','D_LE_C_CROSS','D_GT_C_CAP','THREE_COLUMN_INTERIOR']
    models = [(o,a,[o,z,z],[o,z,z]), (o,b,[o,z,z],[z,o,z]), (o,b,[o,z,z],[z,z,o]),
        (o,c,[z,z,o],[z,z,o]), (D2,N2,[x-c,z,b-a],[b-c,z,x-a]),
        (y-c,d*(y-c),[z,d-c,y-d],[z,y-c,z]),
        (D3,N3,[u,(d-c)*(b-a),(b-a)*(y-d)],[(y-c)*(b-d),(y-b)*(x-a),(x-a)*(b-d)])]
    matrix = [[a,a,x],[b,d,d],[b,y,c]]; special = [a,a,c]
    checks = 0; norms = 0
    assert len(data['saddle_cases']) == 7
    for k,(case,model) in enumerate(zip(data['saddle_cases'],models)):
        D,N,mu,prior = model; assert case['name'] == names[k]
        assert sum(mu,z) == D and sum(prior,z) == D; norms += 2
        generators = {name:(poly,False) for name,poly in zip(['a','x','b','d','y','c'],[a,x,b,d,y,c])}
        generators.update({'x-a':(x-a,False),'x-d':(x-d,False),'y-b':(y-b,False),'y-d':(y-d,False),'y-c':(y-c,False)})
        if k == 0: generators['a-b'] = (a-b,False)
        if k >= 1:
            generators['b-a'] = (b-a,True); generators['b'] = (b,True); generators['y'] = (y,True)
        if k == 1: generators['d-b'] = (d-b,False); generators['d'] = (d,True)
        if k >= 2:
            generators['b-d'] = (b-d,True); generators['y-d'] = (y-d,True)
        if k == 2: generators['c-b'] = (c-b,False); generators['c'] = (c,True)
        if k >= 3:
            generators['b-c'] = (b-c,True); generators['y-c'] = (y-c,True)
        if k == 3: generators['c-x'] = (c-x,False)
        if k >= 4:
            generators['x-c'] = (x-c,True); generators['x'] = (x,True)
        if k == 4: generators['c-d'] = (c-d,False); generators['x-d'] = (x-d,True)
        if k >= 5: generators['d-c'] = (d-c,True); generators['d'] = (d,True)
        if k == 5: generators['-u'] = (-u,False)
        if k == 6: generators['u'] = (u,True)
        targets = {('den',0):D, ('value',0):N, ('special',0):N-sum((m*v for m,v in zip(mu,special)),z)}
        for j in range(3):
            targets['primal',j] = mu[j]; targets['prior',j] = prior[j]
            targets['upper',j] = N-sum((m*v for m,v in zip(mu,matrix[j])),z)
            targets['lower',j] = sum((prior[i]*matrix[i][j] for i in range(3)),z)-N
        assert {(v['name'],v['index']) for v in case['sign_identities']} == set(targets)
        for item in case['sign_identities']:
            check_product_proof(targets[item['name'],item['index']], item['polynomial'], item['proof_terms'], generators, item['strict_positive'])
            checks += 1
    assert checks == data['symbolic_sign_identities'] == 105 and norms == data['normalization_identities'] == 14
    return {'identities':checks,'normalizations':norms,'cases':7}


def verify_399(data):
    a,x,b,y,d = variables(5); z = a.cast(0); o = a.cast(1)
    u=x-b; v=y-a; D=u+v; N=x*y-a*b; E=d*D-N
    names=['Y_LE_A','Y_GT_A_X_LE_B','MIXED_MIDDLE_BINDING','MIXED_ENDPOINTS_BINDING']
    models=[(o,a,[o,z],[o,z,z]),(o,b,[z,o],[z,z,o]),
        (D,d*D,[u,v],[z,D,z]),(D,N,[u,v],[y-b,z,x-a])]
    matrix=[[a,x],[d,d],[y,b]];special=[a,b];checks=0;norms=0
    assert len(data['saddle_cases']) == 4
    for k,(case,model) in enumerate(zip(data['saddle_cases'],models)):
        den,num,mu,prior=model;assert case['name']==names[k]
        assert sum(mu,z)==den and sum(prior,z)==den;norms+=2
        generators={name:(poly,False) for name,poly in zip(['a','x','b','y','d'],[a,x,b,y,d])}
        generators.update({'sigma':(x-a,False),'rho':(y-b,False),'x-d':(x-d,False),'y-d':(y-d,False)})
        if k==0:generators['a-y']=(a-y,False)
        if k==1:generators['b-x']=(b-x,False)
        if k>=2:generators.update({'u':(u,True),'v':(v,True)})
        if k==2:generators['E']=(E,False)
        if k==3:generators['-E']=(-E,True)
        targets={('den',0):den,('value',0):num,('special',0):num-sum((m*t for m,t in zip(mu,special)),z)}
        for j in range(2):
            targets['primal',j]=mu[j]
            targets['lower',j]=sum((prior[i]*matrix[i][j] for i in range(3)),z)-num
        for i in range(3):
            targets['prior',i]=prior[i];targets['upper',i]=num-sum((m*t for m,t in zip(mu,matrix[i])),z)
        assert {(v['name'],v['index']) for v in case['identities']}==set(targets)
        for item in case['identities']:
            check_product_proof(targets[item['name'],item['index']],item['polynomial'],item['proof_terms'],generators,item['strict_positive'])
            checks+=1
    assert checks==data['symbolic_nonnegative_identities']==52 and norms==data['normalization_identities']==8
    return {'identities':checks,'normalizations':norms,'cases':4}
