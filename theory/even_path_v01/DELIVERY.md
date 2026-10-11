# Even-path additive policy solver

This supplement accompanies [journal V08, Appendix E.2](../../manuscript/journal_v08/paper.pdf). Download [the five-file ZIP](even_path_v01.zip), or use the exact files in [package/](package/). The separate [fourteen-record control](../record_acquisition_v01/DELIVERY.md) concerns a different source.

From this directory after checkout:

```text
python -B package/alternating_path.py 1 7 2 3 5 1
python -I -B package/verify.py --output ../even_path_result.json
```

The first command prints a policy of exact worst cost11. The verifier replays only five existing fixtures: n6 unit4, n6 asymmetric11, n8 unit4, and two n2 software edge cases. It enumerates their full legal partition worlds and checks classification, paid anchor, priority order, leaf certificates and exact maximum costs. These are implementation and packaging regressions, not new scientific samples or new searches for an adaptivity gap. The analytic all-size theorem supplies the optimality argument.

The package README gives Python requirements, the callback contract and practical size/recursion limits. Only the Python standard library is required. No model key, external solver, repository-specific import or network is needed. Save verifier output outside the exact five-file package into a path that does not already exist.

[REPLAY.json](REPLAY.json) is the actual local verification output from a fresh ZIP extraction into a relocated directory. It contains relative file hashes and the execution scope. It is not a GitHub Actions run, cross-platform validation, a human annotation, natural-workflow advantage or historical certification. The original solver source bytes are unchanged from the previously reviewed implementation. This attachment is separate from the frozen complete-six review archive. No new blanket licence is selected.
