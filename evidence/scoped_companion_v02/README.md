# Scoped machine-evidence companion: public distribution edition

Read the [English scientific companion](SCOPED_EVIDENCE_COMPANION_EN.md),
[Chinese guide](README_ZH.md), and [evidence register](EVIDENCE_REGISTER_V02.json).
The numerical/scientific conclusions are inherited from the retained studies;
this distribution adds no scientific sample or method advantage.

## Packages and actual scope

| Package | Distribution and requirements | Retained validation |
|---|---|---|
| [Wine calibration ZIP](packages/wine_layer_calibration_v01.zip) | The original 25-file ZIP, byte-identical. Python 3.10+ standard library including sqlite3. | [Single relocated replay QA](evidence/iteration305/PACKAGE_ACCEPTANCE_V01.json) and [actual execution](evidence/iteration305/EXECUTION_V01.json). |
| [ValueEval source-bootstrap ZIP](packages/valueeval_bootstrap_v01.zip) | A new 16-file distribution, not the original full ZIP: 12 unchanged original files plus assembly code/docs/manifest. Two original response bodies must be supplied exactly. | [Exact local-import assembly QA](evidence/bootstrap/BOOTSTRAP_ACCEPTANCE_V01.json); the [earlier scientific replay QA](evidence/iteration304/PACKAGE_ACCEPTANCE_V01.json) used the original complete package. |

For Wine, extract the ZIP and follow its README. Its candidate and SQL baseline
each run once in separate processes; 30 semantic certificates are explicitly
rebound to the relative protocol using four changed digest fields. They are not
claimed to be byte-identical to their predecessors. Retained signature evidence
is parsed and bound, without new cryptographic verification or learning runs.

For ValueEval, follow [Source retrieval and offline reconstruction](SOURCE_RECOVERY.md),
then extract the bootstrap ZIP and use its unchanged `hydrate.py
--source-directory <reconstructed source directory> --output <new complete package>`
with Python 3.10+. A retained exact source directory also works. Assembly accepts
only the frozen length and SHA-256 for both missing objects, verifies the original
manifest, and produces the original exact 14-file package with a metadata receipt
outside it. It never runs the scientific replay. Download/import/integrity work
is preparation outside the declared seven-object logical acquisition budget.

**Direct download alone does not recover the frozen organizer snapshot.** The
actual archive-JSON response matched, while the organizer HTML differed in six
bytes of one ten-digit CSS cache parameter. The separate offline tool explicitly
restores that parameter; it requires the resulting full file to match the old
length and SHA-256, and otherwise fails. This is a declared derived reconstruction,
not an HTTP response claiming to be the old snapshot, historical authentication,
or permission to accept an arbitrary edited source. Future source changes can
make reconstruction fail. The original bootstrap remains strict and unchanged.
The [source notice](VALUEEVAL_PUBLIC_NOTICE_V02.md) is the preceding source-review
and direct-GET observation; [the later recovery record](SOURCE_RECOVERY.md) adds
the separate transformation and its actual validation. No integrated online
restoration script or new scientific replay is claimed.

The assembled ValueEval replay additionally requires an externally installed
MiKTeX Windows `pdftotext.exe` with SHA-256
`640b9a93fa31fc093860c635cd410a3e30f7d1e6166cb1130993fb1985f474ff`
and its external installation/DLL dependencies. Other extractors/platforms are
not validated. Earlier relocation was on the same Windows host with old paths
still OS-accessible; neither OS isolation nor cross-machine replay is asserted.

## Provenance, notices and limits

[PUBLIC_EDITION_MAP.json](PUBLIC_EDITION_MAP.json) maps the prior 55-file private
companion to this public derivative. Its [original manifest](provenance/PRIVATE_COMPANION_MANIFEST_V02.json)
is retained as provenance; the [new manifest](MANIFEST.json) binds this edition.
The old full ValueEval ZIP is omitted and remains private. Wine and all retained
evidence payloads are copied exactly. Changed entry text and software-delivery
mapping are explicitly derived, not presented as unchanged historical receipts.

[The new source notice](VALUEEVAL_PUBLIC_NOTICE_V02.md) gives the five unchanged
PDFs' authors, titles, DOIs and ACL CC BY 4.0 attribution. No blanket licence is
extended to the two omitted sources or the project. The [earlier source index](SOURCE_INDEX_V01.json)
and [retained notices](SOURCES_AND_NOTICES.md) describe the original complete
packages and remain historical records; consult this edition's map for what is
actually included now.

Historical receipts and metadata contain inert old machine paths and intentional
public repository/run identities. This is not an anonymized release, a complete
ancestral dependency closure, private author approval, human gold, scientific
ground truth, complete consumed-byte evidence, or authentication of the original
historical execution. Historical links inside exact copied records may still
refer to old workspaces. New entry links are relative.
