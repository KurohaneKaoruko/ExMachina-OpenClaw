# OpenClaw 安装问询

在导入任何 OpenClaw 配置前，必须先向用户问清以下内容，并记录答案。

## 必须先问清
1. 语言：这次安装与后续默认输出使用什么语言？
   默认值：`zh-CN`
2. 全连结指挥体 / 主控体显示名：希望把顶层主控体显示成哪个名字？
   默认值：`ExMachina 主控体`
3. 宿主多 agent 能力：宿主是否支持多 agent 绑定与外部路由？
   默认值：`是`
4. 安装模式：选择 `lite`（不在 OpenClaw 中创建子个体 agent，子个体职责由连结体内联执行）或 `full`（在 OpenClaw 中创建全部子个体 agent）。
   默认值：`full`
5. 人格设定：是否需要自定义 ExMachina 的人格设定？
   默认值：`否`
   说明：如果选择 `是`，则会要求用户输入自定义人格设定的文字说明。

## 可选补充项
1. 其它配置：是否还需要记录渠道绑定、token、workspace 或风格配置？

## 阻断规则
- 在语言、全连结指挥体显示名、配置路径、workspace 路径、多 agent 能力与安装模式未确认前，不得导入任何 settings patch。
- 如果宿主不支持多 agent 绑定与路由，则不得导入本模板。
- ExMachina 创建的 agent 必须继承 OpenClaw 当前默认模型，不得覆写默认模型、provider、API 或其它无关配置。

## 记录方式
- 把答案写入同目录 `intake.template.json`。
- 可配合仓库根目录的 `install.sh` 进行手动导入，或由用户手工合并配置。
