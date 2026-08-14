# Changelog

<!-- version list -->

## v0.16.1 (2026-08-14)

### Bug Fixes

- Point accessibility permission instructions at Python interpreter
  ([#41](https://github.com/marcellovictorino/local-whisper/pull/41),
  [`3d3b438`](https://github.com/marcellovictorino/local-whisper/commit/3d3b438bf0b05094ef05dcbf274dc594f4934d05))

### Chores

- Sync uv.lock to released 0.15.0
  ([#41](https://github.com/marcellovictorino/local-whisper/pull/41),
  [`3d3b438`](https://github.com/marcellovictorino/local-whisper/commit/3d3b438bf0b05094ef05dcbf274dc594f4934d05))

### Code Style

- Fix ruff-format quote style in accessibility permission message
  ([#41](https://github.com/marcellovictorino/local-whisper/pull/41),
  [`3d3b438`](https://github.com/marcellovictorino/local-whisper/commit/3d3b438bf0b05094ef05dcbf274dc594f4934d05))

### Documentation

- Clarify squash-merge discards per-commit conventional types
  ([#41](https://github.com/marcellovictorino/local-whisper/pull/41),
  [`3d3b438`](https://github.com/marcellovictorino/local-whisper/commit/3d3b438bf0b05094ef05dcbf274dc594f4934d05))


## v0.16.0 (2026-08-11)

### Bug Fixes

- Address code-review findings on British spelling feature
  ([#42](https://github.com/marcellovictorino/local-whisper/pull/42),
  [`93f35c8`](https://github.com/marcellovictorino/local-whisper/commit/93f35c87bfa71dbb9a91f60b4fd9283633129612))

- **t-r001**: Expand British spelling map
  ([#42](https://github.com/marcellovictorino/local-whisper/pull/42),
  [`93f35c8`](https://github.com/marcellovictorino/local-whisper/commit/93f35c87bfa71dbb9a91f60b4fd9283633129612))

### Chores

- Sync uv.lock to released 0.15.0
  ([#42](https://github.com/marcellovictorino/local-whisper/pull/42),
  [`93f35c8`](https://github.com/marcellovictorino/local-whisper/commit/93f35c87bfa71dbb9a91f60b4fd9283633129612))

- **finishing/clarity-dedup**: Link spelling reload guidance
  ([#42](https://github.com/marcellovictorino/local-whisper/pull/42),
  [`93f35c8`](https://github.com/marcellovictorino/local-whisper/commit/93f35c87bfa71dbb9a91f60b4fd9283633129612))

- **finishing/docs-drift**: Clarify spelling no-op modes
  ([#42](https://github.com/marcellovictorino/local-whisper/pull/42),
  [`93f35c8`](https://github.com/marcellovictorino/local-whisper/commit/93f35c87bfa71dbb9a91f60b4fd9283633129612))

- **finishing/review**: Preserve British license verb form
  ([#42](https://github.com/marcellovictorino/local-whisper/pull/42),
  [`93f35c8`](https://github.com/marcellovictorino/local-whisper/commit/93f35c87bfa71dbb9a91f60b4fd9283633129612))

- **finishing/simplify**: Inline spelling casing rule
  ([#42](https://github.com/marcellovictorino/local-whisper/pull/42),
  [`93f35c8`](https://github.com/marcellovictorino/local-whisper/commit/93f35c87bfa71dbb9a91f60b4fd9283633129612))

- **finishing/stop-slop**: Tighten spelling preference guidance
  ([#42](https://github.com/marcellovictorino/local-whisper/pull/42),
  [`93f35c8`](https://github.com/marcellovictorino/local-whisper/commit/93f35c87bfa71dbb9a91f60b4fd9283633129612))

- **finishing/test-intent**: Test spelling output across app flows
  ([#42](https://github.com/marcellovictorino/local-whisper/pull/42),
  [`93f35c8`](https://github.com/marcellovictorino/local-whisper/commit/93f35c87bfa71dbb9a91f60b4fd9283633129612))

### Documentation

- **document-spelling-preference**: Document spelling preference
  ([#42](https://github.com/marcellovictorino/local-whisper/pull/42),
  [`93f35c8`](https://github.com/marcellovictorino/local-whisper/commit/93f35c87bfa71dbb9a91f60b4fd9283633129612))

### Features

- Add British spelling preference config
  ([#42](https://github.com/marcellovictorino/local-whisper/pull/42),
  [`93f35c8`](https://github.com/marcellovictorino/local-whisper/commit/93f35c87bfa71dbb9a91f60b4fd9283633129612))

- **british-spelling-normaliser**: Add British spelling normaliser
  ([#42](https://github.com/marcellovictorino/local-whisper/pull/42),
  [`93f35c8`](https://github.com/marcellovictorino/local-whisper/commit/93f35c87bfa71dbb9a91f60b4fd9283633129612))

- **config-spelling-preference**: Expose Whisper spelling preference accessor
  ([#42](https://github.com/marcellovictorino/local-whisper/pull/42),
  [`93f35c8`](https://github.com/marcellovictorino/local-whisper/commit/93f35c87bfa71dbb9a91f60b4fd9283633129612))

- **dictation-spelling-pipeline**: Normalise dictation spelling
  ([#42](https://github.com/marcellovictorino/local-whisper/pull/42),
  [`93f35c8`](https://github.com/marcellovictorino/local-whisper/commit/93f35c87bfa71dbb9a91f60b4fd9283633129612))


## v0.15.0 (2026-08-01)

### Chores

- **deps**: Sync uv.lock to the released 0.14.0 version
  ([#39](https://github.com/marcellovictorino/local-whisper/pull/39),
  [`2df2296`](https://github.com/marcellovictorino/local-whisper/commit/2df2296f9b47e65e9d3795d95a209e467faeec14))

- **dev**: Add just demo-ui to drive every overlay state without a mic
  ([#39](https://github.com/marcellovictorino/local-whisper/pull/39),
  [`2df2296`](https://github.com/marcellovictorino/local-whisper/commit/2df2296f9b47e65e9d3795d95a209e467faeec14))

### Features

- **menubar**: Mirror the mode signal and report session state
  ([#39](https://github.com/marcellovictorino/local-whisper/pull/39),
  [`2df2296`](https://github.com/marcellovictorino/local-whisper/commit/2df2296f9b47e65e9d3795d95a209e467faeec14))

- **overlay**: Bloom pill bars, ease fade, and add mode-aware menu-bar status
  ([#39](https://github.com/marcellovictorino/local-whisper/pull/39),
  [`2df2296`](https://github.com/marcellovictorino/local-whisper/commit/2df2296f9b47e65e9d3795d95a209e467faeec14))

- **overlay**: Bloom the pill bars and ease the show/hide fade
  ([#39](https://github.com/marcellovictorino/local-whisper/pull/39),
  [`2df2296`](https://github.com/marcellovictorino/local-whisper/commit/2df2296f9b47e65e9d3795d95a209e467faeec14))


## v0.14.0 (2026-08-01)

### Features

- Add curl one-liner installer
  ([`a25493a`](https://github.com/marcellovictorino/local-whisper/commit/a25493a29fddc6dc939a0fb14aed1fa435cd7701))

- Add doctor health check
  ([`a25493a`](https://github.com/marcellovictorino/local-whisper/commit/a25493a29fddc6dc939a0fb14aed1fa435cd7701))

- Add macOS menu-bar status item
  ([`a25493a`](https://github.com/marcellovictorino/local-whisper/commit/a25493a29fddc6dc939a0fb14aed1fa435cd7701))

- Adopt Whisper Cut mark for menu-bar icon and pill overlay
  ([`a25493a`](https://github.com/marcellovictorino/local-whisper/commit/a25493a29fddc6dc939a0fb14aed1fa435cd7701))

- Install ergonomics — one-liner installer, doctor check, menu-bar item
  ([`a25493a`](https://github.com/marcellovictorino/local-whisper/commit/a25493a29fddc6dc939a0fb14aed1fa435cd7701))


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
