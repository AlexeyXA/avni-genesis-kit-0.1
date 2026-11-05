from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from avni.constants import AVNI_DIR, LINEAGE_FILE
from avni.core import (
    build_package,
    detect_artifact_drift,
    init_project,
    project_status,
    read_json,
    read_lineage,
    restore_package,
    seal_project,
    sha256_file,
    validate_genome,
    verify_project,
    write_json,
)
from avni.errors import AvniError
from avni.signing import generate_keypair, sign_report, verify_report_signature


def make_project(tmp_path: Path, name: str = "test-agent") -> Path:
    root = tmp_path / name
    init_project(root, name)
    return root


def test_init_validate_and_acceptance(tmp_path: Path):
    root = make_project(tmp_path)
    result = validate_genome(root)
    assert result["genome_id"]
    assert result["acceptance_cases"] == 3
    assert (root / ".avni" / "instance.json").is_file()
    assert len(read_lineage(root / AVNI_DIR / LINEAGE_FILE)) == 1


def test_build_is_byte_for_byte_deterministic(tmp_path: Path):
    root = make_project(tmp_path)
    first = tmp_path / "first.avni.zip"
    second = tmp_path / "second.avni.zip"
    one = build_package(root, first)
    two = build_package(root, second)
    assert one["package_id"] == two["package_id"]
    assert one["package_sha256"] == two["package_sha256"]
    assert first.read_bytes() == second.read_bytes()


def test_restore_creates_child_with_same_genome_and_valid_lineage(tmp_path: Path):
    root = make_project(tmp_path)
    package = tmp_path / "agent.avni.zip"
    build_package(root, package)
    restored = tmp_path / "restored-agent"
    result = restore_package(package, restored)
    source_instance = read_json(root / AVNI_DIR / "instance.json")
    child_instance = read_json(restored / AVNI_DIR / "instance.json")
    assert result["genome_id"] == validate_genome(root)["genome_id"]
    assert child_instance["genome_id"] == source_instance["genome_id"]
    assert child_instance["organism_id"] != source_instance["organism_id"]
    assert child_instance["parent_organism_id"] == source_instance["organism_id"]
    assert ".avni/keys/private_key.pem" in (restored / ".gitignore").read_text(encoding="utf-8")
    entries = read_lineage(restored / AVNI_DIR / LINEAGE_FILE)
    assert len(entries) == 2
    assert entries[-1]["event"] == "restore"
    assert entries[-1]["organism_id"] == child_instance["organism_id"]


def test_seal_records_a_new_child_revision(tmp_path: Path):
    root = make_project(tmp_path)
    before = read_json(root / AVNI_DIR / "instance.json")
    agent = root / "agent" / "agent.py"
    agent.write_text('def run(payload):\n    return {"answer": "revised"}\n', encoding="utf-8")
    result = seal_project(root, note="intentional test revision")
    after = read_json(root / AVNI_DIR / "instance.json")
    assert result["parent_organism_id"] == before["organism_id"]
    assert after["organism_id"] != before["organism_id"]
    assert after["parent_organism_id"] == before["organism_id"]
    assert read_lineage(root / AVNI_DIR / LINEAGE_FILE)[-1]["event"] == "revision"
    assert validate_genome(root)["genome_id"] == after["genome_id"]
    with pytest.raises(AvniError, match="No genome changes"):
        seal_project(root)


def test_verify_and_compare_parent_outputs(tmp_path: Path):
    root = make_project(tmp_path)
    package = tmp_path / "agent.avni.zip"
    build_package(root, package)
    restored = tmp_path / "child"
    restore_package(package, restored)
    parent_result = verify_project(root)
    child_result = verify_project(restored, against=root)
    assert parent_result["success"] is True
    assert parent_result["passed"] == 3
    assert child_result["success"] is True
    assert child_result["comparison"]["same_outputs"] is True
    assert Path(child_result["report"]).is_file()
    assert not (root / "agent" / "__pycache__").exists()
    assert not (restored / "agent" / "__pycache__").exists()


def test_unlisted_file_is_not_packaged(tmp_path: Path):
    root = make_project(tmp_path)
    (root / "notes.txt").write_text("not allowlisted", encoding="utf-8")
    package = tmp_path / "agent.avni.zip"
    build_package(root, package)
    with zipfile.ZipFile(package) as archive:
        assert "notes.txt" not in archive.namelist()
        assert "artifacts/notes.txt" not in archive.namelist()


def test_secret_pattern_is_rejected_even_when_hash_is_updated(tmp_path: Path):
    root = make_project(tmp_path)
    agent = root / "agent" / "agent.py"
    agent.write_text("API_KEY = 'hardcoded-test-secret-value'\n\ndef run(payload):\n    return {'answer': 'ok'}\n", encoding="utf-8")
    genome = read_json(root / "genome.json")
    genome["artifacts"][0]["sha256"] = sha256_file(agent)
    write_json(root / "genome.json", genome)
    with pytest.raises(AvniError, match="credential detected"):
        validate_genome(root)


def test_lineage_tampering_is_detected(tmp_path: Path):
    root = make_project(tmp_path)
    lineage = root / AVNI_DIR / LINEAGE_FILE
    data = json.loads(lineage.read_text(encoding="utf-8").strip())
    data["event"] = "tampered"
    lineage.write_text(json.dumps(data) + "\n", encoding="utf-8")
    with pytest.raises(AvniError, match="entry hash mismatch"):
        read_lineage(lineage)


def test_zip_path_traversal_is_rejected(tmp_path: Path):
    malicious = tmp_path / "malicious.zip"
    with zipfile.ZipFile(malicious, "w") as archive:
        archive.writestr("../outside.txt", "bad")
    with pytest.raises(AvniError, match="relative POSIX path"):
        restore_package(malicious, tmp_path / "destination")
    assert not (tmp_path / "outside.txt").exists()


def test_package_artifact_tampering_is_detected(tmp_path: Path):
    root = make_project(tmp_path)
    package = tmp_path / "agent.avni.zip"
    build_package(root, package)
    tampered = tmp_path / "tampered.zip"
    with zipfile.ZipFile(package) as src, zipfile.ZipFile(tampered, "w") as dst:
        for name in src.namelist():
            data = src.read(name)
            if name == "artifacts/agent/agent.py":
                data += b"\n# injected\n"
            dst.writestr(name, data)
    with pytest.raises(AvniError, match="Artifact integrity failure"):
        restore_package(tampered, tmp_path / "tampered-restore")


def test_ed25519_sign_and_verify_report(tmp_path: Path):
    root = make_project(tmp_path)
    verified = verify_project(root)
    keys_dir = root / AVNI_DIR / "keys"
    private_key, public_key = generate_keypair(keys_dir)
    signature_path = Path(verified["report"] + ".sig.json")
    sign_report(Path(verified["report"]), private_key, signature_path)
    result = verify_report_signature(Path(verified["report"]), signature_path)
    assert result["valid"] is True
    report_path = Path(verified["report"])
    report_path.write_text(report_path.read_text(encoding="utf-8") + " ", encoding="utf-8")
    with pytest.raises(AvniError, match="digest does not match"):
        verify_report_signature(report_path, signature_path)


def test_replicate_event_differs_from_restore(tmp_path: Path):
    root = make_project(tmp_path)
    package = tmp_path / "agent.avni.zip"
    build_package(root, package)
    copy = tmp_path / "replica"
    result = restore_package(package, copy, event="replicate")
    assert result["event"] == "replicate"
    assert read_lineage(copy / AVNI_DIR / LINEAGE_FILE)[-1]["event"] == "replicate"


def test_status_reports_clean_and_dirty_drift(tmp_path: Path):
    root = make_project(tmp_path)
    clean = project_status(root)
    assert clean["dirty"] is False
    assert clean["drift_count"] == 0
    assert clean["genome_aligned"] is True
    assert clean["lineage_aligned"] is True

    agent = root / "agent" / "agent.py"
    agent.write_text('def run(payload):\n    return {"answer": "dirty"}\n', encoding="utf-8")
    dirty = project_status(root)
    assert dirty["dirty"] is True
    assert dirty["drift_count"] == 1
    assert dirty["drift"][0]["path"] == "agent/agent.py"
    assert dirty["drift"][0]["status"] == "modified"
    assert detect_artifact_drift(root)[0]["actual_sha256"] == sha256_file(agent)


def test_verify_against_lists_differing_cases(tmp_path: Path):
    root = make_project(tmp_path)
    package = tmp_path / "agent.avni.zip"
    build_package(root, package)
    child = tmp_path / "child"
    restore_package(package, child)
    agent = child / "agent" / "agent.py"
    agent.write_text('def run(payload):\n    return {"answer": "CHANGED"}\n', encoding="utf-8")
    seal_project(child, note="change outputs for comparison test")
    result = verify_project(child, against=root)
    assert result["comparison"]["same_case_ids"] is True
    assert result["comparison"]["same_outputs"] is False
    assert result["comparison"]["differing_count"] == 3
    assert {item["id"] for item in result["comparison"]["differing_cases"]} == {
        "hello-world",
        "trim-whitespace",
        "empty-text",
    }


def test_seal_stores_note_on_lineage_entry(tmp_path: Path):
    root = make_project(tmp_path)
    agent = root / "agent" / "agent.py"
    agent.write_text('def run(payload):\n    return {"answer": "noted"}\n', encoding="utf-8")
    seal_project(root, note="documented change")
    tip = read_lineage(root / AVNI_DIR / LINEAGE_FILE)[-1]
    assert tip["event"] == "revision"
    assert tip["note"] == "documented change"
