# Reproducing the proof artifacts

[Project overview](../.github/README.md) · [Artifact map](ARTIFACTS.md) · [Version and URL notes](URL_MIGRATION.md)

The commands below replay existing finite proof objects and fixed examples. They do not require model API keys. Use a fresh extraction and keep Python assertions enabled: do not add `-O` or `-OO`.

## 1. Structural purchase-depth proof

**Requirement:** Python 3.10+ and its standard library.

1. Download the [structural proof ZIP at source `ea1a091`](https://github.com/SHiJiE1115/priced-equality-queries/raw/ea1a0914cc642b2ca18787ee1342ab76b7654771/theory/structural_depth_v01/public_structural_depth_v01.zip).
2. Extract it into a new directory and open a terminal in the directory containing `verify.py`.
3. Run:

```console
python -I -X utf8 -B verify.py --out-dir ../fresh-proof-output
```

The output directory must not already exist and must be outside the extracted package.

Expected finite verification:

| Component | Cases | Checked proof work |
| --- | ---: | --- |
| R | 64 | 35,244 proof nodes and 562,548 unit inferences; all cases UNSAT |
| C4 | 64 | 2,331 unit inferences; no witness splits |

The checker reconstructs the formulas. The written coverage, encoding, and policy-transfer arguments remain part of the mathematical proof.

**Public execution evidence:** [run 39358938427, attempt 1](https://github.com/SHiJiE1115/priced-equality-queries/actions/runs/39358938427), executed from `ea1a0914cc642b2ca18787ee1342ab76b7654771`; [retained service artifact and scope](https://github.com/SHiJiE1115/priced-equality-queries/tree/63eebe9d43d0f70d36f29331eee9f8ab9a130118/evidence/structural_depth_hosted_v01). The later archive commit is not the executed source. This is same-checker Windows/Linux reproduction.

The package's original README predates that Linux execution. Its preparation wording is retained as historical; the later execution record above supplies the outcome.

## 2. Fixed depth-four witness and Horn control

**Requirement:** Python 3.10+ and its standard library.

1. Download the [fixed-example ZIP at source `389071e`](https://github.com/SHiJiE1115/priced-equality-queries/raw/389071e9a7b20800c8ce44bd2332e3996e4089c2/theory/fixed_depth_witness_v01/public_fixed_depth_witness_v01.zip).
2. Extract it into a new directory and open a terminal in the directory containing `run.py`.
3. Run:

```console
python -I -X utf8 -B run.py
```

The runner writes output beside itself and rejects existing output files. Use a fresh extraction for each execution.

The complete seven-query source has adaptive cost **9/2** and priority cost **5**. The programs cover all **5,040** seven-query orders, **24** Horn-control orders, and **4,140** legal quotient partitions of the seven-query source. The Horn control is outside the complete equivalence-promise class. The fixed-example checks corroborate the separating examples; they do not verify the universal depth-three or six-query theorem.

The pinned package includes a scoped summary of its fresh Windows replay. Its original public deposit does not contain the later manuscript revision's Linux receipts. This guide makes no claim to redistribute those additional receipts.

## 3. Complete six-query boundary

Download from the [fixed release](https://github.com/SHiJiE1115/priced-equality-queries/releases/tag/complete-six-review-20261011-v01):

- `complete_six_review_v01.zip`
- `verify_download.py`
- `SHA256SUMS`
- `DOWNLOAD_GUIDE.md`

The ZIP is **1,253,960,690 bytes**. Its SHA-256 is:

```text
6d67d683e6b1df885df2c20f4157a11d7f71765ea219f06f9d32d4017b1693e8
```

To validate and optionally extract it:

```console
python -I -X utf8 -B verify_download.py --archive complete_six_review_v01.zip --extract-to complete-six-review
```

The extraction directory must be new. The archive and extracted files together require more than **2.75 GB**, plus filesystem overhead and any new verification output. Omitting `--extract-to` checks the archive without retaining an extracted copy. Integrity checking is distinct from executing the mathematical verification.

After extraction, follow `REVIEWER_GUIDE.md`, `VERSION_MAP.json`, and `execution_evidence/INDEX_V01.json`. The full-run command uses `--seconds 14400`; the wrapper's shorter default does not cover the observed reference execution. An older V03 full run took approximately 3.11 hours, which is not a runtime guarantee.

The recorded full execution covered **2,747,725 explicit six-query cases**. An additional **112,971 cases** are handled by stated analytic reductions. Later distribution checks and correspondence maps must not be described as fresh complete executions of every package version.

## Choosing a workflow

The local commands above are the recommended entrypoints. Historical GitHub Actions runners retain their original repository-identity checks and frozen source bytes. Renaming the repository does not update those identities. A new hosted reproduction would require a separately versioned runner and new execution records; do not edit old receipts or re-create an old tag to represent a new run.
