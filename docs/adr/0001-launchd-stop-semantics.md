# 0001: launchd stop uses bootout/bootstrap, not `launchctl stop`

## Status

Accepted

## Context

The launchd plist sets `KeepAlive` true and `ThrottleInterval` 30s (`setup.sh`).
Empirically, `launchctl stop <label>` kills the running process and launchd,
seeing `KeepAlive` true, respawns it immediately — so `stop` does not actually
stop the service. Two observations on the live daemon, both with the process
up for longer than `ThrottleInterval`: PID 2892 -> 4167 (recorded in the
originating issue), and PID 85215 -> 59320 with one second elapsed.
`ThrottleInterval` bounds the interval between spawns, so it only delays a
respawn when the process exits within 30s of starting — the Accessibility
self-heal case below, not this one. This is surprising for anyone reading `setup.sh`/`justfile`
expecting `stop` to leave the service down.

## Decision

`stop` uses `launchctl bootout` and `start` uses `launchctl bootstrap` instead
of `launchctl stop`/`start`; `restart` uses
`launchctl kickstart -k gui/$(id -u)/com.local-whisper`, which kills and
respawns the job in place. Restart is preferred over `stop && start` because
on the normal path — a job that is already registered — it is a single
operation that neither reads the plist from disk nor deregisters the job, so
there is no window in which the service is stopped and nothing to go wrong if
the plist has been moved or edited since install. `bootout` followed by
`bootstrap` is two steps with the service down in between, and the `bootstrap`
half re-reads the plist, so a wrong path leaves the service off rather than
merely failing to cycle it.

`restart` does fall back to `bootstrap` when `kickstart` reports the job is not
loaded, which reintroduces the plist read for that one case. That is deliberate:
if the job is already absent there is no running service to lose, so the
downside the fallback carries does not apply.

Rejected option: keep `launchctl stop` and just rename/redocument it (e.g. call
it "kick" or document that it always respawns). This was rejected because it
keeps a footgun in the command surface — anyone scripting against `stop`
expecting the service to actually be down (e.g. before an uninstall, or to
free the microphone) would be wrong, and no amount of renaming removes the
`KeepAlive` interaction; it only relabels it. `bootout` gives an actual
"service is gone" state, and `bootstrap` gives a clean, fully-respawned start,
matching how `setup.sh`'s own reinstall path already behaves (the
bootout/bootstrap pair at the end of `setup.sh`).

No command may use `launchctl stop` — with `KeepAlive` true it is a respawn,
not a stop (immediate for a long-running job; `ThrottleInterval` only spaces
respawns when the process exits within 30s of starting, as in the Accessibility
self-heal). Use `bootout` for a real stop, `bootstrap` to bring an unloaded job
back, `kickstart -k` to cycle a loaded one.

## Consequences

- `KeepAlive` and `ThrottleInterval` are left unchanged. They are load-bearing
  for the Accessibility self-heal: macOS only re-reads the Accessibility grant
  on a fresh process, so `_ensure_accessibility()` in
  `src/local_whisper/__main__.py` intentionally exits 0 when permission is
  missing, relying on `KeepAlive` to respawn a fresh process that re-reads the
  grant, and `ThrottleInterval` (30s) to keep that respawn loop from spinning
  hot while the user goes to flip the Accessibility toggle. Switching
  `KeepAlive` to `{SuccessfulExit: false}` would break this self-heal, since a
  clean `exit 0` would then stop being respawned at all.
