# OpenClaw Settings Import

Mode: lite / full (default full)

## Import Rules
- You must complete `install/INTAKE.en.md` first.
- The host must support subagents (sessions_spawn).
- ExMachina agents must inherit OpenClaw's current default model.
- Set `exmachina-main` to `default: true` (primary conductor as the default entry).
- Do not modify existing OpenClaw provider, API, default model, or non-ExMachina configuration.
- Select settings file by mode: `lite` uses `exmachina-en/openclaw.settings.lite.json` (does not create subagent agents in OpenClaw; subagent responsibilities are executed inline by the link body). `full` uses `exmachina-en/openclaw.settings.json` (creates all subagent agents in OpenClaw).
- Recommended: use `install/apply-openclaw-settings.js` to merge the settings patch (`install.sh` / `install.ps1` / `install.cmd` already invoke it).
- Scripted merge requires Node.js; if Node.js is unavailable, merge manually.

## Template Variables
- `{{OPENCLAW_INSTALL_LANGUAGE}}`: default output language for installation and later use.
- `{{OPENCLAW_CONDUCTOR_NAME}}`: display name of the primary conductor.
- `{{EXMACHINA_PACK_ROOT}}`: repository or export package path.

## Pre-Run
- Confirm subagent allowlists and limits are configured (if needed).
- Confirm the workspace path points to this repository or export package.
- The target OpenClaw config should exist; use `--allow-missing` if you need to create a minimal config.
- If `install/intake.template.en.json` already has `target_config_path`, you can omit `--target`.

## Language Pack Note
- Chinese pack: `exmachina/openclaw.settings.lite.json` / `exmachina/openclaw.settings.json` + `install/SETTINGS.md`
- English pack: `exmachina-en/openclaw.settings.lite.json` / `exmachina-en/openclaw.settings.json` + `install/SETTINGS.en.md`
- Install scripts accept `--pack exmachina|exmachina-en` or `--lang zh|en`.

## Reference Files
- `openclaw.settings.lite.json`: lite-mode settings template (no subagent agents in OpenClaw; subagent responsibilities are executed inline).
- `openclaw.settings.json`: full-mode settings template (creates all subagent agents in OpenClaw).
- `BOOTSTRAP.md`: installation entry.
- `QUICKSTART.md`: shortest onboarding path.
- `runtime/README.md`: runtime notes.
