# Cycle Record Git Metadata Design

Date: 2026-04-29
Status: approved for autonomous cron execution
Mode: builder

## Problem statement

Cycle records currently capture summary and artifact paths, but they do not stamp the workspace git state that produced them. That makes later audits weaker because a future cycle has to reconstruct which commit was current when the record was written.

## What makes this cool

A tiny helper becomes much more trustworthy: every generated record can carry the exact HEAD commit and a dirty flag without extra manual work.

## Premises

1. Cycle records are more useful when they capture source provenance at write time.
2. The right first slice is workspace git metadata only, not a full status updater.
3. The helper should stay dependency-free and keep working outside a git repo.

## Approaches considered

### Approach A, explicit metadata only
- Require callers to pass git commit info in `metadata`.
- Pros: smallest code change.
- Cons: easy to forget, fails to standardize provenance.

### Approach B, auto-detect git metadata with graceful fallback
- Detect HEAD commit and dirty state from the output root or current workspace and merge into record metadata.
- Pros: best audit value, no extra caller burden, still small.
- Cons: needs careful fallback behavior when git is unavailable.

### Approach C, full repo snapshot block
- Capture branch, remotes, status summary, and diff stats.
- Pros: richest provenance.
- Cons: larger surface area, noisier records, more test burden.

## Recommendation

Choose Approach B. It adds real compounding value while keeping the helper small and resilient.

## Design

### Behavior

- When `write_cycle_record()` runs, it should attempt to detect git metadata for the workspace rooted at `root`.
- It should merge two generated fields into the stored `metadata` object when available:
  - `gitHead`: full commit SHA from `git rev-parse HEAD`
  - `gitDirty`: boolean, true when tracked or untracked changes exist
- Caller-provided metadata keys other than these should be preserved.
- Auto-detected values should win for `gitHead` and `gitDirty` so records reflect actual write-time state.
- If git commands fail, leave metadata untouched except for preserving caller values.

### Markdown rendering

- Add a `## Metadata Details` section when the metadata object is non-empty.
- Render each metadata key as a bullet with stable key ordering.

### Error handling

- Git detection failures must not fail record generation.
- Non-git directories should still produce valid markdown and JSON files.

### Testing

Add unit coverage for:
- auto-detected git metadata merged into JSON and markdown
- graceful fallback when git commands fail
- stable rendering of metadata details

## Success criteria

- Generated cycle record JSON includes `metadata.gitHead` and `metadata.gitDirty` when run in this workspace.
- Markdown record shows metadata details clearly.
- Tests pass locally.
