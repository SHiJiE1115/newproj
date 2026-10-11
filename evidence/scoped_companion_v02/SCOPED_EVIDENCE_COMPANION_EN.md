# Scoped machine evidence for academic claims

Two retrospective development studies examine what retained research materials can certify. The Wine study checks whether numerical outputs, selected read observations and retained signature evidence belong to the same prospective execution. The ValueEval study measures the whole-file budget required to connect five paper rows to organizer records. Both have successful scoped outputs, and both are matched by fixed methods given the same information. They supply reproducibility examples and boundaries for interpretation; they do not establish an application advantage for the query-policy theorems in the accompanying manuscript.

## Claims and evidence units

A certificate states a particular relation between identified materials. A reported-result certificate connects an exact paper row, dataset, metric and run identifier to organizer records. An artifact certificate checks retained output arithmetic and byte bindings. A prospective-execution certificate additionally needs evidence about an identified execution under a declared observation contract. Authenticating an original historical experiment is a stronger claim requiring evidence about that historical event.

These levels are not a score of scientific quality. Agreement among files does not establish scientific truth, and absence of sufficient evidence is recorded as unresolved rather than as a false claim. Repeated references to one execution identity count once. Distinct execution identifiers do not by themselves establish statistical independence.

## Wine study

### Materials and comparison

The materials are three retained packets from successive hosted attempts, denoted v07, v08 and v09. The last is GitHub run 38136338509, attempt 1. Each packet comprises a receipt archive and separately pinned verification records. The v07 archive has no result CSV or author summary. Where these outputs are present, in v08 and v09, this study re-extracts them, checks the 25 prescribed draws and seed sequence, recomputes the mean and population standard deviation, and checks the output hashes, parameters and nonce. It does not run the learning experiment again.

The joint execution key consists of repository, source commit, run identifier, attempt, protocol digest and archive digest. The numeric check also binds the CSV donor to the summary recipient. The chosen target is the reported Wine cell, 0.904 plus or minus 0.046 at three decimal places. These are selected development materials, and the target is not an independent blind prediction.

The candidate passes admitted facts into the existing rules engine and its certificate checker. A separate implementation extracts the same information and uses SQLite and hash joins. The checker validates the rules applied to the admitted facts; it does not independently authenticate the extractor. Selected read support and signature support in this calibration use retained verification evidence. Neither implementation performs fresh cryptographic signature verification or proves the full set of bytes consumed by the historical author experiment.

### Results

Here S means supported under the stated layer contract and U means unresolved.

| Scenario | Artifact arithmetic | Selected read support | Retained signature identity | Same-target joint support | Original 2020 execution | Distinct joint identities |
|---|---:|---:|---:|---:|---:|---:|
| v07 original | U | U | U | U | U | 0 |
| v08 original | S | U | U | U | U | 0 |
| v09 original | S | S | S | S | U | 1 |
| v08 target with v09 read and signature records | S | U | U | U | U | 0 |
| v09 target with v08 CSV | U | S | S | U | U | 0 |
| Duplicate reference to v09 | S | S | S | S | U | 1 |

The first three rows are real retained execution archives. The next two are constructed cross-archive controls; the last is a constructed duplicate-reference control. They are not six independent experiments. The two implementations agree on all 30 layer labels. In particular, v08 retains artifact-level support despite insufficient selected-read evidence. The two splices do not support the joint target, and a duplicate adds no new certified execution identity.

The accepted SQL implementation is V02. A code review of V01 identified an incomplete general donor-identity condition even though the existing mixed-output fixture already failed its digest check. V02 adds the full donor key and nonce derivation and uses the protocol's HALF_UP rounding. The old implementation and its receipts remain available as development history. No accuracy, sensitivity or natural error-rate estimate is inferred from the six selected scenarios.

The [Wine calibration record](evidence/history/RESEARCH_ITERATION_302_ZH.md) explains the controls. The [frozen delivery record](evidence/history/WINE_DELIVERY_VALIDATION_V01.json) identifies the accepted implementations, results and unchanged input hashes.

## ValueEval study

### Materials and acquisition contract

Five known-positive exact-ID cases were selected after the earlier 29-paper development audit. Each certificate connects an author's Main/All F1 row to the captured organizer leaderboard and a published valid archived evaluation of an uploaded prediction. The uploaded-prediction records do not certify the historical execution of the author's software.

The purchase menu consists of seven complete objects: the shared leaderboard HTML, the shared archive JSON and five author PDFs. Every allowed certificate requires both shared objects and its own PDF. Prices are their known retained byte lengths. This is an offline known-price contract; the prices were not shown to be available before the original network downloads.

The two shared objects cost 493,998 bytes. A fixed order acquires them once, then acquires PDFs in ascending byte length. Before each PDF, the budget is set to one byte below the next threshold to check that acquisition is denied before reading; the budget is then raised to the threshold. Each purchased PDF enters the text extractor through standard input using the already acquired bytes. Old extracted text and old certificates are excluded from the decision process and are compared only after the replay ends.

### Results and exact budget bound

| Certificate coverage | Minimum payload budget in bytes | Newly included leaderboard ordinal |
|---:|---:|---:|
| 1 | 637,064 | 35 |
| 2 | 920,962 | 16 |
| 3 | 1,214,497 | 41 |
| 4 | 1,721,954 | 3 |
| 5 | 2,415,058 | 13 |

The executed replay purchased seven objects once each, emitted five certificates and denied all five below-threshold reads without increasing the paid-byte counter. An independent metadata calculation over all 128 object subsets recovered the same coverage thresholds. The subsets are dependency calculations, not 128 acquisition experiments. The five extracted texts and full certificates match their frozen predecessors.

For any positive coverage k, every allowed set of k certificates requires the shared objects and k distinct PDFs. Its cost is at least 493,998 plus the sum of the k smallest PDF lengths. The fixed order attains this bound for every k. This is a simple dependency argument within this seven-object menu, not a lower bound over every possible semantic inference or proof system. Sharing the common sources was already present in the fixed verifier.

The original replay took 3.099386 seconds of local child-process wall time, using already present and previously read files. It is not a cold-cache or network benchmark. The budget counts logical source bytes in the replay; preparation, hashing during delivery, executable loading and post-run QA are separate work. The five cases retain their original post hoc selection from 29 and provide no general accuracy estimate.

The [budget calibration record](evidence/history/RESEARCH_ITERATION_303_ZH.md) gives the timing scope. The [frozen delivery record](evidence/history/VALUEEVAL_DELIVERY_VALIDATION_V01.json) binds the protocol, actual execution and independent QA.

## Relation to the theory manuscript

The [theory manuscript](evidence/theory/paper.tex) compares minimax classification under complete equivalence-partition promises. It specifies an equality-query menu and a purchased-set cost for both adaptive and global-order policies. The experiments here use complete files, execution identities and ordinary joins. Neither supplies the full possible-world promise or the native priced query contract required to transfer the seven-query separation to an academic workflow.

The Wine calibration tests evidence admission and joint identity, not acquisition-policy superiority. The ValueEval task has an exact fixed-order optimum under its declared dependencies. Its result cannot become a positive adaptivity result by splitting a shared file into artificially cheap row queries, withholding information from the fixed baseline, or counting cached data as free for only one method.

The examples therefore support a functioning scoped certification prototype and reproducible evidence handling. The theory contribution remains a separate query-model result. A further application claim would need an independently justified native action menu, complete relevant alternatives, actual costs and a comparison with strong methods receiving the same information. A lower burden applies to the narrower report and artifact certificates already demonstrated here.

## Reproduction scope

The [Wine package](packages/wine_layer_calibration_v01.zip) preserves its original ZIP bytes and its completed single local Windows relocation: the candidate and independent SQL baseline each exited zero once before old reference results were compared. Its relative protocol changes exactly four fields in each of the 30 semantic certificates (snapshot, scope, input and certificate digest); the rest of the candidate report is compared exactly. This is not byte-identical reuse of the old certificates. The SQL scientific output is preserved with declared administrative paths/resource-check and clock changes. [Wine acceptance](evidence/iteration305/PACKAGE_ACCEPTANCE_V01.json) records that execution.

The public [ValueEval bootstrap](packages/valueeval_bootstrap_v01.zip) is a new distribution edition, not the original complete ZIP. It retains twelve original members, including the unchanged parser, protocol, expected output and original manifest. It omits the organizer HTML and archive JSON; strict source download or exact local import must restore both before the original fourteen-file inventory can pass. The [local-import assembly check](evidence/bootstrap/BOOTSTRAP_ACCEPTANCE_V01.json) checks byte reconstruction only and does not rerun the scientific calibration. The [earlier ValueEval scientific acceptance](evidence/iteration304/PACKAGE_ACCEPTANCE_V01.json) belongs to the original complete ZIP. Its five certificates and all non-timing scientific fields remain the reference result.

At the recorded live check the archive JSON matched, but the organizer HTML returned a different digest: six bytes in one CSS cache parameter had changed. Direct download alone therefore does not reproduce the frozen snapshot. A later, separately executed [offline reconstruction](SOURCE_RECOVERY.md) restores that single parameter and requires the entire resulting file to match the original length and SHA-256. The scientific bootstrap remains unchanged and accepts only exact input bytes. This derived reconstruction is not a historical HTTP response or authentication of historical execution; future unrelated source changes cause failure. The [source notice](VALUEEVAL_PUBLIC_NOTICE_V02.md) is the preceding direct-GET observation and paper attribution. Retrieval, reconstruction and assembly are separately documented preparation outside the unchanged seven-object scientific budget; they do not make either source free for that contract. No integrated online-restoration execution or new scientific calibration is asserted.

Wine requires Python 3.10+ with sqlite3 in the standard library. ValueEval additionally requires the externally installed MiKTeX Windows PDF text extractor of SHA-256 `640b9a93fa31fc093860c635cd410a3e30f7d1e6166cb1130993fb1985f474ff`; its executable, DLLs and installation are not bundled. Other extractors and operating systems were not validated. Old workspaces remained OS-accessible during the earlier local relocation checks; no OS-isolation or cross-machine claim is made. Package distribution and reconstruction add no research sample, fresh learning run, fresh cryptographic verification or independent scientific replication.

New entry links are relative. Exact historical receipts retain inert absolute paths and public provenance identities; this companion is not anonymized and does not claim every historical dependency. The [edition map](PUBLIC_EDITION_MAP.json) records the changed distribution and entry text, while the new manifest covers the public edition. All study labels remain machine-derived under explicit contracts, not human gold. Source-specific notices are retained; no blanket project licence or author approval is asserted. The frozen theory and original research evidence remain unchanged.
