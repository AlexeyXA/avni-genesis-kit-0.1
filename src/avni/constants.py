"""Shared constants for AVNI Genesis Kit."""

from __future__ import annotations

import re

GENOME_FILE = "genome.json"
ACCEPTANCE_FILE = "acceptance.json"
AVNI_DIR = ".avni"
LINEAGE_FILE = "lineage.jsonl"
INSTANCE_FILE = "instance.json"

MAX_PACKAGE_BYTES = 100 * 1024 * 1024
MAX_PACKAGE_FILES = 1000
DEFAULT_TIMEOUT_SECONDS = 5.0

DEFAULT_GITIGNORE = (
    ".avni/keys/private_key.pem\n"
    ".avni/reports/\n"
    "dist/\n"
    "__pycache__/\n"
    "*.py[cod]\n"
    ".venv/\n"
    "venv/\n"
)

SECRET_FILENAME_PARTS = (
    ".env",
    "id_rsa",
    "id_ed25519",
    "private_key",
    "credentials",
    "secrets.json",
)

SECRET_PATTERNS = [
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(rb"AKIA[0-9A-Z]{16}"),
    re.compile(rb"(?i)\bsk-[A-Za-z0-9_-]{20,}"),
    re.compile(
        rb"(?i)(?:api[_-]?key|client[_-]?secret|password|access[_-]?token)\s*[:=]\s*['\"][^'\"]{8,}['\"]"
    ),
]

RESERVED_PATH_PARTS = {".git", ".avni", ".venv", "venv", "dist", "__pycache__"}
