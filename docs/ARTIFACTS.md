# Artifact and theorem map

[Project overview](../.github/README.md) · [Reproduction](REPRODUCING.md)

The manuscript *Exact Adaptivity Thresholds for Priced Equality Queries under Complete Equivalence Promises* uses several distinct proof components. This page identifies their roles without changing the underlying artifacts.

| Mathematical obligation | Public material | What must be read or checked |
| --- | --- | --- |
| Priority replacement for strategies of purchase depth at most three | [Structural package](https://github.com/SHiJiE1115/priced-equality-queries/tree/ea1a0914cc642b2ca18787ee1342ab76b7654771/theory/structural_depth_v01) | The R and C4 finite premises, plus the written normalization, coverage, encoding, and gluing arguments |
| A depth-four separating strategy on a complete seven-query source | [Fixed-example package](https://github.com/SHiJiE1115/priced-equality-queries/tree/389071e9a7b20800c8ce44bd2332e3996e4089c2/theory/fixed_depth_witness_v01) | Exact source realization, direct minimax and integer-budget checks, and the written order-obstruction proof |
| No separation on complete sources with at most six queries | [Complete-menu release](https://github.com/SHiJiE1115/priced-equality-queries/releases/tag/complete-six-review-20261011-v01) | Complete source catalogue, five-query foundation B5, explicit six-query certificates, and stated analytic reductions |
| Public hosted reproduction of R and C4 | [Original hosted evidence](https://github.com/SHiJiE1115/priced-equality-queries/tree/63eebe9d43d0f70d36f29331eee9f8ab9a130118/evidence/structural_depth_hosted_v01) | Executed source identity, original service artifact, complete outputs, and verification scope |

## Exact finite counts

| Component | Recorded coverage |
| --- | --- |
| Five-query foundation B5 | 9,439 supports, 34,601 pair orbits, 54,021 witnesses |
| Explicit six-query layer | 2,747,725 pair orbits, 4,074,031 priority witnesses |
| Structural depth premises | 64 R formulas and 64 C4 formulas |
| Fixed separating examples | 5,064 orders across two controls; 4,140 legal quotient partitions for the complete seven-query source |

These are finite mathematical objects, not empirical paper samples or LLM evaluation examples. The counts supplement the coverage arguments and do not replace them.

## Scope of the public materials

The model uses deterministic zero-error policies, complete equivalence promises with unrestricted class count, and worst-case normalized nonnegative monotone purchased-set fees. A priority policy may permanently skip queries based on observed answers. The structural extension uses the stated AND-closure and full-support singleton-exchange assumptions.

The current manuscript's additional revision-local receipts and implementation-map supplement are not newly deposited by this navigation update. The fixed public packages listed above remain the versions cited in the manuscript. Earlier manuscript PDFs elsewhere in this repository are historical versions, as described in the [archive guide](ARCHIVE.md).

No general application superiority, human-gold evaluation, proof-assistant formalization, or journal acceptance is asserted by this artifact collection.
