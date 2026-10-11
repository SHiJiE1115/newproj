# Exact submodular-cost ratio for the fixed seven-query source

## Model and scope

The query set is $Q=\{0,1,2,3,4,5,6\}$. The two complete source supports are all free-bit assignments of

\[
\mathcal A=(a,1,a,b,a,c,c),\qquad
\mathcal B=(u,u,0,v,w,w,v).
\]

An adaptive policy is deterministic and zero-error on these complete supports. A strong priority policy fixes a global query order before observing any answer, but may causally and permanently skip queries. For either policy, the cost in a world is $F(S)$, where $S$ is its purchased query set; its objective is the worst cost over legal worlds. Write $A_F$ and $P_F$ for the two optimal costs. In particular $0\le A_F\le P_F$.

Here $F:2^Q\to\mathbb R_{\ge0}$ is finite, normalized ($F(\varnothing)=0$), monotone, and submodular:

\[
F(S)+F(T)\ge F(S\cup T)+F(S\cap T).
\]

The conclusion concerns **this one fixed source and its physical query coordinates**. It is not a theorem about all seven-query sources, all complete copy/pin graphs, or arbitrary non-submodular monotone costs. No claim of novelty or empirical application benefit is made.

## Standing finite-frontier lemma

For an envelope $E$ of maximal purchased path sets, put $v_F(E)=\max_{T\in E}F(T)$. A mask $m$ denotes $\{q: m\mathbin{\&}2^q\ne0\}$.

The already established complete monotone-cost frontiers for this source are:

| Name | Envelope masks | Policy classes |
|---|---|---|
| $G_0$ | $\{3,5\}$ | adaptive and priority |
| $G_1$ | $\{11,28,121\}$ | priority |
| $G_2$ | $\{11,57,60,105\}$ | adaptive and priority |
| $G_3$ | $\{19,20\}$ | adaptive and priority |
| $G_4$ | $\{35,49,52\}$ | adaptive and priority |
| $G_5$ | $\{67,84,113\}$ | adaptive and priority |
| $E_1$ | $\{11,28,57,105,120\}$ | adaptive |
| $E_2$ | $\{28,43,57,120\}$ | adaptive |

Thus

\[
P_F=\min_{0\le i\le5}v_F(G_i),\quad
A_F=\min\{v_F(G_0),v_F(G_2),v_F(G_3),v_F(G_4),v_F(G_5),v_F(E_1),v_F(E_2)\}.
\]

This lemma is a finite computational proof dependency, not a consequence of the algebra below. Its completeness is inherited from the existing full-frontier verification; the saved policy witnesses alone establish attainability, not completeness. For the upper bound below it suffices that the adaptive frontier is complete and the displayed priority policies are valid. The matching lower bound uses completeness of both frontiers.

For readability write $F(0345)$ for $F(\{0,3,4,5\})$, and similarly for other strings of distinct coordinates. Define

\[
\begin{aligned}
H_1&=v_F(E_1)=\max\{F(013),F(234),F(0345),F(0356),F(3456)\},\\
H_2&=v_F(E_2)=\max\{F(234),F(0135),F(0345),F(3456)\}.
\end{aligned}
\]

## Theorem

For every normalized monotone submodular $F$ on this source:

1. $A_F=0$ implies $P_F=0$.
2. If $P_F>A_F$, then the strengthened inequality
   \[
   3P_F+F(3)\le4A_F
   \]
   holds.
3. Consequently $P_F/A_F\le4/3$ whenever $A_F>0$. The maximum is exactly $4/3$, already within coverage costs.
4. On strictly increasing submodular costs, and on strictly increasing coverage costs, the supremum is $4/3$ but is not attained. Strictly increasing means $F(S)<F(T)$ whenever $S\subsetneq T$.

No normalization of $A_F$ to one, continuity assumption on the set function, or LP dual certificate is required for the upper bound.

### Step 1: a three-inequality submodular bound

Set $Y=03456$, $X=2345$, $Z=014$, $I=345$, and $J=34$. Two applications of submodularity give

\[
\begin{aligned}
F(0345)+F(3456)&\ge F(Y)+F(I),\\
F(234)+F(I)&\ge F(X)+F(J).
\end{aligned}
\]

For the first adaptive-only envelope, a third application, followed by monotonicity, gives

\[
F(013)+F(J)\ge F(0134)+F(3)\ge F(Z)+F(3).
\]

Adding cancels $F(I)$ and $F(J)$, so

\[
F(Y)+F(X)+F(Z)+F(3)
\le F(013)+F(234)+F(0345)+F(3456)
\le4H_1.\tag{1}
\]

For the second adaptive-only envelope, replace only the third inequality by

\[
F(0135)+F(J)\ge F(01345)+F(3)\ge F(Z)+F(3).
\]

The first two are unchanged, yielding

\[
F(Y)+F(X)+F(Z)+F(3)
\le F(0135)+F(234)+F(0345)+F(3456)
\le4H_2.\tag{2}
\]

All unions and intersections in these three applications are literal set operations on the seven original query coordinates.

### Step 2: valid priority policies expose the three large sets

Suppose first that $P_F>H_1$. Since $P_F\le v_F(G_i)$ for each valid priority envelope, and all its other paths have cost at most $H_1$:

- In $G_1=\{013,234,Y\}$, the first two costs are at most $H_1$, hence $F(Y)\ge P_F$.
- In $G_2=\{013,0345,X,0356\}$, the three paths other than $X$ belong to $E_1$, hence $F(X)\ge P_F$.
- In $G_3=\{Z,24\}$, monotonicity gives $F(24)\le F(234)\le H_1$, hence $F(Z)\ge P_F$.

Inserting these three lower bounds into (1) proves

\[
P_F>H_1\quad\Longrightarrow\quad3P_F+F(3)\le4H_1.\tag{3}
\]

Next suppose that $P_F>H_2$:

- In $G_1$, $013\subseteq0135$ and $234\in E_2$, so $F(Y)\ge P_F$.
- In $G_4=\{015,045,245\}$, $015\subseteq0135$ and $045\subseteq0345$, so $F(245)\ge P_F$. Since $245\subseteq X$, monotonicity implies $F(X)\ge P_F$.
- In $G_3$, $24\subseteq234$ again implies $F(Z)\ge P_F$.

Equation (2) now proves

\[
P_F>H_2\quad\Longrightarrow\quad3P_F+F(3)\le4H_2.\tag{4}
\]

This argument uses the optimum over **all** priority policies only through its being no greater than each displayed valid policy's cost. It does not mistake a selected priority strategy for a priority lower bound.

### Step 3: pass from the two envelopes to the adaptive optimum

If a shared envelope $G_0,G_2,G_3,G_4$, or $G_5$ attains $A_F$, its valid priority policy gives $P_F\le A_F$, and thus equality. Otherwise some $E_i$ attains $A_F$. More generally, whenever $P_F>A_F$, no shared envelope can attain $A_F$, so at least one of $H_1,H_2$ equals $A_F$. Applying (3) or (4) proves the claimed strengthened inequality.

If $A_F=0$ but $P_F>0$, that same implication would give $3P_F+F(3)\le0$, contradicting nonnegativity. Therefore $A_F=0\Rightarrow P_F=0$.

For $A_F>0$, equality $P_F=A_F$ has ratio one. In the remaining case, dropping $F(3)\ge0$ from the strengthened inequality gives $P_F/A_F\le4/3$.

### Step 4: attainment and the strictly increasing class

The separately evaluated coverage construction is

\[
F_0(S)=|S\cap\{0,1,4,6\}|+2\mathbf1\{2\in S\}
       +\mathbf1\{S\cap\{0,5\}\ne\varnothing\}.
\]

Its complete frontier costs are $A_{F_0}=3$ and $P_{F_0}=4$. It is normalized, monotone and submodular because it is a nonnegative weighted resource coverage function. Thus the upper bound is attained within the smaller coverage class and is exact for both classes.

If $F$ is strictly increasing and normalized, $F(3)>F(\varnothing)=0$. Consequently (when $P_F>A_F$) the strengthened inequality gives $P_F/A_F<4/3$. When $P_F=A_F$, the ratio is one. A strictly increasing cost has $A_F>0$: the supports are both nonempty, so a zero-error policy cannot stop at the root, and every nonempty purchased set has positive cost. There are only finitely many such sets. Therefore no strictly increasing cost attains $4/3$.

On the other hand $F_\delta(S)=F_0(S)+\delta|S|$ is strictly increasing coverage for every $\delta>0$. For $0<\delta\le1/2$, its exact ratio is

\[
\frac{P_{F_\delta}}{A_{F_\delta}}=\frac{4+2\delta}{3+4\delta}\longrightarrow\frac43
\quad\text{as }\delta\downarrow0.
\]

This proves the stated supremum and nonattainment for each strictly increasing class. It does not characterize all maximizers in the non-strict class.

## Package evidence

The mathematical proof above is retained byte-for-byte from the preceding
internal note. The separate internal packaging record binds its original hash;
that machine-specific record is not required to execute this package.

Run this directory's `verify.py --mode all` to rebuild the complete fixed-source
frontiers and check both the additive and coverage certificate families.
`coverage/check_coverage.py` alone inherits the frontier premise.
This standalone package includes the explicit source supports above, but no
broader manuscript or six-query boundary data. No link to a sibling boundary
directory is required or supplied. The coverage LP does not prove the bound for
the whole submodular class; the three-inequality argument above does.
