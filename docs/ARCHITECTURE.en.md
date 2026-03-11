# ExMachina Architecture

## Core Structure

```mermaid
flowchart TD
    U[Task Input / Workspace] --> OC[OpenClaw]
    OC --> P[PROMPT.en.md]
    P --> PACK[exmachina-en/]
    PACK --> BOOT[BOOTSTRAP.md]
    PACK --> MANI[manifest.json]
    PACK --> PROTO[protocols/]
    PACK --> COND[agents/]
    PACK --> BODIES[agents/]
    PACK --> BODYC[agents/]
    PACK --> SUBS[agents/]
    PACK --> RUNTIME[runtime/]
    RUNTIME --> TOP[topology.json]
    RUNTIME --> TASK[task-board.json]
    RUNTIME --> AGENTS[agents/*]
```

## Runtime Collaboration Diagram (lite / full)

```mermaid
flowchart LR
    M[Controller exmachina-main] --> P1[Primary Link Body exmachina-link-knowledge]
    M --> S1[Support Link Body exmachina-link-rationality]
    M --> S2[Support Link Body exmachina-link-validation]
    M --> S3[Support Link Body exmachina-link-documentation]
    M --> S4[Support Link Body exmachina-link-security]

    P1 --> M
    S1 --> M
    S2 --> M
    S3 --> M
    S4 --> M

    M --> TASK[task-board.json]
    TASK --> P1
    TASK --> S1
    TASK --> S2
    TASK --> S3
    TASK --> S4
```

Note: lite mode uses the same link-body topology but does not create subagent agents in OpenClaw. Full mode additionally creates subagent agents.

## Maintenance Principles

- `exmachina-en/` is the single source of truth for prompts and runtime.
- `PROMPT.en.md` must stay consistent with `exmachina-en/` content.
- Topology, task board, and agent status in `runtime/` must remain consistent.
- Multi-agent reporting must use the `[xx-body]:xxx` format.
- Both lite and full modes are supported. Lite does not create subagent agents in OpenClaw; full creates all subagent agents.

