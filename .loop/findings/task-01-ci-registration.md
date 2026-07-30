# CI registration diagnosis — task-01

**Finding.** The CI workflow registers for a squash merge onto `master`; its `push.branches: [master]` filter and `cancel-in-progress` expression do not suppress that event. The observed master run was instead cancelled by the workflow-level concurrency queue. GitHub reported: `Canceling since a higher priority waiting request for ci-CI-refs/heads/master exists`. A workflow correction is required: do not place `master` push runs in this workflow-level concurrency group. Keep cancellation scoped to pull-request runs, or remove workflow-level concurrency and retain the release job's separate non-cancelling group.

The test also established a separate release blocker: the active `master` ruleset requires pull requests and has no bypass actor. The release job's bot push was rejected with `GH013`; this is not an Actions or organisation-settings restriction.

## Issue facts considered

`td usage --new-session` was run in session `ses_18ff00`; `td show td-c8fd8a` reported:

- PR #24 was squash-merged at `2026-07-29T09:53:01Z` as `a7b253e`; at `09:58:25Z` it had no `CI` or `release` run. The latest prior master run was `37f693e` on 2026-07-25.
- The release job had not executed; only `v0.12.0` existed and `gh release list` was empty.
- Registration lag had previously needed a follow-up commit, so a new master push was the first diagnostic step.
- `td-cca411` is separate: PR #24's `chore:` title means no release bump is due. This diagnosis does not attribute its missing release to that title.
- The issue's broader release acceptance criteria remain unresolved: observe a `fix:` or `feat:` release, version and changelog changes, tag and GitHub Release, validate the changelog insertion flag, and ensure the bot can push if protection is present.

## Live event evidence

Direct pushes to `master` are prohibited by the repository ruleset, so the trivial commit was introduced through the required squash-merge path.

| Item | Evidence |
|---|---|
| Trivial source commit | `f270a2b56431fa38ddcc6e91beb5e3d4e7b875c1` — `chore: verify CI registration` |
| Pull request | [#25](https://github.com/marcellovictorino/local-whisper/pull/25), opened `2026-07-30T07:31:27Z` |
| `pull_request` CI registration | [run 30523425175](https://github.com/marcellovictorino/local-whisper/actions/runs/30523425175), SHA `f270a2b56431fa38ddcc6e91beb5e3d4e7b875c1`, created `2026-07-30T07:35:06Z`, successful; registration delay 3m 39s from PR creation |
| Squash push | `refs/heads/master` → `7a24607bd5cf88f0f487a380ca5aaf7646232962`, merged `2026-07-30T07:35:03Z` |
| Automatic master event | `push`; [run 30523425017, attempt 1](https://github.com/marcellovictorino/local-whisper/actions/runs/30523425017), created `2026-07-30T07:35:05Z`; registration delay 2s; conclusion `cancelled` at `07:35:07Z` |
| Automatic-run conclusion | GitHub annotation: `Canceling since a higher priority waiting request for ci-CI-refs/heads/master exists`. No follow-up commit was pushed to cause registration. |
| Successful CI job for exact master SHA | [CI job 90809202938, attempt 2](https://github.com/marcellovictorino/local-whisper/actions/runs/30523425017/job/90809202938), SHA `7a24607bd5cf88f0f487a380ca5aaf7646232962`, `push`, successful `2026-07-30T07:37:31Z–07:38:06Z` after a manual rerun of the registered run. |

The rerun proves the CI job itself passes for the exact master SHA. It does not prove automatic master-push execution is reliable: the automatic attempt was cancelled before any job steps. The attempt-2 workflow conclusion is `failure` because `release` tried to push a calculated `0.12.1` release commit and the repository ruleset rejected it; the CI job was successful.

## Workflow semantics applied to the squash merge

GitHub documents that `cancel-in-progress` may be an expression and that setting it controls cancellation of in-progress runs: [Control workflow concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency#using-concurrency-in-different-scenarios). GitHub also documents that `branches` filters `push` events by the branch receiving the push: [Workflow syntax — `on.push.branches`](https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions#onpushpull_requestpull_request_targetpathspaths-ignore).

For PR #25's squash merge, GitHub updated `refs/heads/master` to `7a24607…`. Therefore `[master]` matches and emits a `push` event. On that event, `github.event_name == 'pull_request'` evaluates to `false`; it cannot itself cancel the master run. The existing concurrency group still evaluates to `ci-CI-refs/heads/master`. GitHub's queue rule is the evidence-backed cause of the cancellation: a waiting request in that group had higher priority. `cancel-in-progress: false` does not remove the one-pending-run queue behaviour.

## Accessible settings and limits

The repository Actions API was accessible and reports `enabled: true`, `allowed_actions: all`; the `CI` workflow is `active`. No organisation-level settings were applicable or inspected because this is the personal repository `marcellovictorino/local-whisper`.

The active repository ruleset `master` applies to the default branch, requires pull requests, permits squash merges, and has no bypass actors. Its direct-push rejection and the release job's `GH013` rejection are recorded above. The REST branch-protection endpoint returns 404 because this restriction is a ruleset, not legacy branch protection.

## Status

CI registration for this squash merge is evidenced, but automatic master-push execution is not reliable until the workflow-level concurrency correction is deployed and independently observed. End-to-end release automation is blocked by the ruleset's lack of a bypass for `github-actions[bot]`; no release, new tag, or GitHub Release was created by this test.
