# Changelog

## 0.1.1 — Usability and robustness

- Added `avni status` with allowlist drift detection (`dirty`, per-file modified/missing).
- `verify --against` now reports `differing_cases`, `only_in_current` and `only_in_baseline` instead of a boolean-only comparison.
- Baseline comparison no longer writes a recursive verification report for the parent project.
- Lineage append uses an advisory file lock and re-reads the chain under the lock (best-effort on platforms without `fcntl`).
- Revision notes from `seal --note` are stored on the lineage entry as well as in genome metadata.
- Extracted shared constants into `avni.constants`.

## 0.1.0 — MVP implementation

- Added GENOME 0.1 validation and artifact allowlisting.
- Added controlled `seal` operation for recording developer-approved revisions.
- Added deterministic ZIP packaging and SHA-256 sidecars.
- Added offline restore and replication with child organism identity.
- Added local hash-chained lineage journal.
- Added acceptance verification in a timed subprocess and parent comparison.
- Added optional Ed25519 report signing and signature verification.
- Added a deterministic example agent, automated tests and GitHub Actions workflow.

Known limitations are documented in `README_RU.md` and `SECURITY.md`.
