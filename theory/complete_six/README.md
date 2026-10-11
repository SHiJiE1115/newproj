# Complete six-query review archive: download and verify

Release location: [complete-six-review-20261011-v01](https://github.com/SHiJiE1115/newproj/releases/tag/complete-six-review-20261011-v01). This preparation record pins the intended assets; consult the public release and later delivery receipt for actual availability.

Download `complete_six_review_v01.zip` and `verify_download.py` from that release. The ZIP is 1,253,960,690 bytes; its SHA256 is:

```text
6d67d683e6b1df885df2c20f4157a11d7f71765ea219f06f9d32d4017b1693e8
```

Use Python 3.10+ to validate the compressed bytes and every member, optionally extracting into a directory that does not exist:

```console
python -I -X utf8 -B verify_download.py --archive complete_six_review_v01.zip --extract-to complete-six-review
```

Run from a directory with enough free space. The frozen inner candidate has 5,569 files and 1,491,310,855 file-content bytes, plus a small outer evidence layer. ZIP, extraction, filesystem overhead and any later replay outputs need separate space. Omitting `--extract-to` validates without writing extracted files. This is an integrity check; it does not execute or prove the mathematics. Preserve any failed attempt.

After extraction, read `README.md`, `SOURCE_NOTICE.md`, `REVIEWER_GUIDE.md`, `VERSION_MAP.json` and `execution_evidence/INDEX_V01.json`. The full mathematical commands and interpreter requirements are in the reviewer guide. The documented full-run command explicitly uses `--seconds 14400`; the wrapper default of 900 seconds is insufficient for the observed reference run. About 3.11 hours was observed for the older V03 bundle, not guaranteed for another machine or version.

The unchanged candidate retains its historical notices and V08 contract. Original V03 completed all four executable boundary layers; 5,534 scientific files are mapped to unchanged candidate content. The candidate itself completed inventory, plan and fixed-seven acceptance, without a fresh full aggregate run. The 112,971 analytically reduced cases remain written obligations; machine checking covered 2,747,725 explicit cases. Exact and derived public execution records are separately labelled.

Publication authorization is current. No blanket project licence is selected here. Human author review and final declarations remain pending. This deposit is not a formal submission, historical-authenticity certification or proof of practical academic-evaluation advantage. The standalone source in the correspondence evidence is journal V02; its two mathematical blocks are unchanged from bound V08, while presentation and case material differ.
