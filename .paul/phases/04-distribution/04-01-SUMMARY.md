---
phase: 04-distribution
plan: 01
subsystem: infra
tags: [launchd, bash, justfile, accessibility, ctypes, macos]

requires:
  - phase: 03-overlay
    provides: complete --run entry point (RecordingOverlay + App)

provides:
  - Accessibility permission check on startup with actionable error
  - setup.sh one-shot install (uv sync + model download + launchd plist)
  - justfile day-to-day ops (install/uninstall/start/stop/status/run/logs)
  - launchd user agent — app auto-starts on login

affects: []  # final phase

tech-stack:
  added: []  # no new deps — ctypes is stdlib, huggingface_hub already present
  patterns:
    - AXIsProcessTrusted() via ctypes for Accessibility check (no pyobjc dep)
    - snapshot_download() for model pre-download (no transcription noise)
    - launchd plist with no KeepAlive (prevents restart loop before Accessibility granted)
    - PYTHONWARNINGS env in plist to suppress pynput semaphore warning

key-files:
  created: [setup.sh, justfile]
  modified: [src/local_whisper/__main__.py]

key-decisions:
  - "setup.sh + justfile dual pattern: setup.sh for git-clone install, justfile delegates to it"
  - "AXIsProcessTrusted() via ctypes: no new deps, early exit before pynput init"
  - "No KeepAlive in plist: prevents restart loop when Accessibility not yet granted"
  - "snapshot_download() for pre-download: silent if cached, shows progress if not — no fake transcription"
  - "uv binary needs Accessibility permission in launchd context, not Terminal"

patterns-established:
  - "launchd user agents: no KeepAlive when permission gates may block startup"
  - "model pre-download: use snapshot_download(), not run() which prints transcription noise"

duration: ~1h
started: 2026-04-27T15:00:00Z
completed: 2026-04-27T16:00:00Z
---

# Phase 4 Plan 01: Distribution — Summary

**launchd service + bash install script: `bash setup.sh` installs local-whisper to auto-start on login, with Accessibility permission check on startup.**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~1h |
| Started | 2026-04-27 |
| Completed | 2026-04-27 |
| Tasks | 3 auto + 1 human-verify |
| Files modified | 3 |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: Accessibility permission check | Pass | ctypes AXIsProcessTrusted(), exits with actionable error + sys.exit(1) |
| AC-2: Launchd install via setup.sh | Pass | plist written to ~/Library/LaunchAgents/, loaded via launchctl |
| AC-3: Starts on login | Pass | RunAtLoad=true in plist |
| AC-4: Clean uninstall | Pass | just uninstall: launchctl unload + rm plist |
| AC-5: Model pre-download | Pass | snapshot_download() gated behind _model_is_cached() check |

## Accomplishments

- `setup.sh`: strict-mode bash, checks uv + macOS, uv sync, model pre-download via snapshot_download, launchd plist with heredoc, loads service, prints Accessibility reminder
- `justfile`: 7 recipes in 3 groups (setup/service/dev); install delegates to setup.sh — single source of truth
- `__main__.py`: `_check_accessibility()` via ctypes before any pynput/AppKit import — clean early exit

## Files Created/Modified

| File | Change | Purpose |
|------|--------|---------|
| `src/local_whisper/__main__.py` | Modified | Added _check_accessibility() before --run branch |
| `setup.sh` | Created | One-shot install: deps + model + launchd plist |
| `justfile` | Created | Day-to-day ops (install/uninstall/start/stop/status/run/logs) |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| snapshot_download() for model pre-download | transcribe.run() always prints transcription noise; snapshot_download() is silent if cached | Clean install output |
| No KeepAlive in plist | If Accessibility not granted, app exits with code 1; KeepAlive would loop indefinitely | Prevents runaway restarts |
| uv binary needs Accessibility (not Terminal) | launchd runs uv directly, not via Terminal — macOS sees uv as the requesting process | User must grant Accessibility to uv binary |
| ctypes for Accessibility check | No pyobjc dependency needed; stdlib only | Zero new deps |

## Deviations from Plan

| Type | Count | Impact |
|------|-------|--------|
| Auto-fixed | 1 | Silent fix during verification |
| Deferred | 0 | — |

### Auto-fixed Issues

**1. Model pre-download used transcribe.run() — printed transcription noise**
- Found during: human checkpoint verification
- Issue: `run(np.zeros(1600, dtype='float32'))` printed "Transcribing with...", elapsed time, progress bars — looked like actual transcription was running
- Fix: replaced with `snapshot_download()` gated on `_model_is_cached()` — silent if cached, shows HF download progress if not
- Files: setup.sh

## Issues Encountered

| Issue | Resolution |
|-------|------------|
| Service exited with code 1 after install | Accessibility permission not granted to uv binary; user granted in System Settings → fixed |

## Next Phase Readiness

**Ready:**
- v0.1 MVP complete — all 4 phases shipped
- Install path: `git clone && bash setup.sh`
- Day-to-day: `just install/uninstall/logs/run`

**Concerns:**
- Leaked semaphore warning on exit still present (non-blocking; PYTHONWARNINGS in plist suppresses it in service context)

**Blockers:**
- None

---
*Phase: 04-distribution, Plan: 01*
*Completed: 2026-04-27*
