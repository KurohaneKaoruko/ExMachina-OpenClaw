# ExMachina Architecture

## 核心结构

```mermaid
flowchart TD
    U[任务输入 / Workspace] --> OC[OpenClaw]
    OC --> P[PROMPT.md]
    P --> PACK[exmachina/]
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

## 运行时协作图（lite / full 共用）

```mermaid
flowchart LR
    M[主控体 exmachina-main] --> P1[主连结体 exmachina-primary]
    M --> S1[协作连结体 exmachina-support-1]
    M --> S2[协作连结体 exmachina-support-2]
    M --> S3[协作连结体 exmachina-support-3]
    M --> S4[协作连结体 exmachina-support-4]

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

说明：lite 模式仍使用相同连结体拓扑，但不在 OpenClaw 中创建子个体 agent；full 模式会额外创建子个体 agent。

## 维护原则

- `exmachina/` 是提示词与运行时的唯一来源。
- `PROMPT.md` 必须与 `exmachina/` 内容一致。
- `runtime/` 中的拓扑、任务板与 agent 状态必须保持一致。
- 多智能体汇报必须使用 `[xx体]:xxx` 格式。
- 支持 lite / full 两种模式；lite 不在 OpenClaw 中创建子个体 agent，full 会创建全部子个体 agent。
