# Required trace-isolation evidence: bounded baseline correction

This directory records one retained positive input and one synthetic field-erasure
control. The SQL baseline omitted a required admission predicate; its corrected
version now requires that predicate. This is a software correction with a bounded
regression, not a new theory result or a natural-material error-rate estimate.

## Observed result

| Report input | Candidate | Original SQL baseline | Corrected SQL baseline |
|---|---|---|---|
| Original v09 report | admitted | admitted | admitted |
| Only trace_isolation_observed removed | unresolved | admitted | unresolved |

The synthetic fixture deletes only
`/receipt_audit/checks/trace_isolation_observed`, preserving the three summary PASS
statuses and all other report values. Both adapters load the same derived report
bytes with a new descriptor and the same unchanged tar, direct report and release
gate. The baseline uses its own source inspection, arithmetic and signature
admission, followed by an actual SQLite identity join. The numeric and retained
signature premises remain positive in both cases. Missing evidence does not prove
that the physical execution was unisolated or that no read occurred.

The required predicate comes from the frozen v09 observer-isolation contract and
the candidate's explicit required-field list. The old SQL helper checks selected
execution/read/order flags and summary statuses but does not independently
recompute the missing isolation predicate. The minimal patch adds this field to
its required candidate flags, using its existing strict-true check.

## Reproduce the differential

Extract the [previous v02 package](../typed_admission_correction_v01/wine_layer_calibration_v02.zip)
to a directory and use Python 3.11 or later. The output parent must exist and have
at least 64 MiB free; the output directory must be new and outside the bundle.

```text
python -I -X utf8 -B reproduce_read_erasure.py --bundle PATH_TO_EXTRACTED_V02 --output NEW_OUTPUT_DIRECTORY
```

The [script](reproduce_read_erasure.py) verifies code/input pins, freezes the two
fixtures, executes the original control, produces the exact one-field code patch,
and executes the corrected control. Both modes record the observations even if
the predicted result is falsified. It uses only the standard library and performs
no network requests or fresh signature verification. It is not the original
frozen CLI and does not bypass that CLI's input or protocol hashes.

## Corrected full package

Extract [wine_layer_calibration_v03.zip](wine_layer_calibration_v03.zip) and follow
its README (`python -I -X utf8 -B run.py --output NEW_OUTPUT_DIRECTORY`). This keeps
the v02 typed-exit candidate correction and adds the one-field SQL baseline fix.
The protocol, 17 inputs and two original reference results are unchanged. The
package was extracted to a new directory and both candidate and baseline were
actually executed. All six original scenarios, 30 layer labels and identity counts
remain unchanged. The comparison explicitly accounts for the new required flag
and, for v07, its missing-field diagnostic; it does not discard those diagnostics.

## Receipts and limits

- [Plan frozen before the original control](PLAN_V01.json).
- [Original result](results/original_probe.json), [corrected result](results/patched_probe.json), and [exact patch](trace_isolation.patch).
- [Portable original](results/portable_original_probe.json) and [portable corrected](results/portable_patched_probe.json): execution of the same two inputs through the portable entry, not two more unique interventions.
- [Independent AI technical QA](results/INDEPENDENT_ERASURE_QA_V01.json), [package build](results/PACKAGE_BUILD_V01.json), [execution](results/PACKAGE_EXECUTION_V01.json), and [acceptance](results/PACKAGE_ACCEPTANCE_V01.json).
- [File manifest](MANIFEST.json).

Semantic certificates are checked against the facts admitted by an adapter. The
original baseline's incorrect support on the derived report also yields a valid
certificate for its incorrect fact projection. This demonstrates the boundary of
that checker; it does not certify the external fact. Certificate snapshot digests
bind the new fixture and code scope while the library's old scope label is retained.

The retained real v09 report includes the required flag. Neither the old real-run
results nor any original frozen package is overwritten. This control does not
establish general adapter equivalence, application advantage, human gold, an
attestation forgery, or original historical-execution authentication. The raw JSON
receipts retain inert originating Windows paths for audit; those paths are not
portable dependencies. No author approval or journal submission is implied.
