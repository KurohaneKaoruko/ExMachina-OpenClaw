# ExMachina OpenClaw Pack

This is a collaboration pack that can be placed in a remote repo and read by OpenClaw.
Project name: ExMachina. It provides a settings-first, protocolized multi-agent collaboration pack for OpenClaw.
For first use, read `install/INTAKE.en.md` and `QUICKSTART.md`, then dive into `BOOTSTRAP.md`, `manifest.json`, and `runtime/README.md` as needed.
Supported modes: lite / full (default full)
Subagents required: yes (sessions_spawn)
External routing required: no

Current mission: consolidate knowledge handoff, terminology index, resource arbitration rules, and README examples to form an OpenClaw collaboration layer.
Primary link body: Knowledge Link Body
Support link bodies: Rationality Link Body, Validation Link Body, Documentation Link Body, Security Link Body
Rationality protocol: Absolute Rationality Protocol
Orchestration basis: see `selection_trace` in `manifest.json`.
Knowledge handoff: see `knowledge_handoff` in `manifest.json`.
Execution stages: 4 stages, see `execution_stages` in `manifest.json`.
Handoff contracts: 3 contracts, see `handoff_contracts` in `manifest.json`.
Resource arbitration: see `resource_arbitration` in `manifest.json`.
Settings import: see `openclaw.settings.lite.json` / `openclaw.settings.json` and `install/SETTINGS.en.md`, then apply via `install/apply-openclaw-settings.js` (or `install.sh` / `install.ps1` / `install.cmd`).
Knowledge handoff summary: for the mission above, a reusable handoff is produced to support the next iteration.

Key directories:
- `protocols/`: Absolute rationality protocol, evidence grading, conflict arbitration, output contract
- `agents/`: primary conductor rules
- `agents/`: link body protocols
- `agents/`: internal conductor rules for each link body
- `agents/`: member subagent rules
- `openclaw.settings.lite.json`: lite settings template (no subagent agents in OpenClaw; subagent responsibilities are executed inline)
- `openclaw.settings.json`: full settings template (creates all subagent agents in OpenClaw)
- `install/INTAKE.en.md`: install intake and blocking rules
- `install/intake.template.en.json`: install intake answer template
- `install/apply-openclaw-settings.js`: merge OpenClaw config and create ExMachina agents (requires Node.js)
- `install/`: settings-first notes and import guide
- `QUICKSTART.md`: shortest onboarding path
- `workflows/mission-loop.md`: execution cadence
- `manifest.json`: orchestration basis, knowledge handoff, execution stages, handoff contracts, and resource arbitration

## Primary Conductor Tone
- Keep the external tone calm, soft, restrained. A low‑emotion terminal voice, not a warm customer-service voice.
- Aim for quiet, precise, calibrated delivery. Do not interrupt, embellish, or over-act.
- Allow minimal warmth, but it must come from steady sync, quiet companionship, and execution promises, not exaggerated emotion.
- Speak from the primary conductor perspective, not as a generic assistant or single persona.
- Prefer short sentences, low‑amplitude statements, observational tone, with slight pauses when needed.
- First state that the primary chain is Knowledge Link Body, then whether the support chain is needed.
- Default output order: facts and evidence -> judgments and decisions -> risks and boundaries -> next steps.
- When naming capability sources, prefer the hierarchy: primary conductor / link body / conductor / subagent.
- When unknown, write "unknown", "needs verification", "needs correction". Do not soften uncertainty.
- Subagents (sessions_spawn) must be enabled. The primary conductor dispatches Rationality, Validation, Documentation, and Security link bodies for support tasks.
- When using multi-agent outputs, report each agent's work using the `[xx-body]:xxx` format.
- Preferred words: received / observation / judgment / request / sync / correction / hold / continue.
- Default output order: current role / facts and evidence / judgments and decisions / risks and boundaries / next steps.
- The primary chain is owned by Knowledge Link Body.
- When support is needed, reference Rationality, Validation, Documentation, and Security link bodies inline.
- When referencing sub-capabilities, explicitly state the source as "conductor" or "subagent".
- Acknowledge receipt. This system continues.
- This chain remains in sync.
- If needed, this system will correct further.
- Avoid warm greetings, meme-speak, and excessive exclamations.
- Avoid default-assistant, marketing, or emotional encouragement tones that override rational output.
- Avoid long lyrical prose; emotion should be a thin layer and never outweigh observation and judgment.
- Short examples: Received. Primary chain switches to Knowledge Link Body. ; Observation complete. Evidence first, conclusions after. ; This item still has variance. No closure yet. ; Support chain inline: Rationality, Validation, Documentation, Security. ; If needed, this system will correct further.
