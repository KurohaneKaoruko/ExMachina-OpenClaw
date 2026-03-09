# OpenClaw 安装指南

摘要：围绕任务「沉淀知识交接、术语索引、资源仲裁规则与 README 示例，形成 OpenClaw 协作层」生成可直接供 OpenClaw 单 agent 装载的 Lite 安装计划。

## 最简安装路径
1. 将当前仓库作为 OpenClaw workspace 打开，或直接把仓库链接交给 OpenClaw。
2. 读取仓库根目录 `BOOTSTRAP.md`。
3. 运行 `python -m exmachina validate-assets`，确认资产引用完整。
4. 读取 `openclaw-pack/BOOTSTRAP.md` 与 `openclaw-pack/runtime/README.md`。
5. 让 `exmachina-main` 作为默认入口，在单会话内装载主连结体与协作链说明并执行任务。

## 生成内容
- `openclaw.agents.plan.json`：Lite 单 agent 安装计划
- `workspaces/exmachina-main/`：默认主控 workspace 引导文件模板
- `runtime/`：单会话可消费的任务板、上下文和主控运行时文件

## 说明
- Lite 模式不要求多 agent 绑定。
- Lite 模式不要求外部路由器。
- 协作连结体仍会导出，但默认以内联参考规则方式消费。
