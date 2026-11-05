# AVNI Genesis Kit MVP Specification 0.1

## Product promise

Package a Python agent as an allowlisted, content-addressed artifact; restore it offline in a clean directory; run declared acceptance cases; and preserve a verifiable local lineage record.

## Core identities

- `genome_id`: SHA-256 of canonical JSON serialization of `genome.json` (without a trailing newline).
- `organism_id`: unique ID assigned to one instantiated member of a lineage.
- `package_id`: SHA-256 of canonical package identity data (genome digest, artifact metadata, lineage digest, source organism ID).
- `package_sha256`: SHA-256 of the actual ZIP bytes.

A replicate/restore has a new `organism_id`, retains `genome_id`, and points to the package source as `parent_organism_id`.

## Package layout

```text
avni-package.json
genome.json
artifacts/<allowlisted project paths>
history/lineage.jsonl
```

The package is a ZIP with sorted entries, fixed timestamps, fixed file modes, and no compression. It contains no `.avni/keys`, environment files, or non-allowlisted project files.

## Verification

Each acceptance case has a unique ID, JSON input and JSON expected output. Each case runs in a fresh subprocess with a timeout. The process environment is reduced but not sandboxed. Results are compared as parsed JSON values.

## Provenance

The local lineage journal is JSONL with monotonically increasing sequence numbers, previous-entry hashes, and entry hashes. Ed25519 signatures can be produced for verification reports. Neither feature alone constitutes trusted execution or remote immutable storage.

## Explicit exclusions

No code mutation, no autonomous self-improvement, no LLM behavior claims, no secret inheritance, no dependency installation during restore, and no claim of cross-platform hermetic builds.
