# Priced Equality Queries

## Exact Adaptivity Thresholds for Priced Equality Queries under Complete Equivalence Promises

Computational proof artifacts, exact verification programs, and reproduction records for the study of adaptive and globally ordered equality-query strategies.

**[Reproduce the results](../docs/REPRODUCING.md)** · **[Artifact and theorem map](../docs/ARTIFACTS.md)** · **[Cite the artifacts](../docs/CITATION.md)** · **[Historical studies](../docs/ARCHIVE.md)**

### Research overview

When observations have a cost, can choosing the next query from previous answers save more than fixing a global order in advance? This project studies deterministic, zero-error classification between two complete equivalence promises. A query asks whether two records belong to the same equivalence class. The comparison permits a fixed-order strategy to skip queries using the answers already observed.

The manuscript establishes two sharp thresholds under this model:

| Resource | Replacement result | First separating example |
| --- | --- | --- |
| **Purchase depth** | Every correct adaptive strategy buying at most three queries per input admits one priority replacement that is no more costly for every normalized nonnegative monotone set fee. | A depth-four adaptive strategy separates on a complete seven-query instance. |
| **Available queries** | On complete sources with at most six queries, adaptive and priority optimum worst-case costs agree for every such fee. | Seven queries suffice for a strict cost advantage with positive additive prices. |

For the fixed separating instance, the adaptive cost is **9/2**, while every priority strategy costs at least **5**. The structural depth result also extends to the stated class of disjoint AND-closed supports with full-support singleton exchange. See the manuscript for the definitions, written reductions, and theorem scope.

### Main artifacts

| Package | Contents | Start here |
| --- | --- | --- |
| **Structural depth-three proof** | R64 and C4 propositional certificates, independent proof-checking programs, and written reductions. | [Pinned package](https://github.com/SHiJiE1115/priced-equality-queries/tree/ea1a0914cc642b2ca18787ee1342ab76b7654771/theory/structural_depth_v01) · [Recorded Linux execution](https://github.com/SHiJiE1115/priced-equality-queries/tree/63eebe9d43d0f70d36f29331eee9f8ab9a130118/evidence/structural_depth_hosted_v01) |
| **Fixed separating examples** | The seven-query complete source and a separate Horn control; direct minimax and independently implemented integer-budget checks. | [Pinned package](https://github.com/SHiJiE1115/priced-equality-queries/tree/389071e9a7b20800c8ce44bd2332e3996e4089c2/theory/fixed_depth_witness_v01) |
| **Complete six-query boundary** | Complete support catalogue, five-query foundation, six-query certificates, and version-specific execution records. **Archive: 1.25 GB.** | [Download release](https://github.com/SHiJiE1115/priced-equality-queries/releases/tag/complete-six-review-20261011-v01) · [Pinned delivery record](https://github.com/SHiJiE1115/priced-equality-queries/blob/57ed5b69243fec06c2a7a58f062f3793f6557738/theory/complete_six/PUBLIC_DELIVERY_RECEIPT_V01.json) |

### Reproduction

Start with the two compact packages. Both use **Python 3.10 or later and the standard library**; neither requires an LLM API or a paid service. Each archive must be extracted into a fresh directory. The [reproduction guide](../docs/REPRODUCING.md) gives download links, commands, expected results, and the distinction between verification and a new execution.

The large boundary archive has additional storage and runtime requirements. It is a separate proof dependency, not a prerequisite for running the compact structural or fixed-instance checks.

### Reading the evidence

- Exact finite verification and the written mathematical reductions jointly support the results. The complete proof has not been formalized in a proof assistant.
- Fixed-example checks do not prove the universal depth-three or six-query assertions. Each package has a separate obligation and execution history.
- Older application studies, including negative model-comparison results, are retained in the [historical archive guide](../docs/ARCHIVE.md). They do not establish an advantage in practical academic evaluation.
- Earlier public manuscript versions are historical reading copies. This repository update does not publish the current manuscript or imply journal submission or acceptance.

### Versions, citation, and reuse

The canonical repository is **`SHiJiE1115/priced-equality-queries`**, formerly `SHiJiE1115/newproj`. Existing commit hashes, scientific files, releases, and original execution identities are preserved. See the [URL and version note](../docs/URL_MIGRATION.md) for the four fixed manuscript references and historical workflow compatibility.

Use a fixed commit or release when citing an artifact; the default branch is an evolving navigation layer. [Citation guidance](../docs/CITATION.md) is provided separately from manuscript attribution.

Component-specific source and distribution notices remain applicable. No repository-wide license is added by this documentation update. For a reproducibility issue, [open an issue](https://github.com/SHiJiE1115/priced-equality-queries/issues) with the package version, Python version, command, and observed result, omitting credentials and personal machine information.
