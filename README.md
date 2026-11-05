# AVNI Genesis Kit 0.1

**Verified Agent Handoff** — a small, local-first CLI for packaging, restoring, verifying and tracking the lineage of Python AI agents.

This is an experimental MVP. It does **not** claim autonomous self-improvement, safe execution of untrusted code, bit-for-bit reproducibility across arbitrary platforms, or equivalence of arbitrary LLM outputs.

## What it does

- Describes a Python agent using `genome.json` (`avni.genome` 0.1).
- Validates explicitly allowlisted artifacts and their SHA-256 hashes.
- Rejects common credential-bearing filenames and several high-confidence secret patterns.
- Builds a deterministic ZIP package containing the genome, allowlisted files, package manifest and lineage history.
- Restores or replicates a package into a new directory and assigns a child `organism_id` while retaining the same `genome_id`.
- Runs fixed acceptance cases in a separate Python process with a timeout and a reduced environment.
- Compares behavior against a parent project for the included test cases.
- Maintains a local hash-chained lineage journal.
- Optionally signs verification reports with Ed25519 (`cryptography` extra).
- **`avni status`** reports organism identity and allowlist drift without running tests.

## Requirements

- Python 3.11+
- No mandatory third-party runtime dependencies.
- Optional report signing: `cryptography`.

## Install from source

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
python -m pip install -e ".[signing,dev]"
```

For core functionality only, use `python -m pip install -e .`.

## 10-minute walkthrough

```bash
avni init hello-agent
cd hello-agent
avni validate
avni status
avni verify
avni build
avni restore dist/hello-agent-0.1.0.avni.zip --dest ../hello-agent-restored
cd ../hello-agent-restored
avni verify --against ../hello-agent
avni lineage
```

`replicate` and `restore` both create a new child organism from the package. The event name in lineage differs. A restored child has a new `organism_id`, the same `genome_id`, and a parent link to the package's source organism.

### Sign a report

```bash
# From the project directory
avni keygen
avni verify --sign
# Copy the exact report path printed by the command above:
avni verify-report .avni/reports/verification-<timestamp>-<id>.json
```

Replace the placeholder with the exact report filename printed by `avni verify --sign`. The private key is written to `.avni/keys/private_key.pem`; `.gitignore` excludes it. Back it up securely. The signature record embeds the public key, allowing integrity verification, but that alone does not establish a trusted identity. Distribute the expected public-key fingerprint through a separate trusted channel when identity matters.

## Project layout

```text
hello-agent/
├── genome.json
├── acceptance.json
├── agent/
│   └── agent.py
├── .avni/
│   ├── instance.json
│   ├── lineage.jsonl
│   ├── keys/                 # generated locally; private key is ignored by Git
│   └── reports/              # generated verification reports
└── dist/                     # generated portable package
```

## Genome contract

`genome.json` has the following required top-level fields:

- `format`: `avni.genome`
- `format_version`: `0.1`
- `organism`: `name`, `version`
- `runtime`: `language: python`, `python`, `entrypoint: path.py:run`
- `artifacts`: explicit allowlist of `path`, `sha256`, and optional `role`
- `interface`: JSON input/output declaration
- `secrets`: `required_env` names and `package_values: false`

The artifact list is an allowlist: files not named there are not included in the package. After intentionally changing an allowlisted file, run `avni seal --note "what changed"`. It recalculates artifact hashes and records a new child organism revision. `avni validate` detects unsealed drift. `seal` is a developer-approved revision operation; it is not autonomous AI mutation.

## Commands

```text
avni init NAME [--path DIR]
avni validate [DIR]
avni status [DIR]
avni seal [DIR] [--note TEXT]
avni build [DIR] [--output FILE]
avni replicate PACKAGE --dest DIR
avni restore PACKAGE --dest DIR
avni verify [DIR] [--against PARENT_DIR] [--timeout SECONDS] [--sign]
avni lineage [DIR]
avni keygen [DIR]
avni verify-report REPORT [--signature FILE]
```

## Security model and limitations

- **Not a sandbox:** the verifier runs the agent in a subprocess with a timeout and a reduced environment. The agent still runs with the current user's OS permissions and may access the network. Only verify code you trust. Do not use this MVP to execute third-party packages.
- **Secret scanning is heuristic:** allowlisting and common-pattern scanning reduce accidental leakage; they do not guarantee that all secrets are detected. Review packages before sharing.
- **Hash chains are tamper-evident, not tamper-proof:** someone with write access to the entire journal can rewrite it and recompute hashes. Use signed reports and externally stored checkpoints for stronger auditability.
- **Ed25519 report signatures:** prove that a report has not changed relative to the embedded public key. They do not prove who controlled the private key or whether the execution environment was trustworthy.
- **Behavioral checks are bounded:** `verify` establishes expected outputs only for the acceptance cases shipped with the genome. It does not prove general equivalence or LLM quality.

See `docs/SPECIFICATION.md`, `docs/PRODUCT_POSITIONING.md`, and `SECURITY.md` for details.
