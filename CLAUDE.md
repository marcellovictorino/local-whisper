## Agent skills

### Issue tracker

Issues are tracked with the `td` CLI (local SQLite under `.todos/`, gitignored). Run `td usage --new-session` at the start of each session to see current focus and next work. See `docs/agents/issue-tracker.md`.

### Triage labels

Triage uses the canonical labels (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Domain docs are single-context (`CONTEXT.md` at root + `docs/adr/`). See `docs/agents/domain.md`.

### Release-PR workflow runs

The release-automation PR (`chore(release): x.y.z`, opened by `github-actions[bot]` via `peter-evans/create-pull-request` in `.github/workflows/ci.yml`) is authored with the default `GITHUB_TOKEN`. GitHub's anti-recursion guard blocks its `pull_request`-triggered `CI`/`lint` runs in `action_required` state — they never start on their own. Same thing can happen again right after that PR merges, if the merge itself re-triggers gated runs.

Whenever a release PR is opened or merged, check `gh run list --branch release/next --limit 5` (or the equivalent for the active release branch) for runs stuck in `action_required`, and approve them: `gh api repos/{owner}/{repo}/actions/runs/{run_id}/approve -X POST`. Don't wait to be asked.
