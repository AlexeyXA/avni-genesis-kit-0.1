"""Isolated subprocess entry point used by `avni verify`.

This is process isolation for timeout and environment hygiene, NOT a security sandbox.
Do not use it to execute packages from untrusted parties.
"""

from __future__ import annotations

import contextlib
import importlib.util
import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: _runner.py AGENT_FILE INPUT_JSON", file=sys.stderr)
        return 2

    agent_path = Path(sys.argv[1]).resolve()
    sys.dont_write_bytecode = True
    try:
        payload = json.loads(sys.argv[2])
        spec = importlib.util.spec_from_file_location("avni_agent_under_test", agent_path)
        if spec is None or spec.loader is None:
            raise RuntimeError("cannot load agent entrypoint")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if not callable(getattr(module, "run", None)):
            raise RuntimeError("entrypoint must expose callable run(payload)")
        # Reserve stdout for the machine-readable result.
        with contextlib.redirect_stdout(sys.stderr):
            result = module.run(payload)
        encoded = json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        print(encoded)
        return 0
    except Exception as exc:  # controlled boundary: return a structured process failure
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
