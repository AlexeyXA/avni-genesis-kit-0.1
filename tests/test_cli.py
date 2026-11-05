from __future__ import annotations

from pathlib import Path

from avni.cli import main


def test_cli_init_validate_build_verify(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["init", "cli-agent"]) == 0
    capsys.readouterr()
    project = tmp_path / "cli-agent"
    assert main(["validate", str(project)]) == 0
    assert '"valid": true' in capsys.readouterr().out
    assert main(["build", str(project)]) == 0
    capsys.readouterr()
    assert (project / "dist" / "cli-agent-0.1.0.avni.zip").is_file()
    assert main(["verify", str(project)]) == 0
    assert '"success": true' in capsys.readouterr().out


def test_cli_returns_nonzero_on_failed_acceptance(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["init", "broken-agent"]) == 0
    capsys.readouterr()
    agent = tmp_path / "broken-agent" / "agent" / "agent.py"
    agent.write_text("def run(payload):\n    return {'wrong': True}\n", encoding="utf-8")
    assert main(["seal", str(tmp_path / "broken-agent"), "--note", "intentionally broken for a test"]) == 0
    capsys.readouterr()
    code = main(["verify", str(tmp_path / "broken-agent")])
    assert code == 1
    assert '"failed": 3' in capsys.readouterr().out


def test_cli_status_clean_and_dirty(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["init", "status-agent"]) == 0
    capsys.readouterr()
    project = tmp_path / "status-agent"
    assert main(["status", str(project)]) == 0
    out = capsys.readouterr().out
    assert '"dirty": false' in out
    agent = project / "agent" / "agent.py"
    agent.write_text("def run(payload):\n    return {'answer': 'x'}\n", encoding="utf-8")
    assert main(["status", str(project)]) == 1
    out = capsys.readouterr().out
    assert '"dirty": true' in out
    assert "agent/agent.py" in out
