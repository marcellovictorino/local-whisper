import argparse
import json
import logging
import threading

from local_whisper import _setup_logging, audio, transcribe

logger = logging.getLogger("local_whisper")


def _check_accessibility() -> bool:
    """Return True if this process has Accessibility permission."""
    import ctypes
    import ctypes.util

    lib_path = ctypes.util.find_library("ApplicationServices")
    if not lib_path:
        return True  # can't check, proceed optimistically
    try:
        lib = ctypes.cdll.LoadLibrary(lib_path)
        lib.AXIsProcessTrusted.restype = ctypes.c_bool
        lib.AXIsProcessTrusted.argtypes = []
        return bool(lib.AXIsProcessTrusted())
    except Exception:
        return True  # can't check, proceed optimistically


def _prompt_accessibility() -> None:
    """Ask macOS to show the Accessibility grant dialog for this process.

    The prompting variant pre-adds the running process (the venv Python
    interpreter, which launchd runs directly) to the Accessibility list, so
    the user only has to flip the toggle instead of hunting for the binary.
    Best-effort: :func:`_check_accessibility` is the actual gate.
    """
    try:
        from ApplicationServices import (
            AXIsProcessTrustedWithOptions,
            kAXTrustedCheckOptionPrompt,
        )

        AXIsProcessTrustedWithOptions({kAXTrustedCheckOptionPrompt: True})
    except Exception:  # noqa: BLE001 — dialog is a convenience, not a gate
        logger.debug("Could not trigger the Accessibility prompt dialog.", exc_info=True)


def _ensure_accessibility() -> None:
    """Ensure Accessibility permission, or exit cleanly so launchd respawns.

    macOS does not let a *running* process observe a permission granted
    mid-life — the trust check only re-reads on a fresh process. So if
    permission is missing we pop the native dialog once (which pre-adds this
    binary to the Accessibility list) and exit 0. launchd's KeepAlive +
    ThrottleInterval respawns a fresh process that re-reads the grant, so the
    service self-heals within ~30s of the user flipping the toggle — no manual
    restart, and no infinite crash-loop (each spawn is throttled).
    """
    if _check_accessibility():
        return
    _prompt_accessibility()
    logger.warning(
        "Accessibility permission required. Enable local-whisper under System "
        "Settings → Privacy & Security → Accessibility. The service restarts "
        "itself and begins working within ~30s of granting."
    )
    raise SystemExit(0)


_SERVICE_LABEL = "com.local-whisper"

# LLM env vars snapshotted into the launchd plist by setup.sh; absence only
# disables the optional adapt/command LLM modes — plain dictation stays local.
_LLM_ENV_VARS = (
    "OPENAI_API_KEY",
    "LOCAL_WHISPER_OPENAI_API_KEY",
    "LOCAL_WHISPER_COMMAND_MODEL",
    "LOCAL_WHISPER_OPENAI_BASE_URL",
)


def _service_loaded() -> bool:
    """Return True if the launchd agent is currently loaded (best-effort)."""
    import subprocess

    try:
        result = subprocess.run(["launchctl", "list"], capture_output=True, text=True, check=False)
    except OSError:
        return False
    return _SERVICE_LABEL in result.stdout


def _doctor_checks() -> list[tuple[str, bool, str, bool]]:
    """Collect health-check results as ``(name, ok, detail, critical)`` tuples.

    Split from the print layer so it can be unit-tested without real
    permissions or hardware. ``critical=True`` checks gate the exit code:
    macOS platform, Accessibility permission, and a cached model are each
    required for dictation to work at all, so a failure there is fatal.
    ``critical=False`` checks (launchd service not loaded, LLM env vars absent)
    are warnings — plain dictation is fully local and works without the
    background service or any LLM configuration.
    """
    import os
    import platform

    checks: list[tuple[str, bool, str, bool]] = []

    is_macos = platform.system() == "Darwin"
    checks.append(("Platform", is_macos, platform.platform(), True))

    checks.append(
        (
            "Accessibility",
            _check_accessibility(),
            "keystroke-synthesis permission (System Settings → Privacy & Security → Accessibility)",
            True,
        )
    )

    model = transcribe.get_model()
    cached = transcribe._model_is_cached(model)
    size = transcribe._MODEL_SIZES.get(model, "unknown size")
    model_detail = f"{model} ({size})"
    if not cached:
        model_detail += " — not downloaded; run: bash setup.sh"
    checks.append(("Model cached", cached, model_detail, True))

    loaded = _service_loaded()
    service_detail = f"{_SERVICE_LABEL} loaded" if loaded else f"{_SERVICE_LABEL} not loaded (run: just install)"
    checks.append(("launchd service", loaded, service_detail, False))

    set_vars = [name for name in _LLM_ENV_VARS if os.environ.get(name)]
    llm_detail = (
        ", ".join(set_vars) if set_vars else "none set — LLM adapt/command modes disabled; plain dictation unaffected"
    )
    checks.append(("LLM env vars", bool(set_vars), llm_detail, False))

    return checks


def _doctor() -> int:
    """Print a health report and return a shell exit code.

    Turns local-whisper's silent failure modes (missing Accessibility grant,
    model not cached) into a loud, explicit status report. Marks each line
    ``✓`` (ok), ``✗`` (critical failure), or ``⚠`` (warning). Returns 0 only
    when every CRITICAL check passes; warnings are reported but do not fail.
    """
    critical_ok = True
    for name, ok, detail, critical in _doctor_checks():
        if ok:
            marker = "✓"
        elif critical:
            marker = "✗"
            critical_ok = False
        else:
            marker = "⚠"
        print(f"{marker} {name}: {detail}")

    if critical_ok:
        print("\nAll critical checks passed.")
        return 0
    print("\nCritical checks failed — see ✗ above.")
    return 1


def main() -> None:
    """CLI entry point for local-whisper."""
    _setup_logging()
    parser = argparse.ArgumentParser(
        prog="local-whisper",
        description="Local offline speech-to-text on Apple Silicon.",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help=(
            "Start the background listener. "
            "Hold Right ⌘ to dictate. "
            "Select text first, then hold Right ⌘ to apply a voice command to the selection. "
            "Hold Right ⌥ to dictate with LLM reshaping for the frontmost app "
            "(LLM features require LOCAL_WHISPER_OPENAI_API_KEY env var)."
        ),
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Record N seconds and print transcription (smoke test).",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=5.0,
        help="Recording duration in seconds for --test mode (default: 5).",
    )
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Run latency benchmark and exit.",
    )
    parser.add_argument(
        "--doctor",
        action="store_true",
        help="Print a health report (permissions, model cache, service, env) and exit non-zero on critical failures.",
    )
    args = parser.parse_args()

    match (args.run, args.benchmark, args.test, args.doctor):
        case (True, _, _, _):
            _ensure_accessibility()

            from local_whisper import menubar
            from local_whisper.app import App
            from local_whisper.overlay import RecordingOverlay

            model = transcribe.get_model()
            backend = transcribe.get_backend(model)
            overlay = RecordingOverlay()
            app = App(overlay=overlay, model=model, backend=backend)
            app.start()

            # Pre-load model and compile Metal shaders so first keypress is instant.
            threading.Thread(target=transcribe.warm_up, args=(model, backend), daemon=True).start()
            transcribe.start_keepalive(model, backend)
            transcribe.start_wake_watcher(model, backend)

            def _quit() -> None:
                app.stop()  # run daemon cleanup synchronously before the app terminates
                overlay.quit()

            # Retain the controller for the app's lifetime; the status item drops
            # off the bar if its owner is released. Built via overlay's on_ready
            # hook so it attaches to the same accessory NSApplication.
            _menu_bar: list[object] = []

            def _session_info() -> dict[str, str]:
                return {"Model": model, "Backend": backend}

            def _install_menu_bar() -> None:
                _menu_bar.append(
                    menubar.install(
                        overlay,
                        reload_config=app._reload_config,
                        quit_app=_quit,
                        session_info=_session_info,
                    )
                )

            try:
                # AppKit event loop on main thread — blocks until quit()
                overlay.run(on_ready=_install_menu_bar)
            except KeyboardInterrupt:
                pass
            finally:
                app.stop()
                overlay.quit()

        case (_, True, _, _):
            from local_whisper import benchmark

            model = transcribe.get_model()
            backend = transcribe.get_backend(model)
            logger.info("Benchmarking %s (%ds audio, 3 runs)...", model, benchmark.DURATION_S)
            results = benchmark.run(model, backend=backend)
            print(json.dumps(results, indent=2))

        case (_, _, True, _):
            model = transcribe.get_model()
            backend = transcribe.get_backend(model)
            logger.info("Speak now — recording for %gs...", args.duration)
            audio_data = audio.record(duration=args.duration)
            text = transcribe.run(audio_data, model=model, backend=backend)
            print(text)

        case (_, _, _, True):
            raise SystemExit(_doctor())

        case _:
            parser.print_help()


if __name__ == "__main__":
    main()
