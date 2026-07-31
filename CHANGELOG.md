# Changelog

<!-- version list -->

## v0.13.1 (2026-07-31)

### Documentation

- **readme**: Correct roadmap version for single-pass decode (v0.13.1)
  ([#36](https://github.com/marcellovictorino/local-whisper/pull/36),
  [`ae10b0d`](https://github.com/marcellovictorino/local-whisper/commit/ae10b0dde96f54e3ab329107003cb59211d49f04))

### Performance Improvements

- **transcribe**: Pin mlx-whisper to single greedy pass (temperature=0.0)
  ([#34](https://github.com/marcellovictorino/local-whisper/pull/34),
  [`690a6c0`](https://github.com/marcellovictorino/local-whisper/commit/690a6c0446fe9059931c9491b45b9575af4263a8))


## v0.13.0 (2026-07-30)

### Bug Fixes

- Install libportaudio2 + Xvfb for Linux CI
  ([#24](https://github.com/marcellovictorino/local-whisper/pull/24),
  [`a7b253e`](https://github.com/marcellovictorino/local-whisper/commit/a7b253e38b588bb328b6e06258bd8bac1c7ec4a8))

- **ci**: Drop top-level concurrency group so master pushes aren't cancelled
  ([#28](https://github.com/marcellovictorino/local-whisper/pull/28),
  [`598b67d`](https://github.com/marcellovictorino/local-whisper/commit/598b67db73ddd1f5115138e8501752bbce2de9e5))

- **config**: Surface malformed config.toml instead of silently disabling features
  ([#27](https://github.com/marcellovictorino/local-whisper/pull/27),
  [`e48692d`](https://github.com/marcellovictorino/local-whisper/commit/e48692d9b62dbaaf3ba89184c224a534bdec716f))

- **t-r001**: Install uv for release job
  ([#31](https://github.com/marcellovictorino/local-whisper/pull/31),
  [`5b119c4`](https://github.com/marcellovictorino/local-whisper/commit/5b119c48615287204720bf48a60567831f7f67e9))

- **t-r001**: Install uv for release job
  ([#30](https://github.com/marcellovictorino/local-whisper/pull/30),
  [`6119de3`](https://github.com/marcellovictorino/local-whisper/commit/6119de3dadf67cb48a1397f76495f73c161d4a59))

- **t-r001**: Remediate release automation
  ([#28](https://github.com/marcellovictorino/local-whisper/pull/28),
  [`598b67d`](https://github.com/marcellovictorino/local-whisper/commit/598b67db73ddd1f5115138e8501752bbce2de9e5))

- **task-03**: Cite Actions permission precedence
  ([#28](https://github.com/marcellovictorino/local-whisper/pull/28),
  [`598b67d`](https://github.com/marcellovictorino/local-whisper/commit/598b67db73ddd1f5115138e8501752bbce2de9e5))

- **task-03**: Clarify bot authorisation evidence
  ([#28](https://github.com/marcellovictorino/local-whisper/pull/28),
  [`598b67d`](https://github.com/marcellovictorino/local-whisper/commit/598b67db73ddd1f5115138e8501752bbce2de9e5))

- **task-03**: Substantiate bot push credential
  ([#28](https://github.com/marcellovictorino/local-whisper/pull/28),
  [`598b67d`](https://github.com/marcellovictorino/local-whisper/commit/598b67db73ddd1f5115138e8501752bbce2de9e5))

### Chores

- Add superset tool config ([#24](https://github.com/marcellovictorino/local-whisper/pull/24),
  [`a7b253e`](https://github.com/marcellovictorino/local-whisper/commit/a7b253e38b588bb328b6e06258bd8bac1c7ec4a8))

- Automate releases and switch CI to Linux
  ([#24](https://github.com/marcellovictorino/local-whisper/pull/24),
  [`a7b253e`](https://github.com/marcellovictorino/local-whisper/commit/a7b253e38b588bb328b6e06258bd8bac1c7ec4a8))

- Automate releases, switch CI to Linux, add README badges
  ([#24](https://github.com/marcellovictorino/local-whisper/pull/24),
  [`a7b253e`](https://github.com/marcellovictorino/local-whisper/commit/a7b253e38b588bb328b6e06258bd8bac1c7ec4a8))

- Loopctl init scaffold ([#27](https://github.com/marcellovictorino/local-whisper/pull/27),
  [`e48692d`](https://github.com/marcellovictorino/local-whisper/commit/e48692d9b62dbaaf3ba89184c224a534bdec716f))

- Loopctl init scaffold ([#28](https://github.com/marcellovictorino/local-whisper/pull/28),
  [`598b67d`](https://github.com/marcellovictorino/local-whisper/commit/598b67db73ddd1f5115138e8501752bbce2de9e5))

- Verify CI registration ([#25](https://github.com/marcellovictorino/local-whisper/pull/25),
  [`7a24607`](https://github.com/marcellovictorino/local-whisper/commit/7a24607bd5cf88f0f487a380ca5aaf7646232962))

- **finishing/docs-drift**: Clarify overlay error signal
  ([#27](https://github.com/marcellovictorino/local-whisper/pull/27),
  [`e48692d`](https://github.com/marcellovictorino/local-whisper/commit/e48692d9b62dbaaf3ba89184c224a534bdec716f))

- **finishing/simplify**: Retain only malformed config state
  ([#27](https://github.com/marcellovictorino/local-whisper/pull/27),
  [`e48692d`](https://github.com/marcellovictorino/local-whisper/commit/e48692d9b62dbaaf3ba89184c224a534bdec716f))

- **finishing/test-intent**: Cover config validator outcomes
  ([#27](https://github.com/marcellovictorino/local-whisper/pull/27),
  [`e48692d`](https://github.com/marcellovictorino/local-whisper/commit/e48692d9b62dbaaf3ba89184c224a534bdec716f))

- **pull-request**: Open implementation pull request
  ([#27](https://github.com/marcellovictorino/local-whisper/pull/27),
  [`e48692d`](https://github.com/marcellovictorino/local-whisper/commit/e48692d9b62dbaaf3ba89184c224a534bdec716f))

- **t-r001**: Remediate eval findings
  ([#27](https://github.com/marcellovictorino/local-whisper/pull/27),
  [`e48692d`](https://github.com/marcellovictorino/local-whisper/commit/e48692d9b62dbaaf3ba89184c224a534bdec716f))

- **task-01**: Produce an evidence-backed diagnosis of CI registration for master pushes. (harness
  commit) ([#28](https://github.com/marcellovictorino/local-whisper/pull/28),
  [`598b67d`](https://github.com/marcellovictorino/local-whisper/commit/598b67db73ddd1f5115138e8501752bbce2de9e5))

### Continuous Integration

- Trigger workflow run (empty commit)
  ([#24](https://github.com/marcellovictorino/local-whisper/pull/24),
  [`a7b253e`](https://github.com/marcellovictorino/local-whisper/commit/a7b253e38b588bb328b6e06258bd8bac1c7ec4a8))

### Documentation

- **t-r001**: Record release PR permission
  ([#31](https://github.com/marcellovictorino/local-whisper/pull/31),
  [`5b119c4`](https://github.com/marcellovictorino/local-whisper/commit/5b119c48615287204720bf48a60567831f7f67e9))

- **task-01**: Bound CI cancellation mitigation
  ([#28](https://github.com/marcellovictorino/local-whisper/pull/28),
  [`598b67d`](https://github.com/marcellovictorino/local-whisper/commit/598b67db73ddd1f5115138e8501752bbce2de9e5))

- **task-01**: Clarify CI registration evidence
  ([#28](https://github.com/marcellovictorino/local-whisper/pull/28),
  [`598b67d`](https://github.com/marcellovictorino/local-whisper/commit/598b67db73ddd1f5115138e8501752bbce2de9e5))

- **task-01**: Diagnose CI registration
  ([#28](https://github.com/marcellovictorino/local-whisper/pull/28),
  [`598b67d`](https://github.com/marcellovictorino/local-whisper/commit/598b67db73ddd1f5115138e8501752bbce2de9e5))

- **task-01**: Preserve CI run evidence
  ([#28](https://github.com/marcellovictorino/local-whisper/pull/28),
  [`598b67d`](https://github.com/marcellovictorino/local-whisper/commit/598b67db73ddd1f5115138e8501752bbce2de9e5))

- **task-01**: Qualify CI concurrency diagnosis
  ([#28](https://github.com/marcellovictorino/local-whisper/pull/28),
  [`598b67d`](https://github.com/marcellovictorino/local-whisper/commit/598b67db73ddd1f5115138e8501752bbce2de9e5))

- **task-01**: Reconcile protection evidence
  ([#28](https://github.com/marcellovictorino/local-whisper/pull/28),
  [`598b67d`](https://github.com/marcellovictorino/local-whisper/commit/598b67db73ddd1f5115138e8501752bbce2de9e5))

- **task-01**: Strengthen CI registration evidence
  ([#28](https://github.com/marcellovictorino/local-whisper/pull/28),
  [`598b67d`](https://github.com/marcellovictorino/local-whisper/commit/598b67db73ddd1f5115138e8501752bbce2de9e5))

- **task-02**: Verify PSR release path
  ([#28](https://github.com/marcellovictorino/local-whisper/pull/28),
  [`598b67d`](https://github.com/marcellovictorino/local-whisper/commit/598b67db73ddd1f5115138e8501752bbce2de9e5))

- **task-03**: Assess PSR bot authorisation
  ([#28](https://github.com/marcellovictorino/local-whisper/pull/28),
  [`598b67d`](https://github.com/marcellovictorino/local-whisper/commit/598b67db73ddd1f5115138e8501752bbce2de9e5))

- **task-04**: Document pull request evidence
  ([#28](https://github.com/marcellovictorino/local-whisper/pull/28),
  [`598b67d`](https://github.com/marcellovictorino/local-whisper/commit/598b67db73ddd1f5115138e8501752bbce2de9e5))

- **task-04**: Record pull request URL
  ([#28](https://github.com/marcellovictorino/local-whisper/pull/28),
  [`598b67d`](https://github.com/marcellovictorino/local-whisper/commit/598b67db73ddd1f5115138e8501752bbce2de9e5))

### Features

- **config-state**: Cache malformed config state
  ([#27](https://github.com/marcellovictorino/local-whisper/pull/27),
  [`e48692d`](https://github.com/marcellovictorino/local-whisper/commit/e48692d9b62dbaaf3ba89184c224a534bdec716f))

- **startup-overlay**: Signal malformed config at startup
  ([#27](https://github.com/marcellovictorino/local-whisper/pull/27),
  [`e48692d`](https://github.com/marcellovictorino/local-whisper/commit/e48692d9b62dbaaf3ba89184c224a534bdec716f))

- **validate-recipe**: Add config validation recipe
  ([#27](https://github.com/marcellovictorino/local-whisper/pull/27),
  [`e48692d`](https://github.com/marcellovictorino/local-whisper/commit/e48692d9b62dbaaf3ba89184c224a534bdec716f))

### Refactoring

- Fix release-automation config gaps found by /simplify
  ([#24](https://github.com/marcellovictorino/local-whisper/pull/24),
  [`a7b253e`](https://github.com/marcellovictorino/local-whisper/commit/a7b253e38b588bb328b6e06258bd8bac1c7ec4a8))

- Reuse config.load_config in validate_config, live-check malformed state
  ([#27](https://github.com/marcellovictorino/local-whisper/pull/27),
  [`e48692d`](https://github.com/marcellovictorino/local-whisper/commit/e48692d9b62dbaaf3ba89184c224a534bdec716f))
