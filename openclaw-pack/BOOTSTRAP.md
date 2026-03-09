# ExMachina · OpenClaw 自举入口

这是 Lite 默认入口：目标是在 **单个主控会话** 中完成装载和执行。

## 当前模式
- 模式：lite
- 多 agent 绑定：不需要
- 外部路由：不需要

## 你只需要做的事
1. 读取 `manifest.json`，确认当前任务、主连结体和协作链。
2. 读取 `protocols/` 下的 4 份协议，再读取 `conductor/00_全连结指挥体.md`。
3. 读取主连结体、主连结指挥体，并把协作连结体当作内联参考规则按需消费。
4. 读取 `runtime/README.md` 与 `runtime/task-board.json`，由 `exmachina-main` 单会话推进任务。

## 当前任务
- 标题：沉淀知识交接、术语索引、资源仲裁规则与 README 示例，形成 OpenClaw 协作层
- 主连结体：知识连结体
- 协作连结体：理性连结体、校验连结体、文档连结体、安全连结体

## 启动语
请读取本项目的 /openclaw-pack/BOOTSTRAP.md，以 Lite 默认路径装载协议、主连结体与协作链说明，由单个主控会话内联完成执行，然后执行任务：沉淀知识交接、术语索引、资源仲裁规则与 README 示例，形成 OpenClaw 协作层。
