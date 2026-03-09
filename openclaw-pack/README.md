# ExMachina OpenClaw Pack

这是一个可直接放入远程仓库并供 OpenClaw 读取的协作包。
项目名为 ExMachina，用于为 OpenClaw 提供协议化、可装载的多智能体协作包。
默认导出模式：lite
多 agent 绑定要求：不需要
外部路由要求：不需要

当前任务：沉淀知识交接、术语索引、资源仲裁规则与 README 示例，形成 OpenClaw 协作层
主连结体：知识连结体
主连结指挥体：知识连结指挥体
协作连结体：理性连结体、校验连结体、文档连结体、安全连结体
理性协议：绝对理性协议
编排依据：见 `manifest.json` 中的 `selection_trace`。
知识交接：见 `manifest.json` 中的 `knowledge_handoff`。
执行阶段：共 4 个阶段，详见 `manifest.json` 中的 `execution_stages`。
交接契约：共 3 份，详见 `manifest.json` 中的 `handoff_contracts`。
资源仲裁：见 `manifest.json` 中的 `resource_arbitration`。
安装计划：见 `manifest.json` 中的 `openclaw_install_plan` 与 `install/INSTALL.md`。
知识交接摘要：围绕任务「沉淀知识交接、术语索引、资源仲裁规则与 README 示例，形成 OpenClaw 协作层」输出可复用的知识交接，支撑下一轮任务继续推进。

关键目录：
- `protocols/`：绝对理性协议、证据分级、冲突裁决、输出契约
- `conductor/`：全连结指挥体规则
- `link-bodies/`：连结体协议
- `link-body-conductors/`：各连结体的内部指挥规则
- `subagents/`：成员子个体规则
- `install/`：OpenClaw 安装计划、workspace 模板与 agent 方案
- `workflows/mission-loop.md`：执行节奏
- `manifest.json`：包含编排依据、知识交接、执行阶段、交接契约和资源仲裁
