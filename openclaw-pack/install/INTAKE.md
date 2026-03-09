# OpenClaw 安装问询

摘要：在安装任务「沉淀知识交接、术语索引、资源仲裁规则与 README 示例，形成 OpenClaw 协作层」前，必须先确认语言、全连结指挥体显示名、安装模式和配置参数。
阻断规则：在语言、全连结指挥体显示名、安装模式、目标配置路径与 workspace 路径未确认前，不得导入 settings patch。

## 必须先问清
1. 语言：这次安装与后续默认输出使用什么语言？
   默认值：zh-CN
   模板变量：`{{OPENCLAW_INSTALL_LANGUAGE}}`
2. 全连结指挥体名字：希望把全连结指挥体 / 主控体显示为哪个名字？
   默认值：ExMachina 主控体
   模板变量：`{{OPENCLAW_CONDUCTOR_NAME}}`
   说明：默认主控来源仍是 全连结指挥体。
   说明：该名字会写入主控 agent 的 display name，并用于安装期提示。
3. 安装模式：这次安装走 lite 还是 full？
   默认值：lite
   模板变量：`{{OPENCLAW_INSTALL_MODE}}`
   说明：lite 走单会话内联协作路径。
   说明：full 需要宿主支持多 agent 绑定与路由。
4. 配置文件路径：本次要写入哪份 OpenClaw 配置文件？
   默认值：~/.openclaw/openclaw.json
5. 仓库 / 导出包路径：把 workspace 指到哪个仓库或导出包路径？
   默认值：{{EXMACHINA_PACK_ROOT}}
   模板变量：`{{EXMACHINA_PACK_ROOT}}`

## 可选补充项
1. 宿主多 agent 能力：宿主是否支持多 agent 绑定与外部路由？
   默认值：False
2. 其它配置：还有哪些渠道绑定、token、workspace 或风格配置需要一并记录？

## 确认清单
- 语言已确认，后续安装说明与交互默认使用该语言。
- 全连结指挥体 / 主控体显示名已确认。
- 安装模式已确认，且与宿主能力匹配。
- 主连结体已确认：知识连结体。
- 协作连结体已确认：理性连结体、校验连结体、文档连结体、安全连结体。
- 目标 OpenClaw 配置路径与 workspace 路径已确认。
- 当前默认模型保持不变，ExMachina agent 将继承现有默认模型。
- 额外配置项已确认或显式留空。

## 模式决议规则
- 如果用户选择 full，但当前导出包是 lite，先重生成 full 包，再继续安装。
- 如果宿主不支持多 agent 绑定与路由，则强制退回 lite。
- 如果配置路径或 workspace 路径未确认，则暂停安装。

## 记录方式
- 把答案写入同目录 `intake.template.json`，或在运行安装脚本时通过 `--answers` 传入。
- 在答案未确认前，不要运行 `install/install_openclaw_settings.py`。
