# Record acquisition: finite control and reproducible supplement

This supplement accompanies [journal V07, Appendix E](../../manuscript/journal_v07/paper.pdf). Download [the original five-file ZIP](record_acquisition_v01.zip), or use the exact files under [package/](package/). The five-file directory is deliberately separate from this delivery note and execution receipt because the verifier checks its exact inventory.

From this directory after checkout:

```text
python -B package/verify.py --bundle package --output ../record_acquisition_result.json
```

Alternatively extract the ZIP into a new directory and follow its README. The output must not exist and must be outside the five-file directory. Python 3.10+ and its standard library are required; no repository-specific imports, model API, solver or network are used.

The ZIP is 10,813 bytes, SHA256 `250dcc12d735088ed3002a31a501e7d29227be4e6a89d2d2461e6071232e3cc7`. Its members exactly match the five files. [REPLAY.json](REPLAY.json) preserves the actual local relocated-directory result, with relative file hashes. That run used Windows and Python 3.12.14, completed with exit 0 and status PASS_RECORD_ACQUISITION_VERIFICATION, and took about 1.21 seconds. It was not an Actions run, a cross-platform test or a separate execution from an extracted ZIP. The publication commit packages the already executed bytes.

The check establishes unit-record adaptive = priority = 4 and matched-price adaptive = priority = 15/4. It considers all 91 first record pairs and 1092 third choices for the unit lower bound. For matched prices it establishes infeasible integer budget14 in 3233 states and validates all 83 nodes and 53 terminal states of the budget15 policy, including exhaustive responses, pure labels and the common global order.

Only relative equality among acquired records is revealed. All legal cross-block merges remain. Matching the price of each isolated original pair does not preserve the original action/information contract. These are finite synthetic model controls, not independent scientific studies, human gold labels, evidence of natural-workflow gains or historical provenance certification. The older complete-six archive and fixed-seven pair-menu supplement remain separate. The package preserves the original policy bytes and gives no new blanket licence grant.
