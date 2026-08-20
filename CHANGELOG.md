# Changelog

<!-- version list -->

## v0.17.0 (2026-08-20)

### Bug Fixes

- Correct ADR respawn claim and quote justfile path interpolations
  ([#46](https://github.com/marcellovictorino/local-whisper/pull/46),
  [`12aa9a1`](https://github.com/marcellovictorino/local-whisper/commit/12aa9a191b56ca89a69f2ec649d44afd7543d6ec))

- Correct the setup-uv cache input name
  ([#45](https://github.com/marcellovictorino/local-whisper/pull/45),
  [`333cd34`](https://github.com/marcellovictorino/local-whisper/commit/333cd347028333479a26b410051b607893ffeb34))

- Fail loudly when restart's bootstrap fallback fails
  ([#46](https://github.com/marcellovictorino/local-whisper/pull/46),
  [`12aa9a1`](https://github.com/marcellovictorino/local-whisper/commit/12aa9a191b56ca89a69f2ec649d44afd7543d6ec))

- Harden CI matrix and Dependabot titles after review
  ([#45](https://github.com/marcellovictorino/local-whisper/pull/45),
  [`333cd34`](https://github.com/marcellovictorino/local-whisper/commit/333cd347028333479a26b410051b607893ffeb34))

- Report PID from restart and reconcile update docs with behaviour
  ([#46](https://github.com/marcellovictorino/local-whisper/pull/46),
  [`12aa9a1`](https://github.com/marcellovictorino/local-whisper/commit/12aa9a191b56ca89a69f2ec649d44afd7543d6ec))

- **t-r001**: Correct pull request release link
  ([#45](https://github.com/marcellovictorino/local-whisper/pull/45),
  [`333cd34`](https://github.com/marcellovictorino/local-whisper/commit/333cd347028333479a26b410051b607893ffeb34))

- **t-r001**: Restore release checklist reference
  ([#45](https://github.com/marcellovictorino/local-whisper/pull/45),
  [`333cd34`](https://github.com/marcellovictorino/local-whisper/commit/333cd347028333479a26b410051b607893ffeb34))

- **t-r001**: Restore self-heal wording, narrow reinstall trigger to setup.sh
  ([#46](https://github.com/marcellovictorino/local-whisper/pull/46),
  [`12aa9a1`](https://github.com/marcellovictorino/local-whisper/commit/12aa9a191b56ca89a69f2ec649d44afd7543d6ec))

- **t3**: Make just start/stop use bootstrap/bootout per ADR 0001
  ([#46](https://github.com/marcellovictorino/local-whisper/pull/46),
  [`12aa9a1`](https://github.com/marcellovictorino/local-whisper/commit/12aa9a191b56ca89a69f2ec649d44afd7543d6ec))

### Chores

- **finishing/claims-sourced**: Fix ADR respawn timing and kickstart uniqueness claims
  ([#46](https://github.com/marcellovictorino/local-whisper/pull/46),
  [`12aa9a1`](https://github.com/marcellovictorino/local-whisper/commit/12aa9a191b56ca89a69f2ec649d44afd7543d6ec))

- **finishing/claims-sourced**: Narrow release input claim
  ([#45](https://github.com/marcellovictorino/local-whisper/pull/45),
  [`333cd34`](https://github.com/marcellovictorino/local-whisper/commit/333cd347028333479a26b410051b607893ffeb34))

- **finishing/clarity-dedup**: Clarify contribution templates
  ([#45](https://github.com/marcellovictorino/local-whisper/pull/45),
  [`333cd34`](https://github.com/marcellovictorino/local-whisper/commit/333cd347028333479a26b410051b607893ffeb34))

- **finishing/clarity-dedup**: Dedup update docs, fix dangling referents, move ADR constraint
  ([#46](https://github.com/marcellovictorino/local-whisper/pull/46),
  [`12aa9a1`](https://github.com/marcellovictorino/local-whisper/commit/12aa9a191b56ca89a69f2ec649d44afd7543d6ec))

- **finishing/docs-drift**: Fix restart fallback claim, update skip scope, ADR citation
  ([#46](https://github.com/marcellovictorino/local-whisper/pull/46),
  [`12aa9a1`](https://github.com/marcellovictorino/local-whisper/commit/12aa9a191b56ca89a69f2ec649d44afd7543d6ec))

- **finishing/review**: Self-heal restart, skip no-op update, doc fallback
  ([#46](https://github.com/marcellovictorino/local-whisper/pull/46),
  [`12aa9a1`](https://github.com/marcellovictorino/local-whisper/commit/12aa9a191b56ca89a69f2ec649d44afd7543d6ec))

- **finishing/security-review**: Quote interpolations, ff-only pull, narrow restart fallback
  ([#46](https://github.com/marcellovictorino/local-whisper/pull/46),
  [`12aa9a1`](https://github.com/marcellovictorino/local-whisper/commit/12aa9a191b56ca89a69f2ec649d44afd7543d6ec))

- **finishing/simplify**: Dedup gui domain string, simplify setup.sh grep
  ([#46](https://github.com/marcellovictorino/local-whisper/pull/46),
  [`12aa9a1`](https://github.com/marcellovictorino/local-whisper/commit/12aa9a191b56ca89a69f2ec649d44afd7543d6ec))

- **finishing/stop-slop**: Tighten release checklist guidance
  ([#45](https://github.com/marcellovictorino/local-whisper/pull/45),
  [`333cd34`](https://github.com/marcellovictorino/local-whisper/commit/333cd347028333479a26b410051b607893ffeb34))

- **t-r001**: Remediate eval findings (harness commit)
  ([#46](https://github.com/marcellovictorino/local-whisper/pull/46),
  [`12aa9a1`](https://github.com/marcellovictorino/local-whisper/commit/12aa9a191b56ca89a69f2ec649d44afd7543d6ec))

- **task-01-python-ci-matrix**: Add Python compatibility CI matrix
  ([#45](https://github.com/marcellovictorino/local-whisper/pull/45),
  [`333cd34`](https://github.com/marcellovictorino/local-whisper/commit/333cd347028333479a26b410051b607893ffeb34))

- **task-02-python-badge**: Correct the README Python badge (harness commit)
  ([#45](https://github.com/marcellovictorino/local-whisper/pull/45),
  [`333cd34`](https://github.com/marcellovictorino/local-whisper/commit/333cd347028333479a26b410051b607893ffeb34))

- **task-03-dependabot**: Configure weekly Dependabot updates
  ([#45](https://github.com/marcellovictorino/local-whisper/pull/45),
  [`333cd34`](https://github.com/marcellovictorino/local-whisper/commit/333cd347028333479a26b410051b607893ffeb34))

- **task-05-issue-template**: Add general issue template
  ([#45](https://github.com/marcellovictorino/local-whisper/pull/45),
  [`333cd34`](https://github.com/marcellovictorino/local-whisper/commit/333cd347028333479a26b410051b607893ffeb34))

### Continuous Integration

- Add Python CI matrix, Dependabot, and contribution templates
  ([#45](https://github.com/marcellovictorino/local-whisper/pull/45),
  [`333cd34`](https://github.com/marcellovictorino/local-whisper/commit/333cd347028333479a26b410051b607893ffeb34))

### Documentation

- **t-r001**: Amend ADR 0001 to cover kickstart, narrow consequences
  ([#46](https://github.com/marcellovictorino/local-whisper/pull/46),
  [`12aa9a1`](https://github.com/marcellovictorino/local-whisper/commit/12aa9a191b56ca89a69f2ec649d44afd7543d6ec))

- **t1**: Record launchd stop semantics ADR
  ([#46](https://github.com/marcellovictorino/local-whisper/pull/46),
  [`12aa9a1`](https://github.com/marcellovictorino/local-whisper/commit/12aa9a191b56ca89a69f2ec649d44afd7543d6ec))

- **t5**: Fix restart guidance and document just update path
  ([#46](https://github.com/marcellovictorino/local-whisper/pull/46),
  [`12aa9a1`](https://github.com/marcellovictorino/local-whisper/commit/12aa9a191b56ca89a69f2ec649d44afd7543d6ec))

- **t6**: Document contributor update path in CONTRIBUTING.md
  ([#46](https://github.com/marcellovictorino/local-whisper/pull/46),
  [`12aa9a1`](https://github.com/marcellovictorino/local-whisper/commit/12aa9a191b56ca89a69f2ec649d44afd7543d6ec))

- **task-02-python-badge**: Correct README Python badge
  ([#45](https://github.com/marcellovictorino/local-whisper/pull/45),
  [`333cd34`](https://github.com/marcellovictorino/local-whisper/commit/333cd347028333479a26b410051b607893ffeb34))

- **task-04-pr-template**: Add pull request template
  ([#45](https://github.com/marcellovictorino/local-whisper/pull/45),
  [`333cd34`](https://github.com/marcellovictorino/local-whisper/commit/333cd347028333479a26b410051b607893ffeb34))

### Features

- Add update and restart recipes, fix stop/start to use bootout/bootstrap
  ([#46](https://github.com/marcellovictorino/local-whisper/pull/46),
  [`12aa9a1`](https://github.com/marcellovictorino/local-whisper/commit/12aa9a191b56ca89a69f2ec649d44afd7543d6ec))

- Bump minimum Python to 3.12, test 3.12-3.14
  ([#57](https://github.com/marcellovictorino/local-whisper/pull/57),
  [`63fe636`](https://github.com/marcellovictorino/local-whisper/commit/63fe63645746e312e6b9ab32d6592a6416c833c8))

- **t2**: Add restart recipe for launchd service
  ([#46](https://github.com/marcellovictorino/local-whisper/pull/46),
  [`12aa9a1`](https://github.com/marcellovictorino/local-whisper/commit/12aa9a191b56ca89a69f2ec649d44afd7543d6ec))

- **t4**: Add just update recipe (pull, sync, restart, worktree guard)
  ([#46](https://github.com/marcellovictorino/local-whisper/pull/46),
  [`12aa9a1`](https://github.com/marcellovictorino/local-whisper/commit/12aa9a191b56ca89a69f2ec649d44afd7543d6ec))


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
