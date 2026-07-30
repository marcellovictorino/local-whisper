# CI registration diagnosis — task-01

**Finding.** The CI workflow registered for a squash merge onto `master`; neither its `push.branches: [master]` filter nor its `cancel-in-progress` expression suppressed that event. GitHub cancelled the registered master run in the workflow-level concurrency queue: `Canceling since a higher priority waiting request for ci-CI-refs/heads/master exists`. A workflow correction is required: master-push runs must not share this workflow-level queue. Keep cancellation scoped to pull-request runs, or remove workflow-level concurrency while retaining the release job's separate non-cancelling queue.

A separate release blocker was observed. The active `master` ruleset requires pull requests and has no bypass actor. The release job's bot push was rejected with `GH013`; the available repository evidence does not indicate an Actions or organisation-settings restriction.

**Terms.** A *workflow run* is GitHub's complete CI execution; a *CI job* is one part of that run. A *ref* is the branch name GitHub updated. A *concurrency group* is GitHub's queue for runs with the same group name. A *ruleset* is the repository policy that governs branch updates.

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
| Registration negative control | The [commit record](https://api.github.com/repos/marcellovictorino/local-whisper/commits/7a24607bd5cf88f0f487a380ca5aaf7646232962) timestamps the master update at `07:35:02Z`; the [master history query](https://api.github.com/repos/marcellovictorino/local-whisper/commits?sha=master&per_page=100) returns `7a24607…` as its newest commit. The [attempt-1 record](https://api.github.com/repos/marcellovictorino/local-whisper/actions/runs/30523425017/attempts/1) timestamps registration at `07:35:05Z`. Therefore no subsequent master push preceded registration; no follow-up commit nudged it. |
| Automatic-run conclusion | GitHub annotation: `Canceling since a higher priority waiting request for ci-CI-refs/heads/master exists`. |
| Manual rerun job | [CI job 90809202938, attempt 2](https://github.com/marcellovictorino/local-whisper/actions/runs/30523425017/job/90809202938), SHA `7a24607bd5cf88f0f487a380ca5aaf7646232962`, `push`, successful `2026-07-30T07:37:31Z–07:38:06Z`. |

The rerun proves the CI job passes for the exact master SHA. It does not prove automatic master-push execution is reliable: the automatic attempt was cancelled before any job steps. The [attempt-2 workflow record](https://api.github.com/repos/marcellovictorino/local-whisper/actions/runs/30523425017/attempts/2) has conclusion `failure`; its release job tried to push a calculated `0.12.1` release commit and was rejected by the ruleset, while the CI job succeeded.

**Blocked CI-run criterion.** No successful *workflow run* exists for master SHA `7a24607bd5cf88f0f487a380ca5aaf7646232962`: attempt 1 was automatically cancelled and manual attempt 2 failed overall. The successful CI job is not substituted for a successful workflow run. This criterion remains **BLOCKED** until a successful automatic `push` workflow run for this exact SHA can be linked; that evidence cannot be created safely without changing historical master.

## Workflow semantics applied to the squash merge

GitHub documents that `cancel-in-progress` may be an expression and that setting it controls cancellation of in-progress runs: [Control workflow concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency#using-concurrency-in-different-scenarios). GitHub also documents that `branches` filters `push` events by the branch receiving the push: [Workflow syntax — `on.push.branches`](https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions#onpushpull_requestpull_request_targetpathspaths-ignore).

For PR #25's squash merge, GitHub updated `refs/heads/master` to `7a24607…`. Therefore `[master]` matches and emits a `push` event. On that event, `github.event_name == 'pull_request'` evaluates to `false`; it cannot itself cancel the master run. The existing concurrency group still evaluates to `ci-CI-refs/heads/master`. GitHub's queue rule is the evidence-backed cause of the cancellation: a waiting request in that group had higher priority. `cancel-in-progress: false` does not remove the one-pending-run queue behaviour.

## Settings evidence and limits

The [repository Actions permissions response](https://api.github.com/repos/marcellovictorino/local-whisper/actions/permissions) returned `enabled: true` and `allowed_actions: all`. The [CI workflow response](https://api.github.com/repos/marcellovictorino/local-whisper/actions/workflows/ci.yml) returned `state: active`. These are repository-level settings. No organisation was involved: the repository is owned by the `marcellovictorino` user account, so no organisation Actions setting was queried or inferred.

The [ruleset response](https://api.github.com/repos/marcellovictorino/local-whisper/rulesets/15625854) returned active ruleset `master`, `bypass_actors: []`, and a `pull_request` rule allowing only `squash` merges for the default branch. The [legacy branch-protection endpoint](https://api.github.com/repos/marcellovictorino/local-whisper/branches/master/protection) returned HTTP 404, which distinguishes it from legacy branch protection. The failing [release job](https://github.com/marcellovictorino/local-whisper/actions/runs/30523425017/job/90809308080) is the direct evidence of the bot's `GH013` rejection.

## Status

CI registration for this squash merge is evidenced, but automatic master-push execution is not reliable until the workflow-level concurrency correction is deployed and independently observed. The successful-workflow-run criterion is **BLOCKED** as stated above. End-to-end release automation is blocked by the ruleset's lack of a bypass for `github-actions[bot]`; no release, new tag, or GitHub Release was created by this test.
