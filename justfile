set shell := ["bash", "-c"]

project_dir := justfile_directory()
uv          := `which uv`
plist_name  := "com.local-whisper"
plist_dest  := env_var("HOME") / "Library/LaunchAgents" / plist_name + ".plist"
log_file    := env_var("HOME") / "Library/Logs/local-whisper.log"

# Install local-whisper as a background service (starts on login)
[group('setup')]
install:
    bash {{justfile_directory()}}/setup.sh

# Remove the background service
[group('setup')]
uninstall:
    launchctl bootout "gui/$(id -u)" "{{plist_dest}}" 2>/dev/null || true
    rm -f "{{plist_dest}}"
    @echo "local-whisper uninstalled."

# Start the service (bootstrap; use after stop, or if not loaded)
[group('service')]
start:
    launchctl bootstrap "gui/$(id -u)" "{{plist_dest}}"

# Stop the service (bootout — actually stops it, unlike `launchctl stop`)
[group('service')]
stop:
    launchctl bootout "gui/$(id -u)" "{{plist_dest}}"

# Restart the service (kickstart forces a fresh process; falls back to bootstrap if not loaded)
[group('service')]
restart:
    #!/usr/bin/env bash
    set -uo pipefail
    kickstart_err="$(launchctl kickstart -k "gui/$(id -u)/{{plist_name}}" 2>&1)"
    kickstart_status=$?
    if [[ $kickstart_status -ne 0 ]]; then
        if [[ "$kickstart_err" == *"Could not find service"* ]]; then
            echo "Job not loaded — bootstrapping instead."
            launchctl bootstrap "gui/$(id -u)" "{{plist_dest}}"
        else
            echo "$kickstart_err" >&2
            echo "kickstart failed (exit $kickstart_status)." >&2
            exit "$kickstart_status"
        fi
    fi
    sleep 1
    launchctl print "gui/$(id -u)/{{plist_name}}" >/dev/null || { echo "Not loaded" >&2; exit 1; }

# Pull latest, sync deps, and restart — refuses to run from a linked worktree
[group('service')]
update:
    #!/usr/bin/env bash
    set -euo pipefail
    cd "{{project_dir}}"
    if [[ "$(git rev-parse --git-dir)" != "$(git rev-parse --git-common-dir)" ]]; then
        echo "Refusing to update: $(pwd) is a linked git worktree." >&2
        echo "The launchd plist hard-codes the canonical clone directory it was installed from (see README > Updating). Run 'just update' from that clone instead." >&2
        exit 1
    fi
    before="$(git rev-parse HEAD)"
    git pull --ff-only
    after="$(git rev-parse HEAD)"
    if [[ "$before" == "$after" ]]; then
        echo "Already up to date — nothing to do."
        exit 0
    fi
    echo "Updating $before..$after:"
    git log --oneline --no-decorate "$before..$after"
    changed="$(git diff --name-only "$before" "$after")"
    if grep -qE '^setup\.sh$' <<< "$changed"; then
        echo "setup.sh changed (plist contents / env-var capture) — run 'just install' instead of restarting."
        exit 0
    fi
    {{uv}} sync
    just restart

# Show service status
[group('service')]
status:
    launchctl list | grep {{plist_name}} || echo "Not loaded"

# Run in foreground (for debugging — Ctrl+C to quit)
[group('dev')]
run:
    {{uv}} run python -m local_whisper --run 2> >(grep -v "MallocStackLogging" >&2)

# Cycle the overlay + menu-bar item through every visual state (no mic needed)
[group('dev')]
demo-ui mode="":
    {{uv}} run python scripts/demo_ui.py {{mode}} 2> >(grep -v "MallocStackLogging" >&2)

# Stream service logs
[group('dev')]
logs:
    tail -f {{log_file}}

# Validate the user config TOML
[group('dev')]
validate-config:
    {{uv}} run python scripts/validate_config.py

# Run tests
[group('dev')]
test:
    {{uv}} run pytest tests/ -v

# Run linter + formatter check
[group('dev')]
lint:
    {{uv}} run ruff check src/ tests/ scripts/validate_config.py
    {{uv}} run ruff format --check src/ tests/ scripts/validate_config.py

# Health check: permissions, model cache, service, LLM env (exits non-zero on critical failure)
[group('dev')]
doctor:
    {{uv}} run python -m local_whisper --doctor

# Benchmark transcription latency (model from config or default)
[group('dev')]
benchmark:
    {{uv}} run python -m local_whisper --benchmark

# Record a 30s audio sample for accuracy comparison (reads from mic)
[group('dev')]
record-sample:
    {{uv}} run python tests/record_sample.py

# Compare accuracy + latency across models using recorded sample
[group('dev')]
compare:
    {{uv}} run python tests/benchmark_compare.py --out tests/results.json

# Install pre-commit hooks (run once after cloning)
[group('dev')]
hooks:
    {{uv}} run pre-commit install
