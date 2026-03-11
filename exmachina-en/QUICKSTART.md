# QUICKSTART

Current mode: lite / full (default full)

## Shortest Path
1. Confirm all questions in `install/INTAKE.en.md` (language, conductor display name, config path, workspace path, host subagent capability, install mode).
2. Apply settings by mode: `lite` uses `openclaw.settings.lite.json`; `full` uses `openclaw.settings.json`; use `install/apply-openclaw-settings.js` (or `install.sh` / `install.ps1` / `install.cmd`) with a target config path.
3. Configure subagent allowlists/limits (if required by the host).
4. Let `exmachina-main` read `runtime/` and dispatch other agents by the task board.

## Key Files
- `openclaw.settings.lite.json`: lite-mode settings template (no subagent agents in OpenClaw; subagent responsibilities are executed inline).
- `openclaw.settings.json`: full-mode settings template (creates all subagent agents in OpenClaw).
- `install/INTAKE.en.md`: install intake.
- `runtime/topology.json`: multi-agent topology and routing summary.
- `runtime/task-board.json`: phased task board.
- `runtime/agents/`: per-agent spec, queue, and status.
- `BOOTSTRAP.md`: install and execution entry.

## Runtime Constraints
- Multi-agent reporting must use the `[xx-body]:xxx` format.
- If the host does not support subagents (sessions_spawn), do not import this pack.
