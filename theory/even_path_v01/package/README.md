# Complete even-path record acquisition: additive solver

This five-file supplement provides an exact additive-cost solver and a bounded replay of five previously fixed fixtures. Python 3.10 or later and its standard library are sufficient. It uses no network, model API, external project module, solver installation or downloaded dataset. This package is prepared for distribution; this README does not assert that a new hosted run or public upload has occurred.

## Mathematical scope

For even n >= 2, the physical records are 0,...,n-1. Source A contains every equivalence partition satisfying (0~1),(2~3),...,(n-2~n-1). Source B contains every partition satisfying (1~2),(3~4),...,(n-3~n-2) and 0 not~n-1. All other merges are allowed. The number of equivalence classes is unrestricted.

An action buys one unread record. Its response reveals that record's equivalences to previously bought records, including the possibility of a fresh class. Absolute class names, content, file size and timing are not observable. The first record gives no informative response and is nevertheless included in the purchased set and paid for. The solver uses only equality to this original anchor, while ignoring additional available relations. Both policy classes receive the same relative-record oracle. A strong priority policy fixes one record permutation and may causally skip records permanently or stop.

Journal manuscript V08, Appendix E.2 (Theorem 8 and Corollaries 9-10 in the reviewed build), gives the complete-source containment proof and additive recurrence. Every adaptive policy has a correct priority policy whose purchased sets are contained in corresponding paths on possibly different legal hard worlds. The proof retains the actual first anchor and extends the tree to every legal multicolour partition. This implies equality for all normalized monotone purchased-set costs; the implementation here optimizes **only nonnegative additive prices**. The order may depend on prices. This source is different from the earlier fourteen-record control and supplies no all-price theorem for that source.

Path transition search is related to classical inconsistent chain 2-CNF search: Lovasz, Naor, Newman and Wigderson, *Search Problems in the Decision Tree Model*, SIAM Journal on Discrete Mathematics 8(1), 119-132 (1995), Section 4, DOI 10.1137/S0895480192233867. Alphabetic search trees and minimax interval decomposition are established techniques; no new generic search or DP algorithm is claimed. The specific relational containment and full-world lifting argument is given in the manuscript. No third-party paper bytes are included.

## Solver usage

    python -B alternating_path.py 1 7 2 3 5 1

The output contains one anchor, the exact worst cost, an alphabetic policy tree and its fixed record permutation. CLI prices are exact nonnegative integer, rational (for example 3/2), or finite decimal strings. The Python `solve(prices)` API accepts integers, Fraction objects or such strings; boolean and binary-float objects are rejected. The number of prices must be even and at least two. Zero prices are supported. Negative prices, randomization, errors, expected costs, answer-dependent charges and arbitrary nonadditive costs are outside this solver contract.

`execute(policy, acquire)` first calls `acquire(record, None)` to buy the anchor and ignores its return. Later calls are `acquire(record, anchor)` and must return a bool indicating equality to the original anchor. The caller must provide a world satisfying the source promise and a trusted solver-produced policy. The callback buys the record; comparisons among already acquired records are free. The priority witness uses the anchor followed by tree preorder, and can skip intervening off-path nodes causally. The callback API is not a real-file acquisition adapter.

## Exact recurrence and size limits

For cyclic cut intervals use D[a,1]=0 and

    D[a,l] = min over 1 <= s < l of
             c[(a+s) mod n] + max(D[a,s], D[(a+s) mod n,l-s]).

The optimum is min_i(c[i]+D[i,n]). One shared table serves all anchors, with n squared states and n squared times (n-1)/2 split candidates. It uses O(n cubed) exact arithmetic operations and O(n squared) stored values/splits. Rational bit lengths affect the actual computational cost. This is minimax node-priced search, not expected weighted-leaf coding.

The preserved solver recursively reconstructs and serializes its tree; deep trees can hit Python recursion limits. Zero-price ties can produce such deep trees. Cubic time and quadratic storage also limit practical sizes. This small package makes no unbounded-input resource guarantee and performs no large-size benchmark. It deliberately preserves the reviewed solver bytes rather than changing its implementation.

## Fixed replay

After extracting all five files into one directory, run from that directory:

    python -I -B verify.py --output ../verification.json

Choose a new output file outside the extracted package, with an existing parent directory. Existing output files are refused. No execution output belongs inside the five-file package. The verifier loads only its sibling solver after digest verification; it sets bytecode writing off and requires the exact package inventory. It rechecks all member bytes after replay. On a caught verification failure it records a FAIL result and exits nonzero; invalid output destinations fail before running fixtures.

The only replay contracts are:

| Fixture | Prices | Expected worst cost | A worlds | B worlds |
|---|---|---:|---:|---:|
| n6_unit | 1,1,1,1,1,1 | 4 | 5 | 10 |
| n6_asymmetric | 1,7,2,3,5,1 | 11 | 5 | 10 |
| n8_unit | 1,1,1,1,1,1,1,1 | 4 | 15 | 37 |
| n2_zero | 0,0 | 0 | 1 | 1 |
| n2_rational | 0,3/2 | 3/2 | 1 | 1 |

The verifier independently generates set partitions by recursively choosing the block containing the least unused record, then filters the complete A/B constraints. It checks Bell counts 203, 4140 and 2 as applicable, and visits all 82 existing scientific-fixture world traces plus four software-edge traces. It checks callback acquisitions, the first anchor and its price, the global order, all-world labels, acquired ordinary-edge or endpoint-seam certificates, exact path sums and observed maximum. `fixtures.json` explains each expected value's source. The two six-record expectations came from earlier independent adaptive/all-order calculations. The eight-record expectation is supported by the previously checked alphabetic family plus the analytic theorem, not an enumerated adaptive frontier. This replay supplies implementation regression evidence; it does not recompute those lower bounds or prove the arbitrary-size theorem by testing.

## Files and integrity

- `alternating_path.py`: byte-identical frozen solver, SHA256 f9127ebd2c8386f5a338dab5b462490e6ff58cefe113816fab7b54b123ea4b3b.
- `verify.py`: self-contained fixed-fixture replay and package-integrity checks.
- `fixtures.json`: exact five fixture contracts and provenance limits.
- `README.md`: model, use, limits and evidence scope.
- `MANIFEST.json`: relative names, byte counts and SHA256 for the other four members; it explicitly excludes itself. The external ZIP/preparation or delivery receipt binds the manifest and ZIP.

Hashes identify bytes, not signatures or scientific correctness. This is a synthetic mechanical model supplement. It supplies no human review, author approval, historical experiment authentication, natural academic-evidence advantage, publication acceptance or new literature-priority certification. No blanket licence or ownership statement for the whole research project is supplied by this package.
