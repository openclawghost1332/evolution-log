import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REQUIRED_FIELDS = ("id", "timestamp", "summary", "artifacts", "changes")


def _validate_payload(payload: dict[str, Any]) -> dict[str, Any]:
    for field in REQUIRED_FIELDS:
        if field not in payload:
            raise ValueError(f"Missing required field: {field}")

    normalized = dict(payload)
    normalized["timestamp"] = _parse_timestamp(payload["timestamp"])
    normalized["incidentsProvided"] = "incidents" in payload
    if normalized["incidentsProvided"]:
        normalized["incidents"] = list(payload["incidents"])
    normalized.setdefault("trigger", None)
    normalized.setdefault("type", None)
    normalized.setdefault("result", None)
    normalized.setdefault("blockers", [])
    normalized.setdefault("notes", [])
    normalized.setdefault("metadata", {})
    return normalized


def _parse_timestamp(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError as exc:
        raise ValueError(f"Invalid timestamp: {value}") from exc


def _render_list(items: list[Any]) -> str:
    if not items:
        return "- None."
    return "\n".join(f"- {item}" for item in items)


def _detect_git_metadata(root: Path) -> dict[str, Any]:
    try:
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        dirty = bool(
            subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return {}

    if not head:
        return {}

    return {"git": {"head": head, "dirty": dirty}}


def _render_metadata_details(metadata: dict[str, Any]) -> str:
    if not metadata:
        return ""

    details: list[str] = []
    for key, value in metadata.items():
        if isinstance(value, dict):
            for nested_key, nested_value in value.items():
                details.append(f"- {key}.{nested_key}: {json.dumps(nested_value)}")
        else:
            details.append(f"- {key}: {value}")

    return "\n## Details\n" + "\n".join(details)


def _render_markdown(payload: dict[str, Any], artifact_path: str, json_path: str) -> str:
    metadata = [
        f"- ID: {payload['id']}",
        f"- Timestamp: {payload['timestamp'].strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"- Artifact: {artifact_path}",
        f"- JSON: {json_path}",
    ]
    for key in ("trigger", "type", "result"):
        if payload.get(key):
            metadata.append(f"- {key.capitalize()}: {payload[key]}")

    incidents_section = ""
    if payload.get("incidentsProvided"):
        incidents_section = f"\n\n## Incidents\n{_render_list(payload.get('incidents', []))}"

    notes_section = ""
    if payload.get("notes"):
        notes_section = f"\n\n## Notes\n{_render_list(payload['notes'])}"

    metadata_text = "\n".join(metadata)
    details_section = _render_metadata_details(payload.get("metadata", {}))

    return (
        "# Cycle Record\n\n"
        "## Metadata\n"
        f"{metadata_text}\n\n"
        "## Summary\n"
        f"{payload['summary']}\n\n"
        "## Changes\n"
        f"{_render_list(payload['changes'])}\n\n"
        "## Artifacts\n"
        f"{_render_list(payload['artifacts'])}\n\n"
        "## Blockers\n"
        f"{_render_list(payload['blockers'])}"
        f"{incidents_section}"
        f"{details_section}"
        f"{notes_section}\n"
    )


def _upsert_published_project_from_metadata(state: dict[str, Any], metadata: dict[str, Any]) -> None:
    project = metadata.get("publishedProject")
    if not isinstance(project, dict):
        return

    source = project.get("source")
    if not source:
        return

    published_projects = state.setdefault("publishedProjects", [])
    if not isinstance(published_projects, list):
        return

    for index, existing in enumerate(published_projects):
        if isinstance(existing, dict) and existing.get("source") == source:
            published_projects[index] = {**existing, **project}
            return

    published_projects.append(project)


def _sync_preview_registry_from_state(root: Path, state: dict[str, Any]) -> None:
    registry_path = root / "previews" / "registry.json"
    if not registry_path.exists():
        return

    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    previews = registry.get("previews")
    if not isinstance(previews, list):
        return

    preview_by_path = {
        preview.get("path"): preview
        for preview in previews
        if isinstance(preview, dict) and preview.get("path")
    }
    changed = False
    for project in state.get("publishedProjects", []):
        if not isinstance(project, dict):
            continue
        source = project.get("source")
        updated_at = project.get("updatedAt")
        preview = preview_by_path.get(source)
        if preview and updated_at and preview.get("updatedAt") != updated_at:
            preview["updatedAt"] = updated_at
            changed = True

    if changed:
        registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")



def _update_state_file(
    payload: dict[str, Any],
    root: Path,
    state_path: Path,
    state_mode: str,
    artifact_path: Path,
) -> None:
    resolved_state_path = state_path if state_path.is_absolute() else root / state_path
    state = json.loads(resolved_state_path.read_text(encoding="utf-8"))
    timestamp = payload["timestamp"].strftime("%Y-%m-%dT%H:%M:%SZ")

    if state_mode == "started":
        state["currentCycle"] = {
            "id": payload["id"],
            "summary": payload["summary"],
            "artifact": artifact_path.as_posix(),
            "startedAt": timestamp,
        }
    elif state_mode == "completed":
        state["lastCompletedCycle"] = {
            "id": payload["id"],
            "summary": payload["summary"],
            "artifact": artifact_path.as_posix(),
            "completedAt": timestamp,
        }
        state["currentCycle"] = None
        state["openBlockers"] = payload["blockers"]
        if payload.get("incidentsProvided"):
            state["incidents"] = payload.get("incidents", [])
        _upsert_published_project_from_metadata(state, payload.get("metadata", {}))
    else:
        raise ValueError(f"Unsupported state mode: {state_mode}")

    state["updatedAt"] = timestamp
    resolved_state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    if state_mode == "completed":
        _sync_preview_registry_from_state(root, state)



def write_cycle_record(
    payload: dict[str, Any],
    root: Path,
    state_path: Path | None = None,
    state_mode: str | None = None,
) -> dict[str, str]:
    normalized = _validate_payload(payload)
    normalized["metadata"] = {
        **normalized["metadata"],
        **_detect_git_metadata(root),
    }
    timestamp = normalized["timestamp"]
    day_dir = Path("cycles") / timestamp.strftime("%Y-%m-%d")
    artifact_path = day_dir / f"{normalized['id']}.md"
    json_path = day_dir / f"{normalized['id']}.json"

    record = {
        "id": normalized["id"],
        "timestamp": timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "summary": normalized["summary"],
        "artifacts": normalized["artifacts"],
        "changes": normalized["changes"],
        "trigger": normalized["trigger"],
        "type": normalized["type"],
        "result": normalized["result"],
        "blockers": normalized["blockers"],
        "notes": normalized["notes"],
        "metadata": normalized["metadata"],
        "artifact": artifact_path.as_posix(),
        "json": json_path.as_posix(),
    }
    if normalized.get("incidentsProvided"):
        record["incidents"] = normalized.get("incidents", [])

    output_dir = root / day_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    (root / artifact_path).write_text(
        _render_markdown(normalized, record["artifact"], record["json"]),
        encoding="utf-8",
    )
    (root / json_path).write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    if state_path and state_mode:
        _update_state_file(normalized, root, state_path, state_mode, artifact_path)
    return {"artifact": record["artifact"], "json": record["json"]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--root", default=".")
    parser.add_argument("--state")
    parser.add_argument("--state-mode", choices=("started", "completed"))
    args = parser.parse_args(argv)

    if args.state_mode and not args.state:
        raise ValueError("--state-mode requires --state")

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    result = write_cycle_record(
        payload,
        Path(args.root),
        state_path=Path(args.state) if args.state else None,
        state_mode=args.state_mode,
    )
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
