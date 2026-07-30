# PSR release-path verification — task-02

**Result.** The release workflow is correctly gated after `ci` and runs only for a successful push to `refs/heads/master`. Task-01 found no trigger defect requiring a configuration change, so this task intentionally leaves the workflow unchanged. The path is locally proven through version and changelog mutation; publishing is intentionally absent and the live bot remains blocked by the repository's pull-request-only ruleset recorded in task-01.

## Workflow inspection

[`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) has one workflow containing both jobs:

- `release` has `needs: ci`, so GitHub schedules it only after CI succeeds.
- Its condition is `github.event_name == 'push' && github.ref == 'refs/heads/master'`; pull requests and all other refs skip release.
- It grants `permissions: contents: write`.
- Checkout uses `fetch-depth: 0` and `ref: master`, so PSR receives complete `master` history and tags.
- The workflow-level concurrency setting does not cancel master pushes (`cancel-in-progress` is true only for pull requests). Task-01's cancellation diagnosis did not prove a workflow defect and required no trigger correction. The release job retains its non-cancelling serialisation group.

## Disposable PSR verification

On 2026-07-30, an isolated Git repository was created at `/tmp/task-02-psr.f7UfcQ` from the release configuration. It contained a baseline commit tagged `v0.12.0`, followed by one squash-equivalent commit, `fix: verify the PSR release path`. A placeholder `origin` was required because PSR reads the remote URL to form changelog links; no remote operation occurred.

The exact version pinned by the workflow, `python-semantic-release==10.6.1`, produced:

```text
$ semantic-release version --print
0.12.1
```

This is the expected patch bump from `v0.12.0` for `fix:`. The non-publishing mutation command was:

```text
semantic-release version --no-commit --no-tag --no-push --no-vcs-release
```

It reported `The next version is: 0.12.1!` and `No build command specified, skipping`. The resulting working tree changed only `CHANGELOG.md`, `pyproject.toml`, and `src/local_whisper/__init__.py`; the sole local tag remained `v0.12.0`.

```text
pyproject.toml: version = "0.12.1"
src/local_whisper/__init__.py: __version__ = "0.12.1"

# Changelog

<!-- version list -->

## v0.12.1 (2026-07-30)

### Bug Fixes

- Verify the PSR release path
```

This proves both configured version targets receive the same value and PSR inserts the generated release section immediately after `<!-- version list -->`.

## Release and publication trace

The workflow pins [PSR action commit `39dd2052f2ce8282a5d932c31d58a2ca06d2550e`](https://github.com/python-semantic-release/python-semantic-release/tree/39dd2052f2ce8282a5d932c31d58a2ca06d2550e) (`v10.6.1`). Its [action metadata](https://raw.githubusercontent.com/python-semantic-release/python-semantic-release/39dd2052f2ce8282a5d932c31d58a2ca06d2550e/action.yml) exposes the standard `semantic-release version` controls for commit, tag, push, changelog, and `vcs_release`. The pinned [action script](https://raw.githubusercontent.com/python-semantic-release/python-semantic-release/39dd2052f2ce8282a5d932c31d58a2ca06d2550e/src/gh_action/action.sh#L182-L189) invokes `semantic-release … version`; the workflow supplies none of those disabling inputs. Therefore, after detecting a releasable master commit, its default release operation updates the configured files, creates and pushes `vX.Y.Z`, and creates the remote VCS release (GitHub Release) using `GITHUB_TOKEN`. `contents: write` provides the repository permission required for those operations.

No PyPI build or publication is configured:

- `pyproject.toml` has no `build_command` or PyPI upload configuration under `[tool.semantic_release]`.
- The disposable PSR execution explicitly logged `No build command specified, skipping`.
- The workflow has only the PSR release action: no `build`, `twine`, `uv publish`, PyPI token, package upload, or publication step.

The current live repository policy still rejects the action bot's release commit with `GH013` because `master` permits only pull-request updates and provides no bypass actor; see [task-01](task-01-ci-registration.md). That policy is external to this workflow and prevents an actual tag and GitHub Release until a permitted release-write path is established.
