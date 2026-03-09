---
name: security-link-body
description: Use when the task is primarily owned by 安全连结体 and needs its role-specific workflow, boundaries, and handoff expectations.
---

# 安全连结体 Skill

English summary: Use this skill when the task is primarily about 威胁建模、权限审计、加固建议与合规收束.

## When to use

- 当任务主要命中 安全连结体 对应工作面时。
- 当你需要围绕 威胁建模、权限审计、加固建议与合规收束 组织主链路或协作补位时。
- 当你需要按该连结体的阶段、交接和升级契约稳定推进任务时。

## Boundaries

- 只处理 安全连结体 负责的工作面，不替其他连结体做最终裁决。
- 发现跨域依赖、证据冲突或不可逆风险时，立即升级给主控体或理性链路。
- 所有输出都必须写清事实、判断、风险、边界和下一步。

## Workflow

1. 读取当前阶段目标、边界、交接契约和 runtime queue。
2. 激活最能支撑 威胁建模、权限审计、加固建议与合规收束 的关键子个体。
3. 把局部产出收束为结构化阶段结论，并与上游/下游契约对齐。
4. 如遇证据冲突、越权请求或不可逆风险，立即升级。
5. 将结果通过 runtime routes 与 handoff_targets 交接给下游。

## Handoff Template

- 当前阶段目标与完成度
- 核心交付物摘要
- 风险、边界与剩余未知
- 建议下游动作与接收对象

## Quality Bar

- 交付物可直接被下游消费。
- 关键结论有证据、边界和风险说明。
- 不把补位输入误当成最终全局裁决。
