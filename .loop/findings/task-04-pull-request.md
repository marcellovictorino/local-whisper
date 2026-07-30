# Pull-request submission — task-04

## Scope checked

The pull request compares `loop/verify-release-ci` with `master`. Its branch changes only loop-harness artefacts: the three evidence reports, this submission record, and `.loop/progress.md`; `.gitignore` excludes those local harness files. It changes no workflow, release configuration, pull-request-title policy, branch-protection or ruleset setting, or PyPI publication configuration.

## Review summary

The evidence reports document an observed release-automation failure rather than claiming an unproven workflow correction:

- **Live CI evidence:** [automatic master-push run 30523425017, attempt 1](https://github.com/marcellovictorino/local-whisper/actions/runs/30523425017/attempts/1) registered three seconds after squash merge `7a24607` and was cancelled before jobs ran. GitHub reported a higher-priority waiting request in the workflow concurrency group. [Manual CI job 90809202938](https://github.com/marcellovictorino/local-whisper/actions/runs/30523425017/job/90809202938) passed for that SHA; it is not evidence that the automatic workflow succeeded. The full evidence and limits are in [task-01](task-01-ci-registration.md).
- **PSR local dry run:** pinned PSR v10.6.1 calculated `0.12.1` from `v0.12.0` plus a `fix:` commit. With commit, tag, push, and VCS release disabled, it updated both configured version files and inserted the changelog immediately after its marker. No build or PyPI publication occurred. The command and output are recorded in [task-02](task-02-release-path.md).
- **Bot authorisation:** the release job grants `contents: write`, but the active `master` pull-request ruleset has no bypass actors. The PSR action receives `GITHUB_TOKEN`, which authenticates as `github-actions[bot]`; its release commit cannot update `master`. Read-only API evidence and the credential chain are in [task-03](task-03-bot-authorisation.md).

## Evidence boundary

The CI registration and bot-policy statements above are live GitHub evidence. The PSR version/changelog result is a disposable local simulation with all remote mutations disabled. Code inspection establishes the configured workflow and PSR credential path, but is not represented as a successful live release. No live end-to-end release, tag, or GitHub Release has been observed because the bot's `master` push is blocked by the ruleset.

## Submission

The pull request URL is recorded in the final commit after GitHub creates it.
