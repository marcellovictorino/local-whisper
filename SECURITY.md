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

## Architecture

local-whisper is a local-only macOS application. Audio capture and transcription
("core dictation") run entirely on-device via MLX-based Whisper/Parakeet models — no
audio or transcript leaves the machine for the core dictation path.

An optional, opt-in LLM clean-up step can post-process the raw transcript through any
OpenAI-compatible API (OpenAI itself, or a compatible endpoint via
`LOCAL_WHISPER_OPENAI_BASE_URL`), using the user's own API key
(`OPENAI_API_KEY` / `LOCAL_WHISPER_OPENAI_API_KEY`). This step is disabled unless
explicitly configured, and when enabled it sends transcript text (and only transcript
text) to that third-party endpoint.

## Scope

In scope:

- Shell invocation and argument handling (`setup.sh`, `install.sh`, daemon entry points).
- Credential handling in `config.toml` and environment variables (e.g. API keys).
- Deserialisation of configuration files or cached model artifacts.
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
