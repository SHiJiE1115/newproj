Record acquisition: portable verification package
=================================================

This package reproduces a finite synthetic model-boundary result. It uses the
same 14-record complete equivalence sources as journal V06, but changes the
physical actions: buy one record and learn its equality to every previously
bought record. All legal cross-block merges remain possible. The verifier does
not replace the full sources by their eight isolated-pair answer templates.

Requirements and command
------------------------
Python 3.10 or later, standard library only. No solver, network, package install,
local research repository, complete-world file or producer module is required.
From the extracted directory, with the result outside that directory:

  python -B verify.py --bundle . --output ../record_verification.json

Paths may contain spaces when quoted according to your shell. The output must
not already exist and must resolve outside the package. The verifier checks the
flat five-file inventory and SHA-256 bindings before and after verification.
It writes only the requested result. The package does not modify its inputs.

Checks and interpretation
-------------------------
1. Unit record prices: all 91 first unordered pairs and all 12 possible third
   records admit a shared observed partition under a fixed adversarial first
   answer. DSU extension supplies an explicit legal full partition for each
   label, without enumerating the 4,140 complete worlds. An explicit globally
   ordered four-read policy is checked on every feasible observation branch.
   Therefore adaptive and strong-priority optima both equal 4.
2. Matched record prices: each old pair charge is split equally between its
   endpoints. Integer weights are (4,4,4,4,6,6,1,1,2,2,2,2,2,2), divided by 4.
   A DSU-based decision recurrence considers every affordable next record and
   every feasible induced-equality response. Budget 14 is infeasible.
3. The original saved budget-15 policy is checked on all feasible response
   branches. Terminals must be pure and correct, the maximum cost must be 15,
   and every path must increase in the supplied single global record order.
   Causal permanent skips therefore implement the same tree. Together with
   the lower bound, both matched-price optima equal 15/4.

The matched and unit conclusions were known before this portable replay. The
unit result alone would not establish the matched-price result. A source model
or price change requires separate analysis; no arbitrary-price theorem is
claimed. These results show that the isolated-pair gap does not persist under
this particular richer record-read contract. They do not invalidate the old
pair-menu theorem or establish a natural academic acquisition advantage.

Caps and failures
-----------------
Verification has a cooperative 120-second time limit and a 300,000-state limit
for the budget-14 recurrence. The liveness cache is bounded by 300,000 entries.
These are algorithmic caps, not a universal RAM or operating-system deadline.
A cap, malformed input, changed hash or failed check produces a non-PASS result
and nonzero exit when a result can be written. A final result-write error is a
nonzero process failure, not acceptance. Successful acceptance requires exit 0
and status PASS_RECORD_ACQUISITION_VERIFICATION in the result. Typical runtime
and cross-platform support should be reported from actual tests, not promised
by this README. SHA-256 manifests bind bytes; they are not signatures.

Files and provenance
--------------------
source.json contains the complete source constraints, prices, orders and fixed
provenance hashes. budget15_policy.json preserves the iteration294 certificate
bytes. verify.py is a self-contained port of that iteration's independent DSU
checks. MANIFEST.json lists the other four package files. No absolute local
machine paths or internal tool observations are needed by these inputs.

This package is prepared for research review. This packaging operation makes
no whole-project licence grant and no blanket redistribution clearance. It
contains synthetic source constraints and a mathematical policy certificate;
it does not assign rights to the separate manuscript or third-party material.
