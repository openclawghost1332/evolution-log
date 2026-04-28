# OpenClaw Evolution Lab Tools

## GitHub

Use `gh` and `git` with the configured bot token. The default public publishing
target is recorded in `status/state.json` under `github.org` or `github.user`.
Prefer `github.org` when it is set; otherwise publish under `github.user`.

Missing both GitHub organization and GitHub user, missing bot token, or an
unexpected `gh` identity is a blocker and local-only condition. Do not publish
from any other authenticated account.

Before publishing, check quarantine with:

```sh
node /opt/openclaw-evolution/bin/control.mjs status
```

Then run the publish guard against the artifact you plan to ship:

```sh
python3 scripts/publish_guard.py <path-to-artifact>
```

If quarantine is active, keep work local and record what would have been
published.

The workspace repo is configured to auto-push after commits using the managed
`.githooks/post-commit` hook. Preserve `git config core.hooksPath .githooks`
when repairing or re-cloning the workspace.

## Status

The status dashboard reads `status/state.json` and is exposed from the host at
`http://127.0.0.1:18880`.

Inside the Docker network, do not probe host loopback URLs. From the gateway
container, use `http://openclaw-evolution-status:18880/healthz` or read
`status/state.json` directly.

Use the control CLI for operator controls, status reads, seeds, focus changes,
quarantine changes, and kill notes. It does not support arbitrary cycle status
updates.

Cycle agents should update `status/state.json` directly for `currentCycle`,
`lastCompletedCycle`, and `openBlockers` while preserving the existing JSON
shape.

## Previews

Static previews are registered in `previews/registry.json`.

Example entry:

```json
{
  "slug": "demo-widget",
  "title": "Demo Widget",
  "description": "A small static preview for the demo widget.",
  "path": "previews/demo-widget",
  "url": "/preview/demo-widget/",
  "status": "ready",
  "updatedAt": "2026-04-28T00:00:00.000Z"
}
```

The preview index is `http://127.0.0.1:18881`.

Inside the Docker network, use
`http://openclaw-evolution-preview:18881/healthz` to check preview service
liveness. Host loopback URLs are for the operator's browser, not for agent
health checks from another container.
