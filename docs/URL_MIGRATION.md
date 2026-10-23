# Canonical URLs and preserved versions

[Project overview](../.github/README.md) · [Citation guidance](CITATION.md)

The repository was renamed from **`SHiJiE1115/newproj`** to **`SHiJiE1115/priced-equality-queries`** on 23 October 2026. This is a repository presentation change. Commit hashes, scientific file contents, release assets, and original execution identities are preserved.

Canonical repository: **https://github.com/SHiJiE1115/priced-equality-queries**

## Four fixed manuscript references

The following references keep their full commit and file/directory suffixes. New citations may use the canonical links. Existing manuscript links using `newproj` rely on GitHub's repository-rename redirects.

| Reference | Canonical target |
| --- | --- |
| Complete six-query delivery | [Delivery receipt, `57ed5b6`](https://github.com/SHiJiE1115/priced-equality-queries/blob/57ed5b69243fec06c2a7a58f062f3793f6557738/theory/complete_six/PUBLIC_DELIVERY_RECEIPT_V01.json) |
| Structural hosted evidence | [Original execution archive, `63eebe9`](https://github.com/SHiJiE1115/priced-equality-queries/tree/63eebe9d43d0f70d36f29331eee9f8ab9a130118/evidence/structural_depth_hosted_v01) |
| Fixed witness | [Source package, `389071e`](https://github.com/SHiJiE1115/priced-equality-queries/tree/389071e9a7b20800c8ce44bd2332e3996e4089c2/theory/fixed_depth_witness_v01) |
| Structural proof | [Source package, `ea1a091`](https://github.com/SHiJiE1115/priced-equality-queries/tree/ea1a0914cc642b2ca18787ee1342ab76b7654771/theory/structural_depth_v01) |

The old namespace must not be reused for a different repository: doing so would remove the redirect. Users maintaining a local clone can update its remote:

```console
git remote set-url origin https://github.com/SHiJiE1115/priced-equality-queries.git
```

## Historical execution identity

Old runs, signed metadata, and frozen runner code correctly record `SHiJiE1115/newproj`. Those identities are not replaced with the new name. Several historical hosted runners enforce the old repository identity, and the structural workflow also restricts its original tag event. Their original execution records remain valid within their stated scope; they are not general launchers for new runs under the renamed repository.

Use the compact packages' local commands for verification. A future hosted run needs a separately versioned runner and fresh receipts, not rewritten historical records.

## Redirect limits

[GitHub's repository-rename documentation](https://docs.github.com/en/repositories/creating-and-managing-repositories/renaming-a-repository) explains ordinary web and Git redirects and the exceptions for GitHub Pages project URLs and action references. This repository had neither a Pages project site nor a custom action at the time of this rename. The default branch remains `main`.

The new landing page lives in `.github/README.md`, which GitHub [displays ahead of a root README](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes). This leaves the historical root README and source freeze intact.
