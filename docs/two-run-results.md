# Two-Run Results

## Run 1 — Initial comparison

The first monitoring run checked all five companies:

- Norsk Hydro
- Constellium
- Alcoa
- Ma'aden
- Rio Tinto

The process discovered and stored official publication pages and their content hashes in the local database.

The first run established the baseline used for future comparisons.

## Run 2 — Later comparison

The monitoring process was run again after the baseline had been stored.

Results:

| Company | Status | New | Updated |
|---|---|---:|---:|
| Norsk Hydro | OK | 0 | 0 |
| Constellium | OK | 0 | 0 |
| Alcoa | OK | 0 | 0 |
| Ma'aden | OK | 0 | 0 |
| Rio Tinto | OK | 0 | 0 |

The daily report stated:

> No new or meaningfully changed publications.

All five website checks completed successfully.

## How the process decided what changed

For each discovered publication, the monitor:

1. Creates a normalized key from the publication title.
2. Checks whether the publication already exists in the local database.
3. Downloads the current publication content.
4. Creates a SHA-256 hash of the content.
5. Compares the current hash with the previously saved version.
6. Reports the publication as `NEW` if it has not been seen before.
7. Reports it as `UPDATED` if the content or source URL has changed.
8. Treats unchanged publications as `SEEN` and does not report them as changes.
9. Saves the latest version so it can be compared during the next daily run.

This allows the second run to distinguish between genuinely new or changed publications and pages that have remained unchanged.