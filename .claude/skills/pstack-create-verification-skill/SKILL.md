---
name: pstack-create-verification-skill
description: Generate a project-local verification skill that drives this app the way a user does, in any language or on any platform. Use when explicitly invoked, or when the user asks to create, generate, or scaffold a verification skill, a control skill, or a feature map for a repo that has no scripted way to prove real app behavior. Not for running an existing test suite.
---

# Create a verification skill

Every serious project needs a scripted way to drive the real app and prove behavior: launch it, exercise a feature the way a user would, and capture evidence. This skill generates that as a project-local skill (`.claude/skills/verify-<app>/`) tailored to the repo. You write the generator's output for the next agent, not for a human: it will be read cold, mid-task, by an agent that has never seen the app.

## 1. Interview the repo, not the user

Answer these from the codebase and only ask the user what you cannot observe:

- **Surface:** what does a user actually touch? A web UI, a CLI/TUI, a desktop app, a menubar or tray app, an API, a mobile app, a library? A repo can have several; pick the primary one and note the rest.
- **Run:** how does the app start locally? Prefer the repo's own documented dev command (`justfile` targets, Makefile, package scripts, README quickstart). Note ports, env vars, seed data, auth, required OS permissions.
- **Drive:** how can an agent interact with it programmatically? Existing harnesses first (Playwright/Cypress specs, expect scripts, PTY helpers, curl-able endpoints, a debug port, an existing benchmark or sample-recording command). Only then pick a generic recipe: browser/CDP for web and Electron, a tmux/PTY harness for CLI/TUI, plain HTTP for services, a scripted input injector for hotkey and clipboard apps.
- **Observe:** what evidence can be captured? Screenshots, terminal transcripts, response bodies, logs, exit codes, clipboard contents, generated files, DB state.
- **Isolate:** can two instances run side by side (ports, data dirs, profiles)? If not, say so in the generated skill: refusing to double-drive a shared instance beats corrupting the user's session.

If the checkout doesn't build or start as-is, fix that first (or report it precisely) before generating; a skill written against a broken base teaches wrong steps. When an irrelevant missing asset blocks startup (a static dir the API never serves, a sample config), the generated skill may create it, clearly marked as verification scaffolding, and remove it in cleanup.

## 2. Generate the skill

Write `.claude/skills/verify-<app>/SKILL.md` with YAML frontmatter (`name: verify-<app>` and a `description` that names the app, the surface, and when to reach for it; without frontmatter the skill never registers) and these sections, each grounded in what the interview actually found (no placeholders left):

- **Launch:** the exact command that starts the app for verification, and how to tell it's ready (a log line, a port answering, a prompt, a tray icon present). Include teardown. For a short-lived CLI or TUI there is no server to keep alive: launch means build the binary (or install deps) once, then start each drive in its own isolated PTY or tmux session.
- **Doctor:** one read-only check that answers "is this instance worth driving?" Process up, right version/build, port owned by us, auth valid, required permissions granted. An agent runs this first whenever anything looks off.
- **Drive:** the harness recipe with real selectors/commands from this repo, not examples. Prefer stable handles (ARIA labels, data attributes, prompt strings, route paths, CLI flags) over coordinates and tab order.
- **Evidence:** what to capture for a proof and where it goes. State the proof standards: exercise the real user path, not internal setters or test-only endpoints; capture the action and the resulting state, not just the final screen; verify side effects (files written, rows inserted, clipboard set, messages sent) alongside what's visible; mocks only where a production boundary already isolates the external system. When the safe path is a dry-run or test mode, verify what it actually skips by observing (files, network, git refs) rather than trusting its name: some dry-runs still touch the network or open a browser.
- **Cleanup:** how to tear down instances the run created. Never kill by process name; kill what you started. Cleanup removes instances and scratch state, never the evidence: proof artifacts survive the teardown, in a location the skill names.
- **Helpers:** any script the skill ships is executable and its invocation is shown in the skill body. A helper the reader has to reverse-engineer is not a helper.

## 3. Seed the feature map

Create `.claude/skills/verify-<app>/features/README.md` plus one file per user-facing feature you can identify (aim for the top 3-5 to start, from routes, commands, menus, hotkeys, or docs). Follow the shape in [`references/feature-map-example/`](references/feature-map-example/), with a README index and one file per feature. Each file answers, from the user's point of view: what the feature is, how to reach it, how to drive it with the harness, and what observable end state proves it works. The four H2s are `Sub-features`, `How to get to it (user POV)`, `Driving it with <harness>`, and `Gotchas`. The map is the repo's maintained verification source; a proof that drives one convenient entry point is incomplete when the map lists others.

## 4. Prove the generated skill before handing it over

Run its own instructions end to end once: launch, doctor, drive ONE mapped feature (one is enough; the map exists so later runs can cover the rest), capture evidence, clean up. After cleanup, confirm the evidence still exists at the named location: a cleanup that eats the proof fails this step. Fix what fails, and run the generated cleanup after every failed iteration too, so broken attempts don't strand processes and ports. A generated skill that was never executed is a draft, not a deliverable.

## 5. Offer the maintenance loop

A feature map rots the moment the app changes, so it needs an upkeep pass: cover every feature file from source, exercise every feature live, and ship at most one PR of proven corrections. Upstream pstack ships this as a companion skill, `maintain-verification-skill`, which is **not installed in this repo yet**. Tell the user that, and offer to port it, rather than referring them to a slash command that does not exist here. Suggest a cadence only if they ask.

## Harness notes for Claude Code

- Generated skills live at `.claude/skills/verify-<app>/` and are discovered on the next session. The generated skill is this repo's own artifact, so name it `verify-<app>`, not `pstack-*`; the `pstack-` prefix marks skills ported from upstream pstack.
- Keep the generated skill's `description` narrow enough that it fires on verification intent and not on every mention of testing. Claude Code has no opt-out-of-auto-invocation frontmatter key, so the description is the only gate.
- When the interview needs broad codebase reading, delegate it to background `Agent` calls and keep only their findings in the main thread. Pass file paths, not file contents.
- This repo drives its app through `just` targets (`just doctor`, `just test`, `just record-sample`, `just compare`, `just benchmark`, `just validate-config`). Build the generated Launch, Doctor, Drive and Evidence sections on top of those rather than inventing a parallel entry point.

## Provenance

Ported from [pstack](https://github.com/cursor/plugins/tree/main/pstack) 0.14.5 by Lauren Tan (poteto), MIT licensed. Changes from upstream: skill renamed with the `pstack-` prefix; generated-skill path moved from `.cursor/skills/` to `.claude/skills/`; Cursor-only frontmatter keys removed; `description` tightened because Claude Code ignores `disable-model-invocation`; the step 5 pointer to `/maintain-verification-skill` replaced with an honest not-installed note; `justfile`, menubar/hotkey surfaces, clipboard side effects and OS permissions added to the interview and proof standards for this repo.
