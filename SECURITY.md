# Security Policy

## Reporting a Vulnerability

If you believe you've found a security vulnerability in local-whisper, please report
it privately first:

1. **Preferred:** use [GitHub's private vulnerability reporting](../../security/advisories/new)
   for this repository.
2. If that's not workable, email **marcello@tasman.ai** with details.

**Please do not open a public issue for suspected vulnerabilities.** Public issues are
visible to everyone before a fix exists, which puts users at risk in the meantime.

## Supported Versions

Only the latest tagged version on `master` is supported. There are no LTS branches —
fixes land on `master` and ship in the next tag. Older tags do not receive backports.

## What Leaves Your Machine

local-whisper is a local-only macOS application. Audio capture and transcription
("plain dictation") run entirely on-device via MLX-based Whisper/Parakeet models — no
audio or transcript leaves the machine for the plain dictation path.

Three optional LLM features post-process text through an OpenAI-compatible endpoint
(OpenAI itself, or a compatible endpoint via `LOCAL_WHISPER_OPENAI_BASE_URL`) using an
API key from the environment (`OPENAI_API_KEY` / `LOCAL_WHISPER_OPENAI_API_KEY`):

- **Auto-cleanup** and **adapt mode** (Right ⌥) send the raw transcript.
- **Command mode** (Right ⌘) additionally sends the text currently selected in the
  frontmost application, captured via a synthetic copy
  (`src/local_whisper/command.py`), plus the spoken instruction.

All three paths are inert unless an API key is present in the daemon environment — no
`config.toml` entry is required to activate them. `auto_adapt.apply()` falls back to a
built-in default prompt for any app with no configured prompt
(`src/local_whisper/auto_adapt.py`).

## Scope

In scope:

- Shell invocation and argument handling (`install.sh`, daemon entry points).
- Credential handling in environment variables (API keys) and their propagation into
  the LaunchAgent plist by `setup.sh`.
- Deserialisation of configuration files (`config.toml`) or cached model artifacts.
- The `launchd` installation path: `setup.sh`'s generation of the LaunchAgent plist and
  the plist itself (e.g. embedded paths, environment variables, permissions of the
  installed files).

Out of scope:

- Vulnerabilities in the underlying operating system (macOS).
- Attacks that require physical access to an unlocked device.
- Vulnerabilities in upstream dependencies — report those upstream. Check
  [`uv.lock`](uv.lock) for the exact pinned versions in use.

## Response Expectations

This is a personal, unfunded project. Reports are handled on a best-effort basis —
there is no guaranteed response time or SLA.
