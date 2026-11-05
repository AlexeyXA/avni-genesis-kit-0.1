"""Command-line interface for AVNI Genesis Kit."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from . import __version__
from .constants import AVNI_DIR, LINEAGE_FILE
from .core import (
    build_package,
    init_project,
    project_status,
    read_lineage,
    restore_package,
    seal_project,
    validate_genome,
    verify_project,
)
from .errors import AvniError
from .signing import generate_keypair, sign_report, verify_report_signature


def _json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="avni",
        description="AVNI Genesis Kit — reproducible packaging and verification for Python agents.",
    )
    parser.add_argument("--version", action="version", version=f"avni {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init", help="create a minimal agent project")
    p.add_argument("name", help="human-readable agent name")
    p.add_argument("--path", type=Path, help="project directory (default: ./NAME)")

    p = sub.add_parser("validate", help="validate genome, artifacts and acceptance tests")
    p.add_argument("path", nargs="?", type=Path, default=Path("."))

    p = sub.add_parser("status", help="show organism identity, lineage tip and allowlist drift")
    p.add_argument("path", nargs="?", type=Path, default=Path("."))

    p = sub.add_parser("seal", help="rehash intentional changes and record a child revision")
    p.add_argument("path", nargs="?", type=Path, default=Path("."))
    p.add_argument("--note", help="short human-readable revision note")

    p = sub.add_parser("build", help="create a deterministic portable .avni.zip package")
    p.add_argument("path", nargs="?", type=Path, default=Path("."))
    p.add_argument("--output", type=Path)

    for command, description in (("replicate", "create a new child organism from a package"),
                                 ("restore", "restore a package in a clean directory")):
        p = sub.add_parser(command, help=description)
        p.add_argument("package", type=Path)
        p.add_argument("--dest", required=True, type=Path)

    p = sub.add_parser("verify", help="run acceptance tests and optionally compare with a parent")
    p.add_argument("path", nargs="?", type=Path, default=Path("."))
    p.add_argument("--against", type=Path, help="project directory to compare against")
    p.add_argument("--timeout", type=float, default=5.0, help="per-case subprocess timeout in seconds")
    p.add_argument("--sign", action="store_true", help="sign the report using .avni/keys/private_key.pem")

    p = sub.add_parser("lineage", help="verify and display the append-only hash chain")
    p.add_argument("path", nargs="?", type=Path, default=Path("."))

    p = sub.add_parser("keygen", help="create a local Ed25519 signing keypair")
    p.add_argument("path", nargs="?", type=Path, default=Path("."))

    p = sub.add_parser("verify-report", help="verify an Ed25519-signed verification report")
    p.add_argument("report", type=Path)
    p.add_argument("--signature", type=Path, help="signature JSON (default: REPORT.sig.json)")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            target = args.path if args.path is not None else Path(args.name)
            result = init_project(target, args.name)
            _json({"status": "created", **result})
            print("Next: cd into the project, then run `avni validate`, `avni verify`, and `avni build`.", file=sys.stderr)
            return 0

        if args.command == "validate":
            result = validate_genome(args.path)
            _json({"valid": True, "genome_id": result["genome_id"], "artifacts": result["artifacts"],
                   "acceptance_cases": result["acceptance_cases"]})
            return 0

        if args.command == "status":
            result = project_status(args.path)
            _json(result)
            return 1 if result.get("dirty") else 0

        if args.command == "seal":
            _json(seal_project(args.path, note=args.note))
            return 0

        if args.command == "build":
            _json(build_package(args.path, args.output))
            return 0

        if args.command in ("replicate", "restore"):
            result = restore_package(args.package, args.dest, event=args.command)
            _json(result)
            return 0

        if args.command == "verify":
            if args.timeout <= 0:
                raise AvniError("--timeout must be greater than zero")
            result = verify_project(args.path, against=args.against, timeout=args.timeout)
            signed = None
            if args.sign:
                report_path = Path(result["report"])
                private_key = report_path.parent.parent / "keys" / "private_key.pem"
                signature_path = report_path.with_suffix(report_path.suffix + ".sig.json")
                signature = sign_report(report_path, private_key, signature_path)
                signed = {"signature": str(signature_path), "public_key_fingerprint_sha256": signature["public_key_fingerprint_sha256"]}
            _json({k: v for k, v in result.items() if k not in ("report_data", "actual_by_id")} | {"signed": signed})
            return 0 if result["success"] else 1

        if args.command == "lineage":
            entries = read_lineage(args.path / AVNI_DIR / LINEAGE_FILE)
            _json({"valid": True, "entries": len(entries), "tip": entries[-1]["entry_hash"] if entries else None,
                   "history": entries})
            return 0

        if args.command == "keygen":
            private_path, public_path = generate_keypair(args.path / AVNI_DIR / "keys")
            _json({"created": True, "private_key": str(private_path), "public_key": str(public_path),
                   "warning": "Keep private_key.pem secret and backed up. Never include it in a package or commit it."})
            return 0

        if args.command == "verify-report":
            signature_path = args.signature or args.report.with_suffix(args.report.suffix + ".sig.json")
            _json(verify_report_signature(args.report, signature_path))
            return 0

        parser.error("unknown command")
    except AvniError as exc:
        print(f"AVNI ERROR: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130
    return 2
