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
    launchctl unload {{plist_dest}} 2>/dev/null || true
    rm -f {{plist_dest}}
    @echo "local-whisper uninstalled."

# Start the service (without reinstalling)
[group('service')]
start:
    launchctl start {{plist_name}}

# Stop the service (without uninstalling)
[group('service')]
stop:
    launchctl stop {{plist_name}}

# Show service status
[group('service')]
status:
    launchctl list | grep {{plist_name}} || echo "Not loaded"

# Run in foreground (for debugging — Ctrl+C to quit)
[group('dev')]
run:
    {{uv}} run python -m local_whisper --run

# Stream service logs
[group('dev')]
logs:
    tail -f {{log_file}}

# Run tests
[group('dev')]
test:
    {{uv}} run pytest tests/ -v
