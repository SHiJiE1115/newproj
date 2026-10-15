# Rounded point metrics: conditional FPR identification

This small Python standard-library package reproduces the **MACD conditional
identification calculation from research iteration336**. It does not reproduce
the paper's underlying experiment, the PyHealth source audit, or the pending LLM
batch. No API key, download, third-party Python library or private directory is
required. Python 3.10 or newer is required.

## Run

From this directory, use the manifest hash recorded in `MANIFEST.sha256`:

```text
python -I -X utf8 -B run.py --output-dir results --expect-manifest-sha256 HASH_FROM_MANIFEST_SHA256
```

The output directory must not already exist. `computed.json` contains newly
calculated vertices, bounds and mathematical witnesses. `execution.json` records
the runtime, exit status and result digest. The command computes from `inputs.json`
before loading `expected.json` for a complete, type-sensitive comparison.
The manifest pins the runner, core, inputs, expected results and documentation;
`MANIFEST.sha256` provides its outer digest.

## Inputs and assumptions

The two printed rows have (accuracy, precision, recall, F1):

| Row | Accuracy | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| Baseline | .72 | .55 | .96 | .70 |
| MACD | .85 | .73 | .90 | .80 |

`DERIVATION.json` identifies the versioned source, original table/node locations,
archived source hashes, and the previously executed calculation's hashes.
The input strings are transcribed table facts, **not human gold labels**.
The versioned source is [Table 4 in arXiv:2602.01740v1](https://arxiv.org/html/2602.01740v1#S5.T4).

Each method is conditionally modeled as one binary confusion matrix. All four
point metrics are assumed rounded to the nearest 0.01. Closed +/-0.005 intervals
conservatively include ties. Confidence intervals, bootstrap procedures, McNemar
statistics and actual sample sizes are not modeled or validated.

The exact rational program enumerates all 220 intersections of three of twelve
constraint planes, retains feasible vertices, and computes FPR extrema. With a
strictly positive denominator, the linear-fractional objective attains extrema
at vertices. These are **conditional identification intervals**, not confidence
intervals. Separate per-method ranges are not sharp joint bounds under a common
cohort restriction.

## Retained findings

The independent marginal ranges are approximately .3873044--.4210411 for
Baseline and .1643667--.1877342 for MACD. Their endpoints conservatively include
rounding ties. The published .40 and .17 values are compatible with these
assumptions; compatibility does not imply unique identification.

Two constructed worlds strengthen the non-uniqueness example. Each world uses a
common hypothetical total of 1500, with 500 positives and 1000 negatives:

| World | Baseline TP,FP,FN,TN | MACD TP,FP,FN,TN | FPR pair |
|---|---|---|---|
| A | 480,400,20,600 | 450,170,50,830 | .400, .170 |
| B | 480,398,20,602 | 450,169,50,831 | .398, .169 |

All four point metrics lie strictly inside their rounding intervals in both
worlds. **These counts are mathematical witnesses, never actual or recovered
paper data.** They do not claim to fit the reported accuracy confidence intervals.
Only the four rounded point metrics are being shown insufficient for uniqueness.

The calculation is a scoped evidence-boundary result. It establishes no model
superiority, semantic accuracy, new theorem novelty, human review, historical
authentication or journal acceptance. This addition does not select a blanket
licence for the repository or change earlier frozen evidence.

## Hosted validation

The repository workflow `rrnc-rounded-metrics.yml` computes the same package on
Ubuntu without secrets or model calls. It records the source commit, run ID and
attempt, retains success/failure output, and does not claim that a green workflow
reproduces the original paper's experiments. A hosted result exists only once its
actual execution and generated output have been inspected.
