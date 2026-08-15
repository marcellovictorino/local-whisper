## Summary

<!-- Describe the change and why it is needed. -->

## Checklist

- [ ] `just test` passes
- [ ] `just run` — manual smoke test (hold Right ⌘, speak, release)
- [ ] No new dependencies added without discussion
- [ ] No changes to `overlay.py` or `hotkey.py` unless the issue explicitly requires it
- [ ] PR title follows [Conventional Commits](https://www.conventionalcommits.org/)
  After squash merge, the PR title sets the Conventional Commit type for release computation; internal commit types do not reach `master`. See [Releases](https://github.com/marcellovictorino/local-whisper/blob/master/CONTRIBUTING.md#releases) for the release rule and version-bump effects.
