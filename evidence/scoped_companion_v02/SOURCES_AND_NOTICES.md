# Sources and retained notices

This is a separately delivered source index for the Wine and ValueEval reviewer companion. It does not change either ZIP and is not asserted to be an original member of either ZIP. All observations below come from retained local bytes and records; no network request or experiment was performed to prepare this index.

## ValueEval: seven retained original payloads

The relative paths below are interpreted inside the extracted `valueeval_budget_v01` package. Each payload was checked against its retained GET receipt, protocol pin, and actual ZIP member. The JSON index also gives the receipt byte count and SHA-256.

| Package-relative file | Bytes | SHA-256 | Retained final source URL |
|---|---:|---|---|
| `sources/organizer_main.raw` | 83506 | `f048152d2579be4d8fefa4c807221831233455de935d4ecb1b57f4a96e651fc8` | [source](https://touche.webis.de/semeval23/touche23-web/) |
| `sources/archive_evaluations.raw` | 410492 | `57c14d4055b28c52f0e644a5ff8a965a06c624d1a8987b79fe6b2be5074616ea` | [source](https://archive.tira.io/api/evaluations/valueeval-at-semeval-2023-human-value-detection/arguments-test-20221205-test) |
| `sources/paper_3.pdf` | 507457 | `e7bbfaeceb1b1f8b4b3405130ed947eb60b368fc59552167bef5e91fbf34bdfb` | [source](https://aclanthology.org/2023.semeval-1.34.pdf) |
| `sources/paper_13.pdf` | 693104 | `71e13b29f83eec1af659670370d8ccf6ca7d7d9cd041f35b5b9dfe0a586fc8d1` | [source](https://aclanthology.org/2023.semeval-1.258.pdf) |
| `sources/paper_16.pdf` | 283898 | `854b19cd82e0bb159df13833cb5213cb7c33342dca28b24468a03fd159446a29` | [source](https://aclanthology.org/2023.semeval-1.75.pdf) |
| `sources/paper_35.pdf` | 143066 | `2024c639c24de7bf285cbdec14de4e6dfef4c071e68b21480b3e02a26fa3ccce` | [source](https://aclanthology.org/2023.semeval-1.222.pdf) |
| `sources/paper_41.pdf` | 293535 | `f63bfb85abc690d1a1bfdf5b9a7e5e95f74b26567969bfc8257046a10e783375` | [source](https://aclanthology.org/2023.semeval-1.302.pdf) |

Total retained payload: **2,415,058 bytes**. These are the seven bodies used for the five post hoc exact-ID examples, not seven new downloads. GET receipts establish the saved response and URL bindings, not a general redistribution grant. Original PDF, HTML and JSON contents and their source-specific notices have not been edited.

## Wine: embedded upstream materials

The same pinned author ZIP and Wine input are present in all three exact receipt archives:
- `evidence/v07/receipt.tar`: author ZIP at `inputs/author.zip`; Wine bytes at `inputs/wine.raw`.
- `evidence/v08/receipt.tar`: author ZIP at `inputs/author.zip`; Wine bytes at `inputs/wine.raw`.
- `evidence/v09/receipt.tar`: author ZIP at `inputs/author.zip`; Wine bytes at `inputs/wine.raw`.

### Author code

- Retained source: [author ZIP at pinned commit](https://codeload.github.com/jsleb333/paper-decision-trees-as-partitioning-machines/zip/0f354dac486a9845a9504419e31c84c7eb39507f).
- Bytes: 95119; SHA-256: `1e20fd01e194bc974a64c92130d3cee3367abe5351aaf4d9f1953009620650db`.
- Internal notice member: `paper-decision-trees-as-partitioning-machines-0f354dac486a9845a9504419e31c84c7eb39507f/LICENSE`.
- Actually read notice: **MIT License**, **Copyright (c) 2020 Jean-Samuel Leboeuf**.
- Notice bytes: 1076; SHA-256: `cf58267874c44327801c74e02a6fd7a861b5c9bb37ac077fc22089dd8d17d7e1`.
- The original full notice remains inside the unchanged nested ZIP. This index does not apply that notice to unrelated project files.

### Wine input and existing attribution

- Retained input URL: [wine.data](https://archive.ics.uci.edu/ml/machine-learning-databases/wine/wine.data).
- Bytes: 10782; SHA-256: `6be6b1203f3d51df0b553a70e57b8a723cd405683958204f96d23d7cd6aea659`.
- Existing public guide: [WINE_HOSTED_RUNS.md at ae2ba2d](https://github.com/SHiJiE1115/newproj/blob/ae2ba2d6bd62dd7e7152f519d49569b91d235a1d/WINE_HOSTED_RUNS.md).
- That retained guide attributes UCI Wine to Aeberhard and Forina, gives DOI **10.24432/C5PC7J**, and records **CC BY 4.0** as the UCI source notice. This is a transcription of the existing notice, not a fresh check of current terms.
- Source landing link recorded in that guide: [UCI Wine](https://archive.ics.uci.edu/dataset/109/wine).
- Guide bytes: 4648; SHA-256: `a93e3bac5b7232dce1af2c5650725656d413443437cedd2b442236f0186d6c6f`. Its locally retained publication acceptance binds these exact bytes to the fixed commit; no present-day network retrieval was performed.

## Historical paths and reviewer scope

The executable protocols use relative package paths. The Wine package deliberately retains old absolute paths in historical reports and complete old result references; it is **not anonymized**. Known text fields include:
- `Wine references/BASELINE_RESULT_V02.json`: `protocol.path`, `guard.path`, `script.path`, `original_input_bindings[0..16].path`.
- `Wine evidence/{v07,v08,v09}/POSTRUN_RELEASE_GATE.json`: `candidate_report_path`, `direct_baseline_report_path`.
- `Wine evidence/v07/CANDIDATE_REPORT.json`: `receipt_audit.error_code (embedded historical local path)`.

The JSON source index also retains local receipt and guard paths for audit; its `reviewer_mapping` and the tables above use only package-relative paths and source URLs. Public repository/account, commit and run identifiers remain intentional provenance. A separately derived presentation may replace historical local path text while preserving a binding to the original; such a presentation must not be called byte-identical to the original receipt.

Neither index establishes a whole-project licence, ownership grant, historical experiment authenticity, source independence, human gold, or a new scientific result. The ValueEval replay still requires the externally installed, digest-pinned MiKTeX Windows PDF extractor described in its package README; this index does not bundle that dependency.
