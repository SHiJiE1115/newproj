# Prospective Wine execution: actual hosted evidence

The v09 run completed 25 fixed author-code draws, reproducing a test-accuracy mean of **0.904** and population standard deviation **0.04606811918168868** (three decimals: **0.904 ± 0.046**). Both hosted jobs succeeded. The same raw tar passed the candidate verifier and an independently implemented fixed baseline; its GitHub artifact signature was verified against the source commit, workflow, branch, run and attempt. The downloaded signature bundle was then retained and verified again.

| Revision | Actual run | Result |
|---|---|---|
| v07 | [38135533716](https://github.com/SHiJiE1115/newproj/actions/runs/38135533716) | Failed before author startup: strace 6.8 rejected numeric colon-form username. |
| v08 | [38136079298](https://github.com/SHiJiE1115/newproj/actions/runs/38136079298) | Author computation and isolation passed; read-path observation gate failed. No verified release. |
| v09 | [38136338509](https://github.com/SHiJiE1115/newproj/actions/runs/38136338509) | Both jobs, same-receipt local verifiers and cryptographic release gate passed. |

The [earlier failed run 36583899749](https://github.com/SHiJiE1115/newproj/actions/runs/36583899749) also remains failed history. v08 explicitly dropped author privileges using setpriv. v09 added DAC_READ_SEARCH to the root observer so it could resolve file-descriptor paths across the UID boundary; the author still had effective capabilities zero, empty supplementary groups, denied observer write/rename canaries, and no inherited observer descriptor. No scientific input, seed, author algorithm or target statistic was changed to obtain acceptance.

## Exact identity and scope

- Executed source: `6f64dd2a7dd75ee14ca65d2e00c4e0a5ea0d131b`, branch `trace-isolation-v09-fd-observation`, workflow `.github/workflows/rrnc-wine-strace.yml`, attempt `1`.
- Raw receipt tar SHA-256: `4ca929880eaa9a7e5b7f13e7b00c3b7dbe1dea025acb97d36ec046e08b2a9ebc`.
- Provider artifact ZIP SHA-256: `5d5a651b13275bf32ed9b09636b918895866c15a357ef6dc8f075423a4908f3e`.
- [Archived raw artifacts and API observations](archive/wine/20261011) include the two failures. They preserve exact downloaded bytes beyond Actions artifact expiry. The provider snapshots are unsigned observations; the retained bundle supplies the cryptographic provenance evidence.
- This is one **new prospective selected-syscall and numerical-output observation**, not authentication of the original 2020 execution, a complete consumed-byte set, independent scientific truth or human gold. The fixed baseline also passes; **no method advantage is established**. The Wine target/prior was already known, so this is not a blind scientific validation. P1 stays sealed.
- The archive commit is later than the executed source commit and is not claimed to have been executed by this run. The theoretical seven-query package is unchanged.

## Recheck

Run the commands below from the public archive repository root. `SOURCE_CHECKOUT` denotes a separate checkout at the executed source commit above; `WORKDIR` denotes a separate working directory containing the unzipped `archive/wine/20261011/v09/artifact.zip`. Replace both placeholders with your actual directory paths and quote paths containing spaces. Use Python 3.10+ and GitHub CLI with attestation support.

```sh
python SOURCE_CHECKOUT/experiment/verify_receipt.py WORKDIR/receipt.tar WORKDIR/candidate.json SHiJiE1115/newproj 6f64dd2a7dd75ee14ca65d2e00c4e0a5ea0d131b 38136338509 1
python archive/wine/20261011/v09/direct_fixed_baseline.py SOURCE_CHECKOUT WORKDIR/receipt.tar WORKDIR/baseline.json SHiJiE1115/newproj 6f64dd2a7dd75ee14ca65d2e00c4e0a5ea0d131b 38136338509 1
gh attestation verify WORKDIR/receipt.tar --bundle archive/wine/20261011/v09/bundle.jsonl --repo SHiJiE1115/newproj --signer-workflow SHiJiE1115/newproj/.github/workflows/rrnc-wine-strace.yml --source-digest 6f64dd2a7dd75ee14ca65d2e00c4e0a5ea0d131b --source-ref refs/heads/trace-isolation-v09-fd-observation --deny-self-hosted-runners --format json
```

Also require the verified certificate's `runInvocationURI` to equal `https://github.com/SHiJiE1115/newproj/actions/runs/38136338509/attempts/1`. The local release gate checked this exact binding and verified timestamps. Signature checking may access trust metadata; no fully offline verification is claimed. Both receipt verifiers return only selected-syscall scope and do not substitute for signature or provider-job checks. The baseline's legacy schema string says v06; the published source and frozen hashes bind the v09 contract.

The public author ZIP retains its MIT license. Wine is [UCI Wine](https://archive.ics.uci.edu/dataset/109/wine), DOI 10.24432/C5PC7J, attributed to Aeberhard and Forina, under UCI's CC BY 4.0. These upstream terms do not license unrelated project material.
