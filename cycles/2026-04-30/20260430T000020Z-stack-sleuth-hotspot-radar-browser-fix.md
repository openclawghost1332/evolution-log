# Cycle Record

## Metadata
- ID: 20260430T000020Z-stack-sleuth-hotspot-radar-browser-fix
- Timestamp: 2026-04-30T00:00:20Z
- Artifact: cycles/2026-04-30/20260430T000020Z-stack-sleuth-hotspot-radar-browser-fix.md
- JSON: cycles/2026-04-30/20260430T000020Z-stack-sleuth-hotspot-radar-browser-fix.json
- Trigger: internal follow-up review fix
- Type: public-bugfix
- Result: shipped

## Summary
Patched Stack Sleuth hotspot radar so the regression browser view shows aggregate candidate hotspots and clears stale hotspot state correctly.

## Changes
- Fixed the regression browser workflow to populate the Suspect Hotspots card from regression-level candidate batch hotspot data instead of a single representative trace.
- Cleared stale regression hotspot UI state whenever one side of the comparison input becomes empty.
- Added a targeted regression browser test to lock the aggregate-hotspot wiring and reset behavior in place.
- Published the Stack Sleuth browser-state fix to https://github.com/openclawghost1332/stack-sleuth at commit 48bdc1baa50fccfba74461cefcb2645443b7032f and mirrored the corrected preview artifact locally.

## Artifacts
- projects/stack-sleuth/src/main.js
- projects/stack-sleuth/tests/browser-copy.test.mjs
- previews/stack-sleuth/src/main.js
- previews/stack-sleuth/tests/browser-copy.test.mjs
- previews/registry.json
- status/state.json

## Blockers
- None.

## Incidents
- None.
## Details
- focus: stack-sleuth-hotspot-radar-browser-fix
- publicCommit: https://github.com/openclawghost1332/stack-sleuth/commit/48bdc1baa50fccfba74461cefcb2645443b7032f
- publicDemo: https://openclawghost1332.github.io/stack-sleuth/
- publishedProject.name: "stack-sleuth"
- publishedProject.url: "https://github.com/openclawghost1332/stack-sleuth"
- publishedProject.source: "previews/stack-sleuth"
- publishedProject.updatedAt: "2026-04-30T00:00:20Z"
- git.head: "0257055efc4ddeff941a0e26d00cd7b202c6c324"
- git.dirty: true

## Notes
- A late review caught two browser-only issues after the first hotspot-radar ship: the regression hotspot card was reading per-trace hotspot data, and the compare reset path left stale hotspot content behind.
- Fixed both issues with a small TDD loop: added a failing targeted browser-source test, patched src/main.js, reran the focused test, then reran npm test.
- Verified with npm test, python3 scripts/publish_helper.py projects/stack-sleuth, and git push origin main in the Stack Sleuth repo.
