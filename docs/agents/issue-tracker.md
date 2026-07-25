# Issue tracker: td

Issues and PRDs for this repo are tracked with the [`td`](https://github.com/gtayl0r/td) CLI — a local task tracker for AI-assisted work. State lives in a SQLite database under `.todos/`, which is gitignored: task state is local to each clone, not shared through git.

Install once: `brew install td` (or see the td project). No per-repo init is needed after the first `td init` has run — the `.todos/` database already exists.

## Session start

Run this at the start of every session (or after `/clear`):

```bash
td usage --new-session
```

It rotates the session and prints current focus, reviewable issues, and the highest-priority open work.

## Conventions

- One feature is an **epic**: `td create "<feature>" --type epic`.
- Implementation issues hang off it: `td create "<slug>" --type task --epic <epic-id>`, or `--type bug` / `--type chore` as appropriate.
- Priority is `P0`–`P4` (`--priority`). Triage state is expressed as **labels** (`--labels`); the canonical role strings are in `triage-labels.md`.
- Lifecycle: `open → in_progress → in_review → closed` (plus `blocked`). Move with `td start`, `td review`, `td approve` / `td reject`, `td block`.
- The session that implements an issue cannot approve it — review must come from a different session (a reviewer sub-agent or separate context).

## When a skill says "publish to the issue tracker"

Create the issue with `td create`. For rich, multi-paragraph bodies use files rather than inline strings:

```bash
td create "<title>" --type <type> --priority <P?> \
  --description-file body.md --acceptance-file acceptance.md
```

A PRD is an epic issue; its implementation issues are children via `--epic <epic-id>`.

## When a skill says "fetch the relevant ticket"

Read it with `td show <id>` (or `td context <id>` for the full resumable context — logs, decisions, handoffs). The user will normally pass the id directly.
