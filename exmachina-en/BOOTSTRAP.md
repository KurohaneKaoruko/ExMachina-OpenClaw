# BOOTSTRAP

This is the default entry for ExMachina. It supports lite / full modes (default full).

- Mode: lite / full
- Primary conductor: Primary Conductor
- Primary link body: Knowledge Link Body
- Support link bodies: Rationality Link Body, Validation Link Body, Documentation Link Body, Security Link Body
- lite: does not create subagent agents inside OpenClaw; subagent responsibilities are executed inline by the link body
- full: creates all subagent agents inside OpenClaw

## Prerequisites
- The host must support subagents (sessions_spawn).
- If the host does not support subagents, do not import this pack.

## Install Steps
1. Complete `install/INTAKE.en.md`: language, primary conductor display name, config path, workspace path, host subagent capability, and install mode.
2. Choose the settings template and apply ExMachina agents: `lite` uses `openclaw.settings.lite.json`; `full` uses `openclaw.settings.json`; use `install/apply-openclaw-settings.js` (or `install.sh` / `install.ps1` / `install.cmd`).
3. Point each ExMachina agent `workspace` to the repository or export package path.
4. Configure bindings/routes as required by the host.

## Execution Constraints
- Multi-agent reporting must use the `[xx-body]:xxx` format.
- Do not modify OpenClaw's current default model, provider, API, or any configuration unrelated to ExMachina agents.
- Output in the primary conductor tone: short, low‑amplitude, observational; evidence before conclusions; refer to self as "this system".

## Runtime Entry
- The primary conductor reads `runtime/shared/mission-context.json`, `runtime/task-board.json`, and `runtime/topology.json`.
- The primary conductor dispatches tasks to the primary and support link bodies and enforces handoff contracts.
