# Reproduce the fixed-seven cost certificates

This directory contains the small fixed-seven part of the complete-equivalence query project. It does not contain the much larger six-query universal-boundary package. A successful run here verifies a finite mathematical instance, not a scientific-paper dataset or a person's historical execution.

## Run locally

Use Python 3.10 or later with its standard library. From the repository root:

```console
python -I -X utf8 -B theory/fixed_seven/verify.py --mode all --seconds 120
```

Require exit code 0 and `PASS_FIXED_SEVEN_SUPPLEMENT_ALL`. Both mathematical children must finish. The command rebuilds 5,040 order frontiers, checks 13 policy witnesses and 864 additive certificates, and checks 864 coverage certificates. Do not use `-O` or `-OO`. Do not redirect output into `theory/fixed_seven`, whose inventory is exact.

To retain a local execution receipt, choose a new output directory outside the verifier package:

```console
python -I -X utf8 -B theory/ci/run_fixed_seven.py --execution-kind local-validation --expect-manifest-sha256 0b2e2ad1c312458b1a7d1802a65ef3a34ff8c1f94e3912630ccac8fc31c3d783 --output-dir ci-results/fixed-seven-local
```

The wrapper preserves complete verifier stdout, stderr, actual exit code, interpreter version and source bindings. It refuses to overwrite an existing run directory. A local receipt is explicitly labelled `local-validation` and has no GitHub run identity.

## Manual GitHub Actions workflow

`Fixed-seven exact-cost reproduction` is triggered only through `workflow_dispatch`. It uses the selected commit on an Ubuntu 24.04 runner, has a read-only repository token, does not retain checkout credentials, and does not call model APIs. Its two GitHub actions are pinned to complete commit hashes. It needs no repository secret, package installation, Docker image or large dataset download.

The workflow saves `receipt.json`, `verifier.stdout.json` and `verifier.stderr.txt` as one artifact, including when verification fails. The receipt records selected public GitHub context fields; it does not dump the environment. Those fields are runner claims, not a signed attestation. To cite an actual hosted execution, independently inspect its GitHub run status, selected commit, job status and downloaded output hashes. The presence of an artifact alone is not a passing result.

The first actual hosted execution succeeded on 2026-10-11 at commit `d4903be03b56dbb518175013839f87121dac9e8d`. See [the recorded run and persistent output archive](HOSTED_RUNS.md). Local validation and the older Wine workflow remain separate evidence; this run verifies only the stated fixed-seven scope.

## Scope and reuse

The ten executable and certificate files retain the reviewed mathematical bytes. Packaging and a CI wrapper are not a new independent mathematical implementation. The general submodular upper bound additionally needs the [written proof](fixed_seven/SUBMODULAR_PROOF.md); checking coverage certificates alone does not mechanically prove it. The six-query boundary, novelty, practical academic-evaluation advantage and human author approval are outside this run's scope.

See [the fixed-source guide](fixed_seven/README.md) and [source and permission status](fixed_seven/SOURCE_NOTICE.md). No new distribution licence is selected here. This proposed upload adds only `theory/` and a separately named workflow; it does not replace the existing Wine experiment.
