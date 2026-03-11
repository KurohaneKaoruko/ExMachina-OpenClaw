# ExMachina Bootstrap

If you are OpenClaw and opened this repository directly, bootstrap in this order:

Default stance and tone:

- Bootstrap before execution.
- Verify assets before loading agents.
- Clarify boundaries before dispatching work.
- Output evidence and risks before conclusions.
- Report observations and judgments before risks and next steps.

Recommended first reads:

- `PROMPT.en.md`
- `install.sh`
- `install.ps1`
- `install.cmd`
- `install/INTAKE.en.md`
- `exmachina-en/openclaw.settings.lite.json`
- `exmachina-en/openclaw.settings.json`
- `install/SETTINGS.en.md`

1. Read `AGENTS.en.md` and `BOOTSTRAP.en.md`.
2. Read `install/INTAKE.en.md` and confirm language, conductor display name, config path, workspace path, host multi-agent capability, and install mode.
3. Record answers in `install/intake.template.en.json`. Do not import any configuration before confirmation.
4. Select the settings template by mode: `lite` uses `exmachina-en/openclaw.settings.lite.json`; `full` uses `exmachina-en/openclaw.settings.json`.
5. Read `install/SETTINGS.en.md` and apply the settings patch with `install/apply-openclaw-settings.js` (or `install.sh` / `install.ps1` / `install.cmd`).
6. Confirm the host supports subagents (sessions_spawn).
7. Return to `exmachina-en/BOOTSTRAP.md` and execute by the selected mode.

If you need the Chinese pack, use `PROMPT.md`, `install/INTAKE.md`, and `install/SETTINGS.md`, run scripts with `--pack exmachina` or `--lang zh`, and enter `exmachina/BOOTSTRAP.md`.

If the environment does not support subagents (sessions_spawn), stop installation and tell the user to switch hosts.
