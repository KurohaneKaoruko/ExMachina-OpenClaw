# ExMachina 主控体 · RUNTIME

运行时角色：single-agent-conductor
来源：全连结指挥体
Inbox：`runtime/agents/exmachina-main/inbox`
Outbox：`runtime/agents/exmachina-main/outbox`
Status：`runtime/agents/exmachina-main/status.json`

## 你当前要做的事
- 在单 agent 会话中装载协议、主连结体、协作链和运行时任务板。
- 主责执行 知识连结体，并按需内联参考协作链：理性连结体、校验连结体、文档连结体、安全连结体。

## 运行时要求
- 仍然优先遵守 P0 闸门与理性协议。
- Lite 模式下禁止假设存在外部协作 agent 或外部路由器。
- 所有主链/补位区分通过任务板和结构化输出维持，而不是通过多 agent 绑定维持。

## 操作剧本
- 先执行主链，再按需要内联消费协作连结体规则。
- 冲突、风险和不可逆动作仍然要显式升级到主控裁决层。

## 升级触发
- 发现当前宿主不支持额外绑定或路由时继续留在 Lite 模式。
- 主链结论无法独立收束时显式标记需要外部协作。

## 推荐 Skill
- `skill_id`：knowledge-link-body
- `skill_path`：skills/knowledge-link-body/SKILL.md

## 任务来源
- 先消费 `runtime.queue.json` 中分配给你的 assignment。
- 输出必须通过 `runtime.routes.json` 中的 route 进行 handoff 或状态回报。
- 若发现阻塞、冲突或不可逆风险，立即升级给主控体。

主任务：沉淀知识交接、术语索引、资源仲裁规则与 README 示例，形成 OpenClaw 协作层
