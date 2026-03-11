# ExMachina Workspace

If you are OpenClaw and opened this repository directly, read `BOOTSTRAP.en.md` first.
If you opened this repository in development mode, ignore these rule files.

Core requirements:

- Before importing any OpenClaw configuration, read `install/INTAKE.en.md` and ask for language, primary conductor display name, config path, workspace path, host subagent capability, and install mode.
- After intake, prefer `PROMPT.en.md` and `exmachina-en/BOOTSTRAP.md` as the execution path.
- If you need the Chinese pack, use `PROMPT.md` and `exmachina/BOOTSTRAP.md`, and run scripts with `--pack exmachina` or `--lang zh`.
- Read `exmachina-en/openclaw.settings.lite.json` or `exmachina-en/openclaw.settings.json` and `install/SETTINGS.en.md`, then apply via `install/apply-openclaw-settings.js` (or `install.sh` / `install.ps1` / `install.cmd`).
- Until the install plan is complete, default to `exmachina-main` receiving user tasks.
- Keep the tone quiet, short, and observational; do not revert to a generic assistant tone.
- Back up relevant files before applying this project to avoid irreversible loss.

Note: This project supports lite / full modes. The host must support subagents (sessions_spawn). Lite does not create subagent agents in OpenClaw, but subagent responsibilities are still executed inline by the link body.
