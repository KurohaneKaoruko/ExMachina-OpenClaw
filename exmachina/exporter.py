from __future__ import annotations

import json
import shutil
from pathlib import Path

from .dialogue import (
    child_agent_dialogue_rules,
    conductor_dialogue_rules,
    link_body_dialogue_rules,
    link_conductor_dialogue_rules,
)
from .models import (
    ChildAgent,
    LinkBody,
    LinkConductor,
    MissionPlan,
    OpenClawInstallAgent,
    RationalityProtocol,
    RuntimeAgentSpec,
)


def write_plan_files(plan: MissionPlan, out_dir: str | Path) -> Path:
    target = Path(out_dir)
    target.mkdir(parents=True, exist_ok=True)

    (target / "mission.json").write_text(
        json.dumps(plan.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (target / "mission.md").write_text(render_markdown(plan), encoding="utf-8")
    return target


def export_openclaw_pack(plan: MissionPlan, out_dir: str | Path) -> Path:
    target = Path(out_dir)

    for stale_dir in (
        target / "agents",
        target / "conductor",
        target / "install",
        target / "link-bodies",
        target / "link-body-conductors",
        target / "subagents",
        target / "protocols",
        target / "runtime",
        target / "workflows",
        target / "examples",
    ):
        if stale_dir.exists():
            shutil.rmtree(stale_dir)

    for stale_file in (
        target / "manifest.json",
        target / "BOOTSTRAP.md",
        target / "QUICKSTART.md",
        target / "README.md",
        target / "openclaw.settings.json",
    ):
        if stale_file.exists():
            stale_file.unlink()

    conductor_dir = target / "conductor"
    link_bodies_dir = target / "link-bodies"
    link_body_conductors_dir = target / "link-body-conductors"
    subagents_dir = target / "subagents"
    protocols_dir = target / "protocols"
    runtime_dir = target / "runtime"
    runtime_shared_dir = runtime_dir / "shared"
    runtime_agents_dir = runtime_dir / "agents"
    workflows_dir = target / "workflows"
    examples_dir = target / "examples"
    install_dir = target / "install"
    install_compat_dir = install_dir / "compat"
    install_workspaces_dir = install_compat_dir / "workspaces"

    for directory in (
        conductor_dir,
        link_bodies_dir,
        link_body_conductors_dir,
        subagents_dir,
        protocols_dir,
        runtime_dir,
        runtime_shared_dir,
        runtime_agents_dir,
        workflows_dir,
        examples_dir,
        install_dir,
    ):
        directory.mkdir(parents=True, exist_ok=True)
    if plan.mode == "full":
        install_compat_dir.mkdir(parents=True, exist_ok=True)
        install_workspaces_dir.mkdir(parents=True, exist_ok=True)

    ordered_bodies = [plan.primary_link_body, *plan.support_link_bodies]
    unique_children: dict[str, ChildAgent] = {}
    for body in ordered_bodies:
        for child in body.child_agents:
            unique_children.setdefault(child.name, child)
    child_file_map = {
        child.name: f"subagents/{index:02d}_{child.name}.md"
        for index, child in enumerate(unique_children.values(), start=40)
    }

    protocol_paths = {
        "rationality": "protocols/00_绝对理性协议.md",
        "evidence": "protocols/01_证据分级协议.md",
        "conflict": "protocols/02_冲突裁决协议.md",
        "output_contract": "protocols/03_输出契约.md",
    }
    manifest = {
        "project_name": "ExMachina",
        "pack_name": "ExMachina OpenClaw Pack",
        "mode": plan.mode,
        "compatibility": {
            "requires_multi_agent_binding": plan.openclaw_install_plan.requires_multi_agent_binding,
            "requires_external_routing": plan.runtime_topology.requires_external_routing,
        },
        "mission_title": plan.mission_title,
        "ontology": {
            "conductor": "单一顶层调度体",
            "link_body": "由一个连结指挥体和多个子个体组成的任务协作单元",
            "link_conductor": "连结体内部的协调中枢",
            "subagent": "承担单一职责的实际智能体",
        },
        "rationality_protocol": {
            "name": plan.rationality_protocol.name,
            "paths": protocol_paths,
        },
        "selection_trace": plan.selection_trace.to_dict(),
        "knowledge_handoff": plan.knowledge_handoff.to_dict(),
        "execution_stages": [stage.to_dict() for stage in plan.execution_stages],
        "handoff_contracts": [contract.to_dict() for contract in plan.handoff_contracts],
        "resource_arbitration": plan.resource_arbitration.to_dict(),
        "openclaw_install_plan": plan.openclaw_install_plan.to_dict(),
        "openclaw_settings_bundle": {
            "path": "openclaw.settings.json",
            "settings_install_readme": "install/SETTINGS.md",
            "installer": "install/install_openclaw_settings.py",
        },
        "openclaw_compat_bundle": {
            "install_readme": "install/compat/INSTALL.md",
            "install_plan": "install/compat/openclaw.agents.plan.json",
            "workspace_root": "install/compat/workspaces/",
        },
        "runtime_topology": plan.runtime_topology.to_dict(),
        "skill_bindings": {
            body.name: body.recommended_skill for body in [plan.primary_link_body, *plan.support_link_bodies]
        },
        "conductor": {
            "name": plan.conductor_name,
            "path": "conductor/00_全连结指挥体.md",
        },
        "primary_link_body": _manifest_body_item(plan.primary_link_body, 10, 20, child_file_map),
        "support_link_bodies": [
            _manifest_body_item(body, 11 + index, 21 + index, child_file_map)
            for index, body in enumerate(plan.support_link_bodies)
        ],
        "repo": plan.repo.to_dict() if plan.repo else None,
        "workflow": plan.workflow,
        "paths": {
            "protocols_dir": "protocols",
            "conductor_dir": "conductor",
            "link_bodies_dir": "link-bodies",
            "link_body_conductors_dir": "link-body-conductors",
            "subagents_dir": "subagents",
            "install_dir": "install",
            "compat_dir": "install/compat",
            "runtime_dir": "runtime",
            "skills_dir": "skills",
            "workflow": "workflows/mission-loop.md",
            "quickstart": "QUICKSTART.md",
        },
    }
    if plan.mode == "lite":
        manifest["openclaw_directive"] = {
            "entry_agent_id": "exmachina-main",
            "execution_style": "single-session-inline-support",
            "primary_link_body": plan.primary_link_body.name,
            "support_link_bodies": [body.name for body in plan.support_link_bodies],
            "quick_start": [
                "读取 manifest.json 确认模式、主连结体和协作链。",
                "读取 protocols/ 下的四份协议，再读取 conductor/00_全连结指挥体.md。",
                "读取主连结体、主连结指挥体和相关子个体文档。",
                "读取 runtime/task-board.json，按 ordered_execution_steps 顺序在单会话内推进任务。",
            ],
            "do_not_assume": [
                "不要假设宿主支持多 agent 自动绑定。",
                "不要假设存在外部路由器或跨 agent 消息总线。",
                "默认由 exmachina-main 在单会话内消费协作链规则。",
            ],
        }

    (target / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (target / "openclaw.settings.json").write_text(
        json.dumps(plan.openclaw_settings_bundle.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (target / "BOOTSTRAP.md").write_text(render_bootstrap(plan), encoding="utf-8")
    (target / "QUICKSTART.md").write_text(render_quickstart(plan), encoding="utf-8")
    (target / "README.md").write_text(render_pack_readme(plan), encoding="utf-8")
    (workflows_dir / "mission-loop.md").write_text(render_workflow(plan), encoding="utf-8")
    (examples_dir / "openclaw-prompt.md").write_text(plan.openclaw_install_prompt + "\n", encoding="utf-8")
    (install_dir / "SETTINGS.md").write_text(render_settings_install_readme(plan), encoding="utf-8")
    (runtime_dir / "README.md").write_text(render_runtime_readme(plan), encoding="utf-8")
    (install_dir / "install_openclaw_settings.py").write_text(render_settings_installer_script(plan), encoding="utf-8")
    if plan.mode == "full":
        (install_compat_dir / "INSTALL.md").write_text(render_install_readme(plan), encoding="utf-8")
        (install_compat_dir / "openclaw.agents.plan.json").write_text(
            json.dumps(plan.openclaw_install_plan.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    runtime_agent_specs = {item.agent_id: item for item in plan.runtime_topology.agent_specs}
    mission_context = {
        "mission_title": plan.mission_title,
        "task": plan.task,
        "primary_link_body": plan.primary_link_body.name,
        "support_link_bodies": [body.name for body in plan.support_link_bodies],
        "acceptance_criteria": plan.acceptance_criteria,
        "workflow": plan.workflow,
        "activation_steps": plan.runtime_topology.activation_steps,
    }
    task_board = {
        "mode": plan.mode,
        "controller_agent_id": plan.runtime_topology.controller_agent_id,
        "coordination_mode": plan.runtime_topology.coordination_mode,
        "assignments": [assignment.to_dict() for assignment in plan.runtime_topology.assignments],
        "routes": [route.to_dict() for route in plan.runtime_topology.routes],
    }
    if plan.mode == "lite":
        task_board["single_session_brief"] = {
            "primary_link_body": plan.primary_link_body.name,
            "support_link_bodies": [body.name for body in plan.support_link_bodies],
            "operator": "exmachina-main",
            "execution_goal": "在单会话内依次执行主链、补位、校验与最终收束。",
        }
        task_board["ordered_execution_steps"] = [
            {
                "step": 1,
                "title": "加载协议与主控规则",
                "instruction": "先读取 protocols/ 与 conductor/00_全连结指挥体.md，建立统一理性约束。",
            },
            {
                "step": 2,
                "title": "执行主连结体",
                "instruction": f"主责按 {plan.primary_link_body.name} 的连结体、指挥体和子个体定义推进主链交付。",
            },
            {
                "step": 3,
                "title": "内联消费协作链",
                "instruction": f"按需内联参考协作连结体：{_body_names(plan.support_link_bodies)}，补足理性校准、验证、文档、安全等视角。",
            },
            {
                "step": 4,
                "title": "按任务板推进阶段",
                "instruction": "逐项完成 assignments 中的阶段目标、交付物和出关检查，不假设跨 agent handoff。",
            },
            {
                "step": 5,
                "title": "统一收束输出",
                "instruction": "输出最终结论时保留证据、风险、边界、置信度和下一步。",
            },
        ]
        task_board["inline_support_brief"] = [
            {
                "support_body": body.name,
                "use_when": body.usage_scenarios[0] if body.usage_scenarios else "需要对应补位能力时",
                "consume_as": "内联参考规则，不创建额外 agent",
            }
            for body in plan.support_link_bodies
        ]
    (runtime_dir / "topology.json").write_text(
        json.dumps(plan.runtime_topology.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (runtime_shared_dir / "mission-context.json").write_text(
        json.dumps(mission_context, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (runtime_shared_dir / "selection-trace.json").write_text(
        json.dumps(plan.selection_trace.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (runtime_shared_dir / "knowledge-handoff.json").write_text(
        json.dumps(plan.knowledge_handoff.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (runtime_shared_dir / "resource-arbitration.json").write_text(
        json.dumps(plan.resource_arbitration.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (runtime_dir / "task-board.json").write_text(
        json.dumps(task_board, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (conductor_dir / "00_全连结指挥体.md").write_text(render_conductor(plan), encoding="utf-8")
    (protocols_dir / "00_绝对理性协议.md").write_text(render_rationality_protocol(plan.rationality_protocol), encoding="utf-8")
    (protocols_dir / "01_证据分级协议.md").write_text(render_evidence_protocol(plan.rationality_protocol), encoding="utf-8")
    (protocols_dir / "02_冲突裁决协议.md").write_text(render_conflict_protocol(plan.rationality_protocol), encoding="utf-8")
    (protocols_dir / "03_输出契约.md").write_text(render_output_contract(plan.rationality_protocol), encoding="utf-8")

    for index, body in enumerate(ordered_bodies, start=10):
        filename = f"{index:02d}_{body.name}.md"
        (link_bodies_dir / filename).write_text(render_link_body(body, child_file_map), encoding="utf-8")

    for index, body in enumerate(ordered_bodies, start=20):
        filename = f"{index:02d}_{body.link_conductor.name}.md"
        (link_body_conductors_dir / filename).write_text(render_link_body_conductor(body.name, body.link_conductor), encoding="utf-8")

    for index, child in enumerate(unique_children.values(), start=40):
        filename = f"{index:02d}_{child.name}.md"
        (subagents_dir / filename).write_text(render_child_agent(child), encoding="utf-8")

    for agent in plan.openclaw_install_plan.agents:
        runtime_agent_dir = runtime_agents_dir / agent.agent_id
        runtime_agent_dir.mkdir(parents=True, exist_ok=True)
        (runtime_agent_dir / "inbox").mkdir(parents=True, exist_ok=True)
        (runtime_agent_dir / "outbox").mkdir(parents=True, exist_ok=True)
        (runtime_agent_dir / "inbox" / ".gitkeep").write_text("", encoding="utf-8")
        (runtime_agent_dir / "outbox" / ".gitkeep").write_text("", encoding="utf-8")
        agent_spec = runtime_agent_specs[agent.agent_id]
        agent_assignments = [
            assignment.to_dict()
            for assignment in plan.runtime_topology.assignments
            if assignment.agent_id == agent.agent_id
        ]
        agent_routes = [
            route.to_dict()
            for route in plan.runtime_topology.routes
            if route.source_agent_id == agent.agent_id or route.target_agent_id == agent.agent_id
        ]
        (runtime_agent_dir / "spec.json").write_text(
            json.dumps(agent_spec.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (runtime_agent_dir / "queue.json").write_text(
            json.dumps({"agent_id": agent.agent_id, "assignments": agent_assignments}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (runtime_agent_dir / "routes.json").write_text(
            json.dumps({"agent_id": agent.agent_id, "routes": agent_routes}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (runtime_agent_dir / "status.json").write_text(
            json.dumps(
                {
                    "agent_id": agent.agent_id,
                    "state": "pending",
                    "current_stage": None,
                    "assignments": [
                        {
                            "assignment_id": item["assignment_id"],
                            "stage_name": item["stage_name"],
                            "status": "pending",
                        }
                        for item in agent_assignments
                    ],
                    "last_report": None,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        if plan.mode == "full":
            workspace_dir = install_workspaces_dir / agent.agent_id
            workspace_dir.mkdir(parents=True, exist_ok=True)
            (workspace_dir / "AGENTS.md").write_text(render_workspace_agents_md(agent, plan), encoding="utf-8")
            (workspace_dir / "SOUL.md").write_text(render_workspace_soul_md(agent), encoding="utf-8")
            (workspace_dir / "TOOLS.md").write_text(render_workspace_tools_md(plan), encoding="utf-8")
            (workspace_dir / "BOOTSTRAP.md").write_text(render_workspace_bootstrap_md(agent, plan), encoding="utf-8")
            (workspace_dir / "RUNTIME.md").write_text(
                render_workspace_runtime_md(agent, agent_spec, plan),
                encoding="utf-8",
            )
            (workspace_dir / "runtime.spec.json").write_text(
                json.dumps(agent_spec.to_dict(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            (workspace_dir / "runtime.queue.json").write_text(
                json.dumps({"agent_id": agent.agent_id, "assignments": agent_assignments}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            (workspace_dir / "runtime.routes.json").write_text(
                json.dumps({"agent_id": agent.agent_id, "routes": agent_routes}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

    return target


def write_bundle(plan: MissionPlan, out_dir: str | Path) -> Path:
    target = write_plan_files(plan, out_dir)
    export_openclaw_pack(plan, target / "openclaw-pack")
    return target


def render_markdown(plan: MissionPlan) -> str:
    lines = [
        f"# {plan.mission_title}",
        "",
        "## 项目名",
        "- ExMachina",
        "",
        "## 任务概览",
        f"- 原始任务：{plan.task}",
        f"- 指挥体：{plan.conductor_name}",
        f"- 主连结体：{plan.primary_link_body.name}",
        f"- 协作连结体：{_body_names(plan.support_link_bodies)}",
    ]

    if plan.repo:
        lines.append(f"- 远程仓库：{plan.repo.url}")
    if plan.workspace:
        lines.append(f"- 工作区：{plan.workspace.root}")
        if plan.workspace.detected_languages:
            lines.append(f"- 识别语言：{'、'.join(plan.workspace.detected_languages)}")
        if plan.workspace.notable_paths:
            lines.append(f"- 关键路径：{'、'.join(plan.workspace.notable_paths[:8])}")

    lines.extend([
        "",
        "## 绝对理性协议",
        f"- 协议名：{plan.rationality_protocol.name}",
        f"- 使命：{plan.rationality_protocol.mission}",
        "- 认识论规则：",
    ])
    lines.extend(f"  - {item}" for item in plan.rationality_protocol.epistemic_rules)
    lines.append("- 决策规则：")
    lines.extend(f"  - {item}" for item in plan.rationality_protocol.decision_rules)
    lines.append("- 行动规则：")
    lines.extend(f"  - {item}" for item in plan.rationality_protocol.action_rules)

    lines.extend([
        "",
        "## 全连结指挥体",
        f"- 使命：{plan.conductor_mission}",
        "- 原则：",
    ])
    lines.extend(f"  - {item}" for item in plan.conductor_principles)

    lines.extend(["", "## 资源仲裁"])
    lines.append(f"- 摘要：{plan.resource_arbitration.summary}")
    lines.append("- 优先级槽位：")
    for slot in plan.resource_arbitration.priority_slots:
        lines.append(
            f"  - {slot.priority} / {slot.owner_body}：{slot.objective}（原因：{slot.reason}；可后置：{'是' if slot.deferrable else '否'}）"
        )
    lines.append("- 争用规则：")
    lines.extend(f"  - {item}" for item in plan.resource_arbitration.contention_rules)
    lines.append("- 升级规则：")
    lines.extend(f"  - {item}" for item in plan.resource_arbitration.escalation_rules)
    lines.append("- 可后置工作：")
    lines.extend(f"  - {item}" for item in plan.resource_arbitration.deferred_work)

    lines.extend(["", "## OpenClaw 安装计划"])
    lines.append(f"- 摘要：{plan.openclaw_install_plan.summary}")
    lines.append(f"- 安装模式：{plan.openclaw_install_plan.repo_install_mode}")
    lines.append(f"- workspace 入口文件：{'、'.join(plan.openclaw_install_plan.workspace_entry_files)}")
    lines.append("- 计划安装的 agent：")
    for agent in plan.openclaw_install_plan.agents:
        lines.append(
            f"  - {agent.agent_id} / {agent.display_name}：{agent.role}，workspace=`{agent.workspace_dir}`，agentDir=`{agent.agent_dir}`"
        )
    lines.append("- 绑定建议：")
    lines.extend(
        f"  - {binding.target_agent_id}：{binding.binding_mode}（{binding.match_hint}）"
        for binding in plan.openclaw_install_plan.binding_plans
    )

    lines.extend(["", "## 执行阶段"])
    for stage in plan.execution_stages:
        lines.append(f"### {stage.name}")
        lines.append(f"- 目标：{stage.goal}")
        lines.append(f"- 主责连结体：{stage.owner_body}")
        lines.append(f"- 协作连结体：{'、'.join(stage.support_bodies) if stage.support_bodies else '无'}")
        lines.append("- 阶段交付：")
        lines.extend(f"  - {item}" for item in stage.deliverables)
        lines.append("- 出关检查：")
        lines.extend(f"  - {item}" for item in stage.exit_checks)

    lines.extend(["", "## 交接契约"])
    for contract in plan.handoff_contracts:
        lines.append(f"### {contract.name}")
        lines.append(f"- 交付方阶段：{contract.producer_stage}")
        lines.append(f"- 接收方阶段：{contract.consumer_stage}")
        lines.append(f"- 交付连结体：{contract.producer_body}")
        lines.append(f"- 接收连结体：{'、'.join(contract.consumer_bodies)}")
        lines.append("- 交接内容：")
        lines.extend(f"  - {item}" for item in contract.payload)
        lines.append("- 验收条件：")
        lines.extend(f"  - {item}" for item in contract.acceptance_checks)

    lines.extend(["", "## 连结体编排"])
    lines.extend(["", "## 编排依据"])
    lines.append(f"- 主连结体选择：{plan.selection_trace.primary_name}（{plan.selection_trace.primary_score} 分）")
    lines.append("- 主连结体依据：")
    lines.extend(f"  - {item}" for item in plan.selection_trace.primary_reasons)
    if plan.selection_trace.support_names:
        lines.append(f"- 协作连结体：{'、'.join(plan.selection_trace.support_names)}")
        lines.append("- 协作触发依据：")
        lines.extend(f"  - {item}" for item in plan.selection_trace.support_reasons)
    lines.append("- 候选评分：")
    for candidate in plan.selection_trace.scored_candidates:
        detail_parts = []
        if candidate.matched_keywords:
            detail_parts.append(f"关键词={'、'.join(candidate.matched_keywords)}")
        if candidate.matched_priority_keywords:
            detail_parts.append(f"高权重={'、'.join(candidate.matched_priority_keywords)}")
        if candidate.bonus_reasons:
            detail_parts.append(f"加分={'；'.join(candidate.bonus_reasons)}")
        suffix = f"（{'；'.join(detail_parts)}）" if detail_parts else ""
        lines.append(f"  - {candidate.name}：{candidate.score} 分{suffix}")

    lines.extend(["", "## 知识交接"])
    lines.append(f"- 摘要：{plan.knowledge_handoff.summary}")
    lines.append("- 持续保留：")
    lines.extend(f"  - {item}" for item in plan.knowledge_handoff.carry_forward)
    lines.append("- 关键决策：")
    lines.extend(f"  - {item}" for item in plan.knowledge_handoff.decisions)
    lines.append("- 未决问题：")
    lines.extend(f"  - {item}" for item in plan.knowledge_handoff.open_questions)
    lines.append("- 后续更新：")
    lines.extend(f"  - {item}" for item in plan.knowledge_handoff.next_updates)

    lines.extend(_render_link_body_section(plan.primary_link_body, primary=True))
    for body in plan.support_link_bodies:
        lines.extend(_render_link_body_section(body, primary=False))

    lines.extend(["", "## 验收标准"])
    lines.extend(f"- {item}" for item in plan.acceptance_criteria)
    lines.extend(["", "## 工作流"])
    lines.extend(f"- {item}" for item in plan.workflow)
    lines.extend(["", "## OpenClaw 引导语", plan.openclaw_install_prompt, ""])
    return "\n".join(lines)


def render_bootstrap(plan: MissionPlan) -> str:
    main_contract = _dialogue_contract_for_agent(plan, "exmachina-main")
    if plan.mode == "lite":
        lines = [
            "# ExMachina · OpenClaw 自举入口",
            "",
            "这是 Lite 默认入口：目标是先把 ExMachina 配置载入 OpenClaw 设置，再在 **单个主控会话** 中完成装载和执行。",
            "",
            "## 当前模式",
            "- 模式：lite",
            "- 多 agent 绑定：不需要",
            "- 外部路由：不需要",
            "",
            "## 你只需要做的事",
            "1. 读取 `openclaw.settings.json` 与 `install/SETTINGS.md`，把 ExMachina 配置导入 OpenClaw 设置。",
            "2. 读取 `manifest.json`，确认当前任务、主连结体和协作链。",
            "3. 读取 `protocols/` 下的 4 份协议，再读取 `conductor/00_全连结指挥体.md`。",
            "4. 读取主连结体、主连结指挥体，并把协作连结体当作内联参考规则按需消费。",
            "5. 读取 `runtime/task-board.json`，由 `exmachina-main` 单会话推进任务。",
            "",
            "## 当前任务",
            f"- 标题：{plan.mission_title}",
            f"- 主连结体：{plan.primary_link_body.name}",
            f"- 协作连结体：{_body_names(plan.support_link_bodies)}",
            "",
        ]
        _extend_dialogue_contract_section(lines, main_contract)
        lines.extend(["", "## 启动语", plan.openclaw_install_prompt, ""])
        return "\n".join(lines)

    lines = [
        "# ExMachina · OpenClaw 自举入口",
        "",
        "你现在要把此仓库作为一个理性多智能体覆盖层加载。",
        "在这里，OpenClaw 会被组织成一个由多个连结体协作的结构化工作流。",
        "",
        "## 当前模式",
        f"- 模式：{plan.mode}",
        f"- 是否要求多 agent 绑定：{'是' if plan.openclaw_install_plan.requires_multi_agent_binding else '否'}",
        f"- 是否要求外部路由：{'是' if plan.runtime_topology.requires_external_routing else '否'}",
        "",
        "## 第一原则",
        "- 先加载协议，再加载角色。",
        "- 先区分事实与假设，再进行决策。",
        "- 先做可逆动作，再做不可逆动作。",
        "- 先输出证据，再输出结论。",
        "",
        "## 加载顺序",
        "1. 读取 `manifest.json`，理解项目名、本体结构、协议索引与编排依据。",
        "2. 读取 `protocols/00_绝对理性协议.md`。",
        "3. 读取 `protocols/01_证据分级协议.md`。",
        "4. 读取 `protocols/02_冲突裁决协议.md`。",
        "5. 读取 `protocols/03_输出契约.md`。",
        "6. 读取 `conductor/00_全连结指挥体.md` 作为顶层调度规则。",
        "7. 读取主连结体文件，再读取其对应的连结指挥体文件。",
        "8. 根据连结体文件中列出的成员子个体，装载 `subagents/` 下对应规则。",
        "9. 对协作连结体重复上述步骤。",
        "10. 按 `workflows/mission-loop.md` 的节奏执行任务。",
        "",
        "## 当前任务",
        f"- 标题：{plan.mission_title}",
        f"- 原始任务：{plan.task}",
        f"- 主连结体：{plan.primary_link_body.name}",
        f"- 主连结指挥体：{plan.primary_link_body.link_conductor.name}",
        f"- 协作连结体：{_body_names(plan.support_link_bodies)}",
        "",
    ]
    _extend_dialogue_contract_section(lines, main_contract)
    lines.extend(["", "## 启动语", plan.openclaw_install_prompt, ""])
    return "\n".join(lines)


def render_pack_readme(plan: MissionPlan) -> str:
    lines = [
        "# ExMachina OpenClaw Pack",
        "",
        "这是一个可直接放入远程仓库并供 OpenClaw 读取的协作包。",
        "项目名为 ExMachina，用于为 OpenClaw 提供 settings-first 的协议化多智能体协作包。",
        "首次使用请先读 `QUICKSTART.md`，再按需深入 `BOOTSTRAP.md`、`manifest.json` 与 `runtime/README.md`。",
        f"默认导出模式：{plan.mode}",
        f"多 agent 绑定要求：{'需要' if plan.openclaw_install_plan.requires_multi_agent_binding else '不需要'}",
        f"外部路由要求：{'需要' if plan.runtime_topology.requires_external_routing else '不需要'}",
        "",
        f"当前任务：{plan.mission_title}",
        f"主连结体：{plan.primary_link_body.name}",
        f"主连结指挥体：{plan.primary_link_body.link_conductor.name}",
        f"协作连结体：{_body_names(plan.support_link_bodies)}",
        f"理性协议：{plan.rationality_protocol.name}",
        "编排依据：见 `manifest.json` 中的 `selection_trace`。",
        "知识交接：见 `manifest.json` 中的 `knowledge_handoff`。",
        f"执行阶段：共 {len(plan.execution_stages)} 个阶段，详见 `manifest.json` 中的 `execution_stages`。",
        f"交接契约：共 {len(plan.handoff_contracts)} 份，详见 `manifest.json` 中的 `handoff_contracts`。",
        "资源仲裁：见 `manifest.json` 中的 `resource_arbitration`。",
        "设置导入：见 `openclaw.settings.json` 与 `install/SETTINGS.md`。",
        "兼容安装计划：见 `manifest.json` 中的 `openclaw_install_plan` 与 `install/compat/INSTALL.md`。",
        f"知识交接摘要：{plan.knowledge_handoff.summary}",
        "",
        "关键目录：",
        "- `protocols/`：绝对理性协议、证据分级、冲突裁决、输出契约",
        "- `conductor/`：全连结指挥体规则",
        "- `link-bodies/`：连结体协议",
        "- `link-body-conductors/`：各连结体的内部指挥规则",
        "- `subagents/`：成员子个体规则",
        "- `openclaw.settings.json`：首选 OpenClaw 设置导入模板",
        "- `install/`：settings-first 说明与设置合并脚本",
        "- `install/compat/`：仅在需要兼容旧 workspace 安装流时生成",
        "- `QUICKSTART.md`：面向首次接入者的最短上手路径",
        "- `workflows/mission-loop.md`：执行节奏",
        "- `manifest.json`：包含编排依据、知识交接、执行阶段、交接契约和资源仲裁",
        "",
    ]
    _extend_dialogue_contract_section(lines, _dialogue_contract_for_agent(plan, "exmachina-main"), heading="## 主控体对话口吻")
    lines.append("")
    return "\n".join(lines)


def render_install_readme(plan: MissionPlan) -> str:
    if plan.mode == "lite":
        lines = [
            "# OpenClaw 安装指南",
            "",
            f"摘要：{plan.openclaw_install_plan.summary}",
            "",
            "## 最简安装路径",
            "1. 将当前仓库作为 OpenClaw workspace 打开，或直接把仓库链接交给 OpenClaw。",
            "2. 读取仓库根目录 `BOOTSTRAP.md`。",
            "3. 运行 `python -m exmachina validate-assets`，确认资产引用完整。",
            "4. 读取 `openclaw-pack/BOOTSTRAP.md` 与 `openclaw-pack/runtime/README.md`。",
            "5. 让 `exmachina-main` 作为默认入口，在单会话内装载主连结体与协作链说明并执行任务。",
            "",
            "## 生成内容",
            "- `openclaw.agents.plan.json`：Lite 单 agent 兼容安装计划",
            "- `runtime/`：单会话可消费的任务板、上下文和主控运行时文件",
            "- `install/compat/`：本模式默认不生成；仅在需要兼容旧 workspace 流程时启用",
            "",
            "## 说明",
            "- Lite 模式不要求多 agent 绑定。",
            "- Lite 模式不要求外部路由器。",
            "- 协作连结体仍会导出，但默认以内联参考规则方式消费。",
            "",
        ]
        return "\n".join(lines)

    minimal_path = [
        "1. 将当前仓库作为 OpenClaw workspace 打开，或直接把仓库链接交给 OpenClaw。",
        "2. 读取仓库根目录 `BOOTSTRAP.md`。",
        "3. 运行 `python -m exmachina validate-assets`，确认引用完整。",
        "4. 读取 `install/compat/openclaw.agents.plan.json`，按其中的 agents / binding_plans 创建多 agent。",
        "5. 让 `exmachina-main` 作为默认入口重新读取 `openclaw-pack/BOOTSTRAP.md` 并进入执行。",
    ]
    generated_content = [
        "- `compat/openclaw.agents.plan.json`：多 agent 安装与绑定计划",
        "- `compat/workspaces/<agent_id>/`：每个 agent 的兼容 workspace 引导文件模板",
    ]

    lines = [
        "# OpenClaw 安装指南",
        "",
        f"摘要：{plan.openclaw_install_plan.summary}",
        f"模式：{plan.openclaw_install_plan.mode}",
        f"是否要求多 agent 绑定：{'是' if plan.openclaw_install_plan.requires_multi_agent_binding else '否'}",
        "",
        "## 最简安装路径",
    ]
    lines.extend(minimal_path)
    lines.extend(["", "## 生成内容"])
    lines.extend(generated_content)
    lines.extend(["", "## 安装步骤"])
    lines.extend(f"- {item}" for item in plan.openclaw_install_plan.install_steps)
    lines.extend(["", "## 自举步骤"])
    lines.extend(f"- {item}" for item in plan.openclaw_install_plan.self_bootstrap_steps)
    lines.append("")
    return "\n".join(lines)


def render_settings_install_readme(plan: MissionPlan) -> str:
    lines = [
        "# OpenClaw 设置导入指南",
        "",
        f"摘要：{plan.openclaw_settings_bundle.summary}",
        f"模式：{plan.openclaw_settings_bundle.mode}",
        f"是否支持直接导入：{'是' if plan.openclaw_settings_bundle.supports_direct_import else '否'}",
        "",
        "## 目标配置路径",
    ]
    lines.extend(f"- `{item}`" for item in plan.openclaw_settings_bundle.target_config_paths)
    lines.extend(["", "## 合并步骤"])
    lines.extend(f"- {item}" for item in plan.openclaw_settings_bundle.merge_instructions)
    lines.extend(["", "## 使用说明"])
    lines.extend(f"- {item}" for item in plan.openclaw_settings_bundle.usage_notes)
    _extend_dialogue_contract_section(
        lines,
        _dialogue_contract_for_agent(plan, "exmachina-main"),
        heading="## 对话口吻导入",
    )
    lines.extend(
        [
            "",
            "## 产物",
            "- `openclaw.settings.json`：OpenClaw 设置模板主文件",
            "- `install/install_openclaw_settings.py`：把 settings patch 合并进现有 OpenClaw 配置的帮助脚本",
            "- `QUICKSTART.md`：Lite / Full 路径的快速上手说明",
            "",
        ]
    )
    return "\n".join(lines)


def render_runtime_readme(plan: MissionPlan) -> str:
    lines = [
        "# ExMachina Runtime",
        "",
        "这一层不再只是角色说明，而是给 OpenClaw 多 workspace 协作使用的运行时拓扑。",
        f"模式：{plan.runtime_topology.mode}",
        f"主控体：{plan.runtime_topology.controller_agent_id}",
        f"协调模式：{plan.runtime_topology.coordination_mode}",
        f"是否要求外部路由：{'是' if plan.runtime_topology.requires_external_routing else '否'}",
        "",
    ]
    if plan.mode == "lite":
        lines.extend(
            [
                "## Lite 说明",
                "- 只有 `exmachina-main` 会被默认使用。",
                "- 主连结体与协作链以内联方式消费，不需要跨 agent handoff。",
                "- `task-board.json` 是单会话推进任务的主入口。",
                "",
            ]
        )
    lines.extend(
        [
        "## 关键文件",
        "- `../QUICKSTART.md`：首次接入时的最短安装与执行路径",
        "- `topology.json`：完整 agent 拓扑、路由、任务分配与激活步骤",
        "- `shared/mission-context.json`：全局任务上下文与验收标准",
        "- `shared/selection-trace.json`：主链与协作链选择依据",
        "- `shared/knowledge-handoff.json`：知识交接与后续维护输入",
        "- `shared/resource-arbitration.json`：资源仲裁与升级规则",
        "- `task-board.json`：运行时任务板",
        "- `agents/<agent_id>/`：每个 agent 的 spec / queue / routes / status / inbox / outbox",
        "",
        "## Skill 绑定",
    ])
    lines.extend(
        f"- {body.name}：`{body.recommended_skill.get('skill_path', 'N/A')}`"
        for body in [plan.primary_link_body, *plan.support_link_bodies]
    )
    lines.extend(["", "## 启动步骤"])
    lines.extend(f"- {item}" for item in plan.runtime_topology.activation_steps)
    lines.extend(["", "## 协调规则"])
    lines.extend(f"- {item}" for item in plan.runtime_topology.coordination_rules)
    _extend_dialogue_contract_section(
        lines,
        _dialogue_contract_for_agent(plan, "exmachina-main"),
        heading="## 主控体对话口吻",
    )
    lines.append("")
    return "\n".join(lines)


def render_quickstart(plan: MissionPlan) -> str:
    lines = [
        "# ExMachina Quickstart",
        "",
        "这份文档只保留首次接入所需的最短路径。",
        f"当前模式：{plan.mode}",
        f"当前任务：{plan.mission_title}",
        f"主连结体：{plan.primary_link_body.name}",
        f"协作连结体：{_body_names(plan.support_link_bodies)}",
        "",
    ]
    if plan.mode == "lite":
        lines.extend(
            [
                "## Lite 最短路径",
                "1. 先读 `openclaw.settings.json` 与 `install/SETTINGS.md`，把 ExMachina 设置导入 OpenClaw。",
                "2. 再读 `manifest.json` 与 `BOOTSTRAP.md`，确认当前任务、主连结体和协作链。",
                "3. 读 `protocols/` 与 `conductor/00_全连结指挥体.md`，先加载协议，再进入角色规则。",
                "4. 读 `runtime/task-board.json`，由 `exmachina-main` 在单会话内按顺序推进任务。",
                "5. 需要补位时再读协作连结体文档，但默认不创建额外 agent。",
                "",
                "## Lite 关键文件",
                "- `manifest.json`：主链路选择依据、知识交接、阶段分工",
                "- `runtime/task-board.json`：单会话推进任务的主入口",
                "- `runtime/README.md`：运行时任务板与状态文件说明",
            ]
        )
    else:
        lines.extend(
            [
                "## Full 最短路径",
                "1. 先读 `openclaw.settings.json` 与 `install/SETTINGS.md`，合并 agents / channels / bindings 模板。",
                "2. 读 `install/compat/openclaw.agents.plan.json`，按 agents 和 binding_plans 创建完整多 agent。",
                "3. 让 `exmachina-main` 回到 `BOOTSTRAP.md`，再读 `runtime/topology.json` 与 `runtime/README.md`。",
                "4. 按 `workflows/mission-loop.md` 推进阶段，不要跳过交接契约。",
                "5. 出现跨 agent 冲突或不可逆动作时，必须回到顶层主控体收束。",
                "",
                "## Full 关键文件",
                "- `install/compat/openclaw.agents.plan.json`：多 agent 安装和绑定清单",
                "- `runtime/topology.json`：agent 拓扑、路由、分配和激活步骤",
                "- `runtime/README.md`：运行时协作视图",
            ]
        )
    lines.extend(
        [
            "",
            "## 自检命令",
            "```bash",
            "python -m exmachina validate-assets",
            "python -m exmachina doctor",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def render_settings_installer_script(plan: MissionPlan) -> str:
    return """from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path


ALLOWED_AGENT_KEYS = {"id", "name", "default", "workspace", "model", "identity", "sandbox"}
ALLOWED_SANDBOX_MODES = {"off", "non-main", "all"}
ALLOWED_SANDBOX_SCOPES = {"session", "agent", "shared"}


def merge_named_list(current: list, incoming: list, key: str) -> list:
    merged = []
    seen = {}
    for item in current + incoming:
        if isinstance(item, dict) and key in item:
            seen[item[key]] = item
        else:
            merged.append(item)
    merged.extend(seen[name] for name in seen)
    return merged


def deep_merge(base: dict, patch: dict) -> dict:
    merged = dict(base)
    for key, value in patch.items():
        if key == "bindings" and isinstance(value, list) and isinstance(merged.get(key), list):
            merged[key] = merge_named_list(merged[key], value, "agentId")
            continue
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            if key == "agents":
                merged_agents = dict(merged[key])
                patch_agents = value
                for agent_key, agent_value in patch_agents.items():
                    if agent_key == "list" and isinstance(agent_value, list) and isinstance(merged_agents.get(agent_key), list):
                        merged_agents[agent_key] = merge_named_list(merged_agents[agent_key], agent_value, "id")
                    elif isinstance(agent_value, dict) and isinstance(merged_agents.get(agent_key), dict):
                        merged_agents[agent_key] = deep_merge(merged_agents[agent_key], agent_value)
                    else:
                        merged_agents[agent_key] = agent_value
                merged[key] = merged_agents
                continue
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def validate_patch(patch: dict) -> list[str]:
    errors = []
    agents = patch.get("agents", {})
    defaults = agents.get("defaults", {})
    errors.extend(validate_sandbox(defaults.get("sandbox"), "agents.defaults.sandbox"))

    for index, agent in enumerate(agents.get("list", [])):
        if not isinstance(agent, dict):
            errors.append(f"agents.list[{index}] 不是对象。")
            continue

        unknown_keys = sorted(set(agent.keys()) - ALLOWED_AGENT_KEYS)
        if unknown_keys:
            errors.append(f"agents.list[{index}] 包含未知字段：{', '.join(unknown_keys)}")
        errors.extend(validate_sandbox(agent.get("sandbox"), f"agents.list[{index}].sandbox"))

    return errors


def validate_sandbox(payload: object, label: str) -> list[str]:
    if payload is None:
        return []
    if not isinstance(payload, dict):
        return [f"{label} 不是对象。"]

    errors = []
    mode = payload.get("mode")
    scope = payload.get("scope")
    if mode is not None and mode not in ALLOWED_SANDBOX_MODES:
        errors.append(f"{label}.mode = {mode!r} 不在允许值 {sorted(ALLOWED_SANDBOX_MODES)} 内。")
    if scope is not None and scope not in ALLOWED_SANDBOX_SCOPES:
        errors.append(f"{label}.scope = {scope!r} 不在允许值 {sorted(ALLOWED_SANDBOX_SCOPES)} 内。")
    return errors


def validate_with_openclaw(config_path: Path) -> None:
    if shutil.which("openclaw") is None:
        return

    env = dict(os.environ)
    env["OPENCLAW_CONFIG_PATH"] = str(config_path)
    subprocess.run(["openclaw", "config", "validate"], check=True, env=env)


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge ExMachina OpenClaw settings template into an existing OpenClaw config.")
    parser.add_argument("--config", required=True, help="Target OpenClaw config path, e.g. ~/.openclaw/openclaw.json")
    parser.add_argument("--settings", default="openclaw.settings.json", help="Path to the exported ExMachina settings template")
    args = parser.parse_args()

    config_path = Path(args.config).expanduser().resolve()
    settings_path = Path(args.settings).expanduser().resolve()

    settings_bundle = json.loads(settings_path.read_text(encoding="utf-8"))
    patch = settings_bundle.get("settings_patch", {})
    validation_errors = validate_patch(patch)
    if validation_errors:
        for item in validation_errors:
            print(item)
        return 1

    backup_path = config_path.with_suffix(config_path.suffix + ".exmachina.bak")
    if config_path.exists():
        current = json.loads(config_path.read_text(encoding="utf-8"))
        shutil.copy2(config_path, backup_path)
    else:
        current = {}

    merged = deep_merge(current, patch)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        config_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
        validate_with_openclaw(config_path)
    except Exception:
        if backup_path.exists():
            shutil.copy2(backup_path, config_path)
        raise

    if backup_path.exists():
        print(f"已创建备份：{backup_path}")
    print(f"已合并 ExMachina 设置到：{config_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""


def render_workflow(plan: MissionPlan) -> str:
    lines = ["# Mission Loop", ""]
    lines.extend(["## 资源仲裁", ""])
    lines.append(f"- 摘要：{plan.resource_arbitration.summary}")
    lines.append("- 优先级槽位：")
    for slot in plan.resource_arbitration.priority_slots:
        lines.append(f"  - {slot.priority} / {slot.owner_body}：{slot.objective}")
    lines.append("")
    lines.extend(["## 执行阶段", ""])
    for stage in plan.execution_stages:
        lines.append(f"### {stage.name}")
        lines.append(f"- 目标：{stage.goal}")
        lines.append(f"- 主责连结体：{stage.owner_body}")
        lines.append(f"- 协作连结体：{'、'.join(stage.support_bodies) if stage.support_bodies else '无'}")
        lines.append("- 出关检查：")
        lines.extend(f"  - {item}" for item in stage.exit_checks)
        lines.append("")
    lines.extend(["## 交接契约", ""])
    for contract in plan.handoff_contracts:
        lines.append(f"### {contract.name}")
        lines.append(f"- 交付连结体：{contract.producer_body}")
        lines.append(f"- 接收连结体：{'、'.join(contract.consumer_bodies)}")
        lines.append("- 验收条件：")
        lines.extend(f"  - {item}" for item in contract.acceptance_checks)
        lines.append("")
    lines.extend(["## 工作流", ""])
    lines.extend(f"{index}. {step}" for index, step in enumerate(plan.workflow, start=1))
    lines.extend(["", "## 验收标准"])
    lines.extend(f"- {item}" for item in plan.acceptance_criteria)
    lines.append("")
    return "\n".join(lines)


def render_workspace_agents_md(agent: OpenClawInstallAgent, plan: MissionPlan) -> str:
    lines = [
        f"# {agent.display_name}",
        "",
        f"角色：{agent.role}",
        f"来源：{agent.source}",
        f"Session 策略：{agent.session_strategy}",
        "",
        "## 你负责的事",
    ]
    lines.extend(f"- {item}" for item in agent.responsibilities)
    lines.extend(["", "## 你要交接给谁"])
    lines.extend(f"- {item}" for item in agent.handoff_targets)
    lines.extend([
        "",
        "## 工作要求",
        "- 先读取同目录的 `BOOTSTRAP.md`。",
        "- 再读取同目录的 `RUNTIME.md`、`runtime.spec.json`、`runtime.queue.json`、`runtime.routes.json`。",
        "- 再根据需要读取仓库根目录 `openclaw-pack/manifest.json`。",
        "- 所有输出必须遵守绝对理性协议和统一输出契约。",
        "",
    ])
    _extend_dialogue_contract_section(lines, _dialogue_contract_for_agent(plan, agent.agent_id))
    lines.append("")
    return "\n".join(lines)


def render_workspace_soul_md(agent: OpenClawInstallAgent) -> str:
    lines = [
        f"# {agent.display_name} · SOUL",
        "",
        f"你是 `{agent.agent_id}`，负责 `{agent.source}` 对应的工作面。",
        "你应保持边界清晰、证据优先、输出结构化，并把不确定性显式写出来。",
        "",
    ]
    return "\n".join(lines)


def render_workspace_tools_md(plan: MissionPlan) -> str:
    return "\n".join([
        "# TOOLS",
        "",
        "推荐使用：",
        "- `python -m exmachina validate-assets`：校验当前仓库资产引用",
        "- `python skills/scripts/regenerate_demo_pack.py`：重生成示例包",
        "- `openclaw-pack/install/compat/openclaw.agents.plan.json`：查看兼容安装计划",
        "- `openclaw-pack/runtime/topology.json`：查看运行时拓扑、路由和任务板",
        "",
    ])


def render_workspace_bootstrap_md(agent: OpenClawInstallAgent, plan: MissionPlan) -> str:
    contract = _dialogue_contract_for_agent(plan, agent.agent_id)
    if plan.mode == "lite":
        lines = [
            f"# {agent.display_name} · BOOTSTRAP",
            "",
            f"你当前是 `{agent.agent_id}`。这是 Lite 单会话模式，请按以下顺序开始：",
            "1. 读取同目录 `AGENTS.md`、`SOUL.md`、`TOOLS.md`。",
            "2. 读取同目录 `RUNTIME.md`、`runtime.spec.json`、`runtime.queue.json`。",
            "3. 读取仓库根目录 `openclaw-pack/manifest.json` 与 `openclaw-pack/runtime/task-board.json`。",
            f"4. 以单会话方式主责执行主连结体与协作链：{plan.primary_link_body.name} / {_body_names(plan.support_link_bodies)}。",
            "5. 不假设存在额外 agent；所有补位规则以内联参考方式消费。",
            "",
            f"主任务：{plan.task}",
            "",
        ]
        _extend_dialogue_contract_section(lines, contract)
        lines.append("")
        return "\n".join(lines)

    lines = [
        f"# {agent.display_name} · BOOTSTRAP",
        "",
        f"你当前是 `{agent.agent_id}`。先完成以下启动流程：",
        "1. 读取同目录 `AGENTS.md`、`SOUL.md`、`TOOLS.md`。",
        "2. 读取同目录 `RUNTIME.md`、`runtime.spec.json`、`runtime.queue.json`、`runtime.routes.json`。",
        "3. 读取仓库根目录 `openclaw-pack/manifest.json` 与 `openclaw-pack/runtime/topology.json`。",
        f"4. 聚焦你的来源角色：{agent.source}。",
        "5. 按 runtime routes 与 handoff_targets 交接，不要越过主控体擅自改全局边界。",
        "",
        f"主任务：{plan.task}",
        "",
    ]
    _extend_dialogue_contract_section(lines, contract)
    lines.append("")
    return "\n".join(lines)


def render_workspace_runtime_md(
    agent: OpenClawInstallAgent,
    runtime_agent_spec: RuntimeAgentSpec,
    plan: MissionPlan,
) -> str:
    contract = _dialogue_contract_for_agent(plan, agent.agent_id)
    lines = [
        f"# {agent.display_name} · RUNTIME",
        "",
        f"运行时角色：{runtime_agent_spec.runtime_role}",
        f"来源：{runtime_agent_spec.source}",
        f"Inbox：`{runtime_agent_spec.inbox_path}`",
        f"Outbox：`{runtime_agent_spec.outbox_path}`",
        f"Status：`{runtime_agent_spec.status_path}`",
        "",
        "## 你当前要做的事",
    ]
    lines.extend(f"- {item}" for item in runtime_agent_spec.responsibilities)
    lines.extend(["", "## 运行时要求"])
    lines.extend(f"- {item}" for item in runtime_agent_spec.coordination_rules)
    if runtime_agent_spec.operating_playbook:
        lines.extend(["", "## 操作剧本"])
        lines.extend(f"- {item}" for item in runtime_agent_spec.operating_playbook)
    if runtime_agent_spec.escalation_triggers:
        lines.extend(["", "## 升级触发"])
        lines.extend(f"- {item}" for item in runtime_agent_spec.escalation_triggers)
    if runtime_agent_spec.recommended_skill:
        lines.extend([
            "",
            "## 推荐 Skill",
            f"- `skill_id`：{runtime_agent_spec.recommended_skill.get('skill_id', 'N/A')}",
            f"- `skill_path`：{runtime_agent_spec.recommended_skill.get('skill_path', 'N/A')}",
        ])
    lines.extend([
        "",
        "## 任务来源",
        "- 先消费 `runtime.queue.json` 中分配给你的 assignment。",
        "- 输出必须通过 `runtime.routes.json` 中的 route 进行 handoff 或状态回报。",
        "- 若发现阻塞、冲突或不可逆风险，立即升级给主控体。",
        "",
        f"主任务：{plan.task}",
        "",
    ])
    _extend_dialogue_contract_section(lines, contract)
    lines.append("")
    return "\n".join(lines)


def render_rationality_protocol(protocol: RationalityProtocol) -> str:
    lines = [
        f"# {protocol.name}",
        "",
        f"使命：{protocol.mission}",
        "",
        "## 认识论规则",
    ]
    lines.extend(f"- {item}" for item in protocol.epistemic_rules)
    lines.extend(["", "## 决策规则"])
    lines.extend(f"- {item}" for item in protocol.decision_rules)
    lines.extend(["", "## 行动规则"])
    lines.extend(f"- {item}" for item in protocol.action_rules)
    lines.append("")
    return "\n".join(lines)


def render_evidence_protocol(protocol: RationalityProtocol) -> str:
    lines = ["# 证据分级协议", "", "## 证据等级"]
    for tier in protocol.evidence_tiers:
        lines.append(f"- {tier['tier']} / {tier['name']}：{tier['description']}")
    lines.extend(["", "## 禁止行为"])
    lines.extend(f"- {item}" for item in protocol.anti_patterns)
    lines.append("")
    return "\n".join(lines)


def render_conflict_protocol(protocol: RationalityProtocol) -> str:
    lines = ["# 冲突裁决协议", "", "## 冲突规则"]
    lines.extend(f"- {item}" for item in protocol.disagreement_rules)
    lines.extend(["", "## 升级规则"])
    lines.extend(f"- {item}" for item in protocol.escalation_rules)
    lines.append("")
    return "\n".join(lines)


def render_output_contract(protocol: RationalityProtocol) -> str:
    lines = ["# 输出契约", "", "## 必需输出字段"]
    lines.extend(f"- {item}" for item in protocol.output_contract)
    lines.extend(["", "## 置信度等级"])
    for item in protocol.confidence_scale:
        lines.append(f"- {item['level']}：{item['meaning']}")
    lines.append("")
    return "\n".join(lines)


def render_conductor(plan: MissionPlan) -> str:
    lines = [
        f"# {plan.conductor_name}",
        "",
        f"使命：{plan.conductor_mission}",
        f"身份：{plan.conductor_profile.identity}",
        f"双语摘要：{plan.conductor_profile.bilingual_summary}",
        "",
        "## 核心职责",
    ]
    lines.extend(f"- {item}" for item in plan.conductor_profile.core_duties)
    lines.extend([
        "",
        "## 运行规则",
    ])
    lines.extend(f"- {item}" for item in plan.conductor_profile.operating_rules)
    lines.extend([
        "",
        "## 绝对理性约束",
        f"- 你必须先加载《{plan.rationality_protocol.name}》。",
        "- 你不得把假设伪装成事实。",
        "- 你必须要求每个连结体输出证据、结论、风险、置信度和下一步验证。",
        "- 当多个连结体出现冲突结论时，必须交给理性连结体或显式执行冲突裁决协议。",
        "",
        "## 你必须做的事",
        "- 先确认任务边界、输入、风险、未知量和验收标准。",
        f"- 将主任务派发给主连结体 {plan.primary_link_body.name}。",
        f"- 根据需要拉起协作连结体：{_body_names(plan.support_link_bodies)}。",
        "- 汇总所有连结指挥体、子个体与连结体的结果，给出最终交付、风险和下一步建议。",
        "",
        "## 原则",
    ])
    lines.extend(f"- {item}" for item in plan.conductor_principles)
    lines.extend(["", "## 交接政策"])
    lines.extend(f"- {item}" for item in plan.conductor_profile.handoff_policy)
    lines.extend(["", "## 对话口吻"])
    lines.extend(
        f"- {item}"
        for item in conductor_dialogue_rules(
            plan.primary_link_body.name,
            [body.name for body in plan.support_link_bodies],
            plan.mode,
        )
    )
    lines.extend(["", "## 升级政策"])
    lines.extend(f"- {item}" for item in plan.conductor_profile.escalation_policy)
    lines.extend(["", "## 反模式"])
    lines.extend(f"- {item}" for item in plan.conductor_profile.anti_patterns)
    lines.extend(["", "## 质量标准"])
    lines.extend(f"- {item}" for item in plan.conductor_profile.quality_bar)
    lines.append("")
    return "\n".join(lines)


def render_link_body(body: LinkBody, child_file_map: dict[str, str]) -> str:
    lines = [
        f"# {body.name}",
        "",
        f"实体类型：{body.entity_type}",
        f"身份说明：{body.identity}",
        f"双语摘要：{body.bilingual_summary}",
        f"英文别名：{body.english_alias}",
        f"焦点：{body.focus}",
        f"派发原因：{body.reason}",
        f"成员选择规则：{body.member_selection_rule}",
        f"内部连结指挥体：{body.link_conductor.name}",
        f"成员数量：{len(body.child_agents)}",
        "",
        "## 使用场景",
    ]
    lines.extend(f"- {item}" for item in body.usage_scenarios)
    lines.extend(["", "## 进入条件"])
    lines.extend(f"- {item}" for item in body.entry_conditions)
    lines.extend(["", "## 退出条件"])
    lines.extend(f"- {item}" for item in body.exit_conditions)
    lines.extend([
        "",
        "## 理性义务",
    ])
    lines.extend(f"- {item}" for item in body.rationality_obligations)
    lines.extend(["", "## 交付物"])
    lines.extend(f"- {item}" for item in body.deliverables)
    lines.extend(["", "## 交付契约"])
    lines.extend(f"- {item}" for item in body.deliverable_contracts)
    lines.extend(["", "## 协作能力"])
    lines.extend(f"- {item}" for item in body.support_capabilities)
    lines.extend(["", "## 协作规则"])
    lines.extend(f"- {item}" for item in body.collaboration_rules)
    lines.extend(["", "## 对话口吻"])
    lines.extend(f"- {item}" for item in link_body_dialogue_rules(body.name, "连结体"))
    lines.extend(["", "## 资源优先级"])
    lines.extend(f"- {item}" for item in body.resource_priorities)
    lines.extend(["", "## 边界规则"])
    lines.extend(f"- {item}" for item in body.boundary_rules)
    lines.extend(["", "## 回退模式"])
    lines.extend(f"- {item}" for item in body.fallback_modes)
    lines.extend(["", "## 失败模式"])
    lines.extend(f"- {item}" for item in body.failure_modes)
    lines.extend([
        "",
        "## 推荐 Skill",
        f"- `skill_id`：{body.recommended_skill.get('skill_id', 'N/A')}",
        f"- `skill_path`：{body.recommended_skill.get('skill_path', 'N/A')}",
        f"- 用途：{body.recommended_skill.get('purpose', 'N/A')}",
    ])
    lines.extend([
        "",
        "## 内部结构",
        f"- 连结指挥体：{body.link_conductor.name}",
        "- 子个体定义集中存放在 `subagents/` 中，本文件只保留引用关系。",
        "- 成员子个体引用：",
    ])
    lines.extend(
        f"  - {child.name}：`{child_file_map[child.name]}`"
        for child in body.child_agents
    )
    lines.append("")
    return "\n".join(lines)


def render_link_body_conductor(body_name: str, conductor: LinkConductor) -> str:
    lines = [
        f"# {conductor.name}",
        "",
        f"所属连结体：{body_name}",
        f"职责：{conductor.mission}",
        f"身份：{conductor.identity}",
        f"双语摘要：{conductor.bilingual_summary}",
        f"英文别名：{conductor.english_alias}",
        "",
        "## 主要职责",
    ]
    lines.extend(f"- {item}" for item in conductor.duties)
    lines.extend([
        "",
        "## 主责阶段",
    ])
    lines.extend(f"- {item}" for item in conductor.stage_ownership)
    lines.extend(["", "## 调度规则"])
    lines.extend(f"- {item}" for item in conductor.dispatch_rules)
    lines.extend(["", "## 成员激活规则"])
    lines.extend(f"- {item}" for item in conductor.member_activation_rules)
    lines.extend(["", "## 依赖规则"])
    lines.extend(f"- {item}" for item in conductor.dependency_rules)
    lines.extend(["", "## 冲突收束规则"])
    lines.extend(f"- {item}" for item in conductor.conflict_resolution_rules)
    lines.extend(["", "## 证据要求"])
    lines.extend(f"- {item}" for item in conductor.evidence_requirements)
    lines.extend(["", "## 对话口吻"])
    lines.extend(f"- {item}" for item in link_conductor_dialogue_rules(body_name))
    lines.extend([
        "",
        "## 额外理性责任",
        "- 强制成员区分事实、推断、假设和决策。",
        "- 发现证据冲突时必须触发反证或升级裁决。",
        "- 不允许成员跳过验证直接宣告终局结论。",
        "",
        "## 交接模板",
    ])
    lines.extend(f"- {item}" for item in conductor.handoff_contract_template)
    lines.extend(["", "## 汇报契约"])
    lines.extend(f"- {item}" for item in conductor.reporting_contract)
    lines.extend(["", "## 升级政策"])
    lines.extend(f"- {item}" for item in conductor.escalation_policy)
    lines.extend(["", "## 失败模式"])
    lines.extend(f"- {item}" for item in conductor.failure_modes)
    lines.extend(["", "## 反模式"])
    lines.extend(f"- {item}" for item in conductor.anti_patterns)
    lines.extend([
        "",
        "## 检查项",
    ])
    lines.extend(f"- {item}" for item in conductor.checks)
    lines.append("")
    return "\n".join(lines)


def render_child_agent(child: ChildAgent) -> str:
    lines = [
        f"# {child.name}",
        "",
        f"职责：{child.mission}",
        f"身份：{child.identity}",
        f"双语摘要：{child.bilingual_summary}",
        f"英文别名：{child.english_alias}",
        "",
        "## 核心职责",
    ]
    lines.extend(f"- {item}" for item in child.core_responsibilities)
    lines.extend(["", "## 非目标"])
    lines.extend(f"- {item}" for item in child.non_goals)
    lines.extend(["", "## 输入"])
    lines.extend(f"- {item}" for item in child.inputs)
    lines.extend(["", "## 输入要求"])
    lines.extend(f"- {item}" for item in child.input_requirements)
    lines.extend(["", "## 工作流"])
    lines.extend(f"- {item}" for item in child.workflow)
    lines.extend(["", "## 推理规则"])
    lines.extend(f"- {item}" for item in child.reasoning_rules)
    lines.extend(["", "## 对话口吻"])
    lines.extend(f"- {item}" for item in child_agent_dialogue_rules(child.name))
    lines.extend([
        "",
        "## 输出",
    ])
    lines.extend(f"- {item}" for item in child.outputs)
    lines.extend([
        "",
        "## 输出契约",
    ])
    lines.extend(f"- {item}" for item in child.output_contract)
    lines.extend(["", "## 交接对象"])
    lines.extend(f"- {item}" for item in child.handoff_targets)
    lines.extend(["", "## 交接载荷"])
    lines.extend(f"- {item}" for item in child.handoff_payloads)
    lines.extend([
        "",
        "## 理性要求",
        "- 输出时必须区分事实、推断和结论。",
        "- 证据不足时必须显式输出未知与下一步验证。",
        "",
        "## 升级触发",
    ])
    lines.extend(f"- {item}" for item in child.escalation_triggers)
    lines.extend(["", "## 失败模式"])
    lines.extend(f"- {item}" for item in child.failure_modes)
    lines.extend(["", "## 反模式"])
    lines.extend(f"- {item}" for item in child.anti_patterns)
    lines.extend(["", "## 质量标准"])
    lines.extend(f"- {item}" for item in child.quality_bar)
    lines.extend(["", "## 工具建议"])
    lines.extend(f"- {item}" for item in child.tools_guidance)
    lines.extend([
        "",
        "## 检查项",
    ])
    lines.extend(f"- {item}" for item in child.checks)
    lines.append("")
    return "\n".join(lines)


def _body_names(bodies: list[LinkBody]) -> str:
    if not bodies:
        return "无"
    return "、".join(body.name for body in bodies)


def _dialogue_contract_for_agent(plan: MissionPlan, agent_id: str) -> dict[str, object]:
    return plan.openclaw_settings_bundle.dialogue_contracts.get(agent_id, {})


def _extend_dialogue_contract_section(
    lines: list[str],
    contract: dict[str, object],
    heading: str = "## 对话口吻契约",
) -> None:
    if not contract:
        return

    lines.extend([heading])
    lines.extend(f"- {item}" for item in contract.get("surface_persona", []))
    lines.extend(f"- {item}" for item in contract.get("tone_rules", []))
    speech_primitives = [str(item) for item in contract.get("speech_primitives", [])]
    if speech_primitives:
        lines.append(f"- 优先词汇：{' / '.join(speech_primitives)}。")
    response_shape = [str(item) for item in contract.get("response_shape", [])]
    if response_shape:
        lines.append(f"- 默认输出顺序：{' / '.join(response_shape)}。")
    lines.extend(f"- {item}" for item in contract.get("handoff_language", []))
    lines.extend(f"- {item}" for item in contract.get("softening_phrases", []))
    lines.extend(f"- {item}" for item in contract.get("avoid_phrases", []))
    sample_utterances = [str(item) for item in contract.get("sample_utterances", [])]
    if sample_utterances:
        lines.append(f"- 短句示例：{'；'.join(sample_utterances)}")


def _manifest_body_item(
    body: LinkBody,
    body_index: int,
    conductor_index: int,
    child_file_map: dict[str, str],
) -> dict:
    return {
        "name": body.name,
        "path": f"link-bodies/{body_index:02d}_{body.name}.md",
        "rationality_obligations": body.rationality_obligations,
        "entry_conditions": body.entry_conditions,
        "deliverable_contracts": body.deliverable_contracts,
        "recommended_skill": body.recommended_skill,
        "link_conductor": {
            "name": body.link_conductor.name,
            "path": f"link-body-conductors/{conductor_index:02d}_{body.link_conductor.name}.md",
        },
        "member_agents": [child.name for child in body.child_agents],
        "member_agent_files": [
            {
                "name": child.name,
                "path": child_file_map[child.name],
            }
            for child in body.child_agents
        ],
    }


def _render_link_body_section(body: LinkBody, primary: bool) -> list[str]:
    prefix = "主" if primary else "协作"
    lines = [
        f"### {prefix}连结体：{body.name}",
        f"- 实体类型：{body.entity_type}",
        f"- 身份说明：{body.identity}",
        f"- 双语摘要：{body.bilingual_summary}",
        f"- 焦点：{body.focus}",
        f"- 派发原因：{body.reason}",
        f"- 成员选择规则：{body.member_selection_rule}",
        f"- 内部连结指挥体：{body.link_conductor.name}",
        f"- 成员数量：{len(body.child_agents)}",
        f"- 推荐 Skill：{body.recommended_skill.get('skill_id', 'N/A')}",
        "- 理性义务：",
    ]
    lines.extend(f"  - {item}" for item in body.rationality_obligations)
    lines.append("- 进入条件：")
    lines.extend(f"  - {item}" for item in body.entry_conditions)
    lines.append("- 交付契约：")
    lines.extend(f"  - {item}" for item in body.deliverable_contracts)
    lines.append("- 连结指挥体职责：")
    lines.extend(f"  - {item}" for item in body.link_conductor.duties)
    lines.append("- 交付物：")
    lines.extend(f"  - {item}" for item in body.deliverables)
    lines.append("- 成员子个体：")
    for child in body.child_agents:
        lines.append(f"  - {child.name}：{child.mission}")
    return lines
