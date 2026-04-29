import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _normalize_timestamp(value: Any) -> Any:
    if not isinstance(value, str):
        return value

    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return value

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _compare_cycle_record(last_completed: dict[str, Any], record: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    comparisons = (
        ("id", "id"),
        ("artifact", "artifact"),
        ("summary", "summary"),
        ("completedAt", "timestamp"),
    )

    for state_field, record_field in comparisons:
        if record_field not in record:
            continue

        state_value = last_completed.get(state_field)
        record_value = record.get(record_field)
        if state_field == "summary" and state_value is None:
            continue
        if _normalize_timestamp(state_value) != _normalize_timestamp(record_value):
            issues.append(
                f"lastCompletedCycle.{state_field} does not match sibling cycle json {record_field}"
            )

    return issues


def _repair_preview_registry(root: Path, state: dict[str, Any]) -> int:
    registry_path = root / "previews" / "registry.json"
    if not registry_path.exists():
        return 0

    registry = _read_json(registry_path)
    previews = registry.get("previews")
    if not isinstance(previews, list):
        return 0

    preview_by_path = {
        preview.get("path"): preview
        for preview in previews
        if isinstance(preview, dict) and preview.get("path")
    }

    repaired = 0
    for project in state.get("publishedProjects", []):
        if not isinstance(project, dict):
            continue

        source = project.get("source")
        updated_at = project.get("updatedAt")
        preview = preview_by_path.get(source)
        if preview and updated_at and preview.get("updatedAt") != updated_at:
            preview["updatedAt"] = updated_at
            repaired += 1

    if repaired:
        registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")

    return repaired


def audit_workspace(root: Path, repair_preview_registry: bool = False) -> dict[str, Any]:
    state = _read_json(root / "status" / "state.json")
    repaired_preview_count = 0
    if repair_preview_registry:
        repaired_preview_count = _repair_preview_registry(root, state)

    issues: list[str] = []
    last_completed = state.get("lastCompletedCycle")
    latest_cycle_id = None
    inspected_record = None
    preview_count = 0
    published_projects = state.get("publishedProjects", [])
    published_project_count = len(published_projects)
    registered_preview_paths: set[str] = set()
    registered_previews: dict[str, dict[str, Any]] = {}

    registry_rel = Path("previews/registry.json")
    registry_path = root / registry_rel
    if not registry_path.exists():
        issues.append(f"Missing preview registry json: {registry_rel.as_posix()}")
    else:
        try:
            registry = _read_json(registry_path)
        except json.JSONDecodeError:
            issues.append(f"Invalid preview registry json: {registry_rel.as_posix()}")
        else:
            previews = registry.get("previews", [])
            if isinstance(previews, list):
                preview_count = len(previews)
                for preview in previews:
                    slug = preview.get("slug", "<unknown>")
                    preview_path = preview.get("path")
                    if not preview_path:
                        issues.append(f"Preview entry missing path: {slug}")
                        continue
                    registered_preview_paths.add(preview_path)
                    registered_previews[preview_path] = preview
                    if not (root / preview_path).exists():
                        issues.append(f"Registered preview path does not exist: {preview_path}")

    for project in published_projects:
        source = project.get("source")
        if source and source not in registered_preview_paths:
            issues.append(
                f"Published project source is not registered in previews/registry.json: {source}"
            )
            continue

        if not source:
            continue

        preview = registered_previews.get(source)
        preview_updated_at = _normalize_timestamp((preview or {}).get("updatedAt"))
        project_updated_at = _normalize_timestamp(project.get("updatedAt"))
        if preview and preview_updated_at != project_updated_at:
            issues.append(
                f"Preview registry metadata is stale for {preview.get('slug', source)}: "
                "previews/registry.json updatedAt does not match "
                "status/state.json publishedProjects updatedAt"
            )

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
            json_path = root / json_rel
            if not json_path.exists():
                issues.append(f"Missing sibling cycle json: {json_rel}")
            else:
                inspected_record = json_rel
                try:
                    record = _read_json(json_path)
                except json.JSONDecodeError:
                    issues.append(f"Invalid sibling cycle json: {json_rel}")
                else:
                    issues.extend(_compare_cycle_record(last_completed, record))

    return {
        "ok": not issues,
        "latestCycleId": latest_cycle_id,
        "checkedRecord": inspected_record,
        "stateSummary": (last_completed or {}).get("summary"),
        "issues": issues,
        "updatedAt": state.get("updatedAt"),
        "openBlockerCount": len(state.get("openBlockers", [])),
        "previewCount": preview_count,
        "publishedProjectCount": published_project_count,
        "repairedPreviewCount": repaired_preview_count,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--repair-preview-registry", action="store_true")
    args = parser.parse_args(argv)
    report = audit_workspace(
        Path(args.root),
        repair_preview_registry=args.repair_preview_registry,
    )
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
