"""Optional Ed25519 signing helpers. Core AVNI commands do not require cryptography."""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
from typing import Any

from .errors import AvniError


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _crypto():
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        return serialization, Ed25519PrivateKey
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise AvniError("Ed25519 signing requires the optional dependency. Install with: pip install -e '.[signing]'") from exc


def generate_keypair(keys_dir: Path) -> tuple[Path, Path]:
    serialization, Ed25519PrivateKey = _crypto()
    keys_dir.mkdir(parents=True, exist_ok=True)
    private_path = keys_dir / "private_key.pem"
    public_path = keys_dir / "public_key.pem"
    if private_path.exists() or public_path.exists():
        raise AvniError(f"Key files already exist in {keys_dir}; refusing to overwrite them")
    key = Ed25519PrivateKey.generate()
    private_bytes = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_bytes = key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    private_path.write_bytes(private_bytes)
    public_path.write_bytes(public_bytes)
    try:
        private_path.chmod(0o600)
    except OSError:
        pass
    return private_path, public_path


def sign_report(report_path: Path, private_key_path: Path, signature_path: Path) -> dict[str, Any]:
    serialization, _ = _crypto()
    from cryptography.hazmat.primitives import hashes

    if not private_key_path.is_file():
        raise AvniError(f"Private signing key not found: {private_key_path}")
    report_bytes = report_path.read_bytes()
    try:
        private_key = serialization.load_pem_private_key(private_key_path.read_bytes(), password=None)
    except Exception as exc:
        raise AvniError(f"Cannot load private key: {exc}") from exc
    signature = private_key.sign(report_bytes)
    public_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    fingerprint = hashlib.sha256(public_bytes).hexdigest()
    record = {
        "format": "avni.signature",
        "format_version": "0.1",
        "algorithm": "Ed25519",
        "report_sha256": hashlib.sha256(report_bytes).hexdigest(),
        "public_key_pem": public_bytes.decode("ascii"),
        "public_key_fingerprint_sha256": fingerprint,
        "signature_base64": base64.b64encode(signature).decode("ascii"),
    }
    signature_path.write_bytes(canonical_json_bytes(record) + b"\n")
    return record


def verify_report_signature(report_path: Path, signature_path: Path) -> dict[str, Any]:
    serialization, _ = _crypto()
    import base64

    try:
        record = json.loads(signature_path.read_text(encoding="utf-8"))
        if record.get("format") != "avni.signature" or record.get("algorithm") != "Ed25519":
            raise AvniError("Unsupported signature format or algorithm")
        report_bytes = report_path.read_bytes()
        actual_hash = hashlib.sha256(report_bytes).hexdigest()
        if actual_hash != record.get("report_sha256"):
            raise AvniError("Report digest does not match the signed digest")
        public_bytes = record["public_key_pem"].encode("ascii")
        expected_fingerprint = hashlib.sha256(public_bytes).hexdigest()
        if expected_fingerprint != record.get("public_key_fingerprint_sha256"):
            raise AvniError("Public-key fingerprint mismatch")
        public_key = serialization.load_pem_public_key(public_bytes)
        signature = base64.b64decode(record["signature_base64"], validate=True)
        public_key.verify(signature, report_bytes)
    except AvniError:
        raise
    except Exception as exc:
        raise AvniError(f"Signature verification failed: {exc}") from exc
    return {
        "valid": True,
        "algorithm": "Ed25519",
        "report_sha256": actual_hash,
        "public_key_fingerprint_sha256": expected_fingerprint,
    }
