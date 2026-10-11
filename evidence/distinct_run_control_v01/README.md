# Wine: two actual execution identities under one fixed design

This review bundle records **one new requested Wine execution**, compared with
one previously retained execution. It is not three execution trials, an
accuracy benchmark, a new learning method, a new dataset, or a new theorem.
The same-information SQL baseline agrees with the semantic candidate in all
three predeclared rows; no method advantage is inferred.

| Frozen comparison | Candidate | Strong SQL baseline | Distinct admitted run events |
|---|---|---|---:|
| Two references to the old event; require two runs | UNRESOLVED | UNRESOLVED | 1 |
| Old event plus the new actual event; require two runs | MET | MET | 2 |
| Same pair; require separation by run, dataset and implementation | UNRESOLVED | UNRESOLVED | 2 |

The final row has two different run identities but the **same pinned dataset
and implementation**. Counts alone do not satisfy all requested dimensions.
All rows share a single artifact-version target and fixed experiment design.
The plan was frozen before requesting the new event; the old successful result
was already known. This control does not establish statistical independence,
independent scientific replication, human gold, complete consumed-byte evidence,
the paper's historical execution, or application superiority.

## Identity and evidence

- Source commit: `6f64dd2a7dd75ee14ca65d2e00c4e0a5ea0d131b`, branch `trace-isolation-v09-fd-observation`.
- Old event: [38136338509, attempt 1](https://github.com/SHiJiE1115/newproj/actions/runs/38136338509).
- New event: [38175966754, attempt 1](https://github.com/SHiJiE1115/newproj/actions/runs/38175966754).
- [Frozen plan](PLAN_V01.json), [pre-dispatch state](INITIAL_PROVIDER_STATE_V01.json),
  [new identity](NEW_RUN_IDENTITY_V01.json), [terminal provider observation](polls/POLL_002.json),
  [capture result](CAPTURE_RESULT_V01.json), and [three-row result](comparison_v01/RESULT_V01.json).
- The [old v03 Wine calibration ZIP](../read_gate_correction_v01/wine_layer_calibration_v03.zip)
  supplies the unchanged old event, signature records and same-information
  semantic/SQL adapter modules. This new bundle does not duplicate that ZIP.
- New provider artifact: [new_run_artifact.zip](new_run_artifact.zip), SHA-256
  `83649090a8e733fb2f1f342fdf6638c5e9de75a0fcc344081e6b5769728141ba`.
  Its `receipt.tar` is included once inside this ZIP, not copied again here.
- [Native and direct reports](new_run_release_gate/POSTRUN_RELEASE_GATE.json)
  and [retained signature acceptance](new_run_signature/ACCEPTANCE.json) bind the
  same tar, source commit, signer workflow, new run ID and attempt.

The separately performed [independent execution QA](INDEPENDENT_EXECUTION_QA_V01.json) is included verbatim; its exact scope and limitations remain those of that report.

The source includes a fixed Ubuntu base-image digest and source/data hashes.
The Dockerfile installs apt packages without version pins, and the hosted runner
image can change. Same code/data/contract therefore does not promise identical
runtime versions or CSV bytes. This control did not alter the original tolerance,
25 draws, seeds, target, author archive or Wine data.

## Recheck the new native receipt

Verify the file hashes against [MANIFEST.json](MANIFEST.json) first. From this
directory, reconstruct only the already included tar into the existing report
directory (the command refuses to replace it):

```sh
python -c "from pathlib import Path; import zipfile; p=Path('new_run_release_gate/receipt.tar'); assert not p.exists(); p.write_bytes(zipfile.ZipFile('new_run_artifact.zip').read('receipt.tar'))"
git clone --no-checkout https://github.com/SHiJiE1115/newproj.git wine_source
git -C wine_source checkout --detach 6f64dd2a7dd75ee14ca65d2e00c4e0a5ea0d131b
python -B wine_source/experiment/verify_receipt.py new_run_release_gate/receipt.tar new_native_verification.json SHiJiE1115/newproj 6f64dd2a7dd75ee14ca65d2e00c4e0a5ea0d131b 38175966754 1
```

The tar SHA-256 must be
`e13c59a72aa48619d02e068d47743f81ae630d4a935ab43c7a4939063c99a7e7`.
Use a new report path and the exact checkout above: the verifier checks its
source freeze, including README and workflow bytes. Checking the current main
checkout is not an equivalent source check. The native verifier uses Python's
standard library; its successful result is scoped selected-syscall/arithmetic
evidence, not a substitute for the provider and signature checks.

Optional fresh verification of the **retained** signature bundle with GitHub CLI:

```sh
gh attestation verify new_run_release_gate/receipt.tar --bundle new_run_signature/sha256-e13c59a72aa48619d02e068d47743f81ae630d4a935ab43c7a4939063c99a7e7.jsonl --repo SHiJiE1115/newproj --signer-workflow SHiJiE1115/newproj/.github/workflows/rrnc-wine-strace.yml --source-digest 6f64dd2a7dd75ee14ca65d2e00c4e0a5ea0d131b --source-ref refs/heads/trace-isolation-v09-fd-observation --deny-self-hosted-runners --format json
```

Also require the verified certificate's run invocation URI to be
`https://github.com/SHiJiE1115/newproj/actions/runs/38175966754/attempts/1`.
Trust-root metadata may require network access; this is not a promise of fresh
fully offline cryptographic verification.

## Comparison adapter and portability boundary

[compare_distinct_events_v01.py](compare_distinct_events_v01.py) is the tested
**Windows project reference adapter**, not a one-command portable package. It
can select `--plan`, `--new-artifacts`, `--v03-package`,
`--old-release-directory`, `--old-signature-directory` and
`--initial-provider-state`. The layout here preserves the expected new-event
names, including `polls/POLL_002.json`; reconstruct the tar as above before use.
Extract the linked v03 ZIP to supply the old event and the five pinned modules.
The adapter still requires a fresh `--storage-guard` satisfying its project-specific
Windows disk-volume contract and a new `--output` directory. No old guard is
included as permission for a new run, and no cross-machine execution of this
adapter is claimed. Inspect the source before adapting its administrative paths;
keep its input hashes and scientific comparisons unchanged.

The included controller and collector are historical execution-source records,
not portable entry points. Do not invoke them to reproduce this comparison:
they contain project paths and the controller can request a new hosted run.
This bundle contains no credentials, private author forms or environment dump.
Historical metadata and source files retain inert Windows paths and intentional
public repository/run identities; the release is not anonymized. Such paths
are provenance, not evidence of a current local prerequisite or authorization.

The native artifact retains the pinned author archive from
[the authors' repository](https://github.com/jsleb333/paper-decision-trees-as-partitioning-machines/tree/0f354dac486a9845a9504419e31c84c7eb39507f)
and [UCI Wine data](https://archive.ics.uci.edu/ml/machine-learning-databases/wine/wine.data),
as did the earlier public Wine evidence. Original embedded notices remain with
those source bytes; no blanket project or third-party licence is newly granted.
This directory is a prepared review bundle; local preparation alone is not a
claim that a repository publication has occurred.
