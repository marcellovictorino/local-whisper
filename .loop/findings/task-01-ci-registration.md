# CI registration diagnosis — task-01

**Finding.** The `push` for the squash merge onto `master` registered a CI workflow in two seconds. GitHub then cancelled its automatic attempt before either job ran, with: `Canceling since a higher priority waiting request for ci-CI-refs/heads/master exists`.

The evidence establishes one immediate cause: GitHub Actions' workflow-level concurrency queue cancelled the registered run. It does **not** identify the competing waiting request. The current API history has no second `master` push CI run in the relevant window, and the queried APIs do not expose a concurrency-queue member for this cancellation. Therefore the deeper cause of the collision is unresolved; a workflow defect cannot be asserted as its root cause.

No workflow correction is **required for registration**: the subscribed event registered. No configuration defect is proven by this incident, so no workflow change should be represented as its correction. If the intended policy is that an unidentified queued request must never cancel a `master` workflow, the one bounded mitigation is to remove the top-level `concurrency` block. The `release` job retains its own non-cancelling `release-${{ github.workflow }}` queue, so release operations remain serialised; the trade-off is that CI jobs for separate master pushes may overlap. This mitigation is not claimed to explain, reproduce, or prove prevention of the unidentified collision.

A separate release blocker is confirmed. The active `master` ruleset requires pull requests and has no bypass actor, so the release job's bot push was rejected with `GH013`.

**Terms.** A *workflow run* is GitHub's complete CI execution; a *CI job* is one part of that run. A *ref* is the branch name GitHub updated. A *concurrency group* is GitHub's queue for runs with the same group name. A *ruleset* is the repository policy governing branch updates.

## Issue facts considered

`td usage --new-session` and `td show td-c8fd8a` were re-run in retry session `ses_2599df` (the original evidence collection used `ses_bd6ee5`). They reported:

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
| Squash push | [`refs/heads/master` at `7a24607bd5cf88f0f487a380ca5aaf7646232962`](https://github.com/marcellovictorino/local-whisper/commit/7a24607bd5cf88f0f487a380ca5aaf7646232962), merged `2026-07-30T07:35:02Z` |
| Automatic master event | `push`; [run 30523425017, attempt 1](https://github.com/marcellovictorino/local-whisper/actions/runs/30523425017/attempts/1), created `2026-07-30T07:35:05Z`; registration delay 2s; conclusion `cancelled` at `07:35:07Z` |
| Registration negative control | The [commit record](https://api.github.com/repos/marcellovictorino/local-whisper/commits/7a24607bd5cf88f0f487a380ca5aaf7646232962) timestamps the master update at `07:35:02Z`; the [master history query](https://api.github.com/repos/marcellovictorino/local-whisper/commits?sha=master&per_page=100) returns `7a24607…` as its newest commit. The [attempt-1 record](https://api.github.com/repos/marcellovictorino/local-whisper/actions/runs/30523425017/attempts/1) timestamps registration at `07:35:05Z`. No subsequent master push preceded registration; no follow-up commit nudged it. |
| Automatic-run conclusion | GitHub annotation: `Canceling since a higher priority waiting request for ci-CI-refs/heads/master exists`. Both attempt-1 jobs were cancelled with no steps: [CI job 90808800056](https://github.com/marcellovictorino/local-whisper/actions/runs/30523425017/job/90808800056) and [release job 90808802742](https://github.com/marcellovictorino/local-whisper/actions/runs/30523425017/job/90808802742). |
| Manual rerun job | [CI job 90809202938, attempt 2](https://github.com/marcellovictorino/local-whisper/actions/runs/30523425017/job/90809202938), SHA `7a24607bd5cf88f0f487a380ca5aaf7646232962`, `push`, successful `2026-07-30T07:37:31Z–07:38:06Z`. |

The rerun proves the CI job passes for the exact master SHA. It does not prove automatic master-push execution is reliable: the automatic attempt was cancelled before job steps. The [attempt-2 workflow record](https://api.github.com/repos/marcellovictorino/local-whisper/actions/runs/30523425017/attempts/2) has conclusion `failure`; its release job tried to push a calculated `0.12.1` release commit and was rejected by the ruleset, while the CI job succeeded.

**Successful historical CI run.** [Run 30154658873](https://github.com/marcellovictorino/local-whisper/actions/runs/30154658873) is a successful `push` workflow run on `master` for exact SHA `37f693e6b49ddb491efc0ab5f0ae912816e6c046` (created `2026-07-25T10:33:01Z`, concluded `success` at `10:33:33Z`). It predates this test and does not establish reliability under the tested configuration.

**Blocked CI-run criterion.** No successful *workflow run* exists for master SHA `7a24607bd5cf88f0f487a380ca5aaf7646232962`: attempt 1 was automatically cancelled and manual attempt 2 failed overall. The successful CI job is not substituted for a successful workflow run. This criterion remains **BLOCKED** until a successful automatic `push` workflow run for this exact SHA can be linked; that evidence cannot be created safely without changing historical master.

## Concurrency evidence and limit

The [attempt-1 run record](https://api.github.com/repos/marcellovictorino/local-whisper/actions/runs/30523425017/attempts/1) identifies a `push` run on `master`, SHA `7a24607…`, created at `07:35:05Z`, then cancelled at `07:35:07Z`.

The following immutable capture was made at `2026-07-30T08:09:23Z`. It queried the [CI master-push endpoint](https://api.github.com/repos/marcellovictorino/local-whisper/actions/workflows/ci.yml/runs?event=push&branch=master&per_page=100) and the [all-workflows endpoint](https://api.github.com/repos/marcellovictorino/local-whisper/actions/runs?per_page=100), then selected records where `created_at >= "2026-07-30T07:30:00Z" and created_at < "2026-07-30T07:40:00Z"`. The endpoints are mutable; this excerpt, including its filter, preserves the evidence considered.

```text
CI master-push records:
[
  {"id":30523425017,"event":"push","head_branch":"master","head_sha":"7a24607bd5cf88f0f487a380ca5aaf7646232962","status":"completed","conclusion":"failure","created_at":"2026-07-30T07:35:05Z","updated_at":"2026-07-30T07:38:57Z","name":"CI"}
]

All workflow records:
[
  {"id":30523425175,"event":"pull_request","head_branch":"chore/verify-ci-registration","head_sha":"f270a2b56431fa38ddcc6e91beb5e3d4e7b875c1","status":"completed","conclusion":"success","created_at":"2026-07-30T07:35:06Z","updated_at":"2026-07-30T07:36:00Z","name":"CI","path":".github/workflows/ci.yml"},
  {"id":30523425168,"event":"pull_request","head_branch":"chore/verify-ci-registration","head_sha":"f270a2b56431fa38ddcc6e91beb5e3d4e7b875c1","status":"completed","conclusion":"success","created_at":"2026-07-30T07:35:06Z","updated_at":"2026-07-30T07:35:12Z","name":"PR title lint","path":".github/workflows/pr-title-lint.yml"},
  {"id":30523425017,"event":"push","head_branch":"master","head_sha":"7a24607bd5cf88f0f487a380ca5aaf7646232962","status":"completed","conclusion":"failure","created_at":"2026-07-30T07:35:05Z","updated_at":"2026-07-30T07:38:57Z","name":"CI","path":".github/workflows/ci.yml"}
]
```

The run's final `failure` in this later listing reflects manual attempt 2; the separately linked attempt-1 record remains the evidence for automatic cancellation. Neither filtered response identifies a second master request.

These queries are a snapshot of visible run history, not evidence that no competing request ever existed. GitHub did not expose the higher-priority request's run ID, event, SHA, timestamp, or evaluated group in the cancellation annotation or queried response. The competing request is therefore **unidentified**, rather than attributed to a PR, a prior master push, or Actions scheduler behaviour.

## Workflow semantics applied to the squash merge

The exact workflow used for the squash commit is [`.github/workflows/ci.yml` at `7a24607…`](https://github.com/marcellovictorino/local-whisper/blob/7a24607bd5cf88f0f487a380ca5aaf7646232962/.github/workflows/ci.yml). Its relevant configuration was:

```yaml
on:
  push:
    branches: [master]
  pull_request:

concurrency:
  group: ci-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}
```

GitHub documents that `cancel-in-progress` may be an expression and that a concurrency group allows at most one running and, by default, one pending workflow; a newly queued workflow replaces an existing pending workflow in that group: [Control workflow concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency#using-concurrency-in-different-scenarios). GitHub documents that a `push.branches` filter runs only for pushes whose receiving branch matches the filter: [Workflow syntax — `on.push.branches`](https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions#onpushbranchestagsbranches-ignoretags-ignore).

PR #25's squash merge updated `refs/heads/master` to `7a24607…`, so `[master]` matched and emitted a `push` event. On that event, `github.event_name == 'pull_request'` evaluates to `false`; the expression cannot itself cancel the master run. The group evaluates to `ci-CI-refs/heads/master`. `cancel-in-progress: false` only declines to cancel a running workflow; it does not remove the documented one-pending-run behaviour. This makes the annotation consistent with a same-group waiting request, but it does not reveal the request or establish why it was present.

The mitigation is deliberately not a correction: remove this workflow-level `concurrency` block, retaining the existing release-job block:

```yaml
concurrency:
  group: release-${{ github.workflow }}
  cancel-in-progress: false
```

That retains release serialisation and removes the workflow-level queue implicated by the cancellation annotation. It permits overlapping CI jobs for separate master pushes, and cannot be claimed to prevent an unexposed scheduler collision. Verify the mitigation by merging one new no-op `chore:` PR through the ruleset, recording the resulting master SHA before any further master update, and requiring that SHA's automatic `push` CI workflow—not a rerun—to conclude `success`. This is a future verification of the mitigation, not evidence for the historical SHA.

## Settings evidence and limits

The repository Actions-permissions response was captured as `{"enabled":true,"allowed_actions":"all"}` from [the API endpoint](https://api.github.com/repos/marcellovictorino/local-whisper/actions/permissions), and the CI-workflow response reports `{"id":267771375,"name":"CI","path":".github/workflows/ci.yml","state":"active"}` from [its endpoint](https://api.github.com/repos/marcellovictorino/local-whisper/actions/workflows/ci.yml). These are repository-level settings. The repository metadata identifies owner `marcellovictorino` as a user account, not an organisation; no organisation Actions setting applies or was inferred.

The [ruleset response](https://api.github.com/repos/marcellovictorino/local-whisper/rulesets/15625854) reports active ruleset `master`, `bypass_actors: []`, and a `pull_request` rule allowing only `squash` merges for the default branch. The [legacy branch-protection endpoint](https://api.github.com/repos/marcellovictorino/local-whisper/branches/master/protection) returned HTTP 404, distinguishing it from legacy branch protection. The failing [release job](https://github.com/marcellovictorino/local-whisper/actions/runs/30523425017/job/90809308080) directly records the bot's `GH013` rejection.

## Status

CI registration for this squash merge is evidenced. Automatic master-push execution is **not demonstrated as reliable** because the only automatic run for the exact SHA was cancelled and the competing request cannot be identified. The successful-workflow-run criterion remains **BLOCKED**. End-to-end release automation remains blocked by the ruleset's lack of a bypass for `github-actions[bot]`; no release, new tag, or GitHub Release was created by this test.
