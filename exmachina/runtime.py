from __future__ import annotations

from .models import (
    ExecutionStage,
    HandoffContract,
    KnowledgeHandoff,
    LinkBody,
    OpenClawInstallPlan,
    ResourceArbitration,
    RuntimeAgentSpec,
    RuntimeAssignment,
    RuntimeRoute,
    RuntimeSharedArtifact,
    RuntimeTopology,
    SelectionTrace,
)


RUNTIME_ROOT = "runtime"
RUNTIME_SHARED_ROOT = f"{RUNTIME_ROOT}/shared"
RUNTIME_AGENTS_ROOT = f"{RUNTIME_ROOT}/agents"
CONTROLLER_AGENT_ID = "exmachina-main"
PRIMARY_AGENT_ID = "exmachina-primary"


def build_runtime_topology(
    mode: str,
    mission_title: str,
    task: str,
    selection_trace: SelectionTrace,
    knowledge_handoff: KnowledgeHandoff,
    execution_stages: list[ExecutionStage],
    handoff_contracts: list[HandoffContract],
    resource_arbitration: ResourceArbitration,
    openclaw_install_plan: OpenClawInstallPlan,
    primary_body: LinkBody,
    support_bodies: list[LinkBody],
) -> RuntimeTopology:
    if mode == "lite":
        return _build_lite_runtime_topology(
            task=task,
            execution_stages=execution_stages,
            resource_arbitration=resource_arbitration,
            primary_body=primary_body,
            support_bodies=support_bodies,
        )

    body_agent_map = _build_body_agent_map(primary_body, support_bodies)
    body_map = {primary_body.name: primary_body, **{body.name: body for body in support_bodies}}
    shared_artifacts = _build_shared_artifacts(openclaw_install_plan)

    routes: list[RuntimeRoute] = []
    dispatch_route_ids: list[str] = []
    stage_support_route_map: dict[tuple[str, str], list[str]] = {}
    stage_handoff_route_map: dict[str, list[str]] = {}
    report_route_map: dict[str, list[str]] = {}
    route_index = 0

    for agent in openclaw_install_plan.agents:
        if agent.agent_id == CONTROLLER_AGENT_ID:
            continue

        route_index += 1
        route_id = f"route-{route_index:02d}-dispatch"
        routes.append(
            RuntimeRoute(
                route_id=route_id,
                source_agent_id=CONTROLLER_AGENT_ID,
                target_agent_id=agent.agent_id,
                contract_name="任务激活派发",
                delivery_mode="dispatch",
                payload=[
                    "任务边界说明",
                    "当前阶段目标",
                    "需遵守的理性协议与资源闸门",
                ],
                acceptance_checks=[
                    "目标 agent 已确认收到任务激活信号。",
                    "目标 agent 已装载本地 runtime 规格与任务队列。",
                ],
                escalation_triggers=["目标 agent 无法确认其输入、边界或职责。"],
                guidance=["收到 dispatch 后先读取 runtime.spec.json 与 runtime.queue.json。"],
            )
        )
        dispatch_route_ids.append(route_id)

    for stage in execution_stages:
        owner_agent_id = body_agent_map.get(stage.owner_body, CONTROLLER_AGENT_ID)
        owner_body = body_map.get(stage.owner_body, primary_body)
        for support_body in stage.support_bodies:
            support_agent_id = body_agent_map.get(support_body, CONTROLLER_AGENT_ID)
            support_profile = body_map.get(support_body, primary_body)
            route_index += 1
            route_id = f"route-{route_index:02d}-support"
            routes.append(
                RuntimeRoute(
                    route_id=route_id,
                    source_agent_id=support_agent_id,
                    target_agent_id=owner_agent_id,
                    contract_name=f"{stage.name} 协作输入",
                    delivery_mode="support-input",
                    payload=[
                        f"{support_body} 视角的补位观察",
                        "风险与反证摘要",
                        "可直接交给主责链路消费的局部结论",
                        *support_profile.deliverable_contracts[:2],
                    ],
                    acceptance_checks=[
                        f"{stage.owner_body} 已确认接收协作输入。",
                        "协作输入已和阶段目标、验收条件对齐。",
                        *owner_body.entry_conditions[:1],
                    ],
                    escalation_triggers=list(support_profile.link_conductor.escalation_policy[:2]),
                    guidance=list(support_profile.collaboration_rules[:2]),
                )
            )
            stage_support_route_map.setdefault((stage.name, support_agent_id), []).append(route_id)

    for contract in handoff_contracts:
        producer_agent_id = body_agent_map.get(contract.producer_body, CONTROLLER_AGENT_ID)
        for consumer_body in contract.consumer_bodies:
            consumer_agent_id = body_agent_map.get(consumer_body, CONTROLLER_AGENT_ID)
            producer_profile = body_map.get(contract.producer_body, primary_body)
            consumer_profile = body_map.get(consumer_body, primary_body)
            route_index += 1
            route_id = f"route-{route_index:02d}-handoff"
            routes.append(
                RuntimeRoute(
                    route_id=route_id,
                    source_agent_id=producer_agent_id,
                    target_agent_id=consumer_agent_id,
                    contract_name=contract.name,
                    delivery_mode="stage-handoff",
                    payload=[*list(contract.payload), *producer_profile.deliverable_contracts[:2]],
                    acceptance_checks=[*list(contract.acceptance_checks), *consumer_profile.entry_conditions[:1]],
                    escalation_triggers=list(producer_profile.link_conductor.escalation_policy[:2]),
                    guidance=list(producer_profile.link_conductor.handoff_contract_template[:2]),
                )
            )
            stage_handoff_route_map.setdefault(contract.producer_stage, []).append(route_id)

    for agent in openclaw_install_plan.agents:
        if agent.agent_id == CONTROLLER_AGENT_ID:
            continue

        route_index += 1
        route_id = f"route-{route_index:02d}-report"
        routes.append(
            RuntimeRoute(
                route_id=route_id,
                source_agent_id=agent.agent_id,
                target_agent_id=CONTROLLER_AGENT_ID,
                contract_name="阶段状态与最终汇总回报",
                delivery_mode="status-report",
                payload=[
                    "当前阶段状态",
                    "关键证据与风险",
                    "是否需要升级裁决",
                ],
                acceptance_checks=[
                    "主控体已收到最新状态。",
                    "需要升级的问题已进入主控裁决路径。",
                ],
                escalation_triggers=["当前阶段无法继续推进。", "发现高风险不可逆动作。"],
                guidance=["状态回报必须引用当前 assignment_id 和关键证据。"],
            )
        )
        report_route_map.setdefault(agent.agent_id, []).append(route_id)

    assignments = _build_runtime_assignments(
        task=task,
        execution_stages=execution_stages,
        openclaw_install_plan=openclaw_install_plan,
        body_map=body_map,
        body_agent_map=body_agent_map,
        dispatch_route_ids=dispatch_route_ids,
        stage_support_route_map=stage_support_route_map,
        stage_handoff_route_map=stage_handoff_route_map,
        report_route_map=report_route_map,
    )
    agent_specs = _build_runtime_agent_specs(openclaw_install_plan, assignments, resource_arbitration, body_map)
    coordination_rules = [
        "运行时采用文件化 workspace 协作：每个 agent 读取本地 runtime 规格与队列，再通过 inbox/outbox/status 文件交接。",
        "主控体负责激活任务、跟踪阶段状态、处理升级裁决，并回收所有阶段产物。",
        "主连结体负责主链路交付；协作连结体只做补位、校验、审计、文档或知识沉淀，不擅自改全局边界。",
        *resource_arbitration.contention_rules,
    ]
    activation_steps = [
        f"主控体读取 `{RUNTIME_SHARED_ROOT}/mission-context.json` 与 `{RUNTIME_ROOT}/topology.json`。",
        "各 agent workspace 先读取本地 `runtime.spec.json`、`runtime.queue.json`、`runtime.routes.json`。",
        "主控体按 dispatch 路由激活主连结体与协作连结体。",
        "各 agent 将阶段结果写入 outbox，并通过 stage-handoff / support-input / status-report 路由交接。",
        "主控体根据状态回报、资源仲裁与知识交接收束最终交付。",
    ]

    return RuntimeTopology(
        mode=mode,
        controller_agent_id=CONTROLLER_AGENT_ID,
        coordination_mode="workspace-file-runtime",
        requires_external_routing=True,
        shared_artifacts=shared_artifacts,
        agent_specs=agent_specs,
        assignments=assignments,
        routes=routes,
        coordination_rules=coordination_rules,
        activation_steps=activation_steps,
    )


def _build_lite_runtime_topology(
    task: str,
    execution_stages: list[ExecutionStage],
    resource_arbitration: ResourceArbitration,
    primary_body: LinkBody,
    support_bodies: list[LinkBody],
) -> RuntimeTopology:
    inline_support_names = [body.name for body in support_bodies]
    shared_artifacts = [
        RuntimeSharedArtifact(
            name="mission-context",
            path=f"{RUNTIME_SHARED_ROOT}/mission-context.json",
            description="Lite 模式下的任务上下文、主链与协作链摘要。",
            consumers=[CONTROLLER_AGENT_ID],
        ),
        RuntimeSharedArtifact(
            name="task-board",
            path=f"{RUNTIME_ROOT}/task-board.json",
            description="Lite 模式下由单 agent 消费的阶段任务板。",
            consumers=[CONTROLLER_AGENT_ID],
        ),
    ]

    assignments = [
        RuntimeAssignment(
            assignment_id="assignment-lite-controller",
            stage_name="全局协调",
            agent_id=CONTROLLER_AGENT_ID,
            source_body="全连结指挥体",
            role="controller",
            goal=f"围绕任务「{task}」在单 agent 会话内协调主链、补位、升级与最终收束。",
            deliverables=["任务边界与验收标准", "Lite 任务板", "最终结构化交付"],
            exit_checks=["主链与协作链职责已在单会话内对齐。", "最终结论、风险与下一步已统一输出。"],
            depends_on=[],
            handoff_routes=[],
            guidance=[
                f"默认由 exmachina-main 同时承担主连结体 {primary_body.name} 和协作链 {('、'.join(inline_support_names) if inline_support_names else '无')} 的协调工作。",
                "不依赖外部多 agent 绑定、跨 agent 路由或状态回流机制。",
            ],
            quality_bar=["仍需保留证据、风险、边界和下一步。", "仍需区分主链交付与协作补位。"],
        )
    ]

    for stage_index, stage in enumerate(execution_stages, start=1):
        assignments.append(
            RuntimeAssignment(
                assignment_id=f"assignment-lite-stage-{stage_index:02d}",
                stage_name=stage.name,
                agent_id=CONTROLLER_AGENT_ID,
                source_body=stage.owner_body,
                role="owner",
                goal=stage.goal,
                deliverables=list(stage.deliverables),
                exit_checks=list(stage.exit_checks),
                depends_on=[] if stage_index == 1 else [execution_stages[stage_index - 2].name],
                handoff_routes=[],
                guidance=[
                    f"以单会话方式内联模拟 {stage.owner_body} 的主责工作。",
                    f"如需补位，内联参考：{('、'.join(stage.support_bodies) if stage.support_bodies else '无协作连结体')}。",
                ],
                quality_bar=list(primary_body.deliverable_contracts[:2]) or ["交付可被下一阶段直接消费。"],
            )
        )

    agent_specs = [
        RuntimeAgentSpec(
            agent_id=CONTROLLER_AGENT_ID,
            display_name="ExMachina 主控体",
            runtime_role="single-agent-conductor",
            source="全连结指挥体",
            workspace_dir="install/workspaces/exmachina-main",
            responsibilities=[
                "在单 agent 会话中装载协议、主连结体、协作链和运行时任务板。",
                f"主责执行 {primary_body.name}，并按需内联参考协作链：{('、'.join(inline_support_names) if inline_support_names else '无')}。",
            ],
            handoff_targets=[],
            inbox_path=f"{RUNTIME_AGENTS_ROOT}/{CONTROLLER_AGENT_ID}/inbox",
            outbox_path=f"{RUNTIME_AGENTS_ROOT}/{CONTROLLER_AGENT_ID}/outbox",
            status_path=f"{RUNTIME_AGENTS_ROOT}/{CONTROLLER_AGENT_ID}/status.json",
            assignments=[assignment.assignment_id for assignment in assignments],
            coordination_rules=[
                f"仍然优先遵守 {resource_arbitration.priority_slots[0].priority} 闸门与理性协议。",
                "Lite 模式下禁止假设存在外部协作 agent 或外部路由器。",
                "所有主链/补位区分通过任务板和结构化输出维持，而不是通过多 agent 绑定维持。",
            ],
            operating_playbook=[
                "先执行主链，再按需要内联消费协作连结体规则。",
                "冲突、风险和不可逆动作仍然要显式升级到主控裁决层。",
            ],
            escalation_triggers=["发现当前宿主不支持额外绑定或路由时继续留在 Lite 模式。", "主链结论无法独立收束时显式标记需要外部协作。"],
            recommended_skill=dict(primary_body.recommended_skill),
        )
    ]

    return RuntimeTopology(
        mode="lite",
        controller_agent_id=CONTROLLER_AGENT_ID,
        coordination_mode="single-agent-inline-support",
        requires_external_routing=False,
        shared_artifacts=shared_artifacts,
        agent_specs=agent_specs,
        assignments=assignments,
        routes=[],
        coordination_rules=[
            "Lite 模式不要求多 agent 绑定与路由，由 exmachina-main 单会话执行。",
            "协作连结体保留为内联参考角色，不要求外部安装器创建额外 agent。",
        ],
        activation_steps=[
            f"由 {CONTROLLER_AGENT_ID} 读取 `runtime/shared/mission-context.json` 与 `runtime/task-board.json`。",
            f"{CONTROLLER_AGENT_ID} 先装载主连结体 {primary_body.name}，再按需内联参考协作链规则。",
            "所有阶段结果在单会话内按任务板推进，不依赖跨 agent handoff。",
        ],
    )


def _build_body_agent_map(primary_body: LinkBody, support_bodies: list[LinkBody]) -> dict[str, str]:
    body_agent_map = {primary_body.name: PRIMARY_AGENT_ID}
    for index, body in enumerate(support_bodies, start=1):
        body_agent_map[body.name] = f"exmachina-support-{index}"
    return body_agent_map


def _build_shared_artifacts(openclaw_install_plan: OpenClawInstallPlan) -> list[RuntimeSharedArtifact]:
    consumer_ids = [agent.agent_id for agent in openclaw_install_plan.agents]
    return [
        RuntimeSharedArtifact(
            name="mission-context",
            path=f"{RUNTIME_SHARED_ROOT}/mission-context.json",
            description="任务全局上下文、验收标准、主链与协作链拓扑。",
            consumers=consumer_ids,
        ),
        RuntimeSharedArtifact(
            name="selection-trace",
            path=f"{RUNTIME_SHARED_ROOT}/selection-trace.json",
            description="主连结体和协作链的选择依据，供主控体与主链路校准。",
            consumers=consumer_ids,
        ),
        RuntimeSharedArtifact(
            name="knowledge-handoff",
            path=f"{RUNTIME_SHARED_ROOT}/knowledge-handoff.json",
            description="任务沉淀、开放问题、后续维护与知识交接清单。",
            consumers=consumer_ids,
        ),
        RuntimeSharedArtifact(
            name="resource-arbitration",
            path=f"{RUNTIME_SHARED_ROOT}/resource-arbitration.json",
            description="P0-P3 资源仲裁与冲突升级规则。",
            consumers=consumer_ids,
        ),
        RuntimeSharedArtifact(
            name="task-board",
            path=f"{RUNTIME_ROOT}/task-board.json",
            description="阶段任务队列、owner/support 分工和依赖关系。",
            consumers=consumer_ids,
        ),
    ]


def _build_runtime_assignments(
    task: str,
    execution_stages: list[ExecutionStage],
    openclaw_install_plan: OpenClawInstallPlan,
    body_map: dict[str, LinkBody],
    body_agent_map: dict[str, str],
    dispatch_route_ids: list[str],
    stage_support_route_map: dict[tuple[str, str], list[str]],
    stage_handoff_route_map: dict[str, list[str]],
    report_route_map: dict[str, list[str]],
) -> list[RuntimeAssignment]:
    assignments = [
        RuntimeAssignment(
            assignment_id="assignment-controller-overview",
            stage_name="全局协调",
            agent_id=CONTROLLER_AGENT_ID,
            source_body="全连结指挥体",
            role="controller",
            goal=f"围绕任务「{task}」设定全局边界、激活执行阶段、处理升级裁决并收束最终交付。",
            deliverables=[
                "任务边界与验收标准",
                "运行时阶段调度板",
                "最终多 agent 汇总结论",
            ],
            exit_checks=[
                "主链路和协作链都已收到激活与角色分工。",
                "所有需要升级的问题都已进入主控裁决。",
                "最终结论、风险和下一步已经统一回收。",
            ],
            depends_on=[],
            handoff_routes=list(dispatch_route_ids),
            guidance=[
                "主控体必须追踪所有 stage owner 的状态和升级信号。",
                "主控体必须在冲突或越权场景下重新收束边界。",
            ],
            quality_bar=[
                "全局边界、验收、升级路径始终清晰。",
                "最终汇总保留证据、风险和后续动作。",
            ],
        )
    ]

    for stage_index, stage in enumerate(execution_stages, start=1):
        owner_agent_id = body_agent_map.get(stage.owner_body, CONTROLLER_AGENT_ID)
        owner_route_ids = [
            *stage_handoff_route_map.get(stage.name, []),
            *report_route_map.get(owner_agent_id, []),
        ]
        depends_on = [] if stage_index == 1 else [execution_stages[stage_index - 2].name]
        owner_profile = body_map.get(stage.owner_body)
        assignments.append(
            RuntimeAssignment(
                assignment_id=f"assignment-stage-{stage_index:02d}-owner-{owner_agent_id}",
                stage_name=stage.name,
                agent_id=owner_agent_id,
                source_body=stage.owner_body,
                role="owner",
                goal=stage.goal,
                deliverables=list(stage.deliverables),
                exit_checks=list(stage.exit_checks),
                depends_on=depends_on,
                handoff_routes=owner_route_ids,
                guidance=list((owner_profile.collaboration_rules if owner_profile else [])[:2])
                + list((owner_profile.link_conductor.dispatch_rules if owner_profile else [])[:2]),
                quality_bar=list((owner_profile.deliverable_contracts if owner_profile else [])[:3]),
            )
        )

        for support_body in stage.support_bodies:
            support_agent_id = body_agent_map.get(support_body, CONTROLLER_AGENT_ID)
            support_profile = body_map.get(support_body)
            assignments.append(
                RuntimeAssignment(
                    assignment_id=f"assignment-stage-{stage_index:02d}-support-{support_agent_id}",
                    stage_name=stage.name,
                    agent_id=support_agent_id,
                    source_body=support_body,
                    role="support",
                    goal=f"为 {stage.owner_body} 在 {stage.name} 中提供 {support_body} 视角的补位、校验或支撑输入。",
                    deliverables=[
                        f"面向 {stage.owner_body} 的协作输入",
                        "局部证据、风险或实现建议",
                    ],
                    exit_checks=[
                        f"协作输入已经通过 support-input 路由交给 {stage.owner_body}。",
                        "协作输出显式区分事实、判断、风险和下一步。",
                    ],
                    depends_on=depends_on,
                    handoff_routes=[
                        *stage_support_route_map.get((stage.name, support_agent_id), []),
                        *report_route_map.get(support_agent_id, []),
                    ],
                    guidance=list((support_profile.support_capabilities if support_profile else [])[:2])
                    + list((support_profile.collaboration_rules if support_profile else [])[:2]),
                    quality_bar=list((support_profile.deliverable_contracts if support_profile else [])[:2]),
                )
            )

    return assignments


def _build_runtime_agent_specs(
    openclaw_install_plan: OpenClawInstallPlan,
    assignments: list[RuntimeAssignment],
    resource_arbitration: ResourceArbitration,
    body_map: dict[str, LinkBody],
) -> list[RuntimeAgentSpec]:
    specs: list[RuntimeAgentSpec] = []
    for agent in openclaw_install_plan.agents:
        agent_assignment_ids = [item.assignment_id for item in assignments if item.agent_id == agent.agent_id]
        source_body = body_map.get(agent.source)
        specs.append(
            RuntimeAgentSpec(
                agent_id=agent.agent_id,
                display_name=agent.display_name,
                runtime_role=agent.role,
                source=agent.source,
                workspace_dir=agent.workspace_dir,
                responsibilities=list(agent.responsibilities),
                handoff_targets=list(agent.handoff_targets),
                inbox_path=f"{RUNTIME_AGENTS_ROOT}/{agent.agent_id}/inbox",
                outbox_path=f"{RUNTIME_AGENTS_ROOT}/{agent.agent_id}/outbox",
                status_path=f"{RUNTIME_AGENTS_ROOT}/{agent.agent_id}/status.json",
                assignments=agent_assignment_ids,
                coordination_rules=[
                    f"必须优先遵守 {resource_arbitration.priority_slots[0].priority} 闸门与主控裁决。",
                    "仅处理分配给自己的阶段任务，不擅自越权改写其他 agent 的职责。",
                    "所有输出必须通过 runtime handoff 路由或状态回报文件沉淀。",
                ],
                operating_playbook=(list(source_body.collaboration_rules[:2]) if source_body else [])
                + (list(source_body.link_conductor.reporting_contract[:2]) if source_body else ["按 runtime 路由回报状态。"]),
                escalation_triggers=(list(source_body.link_conductor.escalation_policy[:2]) if source_body else ["发现高风险或无法继续推进时升级。"]),
                recommended_skill=(dict(source_body.recommended_skill) if source_body else {}),
            )
        )
    return specs
