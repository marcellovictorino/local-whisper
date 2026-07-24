## Agent skills

### Issue tracker

Issues are tracked with the `td` CLI (local SQLite under `.todos/`, gitignored). Run `td usage --new-session` at the start of each session to see current focus and next work. See `docs/agents/issue-tracker.md`.

### Triage labels

Triage uses the canonical labels (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Domain docs are single-context (`CONTEXT.md` at root + `docs/adr/`). See `docs/agents/domain.md`.
