# OpenClaw 安装问询

在导入任何 OpenClaw 配置前，必须先向用户问清以下内容，并记录答案。

## 必须先问清
1. 语言：这次安装与后续默认输出使用什么语言？
   默认值：`zh-CN`
2. 全连结指挥体 / 主控体显示名：希望把顶层主控体显示成哪个名字？
   默认值：`ExMachina 主控体`
3. 配置文件路径：本次要写入哪份 OpenClaw 配置文件？
   默认值：`~/.openclaw/openclaw.json`
4. workspace 路径：把 workspace 指到哪个仓库或导出包路径？
   默认值：`{{EXMACHINA_PACK_ROOT}}`
5. 宿主子代理能力：宿主是否支持子代理（subagents / sessions_spawn）？
   默认值：`是`
6. 安装模式：选择 `lite`（不在 OpenClaw 中创建子个体 agent，子个体职责由连结体内联执行）或 `full`（在 OpenClaw 中创建全部子个体 agent）。
   默认值：`full`

## 可选补充项
1. 其它配置：是否还需要记录渠道绑定、token、workspace 或风格配置？

## 阻断规则
- 在语言、全连结指挥体显示名、配置路径、workspace 路径、子代理能力与安装模式未确认前，不得导入任何 settings patch。
- 如果宿主不支持子代理（subagents / sessions_spawn），则不得导入本模板。
- ExMachina 创建的 agent 必须继承 OpenClaw 当前默认模型，不得覆写默认模型、provider、API 或其它无关配置。

## 记录方式
- 把答案写入同目录 `intake.template.json`。
- 推荐使用 `install/apply-openclaw-settings.js` 合并配置，仓库根目录的 `install.sh` / `install.ps1` / `install.cmd` 已内置调用。
