#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

CONTROL_STATUS_COMMAND = ["node", "/opt/openclaw-evolution/bin/control.mjs", "status"]
PUBLISH_GUARD_COMMAND = [sys.executable, "scripts/publish_guard.py"]


@dataclass
class PublishCheckResult:
    exit_code: int
    message: str


def _read_control_status() -> dict:
    try:
        completed = subprocess.run(
            CONTROL_STATUS_COMMAND,
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        raise RuntimeError(str(exc)) from exc

    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("control status returned invalid JSON") from exc


def check_publish_ready(paths: list[Path]) -> PublishCheckResult:
    try:
        status = _read_control_status()
    except RuntimeError as exc:
        return PublishCheckResult(1, f"publish_helper: unable to read control status: {exc}")

    quarantine = status.get("quarantine")
    if quarantine is True or (isinstance(quarantine, dict) and quarantine.get("active")):
        return PublishCheckResult(1, "publish_helper: blocked, quarantine is active")

    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        return PublishCheckResult(1, f"publish_helper: missing paths: {', '.join(missing)}")

    completed = subprocess.run(
        [*PUBLISH_GUARD_COMMAND, *[str(path) for path in paths]],
        capture_output=True,
        text=True,
    )
    output = completed.stdout.strip() or completed.stderr.strip() or "publish_helper: no output"
    return PublishCheckResult(completed.returncode, output)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run quarantine and publish guard checks before publishing.")
    parser.add_argument("paths", nargs="+")
    args = parser.parse_args(argv)
    result = check_publish_ready([Path(path) for path in args.paths])
    print(result.message)
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
