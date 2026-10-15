# One observed hosted reproduction

[GitHub Actions run 38682872578, attempt 1](https://github.com/SHiJiE1115/newproj/actions/runs/38682872578)
completed successfully on Ubuntu 24.04 at source commit
`7beea07359a15d6084d630a31e0e7bfcc06c4ae7`. It was the push-triggered run of
[the fixed package](https://github.com/SHiJiE1115/newproj/tree/7beea07359a15d6084d630a31e0e7bfcc06c4ae7/evidence/rounded_metrics_v01).

The Linux job recomputed the full rational calculation. Its complete parsed JSON
matches the prior Windows calculation and the retained expected result with
JSON types preserved. Formatting bytes differ between Windows and Linux; their
raw hashes are therefore recorded separately in [SUMMARY.json](SUMMARY.json).

## Retained evidence

- [computed.json](computed.json): original Linux result bytes, including every
  feasible vertex, rational bound, target slice and constructed witness.
- [execution.json](execution.json): original runner receipt, including source
  commit, manifest hash, run identity, runtime and result digests.
- [provider_jobs.json](provider_jobs.json) and
  [provider_artifacts.json](provider_artifacts.json): original public GitHub API
  response snapshots observed after completion.
- [SUMMARY.json](SUMMARY.json): selected run, job and artifact identities, hashes,
  complete comparison result, and limits.

The archive downloaded for this run had SHA-256
`09601458caae8af84e6d209db8e414cb4d4e97e09e4461c214d838d14a8f09a2`.
Both retained output files matched its entries exactly. The provider artifact
was scheduled to expire on 2026-10-29; these copies keep its two output files
available independently of that retention window. `.gitattributes` preserves the
original bytes in Git checkouts.

## What this establishes

This records one concrete hosted execution of the MACD four-rounded-point
conditional identification calculation and its constructed common-cohort
witnesses. The original scientific experiment and the PyHealth calculation are
outside this package. All counts are mathematical witnesses, never recovered
paper data or human gold labels. Accuracy confidence intervals, bootstrap
procedures and McNemar statistics are not modeled. Independent marginal ranges
are not joint sharp bounds for a shared cohort.

Provider observations and hashes are not signed historical execution
authentication. This result establishes no model superiority, semantic accuracy,
human review, new theoretical novelty or guarantee across all environments.
There were no model API calls.

This receipt directory is separate from `evidence/rounded_metrics_v01`. Adding
only these files does not match the rounded-metrics workflow's push-path filter
and does not request another run.
