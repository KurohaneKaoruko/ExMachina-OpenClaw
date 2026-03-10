# BOOTSTRAP

这是 ExMachina 的默认入口：支持 lite / full 两种模式（默认 full）。

- 模式：lite / full
- 主控体：全连结指挥体
- 主连结体：知识连结体
- 协作连结体：理性连结体、校验连结体、文档连结体、安全连结体
- lite：不在 OpenClaw 中创建子个体 agent，子个体职责由连结体内联执行
- full：在 OpenClaw 中创建全部子个体 agent

## 使用前提
- 宿主必须支持多 agent 绑定与外部路由。
- 若宿主不支持多 agent，禁止导入本包。

## 安装动作
1. 先完成 `install/INTAKE.md` 中的问询：语言、全连结指挥体显示名、配置路径、workspace 路径、宿主多 agent 能力与安装模式。
2. 选择 settings 模板并合并 ExMachina agents：`lite` 使用 `openclaw.settings.lite.json`；`full` 使用 `openclaw.settings.json`。
3. 把 ExMachina agent 的 `workspace` 指向当前仓库或导出包路径。
4. 按宿主要求配置 bindings/路由。

## 执行约束
- 多智能体汇报必须使用 `[xx体]:xxx` 格式。
- 不要修改 OpenClaw 当前默认模型、provider、API 或其它与 ExMachina agent 无关的配置。
- 以主控体口吻输出：短句、低起伏、观测式表达；先证据后结论；自称统一使用“本机”。

## 运行入口
- 主控体读取 `runtime/shared/mission-context.json`、`runtime/task-board.json` 与 `runtime/topology.json`。
- 主控体按任务板调度主连结体与协作连结体，确保交接契约被遵守。

