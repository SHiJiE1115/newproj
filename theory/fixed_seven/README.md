# Fixed-seven exact verification package

This internal upload candidate checks one fixed seven-query source. It is a
standalone extraction of existing verification programs and small certificates;
packaging is not a new independent mathematical implementation.

## Run

Python **3.10 or later**, with its standard library only, is required. From this
directory run:

```console
python -I -X utf8 -B verify.py --mode all --seconds 120
```

From the repository root the equivalent command is:

```console
python -I -X utf8 -B theory/fixed_seven/verify.py --mode all --seconds 120
```

Do not use `-O` or `-OO`: assertions are part of the checks. No API, network,
download, third-party solver or mathematical data outside this directory is
needed. The entrypoint and its children do not write result files or bytecode.
Redirect any output **outside** this directory; the inventory rejects additional
or missing files. The time limit is per mathematical child, not a performance
guarantee. A cap, failure, nonzero exit or partial mode is not an all-mode pass.

Require exit code zero and JSON status `PASS_FIXED_SEVEN_SUPPLEMENT_ALL`. That
status requires inventory checks and both children, including:

- both eight-world supports and the complete adaptive frontier;
- all **5,040** global-order frontiers with causal permanent SKIP;
- **13** policy-witness replays and **864** exact additive-price certificates;
- **864** exact coverage-cost certificates, their **12** controls and the
  explicit coverage witness with adaptive cost 3 and priority cost 4.

`--mode files` checks bytes only; `seven` and `coverage` check separate layers.
`coverage` alone inherits the complete-frontier premise. Use `all` to rebuild
that premise and check coverage certificates in the same invocation.

## Scope and written proof

The additive maximum is **5/4** for this fixed source. The coverage maximum is
**4/3**; extension of the upper bound to every normalized monotone submodular
cost requires the [written three-inequality proof](SUBMODULAR_PROOF.md).
Coverage-certificate enumeration alone does not prove that general statement.
The program explicitly leaves `all_submodular_upper_bound_mechanically_proved`
false, and the written proof remains a separate mathematical obligation.

This package does not check the universal six-query boundary, all seven-query
sources, literature novelty, historical scientific execution or application
benefit. It contains no manuscript PDF or journal template. Its fixed Boolean
supports are explicit in the proof and code; a broader manuscript and its
source-realization discussion are not distributed here.

The ten execution files are byte-identical to the previous internal supplement.
This new package has a new exact manifest. Its current-location execution must
be established by the new CI or local receipt, not inferred merely from old
passes. See [SOURCE_NOTICE.md](SOURCE_NOTICE.md) for the internal-preparation
and rights boundary. No publication, author approval or licence grant is implied.
