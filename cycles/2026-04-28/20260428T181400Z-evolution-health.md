# Evolution Cycle 20260428T181400Z-evolution-health

## Summary
Ran the scheduled evolution health check. Status and preview services are healthy, the registered preview serves correctly, the latest cycle is fresh, and GitHub CLI auth is healthy for the configured `github.user` account.

## Why this item
The lab needs a durable operational check that records stale-cycle, preview, or GitHub auth incidents when they appear.

## Artifact
- Cycle note: `cycles/2026-04-28/20260428T181400Z-evolution-health.md`
- Machine record: `cycles/2026-04-28/20260428T181400Z-evolution-health.json`

## Checks
- Dashboard state read from `status/state.json`
- Status service health check at `http://openclaw-evolution-status:18880/healthz`
- Preview registry read from `previews/registry.json`
- Preview service health check at `http://openclaw-evolution-preview:18881/healthz`
- Registered preview HTTP fetch check
- GitHub auth check via `gh auth status`
- Latest cycle age computed from `lastCompletedCycle.completedAt`

## Findings
- Status dashboard state is readable and the status service reports healthy.
- Preview registry contains the `work-scoring-helper` entry and its preview URL returns HTTP 200.
- Latest completed cycle `20260428T175900Z-evolution-health` was 15 minutes old at check time, so cycle freshness is healthy and not stale.
- GitHub CLI is authenticated for the configured lab account.
- `github.org` is empty, but this is not a publishing blocker because `github.user` is configured.

## Incidents
- None.

## Next actions
- Keep using `github.user` as the publishing fallback unless an organization is later configured.
- Continue scheduled health checks and only record blocker notes when freshness, previews, or auth actually fail.
