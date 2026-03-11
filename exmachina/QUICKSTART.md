# QUICKSTART

当前模式：lite / full（默认 full）

## 最短路径
1. 先问清 `install/INTAKE.md` 中的全部问题（语言、主控体显示名、配置路径、workspace 路径、宿主子代理能力与安装模式）。
2. 按模式应用 settings：`lite` 使用 `openclaw.settings.lite.json`；`full` 使用 `openclaw.settings.json`；推荐使用 `install/apply-openclaw-settings.js`（或 `install.sh` / `install.ps1` / `install.cmd`）并指定目标配置路径。
3. 配置 subagents allowlist/限额（如需）。
4. 由 `exmachina-main` 读取 `runtime/` 并按任务板调度其他 agents。

## 关键文件
- `openclaw.settings.lite.json`：轻量模式设置模板（不在 OpenClaw 中创建子个体 agent，子个体职责由连结体内联执行）。
- `openclaw.settings.json`：全量模式设置模板（在 OpenClaw 中创建全部子个体 agent）。
- `install/INTAKE.md`：安装问询。
- `runtime/topology.json`：多智能体拓扑与路由摘要。
- `runtime/task-board.json`：阶段任务板。
- `runtime/agents/`：每个 agent 的规格、队列与状态。
- `BOOTSTRAP.md`：安装与执行入口。

## 运行约束
- 多智能体汇报必须使用 `[xx体]:xxx` 格式。
- 宿主不支持子代理（subagents / sessions_spawn）时，禁止导入本包。

