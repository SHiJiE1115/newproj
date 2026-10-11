# ValueEval public bootstrap: sources and notices

## Public scope and preparation prerequisite

This notice accompanies the public ValueEval bootstrap. Its scientific-package skeleton contains the original 12 members remaining after the two common response bodies are omitted, including five unchanged ACL PDF files. The complete original ValueEval ZIP is retained privately. The bootstrap omits `sources/organizer_main.raw` and `sources/archive_evaluations.raw`; it records their official URLs, exact byte counts and SHA-256 values for strict download or local-file import. Supplemental bootstrap files have their own release manifest and do not replace the original scientific-package manifest.

The preparation step must restore both exact files and verify the original manifest before invoking the unchanged replay. A file of the right size with the wrong SHA-256 is insufficient. At the live check below, the organizer URL returned different bytes, so downloading both current URLs did **not** recover the frozen snapshot. Exact local import of the old organizer response, or another acquisition of those same pinned bytes, remains necessary. This bootstrap alone is not a demonstration of fully automatic public recovery of the frozen snapshot.

The following ACL licence facts apply to the five named papers. They do not license the entire research project, the two omitted sources, or unrelated third-party material. The separate Wine ZIP remains a complete package with its existing notices; Wine was not re-searched in this review.

## Five ACL papers

Each retained PDF carries the 2023 Association for Computational Linguistics copyright notice. Its official entry identifies an ACL publication from 2023. The [ACL copyright policy](https://aclanthology.org/faq/copyright/) and the five entry footers state that ACL materials from 2016 onward are available under [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/). That policy excludes third-party materials.

The five included PDFs retain their original copyright notices and are copied without modification. The attribution below supplies the authors, titles, official sources, DOIs and licence link. These references do not suggest endorsement.

- **Long Ma, Zeye Sun, Jiawei Jiang, Xuan Li (2023).** [PAI at SemEval-2023 Task 4: A General Multi-label Classification System with Class-balanced Loss Function and Ensemble Module](https://aclanthology.org/2023.semeval-1.34/). In *Proceedings of the 17th International Workshop on Semantic Evaluation (SemEval-2023)*, pp. 256-261. Association for Computational Linguistics. DOI: `10.18653/v1/2023.semeval-1.34`. Package file: `sources/paper_3.pdf`.

- **Ignacio Talavera Cepeda, Amalie Brogaard Pauli, Ira Assent (2023).** [Søren Kierkegaard at SemEval-2023 Task 4: Label-aware text classification using Natural Language Inference](https://aclanthology.org/2023.semeval-1.258/). In *Proceedings of the 17th International Workshop on Semantic Evaluation (SemEval-2023)*, pp. 1871-1877. Association for Computational Linguistics. DOI: `10.18653/v1/2023.semeval-1.258`. Package file: `sources/paper_13.pdf`.

- **Georgios Papadopoulos, Marko Kokol, Maria Dagioglou, Georgios Petasis (2023).** [Andronicus of Rhodes at SemEval-2023 Task 4: Transformer-Based Human Value Detection Using Four Different Neural Network Architectures](https://aclanthology.org/2023.semeval-1.75/). In *Proceedings of the 17th International Workshop on Semantic Evaluation (SemEval-2023)*, pp. 542-548. Association for Computational Linguistics. DOI: `10.18653/v1/2023.semeval-1.75`. Package file: `sources/paper_16.pdf`.

- **Ajay Narasimha Mopidevi, Hemanth Chenna (2023).** [Quintilian at SemEval-2023 Task 4: Grouped BERT for Multi-Label Classification](https://aclanthology.org/2023.semeval-1.222/). In *Proceedings of the 17th International Workshop on Semantic Evaluation (SemEval-2023)*, pp. 1609-1612. Association for Computational Linguistics. DOI: `10.18653/v1/2023.semeval-1.222`. Package file: `sources/paper_35.pdf`.

- **Abdul Jawad Mohammed, Sruthi Sundharram, Sanidhya Sharma (2023).** [Friedrich Nietzsche at SemEval-2023 Task 4: Detection of Human Values from Text Using Machine Learning](https://aclanthology.org/2023.semeval-1.302/). In *Proceedings of the 17th International Workshop on Semantic Evaluation (SemEval-2023)*, pp. 2179-2183. Association for Computational Linguistics. DOI: `10.18653/v1/2023.semeval-1.302`. Package file: `sources/paper_41.pdf`.

The retained PDF for the Kierkegaard paper supplies the spelling Søren and the fuller author name Amalie Brogaard Pauli; the current ACL metadata displays Sren and Amalie Pauli. This supplement preserves the PDF wording without editing either record.

## Organizer HTML and archived evaluation JSON

The retained organizer HTML contains a Webis copyright metadata notice and a link to the [Webis terms](https://webis.de/legal.html). No explicit redistribution licence for that complete HTML or the retained archive JSON was established in this bounded review. The JSON contains no licence/copyright/attribution notice fields found by the recorded scan. This absence does not establish that redistribution is prohibited.

The [official task page](https://touche.webis.de/semeval23/touche23-web/) provides result tables and a results download. The [TIRA organizer documentation](https://docs.tira.io/organizers/organizing-tasks.html) describes visibility of unblinded evaluations. Neither observation is used here as a licence for copying the entire retained response. The [TIRA terms page](https://www.tira.io/tos) expressly concerns the forum and is not treated as the archive API terms.

| Original package file | Bytes | SHA-256 | Official recorded source |
|---|---:|---|---|
| `sources/organizer_main.raw` | 83506 | `f048152d2579be4d8fefa4c807221831233455de935d4ecb1b57f4a96e651fc8` | [source](https://touche.webis.de/semeval23/touche23-web/) |
| `sources/archive_evaluations.raw` | 410492 | `57c14d4055b28c52f0e644a5ff8a965a06c624d1a8987b79fe6b2be5074616ea` | [source](https://archive.tira.io/api/evaluations/valueeval-at-semeval-2023-human-value-detection/arguments-test-20221205-test) |

The ACL licence statement is not extended to these two sources. Their omission reflects the absence of an established explicit redistribution grant in this bounded source review; it is not a finding that redistribution is prohibited.

## One-shot live retrieval check

Each official URL received one GET, with no automatic retry or redirect, a 30-second request timeout and a 2 MiB response cap. Both HTTP 200 bodies were fully received and retained only in the private probe archive. No PDF was downloaded. The complete response hashes were compared with the frozen values above.

| Source | GET start UTC | GET end UTC | HTTP | Bytes | Received SHA-256 | Result |
|---|---|---|---:|---:|---|---|
| `organizer` | 2026-10-11T19:48:21.501968+00:00 | 2026-10-11T19:48:22.693338+00:00 | 200 | 83506 | `5e4aeb32be5cad70eb841ca555496a9c950b0e6d329b361c0bf05c9f81fbf3d4` | MISMATCH: refuse this response for frozen replay |
| `archive` | 2026-10-11T19:48:22.708269+00:00 | 2026-10-11T19:48:23.889209+00:00 | 200 | 410492 | `57c14d4055b28c52f0e644a5ff8a965a06c624d1a8987b79fe6b2be5074616ea` | MATCH: exact frozen bytes |

The organizer response has the same length as the retained snapshot but a different digest. It must not be substituted, normalized or reserialized to make the check pass. The archive response matched at this check; future responses are not guaranteed to match. The preparation tool must fail closed on either mismatch and accept an exact local source file only after checking both length and SHA-256.

The original seven-file replay contract charges 2,415,058 payload bytes in total, including both common files. Omitting them from the public transfer does not make them free inputs for the scientific replay. Download/preparation traffic and timings are separate from that contract. This check performed source retrieval only, not a new scientific replay or a new result certification. It made no change to the original ZIP, payloads, protocol, parser, expected results or prior evidence.

Private audit receipts: `organizer_GET_RECEIPT_V01.json` (SHA-256 `0f14d2432ec22c228d6a33a3148fb1db5d9f3597f398dfa3aed59d9aae1c9701`) and `archive_GET_RECEIPT_V01.json` (SHA-256 `695c884f71d48fe57b6aae20162b5e6f41a423bbbd463684d868f696de897574`). These receipt names identify the retained private audit records; they are not represented as payloads included in the public scientific-package skeleton.

## Observation scope

Official source and licence pages were consulted using the web tool; that review completed at **2026-10-11 19:43:16 UTC**. Those observations may reflect indexed/cached pages and are not represented as origin-server timestamps. The live source GET times above are separately recorded by the retrieval process. No new PDF extraction was performed; the retained PDF copyright text and actual payload digests were checked against prior evidence.

This is an inventory of directly supported source and notice facts. It is not legal advice or a blanket permission guarantee.
