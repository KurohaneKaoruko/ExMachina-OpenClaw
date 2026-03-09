# OpenClaw 安装问询

在导入任何 OpenClaw 配置前，必须先向用户问清以下内容，并记录答案。

## 必须先问清
1. 语言：这次安装与后续默认输出使用什么语言？
   默认值：`zh-CN`
2. 全连结指挥体 / 主控体显示名：希望把顶层主控体显示成哪个名字？
   默认值：`ExMachina 主控体`
3. 安装模式：这次安装走 `lite` 还是 `full`？
   默认值：`lite`
4. OpenClaw 配置文件路径：本次要写入哪份 OpenClaw 配置？
   默认值：`~/.openclaw/openclaw.json`
5. workspace 路径：把 workspace 指向哪个仓库或导出包路径？

## 可选补充项
1. 宿主多 agent 能力：宿主是否支持多 agent 绑定与外部路由？
2. 其它配置：是否还需要记录渠道绑定、token、workspace 或风格配置？

## 阻断规则
- 在语言、全连结指挥体显示名、安装模式、配置路径和 workspace 路径未确认前，不得导入任何 settings patch。
- 如果用户选择 `full`，但宿主不支持多 agent 绑定与路由，则必须退回 `lite`。
- 如果用户选择的模式与当前导出包不一致，先重生成对应模式的 pack，再继续安装。
- ExMachina 创建的 agent 必须继承 OpenClaw 当前默认模型，不得覆写默认模型、provider、API 或其它无关配置。

## 记录方式
- 把答案写入同目录 `intake.template.json`。
- 如果后续执行 `openclaw-pack/install/install_openclaw_settings.py`，可通过 `--answers` 传入该文件。
