# Wine receipt admission: typed exit-code correction

This is a bounded correction to the Wine evidence adapter. It adds no theory result.
Independent AI/programmatic [probe QA](results/INDEPENDENT_TYPED_ADMISSION_QA_V01.json): **PASS**, with no claim of human review.
Actual fresh-directory v02 [package regression](results/PACKAGE_ACCEPTANCE_V01.json): **PASS**. The launcher and its candidate and SQL children each ran once and exited zero.

## Observed defect and correction

The plan was frozen before execution: `/ACCEPTANCE.json/verify_exit` must parse as a Python `int` equal to zero. JSON `false` and `0.0` fail this operational receipt schema.
The original adapter used ordinary equality, under which both values compare equal to zero. The independent baseline's retained-signature helper used a strict integer check.
Actual helper calls on identical derived evidence produced:

| JSON value | Required admission | Original adapter | Baseline helper | Patched adapter |
| --- | --- | --- | --- | --- |
| `0` | accept | accept | accept | accept |
| `false` | reject | accept | reject | reject |
| `0.0` | reject | accept | reject | reject |
| `1` | reject | reject | reject | reject |

The two wrongly admitted original cases produced `MET` for the retained-signature and joint layers, with `checker.valid=true`. After correction these cases produce `UNRESOLVED`; their certificates still pass the unchanged semantic checker.
The semantic checker verifies conclusions from the supplied facts. It does not authenticate the adapter's receipt interpretation. A valid certificate therefore does not repair an incorrectly admitted fact.

The [patch](typed_exit.patch) adds a typed-zero helper and uses it for `download_exit`, `verify_exit`, and retained gate `gh_exit_code`. Dynamic fault interventions in this probe vary **only `verify_exit`**; the other two call sites receive the same static correction and are not separately mutation-tested.

## Evidence and scope

- [Original probe](results/original_probe.json): four actual interface calls; two contract mismatches.
- [Patched probe](results/patched_probe.json): the same four cases; zero contract mismatches.
- Both helpers receive identical acceptance, bundle, saved verification output, gate, and identity. The probe calls the baseline's retained-signature helper; it does not execute the later SQL join.
- Only the `verify_exit` token changes in each synthetic receipt. The new fixture and plan are bound into a derived scope; the original pinned CLI is neither invoked nor bypassed by this helper probe.
- These are four synthetic type/value interventions, not four scientific replications or an estimate of natural error frequency. They supply no human gold, fresh signature verification, historical execution authentication, or new author execution.
- The frozen iteration302 inputs contain the valid integer zero. This correction does not overturn their retained results or replace their original records.
- Trace-isolation erasure was not tested in this round; no resolution of that separate question is claimed.

## Corrected package and replay

The corrected package is [wine_layer_calibration_v02.zip](wine_layer_calibration_v02.zip), 999,672 bytes, SHA256 `15ddc558509b0153c7105449fb490fb0ccbb759eedda0e01bd01b2424729518d`. Its [actual regression](results/PACKAGE_ACCEPTANCE_V01.json) preserves all six original scenarios, 30 layer labels and identity counts. The comparison allows only the three typed-exit diagnostics in each applicable signature report plus the previously declared certificate scope rebinding; all remaining report fields are compared exactly. The original protocol, 17 inputs and two retained references remain unchanged.
To replay the corrected calibration after extracting the ZIP, open a shell in its extracted root and run:

```powershell
python -I -X utf8 -B run.py --output "D:/wine-v02-replay-001"
```

Choose a new, nonexistent output directory outside the extracted bundle; its parent must already exist. This command replays the retained calibration, not the four synthetic helper interventions. It does not launch the original Wine author experiment or perform fresh cryptographic verification.

## Frozen history

The prior [v01 companion](../scoped_companion_v02/README.md) and [v01 Wine package](../scoped_companion_v02/packages/wine_layer_calibration_v01.zip) remain the frozen history. The original public snapshot is commit [`eeba70beba1cc69d49daac1b948b0bf182d02966`](https://github.com/SHiJiE1115/newproj/tree/eeba70beba1cc69d49daac1b948b0bf182d02966/evidence/scoped_companion_v02).
The v02 correction is additive; it must not be represented as the bytes or execution history of v01.

## Reproduce the four-case differential

Extract the original v01 ZIP and corrected v02 ZIP into separate directories. From this correction directory run:

```powershell
python -I -X utf8 -B reproduce_typed_exit.py --original "D:/wine-v01" --corrected "D:/wine-v02" --output "D:/typed-exit-replay-001"
```

The output must be new, outside both bundles, with an existing parent. Source and original input pins are checked before helper invocation. The [portable replay result](results/portable_probe.json) records one actual execution of this script, reproducing the same four controls; it is not four additional unique interventions. The complete raw probe reports retain inert paths from the originating Windows environment. None of those paths are executed by the portable script.

The original package's source-specific notices remain in the new package. No blanket licence, fresh signature verification, general malformed-input completeness, or human approval is asserted. This publication fixes an adapter defect and documents the conditional scope of semantic certificate checking; it does not establish a new theoretical contribution.
