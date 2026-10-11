# VPS3 hosted offline audit

[Run 38140070343](https://github.com/SHiJiE1115/newproj/actions/runs/38140070343),
attempt 1, completed successfully on 2026-10-11. The executed source is
[`3f39c2055f81a18513871101d2bedcbb091ea812`](https://github.com/SHiJiE1115/newproj/tree/3f39c2055f81a18513871101d2bedcbb091ea812/evidence/vps3).
The later archive commit records that run; it is not claimed to be its source.

The [durable evidence directory](evidence/vps3/runs/38140070343-attempt1) retains the original Actions
ZIP, exact extracted result files, public run/job/artifact metadata and a file
manifest. The downloaded ZIP matches the API's SHA256 digest. These files remain
in Git after the temporary Actions artifact expires.

## Result

The Linux and relocated Windows verification JSONs are identical after removing
only start and finish timestamps: 12/12 parameters agree with native output and
printed text, 48/48 raw energies equal the stored List slots, and 0/12 parameters
agree with the separate small JSON representation. All 93 raw objects and 49
stored source nodes were checked. Original small views were parsed again from
the included fixed source ZIP. A local single-byte tampering control was rejected.

This is cross-platform reproducibility of a fixed current-artifact audit. It is
not a new VASP calculation, authentication of a historical parser conversion,
physical-truth judgment, human gold evaluation or an adaptive-policy benefit.
Missing CREATE edges remain missing; the reason for the small-JSON discrepancy
is unresolved. Earlier acquisition failures and cache costs are summarized in
the bundle's scoped provenance ledger.

## Reproduce

From the executed source checkout, using Python 3.10+ and a fresh output path:

```sh
python3 -I -X utf8 -B evidence/vps3/run_offline.py --output-dir ci-results/vps3
```

The script uses only the standard library, needs no key and downloads nothing.
See the [source guide](evidence/vps3/README.md) and the bundle's source notice for
attribution, license scope and the retained upstream public database metadata.
This repository also hosts the separate [Wine case](WINE_HOSTED_RUNS.md) and
fixed-seven theory study; VPS3 is not their theoretical or efficiency validation.
