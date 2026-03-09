# ExMachina Runtime

这一层不再只是角色说明，而是给 OpenClaw 多 workspace 协作使用的运行时拓扑。
模式：lite
主控体：exmachina-main
协调模式：single-agent-inline-support
是否要求外部路由：否

## Lite 说明
- 只有 `exmachina-main` 会被默认使用。
- 主连结体与协作链以内联方式消费，不需要跨 agent handoff。
- `task-board.json` 是单会话推进任务的主入口。

## 关键文件
- `topology.json`：完整 agent 拓扑、路由、任务分配与激活步骤
- `shared/mission-context.json`：全局任务上下文与验收标准
- `shared/selection-trace.json`：主链与协作链选择依据
- `shared/knowledge-handoff.json`：知识交接与后续维护输入
- `shared/resource-arbitration.json`：资源仲裁与升级规则
- `task-board.json`：运行时任务板
- `agents/<agent_id>/`：每个 agent 的 spec / queue / routes / status / inbox / outbox

## Skill 绑定
- 知识连结体：`skills/knowledge-link-body/SKILL.md`
- 理性连结体：`skills/rationality-link-body/SKILL.md`
- 校验连结体：`skills/validation-link-body/SKILL.md`
- 文档连结体：`skills/documentation-link-body/SKILL.md`
- 安全连结体：`skills/security-link-body/SKILL.md`

## 启动步骤
- 由 exmachina-main 读取 `runtime/shared/mission-context.json` 与 `runtime/task-board.json`。
- exmachina-main 先装载主连结体 知识连结体，再按需内联参考协作链规则。
- 所有阶段结果在单会话内按任务板推进，不依赖跨 agent handoff。

## 协调规则
- Lite 模式不要求多 agent 绑定与路由，由 exmachina-main 单会话执行。
- 协作连结体保留为内联参考角色，不要求外部安装器创建额外 agent。
