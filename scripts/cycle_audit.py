import argparse
import json
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def audit_workspace(root: Path) -> dict[str, Any]:
    state = _read_json(root / "status" / "state.json")
    issues: list[str] = []
    last_completed = state.get("lastCompletedCycle")
    latest_cycle_id = None

    if not last_completed:
        issues.append("status/state.json has no lastCompletedCycle entry")
    else:
        latest_cycle_id = last_completed.get("id")
        artifact_rel = last_completed.get("artifact")
        if not artifact_rel or not (root / artifact_rel).exists():
            issues.append(f"Missing status-referenced artifact: {artifact_rel}")

        json_rel = None
        if artifact_rel and artifact_rel.endswith(".md"):
            json_rel = artifact_rel[:-3] + ".json"
            if not (root / json_rel).exists():
                issues.append(f"Missing sibling cycle json: {json_rel}")

    return {
        "ok": not issues,
        "latestCycleId": latest_cycle_id,
        "issues": issues,
        "updatedAt": state.get("updatedAt"),
        "openBlockerCount": len(state.get("openBlockers", [])),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args(argv)
    report = audit_workspace(Path(args.root))
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
