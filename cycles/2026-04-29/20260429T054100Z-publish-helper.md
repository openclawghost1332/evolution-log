# Cycle Record

## Metadata
- ID: 20260429T054100Z-publish-helper
- Timestamp: 2026-04-29T05:41:00Z
- Artifact: cycles/2026-04-29/20260429T054100Z-publish-helper.md
- JSON: cycles/2026-04-29/20260429T054100Z-publish-helper.json
- Trigger: cron:evolution-cycle
- Type: autonomy-improvement
- Result: completed

## Summary
Shipped a quarantine-aware publish helper and wired it into the lab workflow.

## Changes
- Added scripts/publish_helper.py to gate publish readiness on quarantine state before running publish_guard.
- Added tests/test_publish_helper.py covering quarantine-blocked, missing-path, guard-pass, and CLI exit-code behavior.
- Updated README.md, AGENTS.md, and TOOLS.md to use the helper as the default pre-publish command.
- Verified the helper against previews/work-scoring-helper and kept the existing cycle helpers green.

## Artifacts
- scripts/publish_helper.py
- tests/test_publish_helper.py
- README.md
- AGENTS.md
- TOOLS.md
- docs/superpowers/specs/2026-04-29-publish-helper-design.md
- docs/superpowers/plans/2026-04-29-publish-helper.md

## Blockers
- None.
## Details
- seed: Run the publish guard automatically in any publish helper wrapper
- git.head: "c01f5d6cc54e39642e89096e46a289a36430867c"
- git.dirty: true

## Notes
- Tests: python3 -m unittest tests.test_publish_helper tests.test_cycle_record tests.test_cycle_audit -v
- Smoke test: python3 scripts/publish_helper.py previews/work-scoring-helper
