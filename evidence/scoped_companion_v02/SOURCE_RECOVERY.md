# Source retrieval and declared offline reconstruction

The public ValueEval bootstrap omits the organizer HTML and archive JSON. It
contains the other twelve unchanged scientific-package members. The two raw
bodies and the original complete ZIP are not redistributed here. This guide
adds a separate offline reconstruction step; it does not change the bootstrap,
the original manifest, the parser, the seven-object budget, or expected results.

## Three separate steps

1. Obtain the response bodies from the [official organizer page](https://touche.webis.de/semeval23/touche23-web/) and [official archive endpoint](https://archive.tira.io/api/evaluations/valueeval-at-semeval-2023-human-value-detection/arguments-test-20221205-test) with your HTTP client. Save the body bytes without reserializing the HTML or JSON, for example as `organizer_response.raw` and `archive_response.raw`. This repository does not include those bodies. Retrieval is separate from the offline program below.
2. Run the [offline restorer](recovery/restore_valueeval_local.py), using Python 3.10+ and a new output directory whose parent already exists. The program makes no network request and starts no scientific worker.
3. Extract [the bootstrap ZIP](packages/valueeval_bootstrap_v01.zip) into a directory such as `valueeval bootstrap`. Its unchanged `hydrate.py` imports the two exact files and verifies all fourteen original members before creating a complete scientific package.

From this companion directory, example commands are:

```text
python -I -X utf8 -B recovery/restore_valueeval_local.py organizer_response.raw archive_response.raw "../restored sources"
python -I -X utf8 -B "valueeval bootstrap/hydrate.py" --source-directory "../restored sources" --output "../complete valueeval package"
```

The first command's output has **two raw files and one restoration receipt**.
The second command's output is the original **fourteen-file scientific package**;
its assembly receipt is outside that package. These are different inventories.
Use the assembled package's unchanged README and `run.py` for a scientific
replay, which additionally requires the specified externally installed MiKTeX
Windows `pdftotext.exe` and installation dependencies. Neither installation nor
cross-platform scientific execution was tested here. An existing exact source
directory may instead be passed directly to `hydrate.py`.

## Exact transformation and failure conditions

The recorded organizer GET returned 83,506 bytes with SHA-256
`5e4aeb32be5cad70eb841ca555496a9c950b0e6d329b361c0bf05c9f81fbf3d4`.
Six bytes differed from the frozen HTML, all within its sole ten-digit CSS cache
parameter. The restorer requires the precise anchored stylesheet syntax and
zero-based span `[543,553)`, then restores that parameter to `1790154639`.
In the observed input the token was `1791724246`; changed offsets were
`546, 547, 548, 550, 551, 552`. No other byte is transformed.

The result must be 83,506 bytes with SHA-256
`f048152d2579be4d8fefa4c807221831233455de935d4ecb1b57f4a96e651fc8`.
The archive input is copied without transformation and must already be 410,492
bytes with SHA-256
`57c14d4055b28c52f0e644a5ff8a965a06c624d1a8987b79fe6b2be5074616ea`.
All these checks precede output creation. Other source changes, unexpected size
or syntax, an existing output directory, or any final digest mismatch cause
failure. Do not update the pins or substitute a semantically similar response.
Future source availability or reconstructibility is not guaranteed.

The organizer output is explicitly a **derived reconstruction**. It is not
represented as the bytes received in the new HTTP response. Its equality to a
retained earlier snapshot does not authenticate that snapshot's historical
acquisition, any historical execution, or the truth of the scientific claims.
The original strict hydrate continues to reject the unmodified drifted response.

## What was actually checked

- The [organizer GET receipt](evidence/source_recovery/organizer_GET_RECEIPT_V01.json), [archive GET receipt](evidence/source_recovery/archive_GET_RECEIPT_V01.json), and [retrieval summary](evidence/source_recovery/PROBE_SUMMARY_V01.json) record two actual one-shot requests. The organizer did not match its frozen digest; the archive did. This was source retrieval, not a scientific replay.
- The [offline execution record](evidence/source_recovery/EXECUTION_V01.json) records one completed local child with exit code zero. Its [restoration receipt](evidence/source_recovery/RESTORATION_RECEIPT_V01.json) binds the supplied response hashes, exact transformation and outputs. No network request was made by this restorer.
- The [independent byte check](evidence/source_recovery/INDEPENDENT_BYTE_CHECK_V01.json) compared both outputs byte for byte with the frozen scientific-package inputs and confirmed unchanged GET inputs. This check did not run the scientific code.
- The earlier [bootstrap acceptance](evidence/bootstrap/BOOTSTRAP_ACCEPTANCE_V01.json) records one exact local import that assembled all fourteen original files and one actual same-length drift rejection. The [failure receipt](evidence/bootstrap/DRIFT_REJECTION_RECEIPT_V01.json) is retained; its partial raw payload is not included.

**No hydrate run was performed on the newly restored directory.** Its compatibility
with the previously tested import is a composition of two observations: the
new outputs equal the same frozen input bytes, and the unchanged hydrate already
assembled those frozen inputs exactly. It is not described as a second observed
assembly or an integrated online-recovery run. No new scientific replay or sample
was added by retrieval, reconstruction, or assembly checks.

The unchanged [source notice](VALUEEVAL_PUBLIC_NOTICE_V02.md) records the preceding
source-rights review and direct-GET result; its warning about direct download
remains accurate. This later guide adds the disclosed offline transformation.
The five PDF attributions and source-specific notices remain intact. There is
no blanket project licence or permission conclusion for the two omitted bodies.
Metadata receipts retain inert historical machine paths and public identities;
they are not anonymous and are not signed attestations. Preparation work and
traffic are outside the unchanged 2,415,058-byte logical acquisition budget,
which still charges all seven raw scientific inputs during replay.
