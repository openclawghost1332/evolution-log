import argparse
import json
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

    notes_section = ""
    if payload.get("notes"):
        notes_section = f"\n\n## Notes\n{_render_list(payload['notes'])}"

    metadata_text = "\n".join(metadata)

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
        f"{notes_section}\n"
    )


def write_cycle_record(payload: dict[str, Any], root: Path) -> dict[str, str]:
    normalized = _validate_payload(payload)
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

    output_dir = root / day_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    (root / artifact_path).write_text(
        _render_markdown(normalized, record["artifact"], record["json"]),
        encoding="utf-8",
    )
    (root / json_path).write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return {"artifact": record["artifact"], "json": record["json"]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--root", default=".")
    args = parser.parse_args(argv)

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    result = write_cycle_record(payload, Path(args.root))
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
