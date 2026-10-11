# VPS3 offline evidence audit

Run from the repository root with Python 3.10+ (standard library only):

```sh
python3 -I -X utf8 -B evidence/vps3/run_offline.py --output-dir ci-results/vps3
```

Use a fresh output directory. The runner verifies the fixed ZIP digest,
extracts its checked members and executes the bundled verifier. No network,
LLM key, AiiDA or VASP installation is needed for this command.

Expected results: 12/12 raw parameter matches with native output and displayed
text, 48/48 exact raw energy/List-slot matches, and 0/12 matches with the separate
small JSON representation. Original small views are re-read from a digest-pinned
source ZIP. Missing historical provenance edges remain missing.

This tests retained bytes and typed ports, not historical execution or physical
truth. It does not establish an adaptive policy advantage. Wine execution and
the fixed-seven theory package remain separate studies. The complete six-query
internal candidate is not part of this delivery.

The extracted `README.md`, `SOURCE_NOTICE.md`, `provenance.json` and
`source_record_metadata.json` describe the fixed target, source attribution,
license scope and retained failures/cache costs. The original archive metadata
contains already-public user and computer fields; this is not an anonymized
archive. No local credentials are packaged.

ZIP SHA256: `eca3ee145c0299b002bc973cd8e43c2b07350e5ebd24e5212c4d353766ae05f3`.

Manifest SHA256: `23e1e9bdbe2d8a0674e1e624be353a22f983be6680d19d8218dcdea67340817f`.

This source commit supplies a manual-only workflow. Hosted results are recorded
separately after an actual run; this source guide alone does not claim CI success.
