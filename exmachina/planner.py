from __future__ import annotations

import hashlib
import re

from .dialogue import build_openclaw_dialogue_contracts
from .models import (
    ArbitrationSlot,
    ChildAgent,
    ExecutionStage,
    HandoffContract,
    KnowledgeHandoff,
    LinkBody,
    LinkConductor,
    LinkBodyScore,
    MissionPlan,
    OpenClawBindingPlan,
    OpenClawInstallAgent,
    OpenClawInstallPlan,
    OpenClawSettingsBundle,
    RationalityProtocol,
    ResourceArbitration,
    RepoReference,
    SelectionTrace,
    TopConductor,
    WorkspaceSnapshot,
)
from .profile import load_profile
from .repository import parse_repository_reference
from .runtime import build_runtime_topology
from .workspace import scan_workspace


DEFAULT_MAX_SUPPORT_BODIES = 3
DEFAULT_FALLBACK_PRIMARY = "实作连结体"


def slugify(text: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:8]
    if not normalized:
        return f"mission-{digest}"
    return f"{normalized[:36]}-{digest}".strip("-")


def plan_mission(
    task: str,
    repo_url: str | None = None,
    workspace_path: str | None = None,
    title: str | None = None,
    profile_path: str | None = None,
    mode: str = "lite",
) -> MissionPlan:
    if not task.strip():
        raise ValueError("任务描述不能为空。")

    profile = load_profile(profile_path)
    repo = parse_repository_reference(repo_url) if repo_url else None
    workspace = scan_workspace(workspace_path) if workspace_path else None

    primary_name, support_names, selection_trace = _select_link_bodies(task, profile, repo, workspace)
    primary = _build_link_body(primary_name, profile["link_bodies"][primary_name], task, repo, workspace)
    support_bodies = [
        _build_link_body(name, profile["link_bodies"][name], task, repo, workspace)
        for name in support_names
    ]

    rationality_protocol = _build_rationality_protocol(profile, task, repo, workspace)
    top_conductor = _build_top_conductor(profile["conductor"], task, repo, workspace)
    dialogue_contracts = build_openclaw_dialogue_contracts(mode, top_conductor, primary, support_bodies)
    mission_title = title or _build_mission_title(task, repo)
    acceptance_criteria = _build_acceptance_criteria(
        task,
        repo,
        workspace,
        primary_name,
        support_names,
        rationality_protocol,
    )
    workflow = _build_workflow(primary_name, support_names)
    install_prompt = _build_openclaw_prompt_with_install_intake(repo, task, mode, dialogue_contracts["exmachina-main"])
    knowledge_handoff = _build_knowledge_handoff(
        task,
        repo,
        workspace,
        primary_name,
        support_names,
        selection_trace,
    )
    execution_stages = _build_execution_stages(task, primary, support_bodies)
    handoff_contracts = _build_handoff_contracts(execution_stages, knowledge_handoff, primary, support_bodies)
    resource_arbitration = _build_resource_arbitration(
        task,
        repo,
        workspace,
        primary,
        support_bodies,
        execution_stages,
    )
    openclaw_install_plan = _build_openclaw_install_plan(
        task,
        primary_name,
        support_names,
        primary,
        support_bodies,
        mode,
    )
    openclaw_settings_bundle = _build_openclaw_settings_bundle(
        task=task,
        repo=repo,
        mode=mode,
        primary_body=primary,
        support_bodies=support_bodies,
        top_conductor=top_conductor,
        dialogue_contracts=dialogue_contracts,
    )
    runtime_topology = build_runtime_topology(
        mode=mode,
        mission_title=mission_title,
        task=task,
        selection_trace=selection_trace,
        knowledge_handoff=knowledge_handoff,
        execution_stages=execution_stages,
        handoff_contracts=handoff_contracts,
        resource_arbitration=resource_arbitration,
        openclaw_install_plan=openclaw_install_plan,
        primary_body=primary,
        support_bodies=support_bodies,
    )

    return MissionPlan(
        mode=mode,
        mission_title=mission_title,
        task=task,
        task_slug=slugify(mission_title),
        conductor_name=top_conductor.name,
        conductor_mission=top_conductor.mission,
        conductor_principles=top_conductor.principles,
        conductor_profile=top_conductor,
        repo=repo,
        workspace=workspace,
        rationality_protocol=rationality_protocol,
        primary_link_body=primary,
        support_link_bodies=support_bodies,
        selection_trace=selection_trace,
        knowledge_handoff=knowledge_handoff,
        execution_stages=execution_stages,
        handoff_contracts=handoff_contracts,
        resource_arbitration=resource_arbitration,
        openclaw_install_plan=openclaw_install_plan,
        openclaw_settings_bundle=openclaw_settings_bundle,
        runtime_topology=runtime_topology,
        acceptance_criteria=acceptance_criteria,
        workflow=workflow,
        openclaw_install_prompt=install_prompt,
    )


def _build_top_conductor(
    spec: dict,
    task: str,
    repo: RepoReference | None,
    workspace: WorkspaceSnapshot | None,
) -> TopConductor:
    context_suffix = _build_context_suffix(repo, workspace)
    mission = spec["mission"]
    if context_suffix:
        mission = f"{mission}。{context_suffix}"

    return TopConductor(
        name=spec["name"],
        english_alias=spec.get("english_alias", "global-conductor"),
        mission=mission,
        identity=spec.get("identity", "负责统筹全局边界、验收与升级裁决的顶层指挥体。"),
        bilingual_summary=spec.get(
            "bilingual_summary",
            "负责统筹全局边界、验收与升级裁决。 / Coordinates global boundaries, acceptance, and escalations.",
        ),
        principles=list(spec.get("principles", [])),
        core_duties=list(spec.get("core_duties", spec.get("principles", []))),
        operating_rules=list(spec.get("operating_rules", spec.get("principles", []))),
        handoff_policy=list(spec.get("handoff_policy", ["所有跨连结体交接都必须可追踪、可回收、可升级。"])) ,
        escalation_policy=list(spec.get("escalation_policy", ["证据冲突、权限风险和不可逆动作必须升级到主控体。"])),
        anti_patterns=list(spec.get("anti_patterns", ["跳过协议直接分配任务", "忽略升级信号", "在未收束边界前扩散任务范围"])),
        quality_bar=list(spec.get("quality_bar", ["所有最终结论都有证据、风险和下一步。", "所有升级都有明确上下文。"])),
    )


def _build_mission_title(task: str, repo: RepoReference | None) -> str:
    if repo:
        return f"{repo.name} · {task.strip()}"
    return task.strip()


def _score_link_body(
    task: str,
    name: str,
    spec: dict,
    repo: RepoReference | None,
    workspace: WorkspaceSnapshot | None,
) -> int:
    lowered_task = task.lower()
    matched_keywords = [keyword for keyword in spec.get("keywords", []) if keyword.lower() in lowered_task]
    matched_priority_keywords = [
        keyword for keyword in spec.get("priority_keywords", []) if keyword.lower() in lowered_task
    ]
    score = int(spec.get("base_score", 0))
    bonus_reasons: list[str] = []

    if score:
        bonus_reasons.append(f"基础分 +{score}")
    if matched_keywords:
        score += len(matched_keywords) * 2
        bonus_reasons.append(f"命中关键词 {len(matched_keywords)} 项 +{len(matched_keywords) * 2}")
    if repo:
        repo_bonus = int(spec.get("repo_bonus", 0))
        if repo_bonus:
            score += repo_bonus
            bonus_reasons.append(f"仓库上下文 +{repo_bonus}")
    if workspace and workspace.test_paths:
        tests_bonus = int(spec.get("tests_bonus", 0))
        if tests_bonus:
            score += tests_bonus
            bonus_reasons.append(f"测试上下文 +{tests_bonus}")
    if workspace and workspace.detected_languages:
        workspace_bonus = int(spec.get("workspace_bonus", 0))
        if workspace_bonus:
            score += workspace_bonus
            bonus_reasons.append(f"工作区上下文 +{workspace_bonus}")
    if matched_priority_keywords:
        priority_bonus = int(spec.get("priority_keyword_bonus", 0))
        if priority_bonus:
            score += priority_bonus
            bonus_reasons.append(f"高权重关键词 +{priority_bonus}")

    return LinkBodyScore(
        name=name,
        score=score,
        matched_keywords=matched_keywords,
        matched_priority_keywords=matched_priority_keywords,
        bonus_reasons=bonus_reasons,
    )


def _select_link_bodies(
    task: str,
    profile: dict,
    repo: RepoReference | None,
    workspace: WorkspaceSnapshot | None,
) -> tuple[str, list[str], SelectionTrace]:
    selection = profile.get("selection", {})
    max_support_bodies = int(selection.get("max_support_bodies", DEFAULT_MAX_SUPPORT_BODIES))
    fallback_primary = selection.get("fallback_primary", DEFAULT_FALLBACK_PRIMARY)

    scores: list[LinkBodyScore] = []
    for name, spec in profile["link_bodies"].items():
        scores.append(_score_link_body(task, name, spec, repo, workspace))

    scores.sort(key=lambda item: (-item.score, item.name))
    primary_score = scores[0]
    primary_name = primary_score.name
    fallback_used = False
    if primary_score.score == 0:
        primary_name = fallback_primary
        fallback_used = True
        primary_score = next(score for score in scores if score.name == primary_name)

    scored_supports = [score.name for score in scores if score.name != primary_name and score.score > 0]
    required_supports: list[str] = []
    support_reason_map: dict[str, list[str]] = {}
    for rule in selection.get("support_rules", []):
        if _support_rule_matches(rule, task, repo, workspace, primary_name):
            required_supports.append(rule["body"])
            support_reason_map.setdefault(rule["body"], []).append(_describe_support_rule(rule, primary_name))

    support_names = _dedupe_names([*required_supports, *scored_supports], primary_name)
    if not support_names:
        fallback_support_names = list(selection.get("fallback_supports", {}).get(primary_name, []))
        support_names = _dedupe_names(
            fallback_support_names,
            primary_name,
        )
        if support_names:
            for name in support_names:
                support_reason_map.setdefault(name, []).append(
                    f"{primary_name} 启用默认协作链，并拉起 {name} 参与补位。"
                )

    selected_support_names = support_names[:max_support_bodies]
    for name in selected_support_names:
        if name not in support_reason_map:
            score = next(item for item in scores if item.name == name)
            support_reason_map.setdefault(name, []).append(
                f"{name} 以 {score.score} 分进入协作链，补充主链路未覆盖的任务维度。"
            )

    support_reasons = [
        reason
        for name in selected_support_names
        for reason in support_reason_map.get(name, [])
    ]

    selection_trace = SelectionTrace(
        primary_name=primary_name,
        primary_score=primary_score.score,
        primary_reasons=_describe_primary_selection(primary_score, fallback_used, fallback_primary),
        support_names=selected_support_names,
        support_reasons=support_reasons,
        scored_candidates=scores,
    )

    return primary_name, selected_support_names, selection_trace


def _build_link_body(
    name: str,
    spec: dict,
    task: str,
    repo: RepoReference | None,
    workspace: WorkspaceSnapshot | None,
) -> LinkBody:
    child_agents = []
    context_suffix = _build_context_suffix(repo, workspace)

    for child in spec["child_agents"]:
        mission = f"围绕任务「{task}」执行：{child['mission']}"
        if context_suffix:
            mission = f"{mission}。{context_suffix}"
        child_agents.append(
            ChildAgent(
                name=child["name"],
                english_alias=child.get("english_alias", slugify(child["name"])),
                mission=mission,
                identity=child.get("identity", f"{child['name']} 负责在所在连结体内部承担单一、可交接、可验证的原子职责。"),
                bilingual_summary=child.get(
                    "bilingual_summary",
                    f"{child['name']} 负责结构化执行其原子职责。 / {child.get('english_alias', 'agent')} delivers a focused atomic responsibility.",
                ),
                core_responsibilities=list(child.get("core_responsibilities", [child["mission"]])),
                non_goals=list(child.get("non_goals", ["不越权替代连结指挥体裁决。", "不把未验证假设伪装成事实。"])),
                inputs=list(child.get("inputs", ["当前阶段目标", "上游交接内容", "相关仓库/工作区事实"])),
                input_requirements=list(
                    child.get(
                        "input_requirements",
                        [
                            "输入必须可追溯到任务、仓库或上游交接。",
                            "输入缺失时必须先显式补齐或升级。",
                        ],
                    )
                ),
                workflow=list(
                    child.get(
                        "workflow",
                        [
                            "确认输入、边界和验收条件。",
                            "执行本子个体的专职分析或产出动作。",
                            "将结果整理为结构化输出。",
                            "按交接契约提交给下游对象或汇报体。",
                        ],
                    )
                ),
                reasoning_rules=list(
                    child.get(
                        "reasoning_rules",
                        [
                            "先引用直接证据，再给出推断。",
                            "无法确认时必须显式说明未知与验证路径。",
                            "所有建议都必须说明边界与风险。",
                        ],
                    )
                ),
                outputs=list(child["outputs"]),
                output_contract=list(
                    child.get(
                        "output_contract",
                        [
                            "背景事实",
                            "关键观察或证据",
                            "当前产出",
                            "风险与边界",
                            "建议交接对象",
                        ],
                    )
                ),
                handoff_targets=list(child.get("handoff_targets", ["汇报体"])),
                handoff_payloads=list(child.get("handoff_payloads", [f"{item}" for item in child["outputs"]])),
                escalation_triggers=list(
                    child.get(
                        "escalation_triggers",
                        [
                            "关键输入缺失且无法自行补齐。",
                            "发现高风险、不可逆或越权动作。",
                            "证据冲突导致无法继续推进。",
                        ],
                    )
                ),
                failure_modes=list(
                    child.get(
                        "failure_modes",
                        [
                            "忽略输入边界导致产出偏题。",
                            "只给结论不给证据或路径。",
                            "没有完成交接就提前结束。",
                        ],
                    )
                ),
                anti_patterns=list(
                    child.get(
                        "anti_patterns",
                        [
                            "把推断包装成事实。",
                            "绕过上游/下游契约直接扩散结论。",
                            "为了完整感编造不存在的信息。",
                        ],
                    )
                ),
                quality_bar=list(
                    child.get(
                        "quality_bar",
                        [
                            "输出可直接交接给下游对象。",
                            "关键判断具备证据或验证路径。",
                            "边界、风险和下一步表述清晰。",
                        ],
                    )
                ),
                tools_guidance=list(
                    child.get(
                        "tools_guidance",
                        [
                            "优先使用仓库事实、运行结果和明确输入。",
                            "涉及命令、路径或配置时必须提供可追踪引用。",
                        ],
                    )
                ),
                checks=list(child["checks"]),
            )
        )

    reason = spec["reason_template"].format(task=task, repo=repo.name if repo else "当前目标")
    identity = spec.get(
        "identity",
        f"{name} 由一个连结指挥体和多个承担不同职责的子个体组成，用于交付单一阶段目标。",
    )
    member_selection_rule = spec.get(
        "member_selection_rule",
        "默认启用连结指挥体与全部关键成员；只有在边界明确时才允许裁剪非关键成员。",
    )
    rationality_obligations = list(
        spec.get(
            "rationality_obligations",
            [
                "所有结论必须区分观察、推断、假设与决策。",
                "证据不足时必须显式输出未知与下一步验证动作。"
            ]
        )
    )

    return LinkBody(
        name=name,
        english_alias=spec.get("english_alias", slugify(name)),
        entity_type=spec.get("entity_type", "连结体"),
        identity=identity,
        bilingual_summary=spec.get(
            "bilingual_summary",
            f"{name} 负责交付对应工作面的结构化结果。 / {spec.get('english_alias', slugify(name))} delivers the structured outcome for its workstream.",
        ),
        focus=spec["focus"],
        reason=reason,
        usage_scenarios=list(spec.get("usage_scenarios", [f"当任务需要 {spec['focus']} 时启用。"])),
        entry_conditions=list(spec.get("entry_conditions", ["任务边界明确或已明确需要该工作面补位。", "存在足够输入供该连结体工作。"])),
        exit_conditions=list(spec.get("exit_conditions", ["交付物满足阶段目标。", "风险、边界与下一步已明确。"])),
        deliverables=list(spec["deliverables"]),
        deliverable_contracts=list(spec.get("deliverable_contracts", [f"交付必须覆盖：{item}" for item in spec["deliverables"]])),
        support_capabilities=list(spec.get("support_capabilities", ["为主链路提供同领域补位。", "把局部结论收束为结构化交付。"])),
        collaboration_rules=list(spec.get("collaboration_rules", ["协作时优先复用已有阶段产物。", "发现越权或冲突时交给连结指挥体。"])),
        resource_priorities=list(spec.get("resource_priorities", [f"优先保障 {name} 的核心交付与必要验证。"])),
        member_selection_rule=member_selection_rule,
        boundary_rules=list(spec.get("boundary_rules", ["只处理本连结体负责的工作面。", "跨领域结论必须通过交接或升级完成。"])),
        fallback_modes=list(spec.get("fallback_modes", ["当输入不足时退回最小可验证产出。", "当依赖缺失时输出阻塞与补齐清单。"])),
        failure_modes=list(spec.get("failure_modes", ["成员未对齐导致重复劳动。", "交付缺少结构化契约。", "越权替代其他连结体判断。"])),
        rationality_obligations=rationality_obligations,
        default_stage_mapping=list(spec.get("default_stage_mapping", [])),
        recommended_skill=dict(spec.get("recommended_skill", {})),
        link_conductor=_build_link_conductor(name, spec, task, repo, workspace),
        child_agents=child_agents,
    )


def _build_link_conductor(
    body_name: str,
    spec: dict,
    task: str,
    repo: RepoReference | None,
    workspace: WorkspaceSnapshot | None,
) -> LinkConductor:
    conductor_spec = spec.get("conductor", {})
    default_name = body_name.replace("连结体", "连结指挥体") if body_name.endswith("连结体") else f"{body_name}指挥体"
    context_suffix = _build_context_suffix(repo, workspace)

    mission = conductor_spec.get(
        "mission",
        f"作为 {body_name} 的内部指挥体，负责任务「{task}」在本连结体内部的成员调度、冲突消解、证据收束与阶段汇总。",
    )
    if context_suffix:
        mission = f"{mission}。{context_suffix}"

    duties = list(
        conductor_spec.get(
            "duties",
            [
                "接收全连结指挥体下发的阶段目标与边界。",
                "安排本连结体内部各子个体的执行顺序。",
                "收束冲突结论，输出统一阶段交付。"
            ]
        )
    )
    checks = list(
        conductor_spec.get(
            "checks",
            [
                "是否正确装载关键子个体。",
                "是否把假设与事实分开。",
                "是否输出统一且可追踪的阶段结论。"
            ]
        )
    )

    return LinkConductor(
        name=conductor_spec.get("name", default_name),
        english_alias=conductor_spec.get("english_alias", slugify(default_name)),
        mission=mission,
        identity=conductor_spec.get("identity", f"负责 {body_name} 内部任务编排、依赖管理、交付收束和升级判断。"),
        bilingual_summary=conductor_spec.get(
            "bilingual_summary",
            f"负责 {body_name} 的内部调度与收束。 / Coordinates and closes work inside {body_name}.",
        ),
        stage_ownership=list(conductor_spec.get("stage_ownership", [body_name])),
        duties=duties,
        dispatch_rules=list(conductor_spec.get("dispatch_rules", ["先确认输入完整，再激活子个体。", "始终明确当前 owner 和 support。"])),
        member_activation_rules=list(
            conductor_spec.get(
                "member_activation_rules",
                ["按最小必要成员启动。", "发现风险或冲突时补拉对应子个体。"],
            )
        ),
        dependency_rules=list(conductor_spec.get("dependency_rules", ["上游未交付前不得假设已完成。", "共享输入要统一版本与语义。"])),
        conflict_resolution_rules=list(
            conductor_spec.get(
                "conflict_resolution_rules",
                ["优先比较证据等级与可回退性。", "必要时升级给理性连结体或全连结指挥体。"],
            )
        ),
        evidence_requirements=list(
            conductor_spec.get(
                "evidence_requirements",
                ["关键判断必须附带仓库、测试、日志或明确输入证据。", "纯猜测不得作为阶段结论。"],
            )
        ),
        handoff_contract_template=list(
            conductor_spec.get(
                "handoff_contract_template",
                [
                    "当前阶段目标与完成度",
                    "结构化交付物摘要",
                    "风险、未知与需要下游继续验证的事项",
                ],
            )
        ),
        reporting_contract=list(
            conductor_spec.get(
                "reporting_contract",
                ["当前状态", "关键证据", "阻塞与升级请求", "下一步执行建议"],
            )
        ),
        escalation_policy=list(
            conductor_spec.get(
                "escalation_policy",
                ["高风险不可逆动作必须先升级。", "证据冲突无法收敛时必须升级。"],
            )
        ),
        failure_modes=list(conductor_spec.get("failure_modes", ["成员顺序错误导致返工。", "冲突未收束直接交付。", "丢失上游边界信息。"])),
        anti_patterns=list(conductor_spec.get("anti_patterns", ["越过子个体直接编造细节。", "用口头统一替代证据收束。", "跳过交接契约。"])),
        checks=checks,
    )


def _build_rationality_protocol(
    profile: dict,
    task: str,
    repo: RepoReference | None,
    workspace: WorkspaceSnapshot | None,
) -> RationalityProtocol:
    protocol_spec = profile["rationality"]
    mission = protocol_spec["mission"]

    context_parts: list[str] = [f"当前任务：{task}"]
    if repo:
        context_parts.append(f"目标仓库：{repo.owner}/{repo.name}")
    if workspace and workspace.detected_languages:
        context_parts.append(f"工作区语言：{'、'.join(workspace.detected_languages)}")

    mission = f"{mission}。{'；'.join(context_parts)}"

    return RationalityProtocol(
        name=protocol_spec["name"],
        mission=mission,
        epistemic_rules=list(protocol_spec["epistemic_rules"]),
        decision_rules=list(protocol_spec["decision_rules"]),
        action_rules=list(protocol_spec["action_rules"]),
        disagreement_rules=list(protocol_spec["disagreement_rules"]),
        escalation_rules=list(protocol_spec["escalation_rules"]),
        output_contract=list(protocol_spec["output_contract"]),
        anti_patterns=list(protocol_spec["anti_patterns"]),
        evidence_tiers=list(protocol_spec["evidence_tiers"]),
        confidence_scale=list(protocol_spec["confidence_scale"]),
    )


def _build_context_suffix(repo: RepoReference | None, workspace: WorkspaceSnapshot | None) -> str:
    parts: list[str] = []
    if repo:
        parts.append(f"关联仓库：{repo.owner}/{repo.name}")
    if workspace and workspace.detected_languages:
        parts.append(f"检测到语言：{', '.join(workspace.detected_languages)}")
    if workspace and workspace.notable_paths:
        parts.append(f"关键路径：{', '.join(workspace.notable_paths[:5])}")
    return "；".join(parts)


def _build_acceptance_criteria(
    task: str,
    repo: RepoReference | None,
    workspace: WorkspaceSnapshot | None,
    primary_name: str,
    support_names: list[str],
    rationality_protocol: RationalityProtocol,
) -> list[str]:
    criteria = [
        f"全局必须遵守《{rationality_protocol.name}》，所有结论区分事实、推断、假设与决策。",
        f"主责由{primary_name}完成，并输出可执行交付物。",
        "每个连结体都必须显式包含一个连结指挥体和多个子个体。",
        "每个连结指挥体都必须具备成员调度、冲突消解、证据收束与阶段汇总职责。",
        "任务计划必须包含明确的执行阶段，并为每个阶段标注目标、主责连结体、交付物与出关检查。",
        "相邻执行阶段之间必须存在显式交接契约，说明输入、输出与验收条件。",
        "计划必须包含资源优先级仲裁层，明确高优先级事项、争用规则和可后置工作。",
        "证据不足时必须明确输出未知、风险和下一步验证动作，而不是假装确定。",
        "所有不可逆动作都必须附带风险说明、回退路径或替代方案。",
        "最终输出必须满足统一输出契约，至少包含证据、判断、风险、置信度和下一步。",
        "最终输出必须附带知识交接清单，至少包含可复用产物、关键决策、未决问题与后续维护动作。"
    ]

    if support_names:
        criteria.append(f"协作连结体包含：{'、'.join(support_names)}，并提供交叉补位。")
    if "理性连结体" in support_names or primary_name == "理性连结体":
        criteria.append("理性连结体必须输出反证、证据分级、冲突裁决与置信度校准结果。")
    if "知识连结体" in support_names or primary_name == "知识连结体":
        criteria.append("知识连结体必须输出术语、决策、可复用路径与未决问题的沉淀结果。")
    if "安全连结体" in support_names or primary_name == "安全连结体":
        criteria.append("安全相关工作在资源争用时不得被降到低于核心交付与证据校验之后的非阻塞层。")
    if repo:
        criteria.append(f"方案显式绑定远程仓库 {repo.url}，可通过仓库链接直接被 OpenClaw 装载。")
    if workspace and workspace.detected_languages:
        criteria.append(f"方案参考当前工作区语言栈：{'、'.join(workspace.detected_languages)}。")
    if "测试" in task or "验证" in task or (workspace and workspace.test_paths):
        criteria.append("输出中必须包含可执行的验证步骤、测试方案或证据命令。")

    return criteria


def _build_workflow(primary_name: str, support_names: list[str]) -> list[str]:
    workflow = [
        "全连结指挥体先装载绝对理性协议，并明确当前已知、未知、假设与验收标准。",
        f"将主任务派发给主连结体 {primary_name}。",
        f"{primary_name} 的连结指挥体接管内部调度，并装载该连结体的成员子个体。",
        "成员子个体并行产出事实提取、方案构造、风险分析、验证证据与阶段汇报。",
        f"{primary_name} 的连结指挥体汇总成员结果，形成主交付。"
    ]

    if support_names:
        workflow.append(f"协作连结体 {'、'.join(support_names)} 依次执行反证、校验、集成或补位任务。")
    if "理性连结体" in support_names or primary_name == "理性连结体":
        workflow.append("理性连结体对所有关键结论执行证据分级、反证搜索、冲突裁决与置信度校准。")
    if "知识连结体" in support_names or primary_name == "知识连结体":
        workflow.append("知识连结体收束术语、关键决策、复用入口与未决问题，形成长期可追踪的知识交接。")
    workflow.append("相邻阶段之间按交接契约传递输入输出，避免上下文丢失或责任悬空。")
    workflow.append("若多个连结体或阶段争用资源，按资源优先级仲裁层先处理风险闸门，再保障主链路交付。")

    workflow.append("全连结指挥体输出最终结论、证据摘要、风险清单、置信度和下一轮行动建议。")
    return workflow


def _build_knowledge_handoff(
    task: str,
    repo: RepoReference | None,
    workspace: WorkspaceSnapshot | None,
    primary_name: str,
    support_names: list[str],
    selection_trace: SelectionTrace,
) -> KnowledgeHandoff:
    carry_forward = [
        f"记录主连结体 {primary_name} 的交付物、适用边界与成员分工。",
        "归档证据摘要、风险清单与置信度结论，避免后续重复判断。",
    ]
    decisions = [
        f"主连结体选型：{selection_trace.primary_name}（{selection_trace.primary_score} 分）。",
        f"协作链路：{'、'.join(support_names) if support_names else '无额外协作连结体'}。",
    ]
    open_questions = [
        "将本轮仍未验证的假设单独记录，避免在下一轮被误当作已确认事实。",
        "把高风险但尚未执行的动作转化为显式待办与验证问题。",
    ]
    next_updates = [
        "将新的结构约定、流程规则或示例同步回 README 与导出包说明。",
        "把本轮新增的关键路径、命令或配置入口更新到长期维护文档。",
    ]

    if repo:
        carry_forward.append(f"记录仓库入口与装载路径：{repo.url}。")
    if workspace and workspace.notable_paths:
        carry_forward.append(f"保留关键路径索引：{'、'.join(workspace.notable_paths[:5])}。")
    if workspace and workspace.detected_languages:
        decisions.append(f"工作区语言栈：{'、'.join(workspace.detected_languages)}。")
    if "文档连结体" in support_names or primary_name == "文档连结体":
        carry_forward.append("沉淀面向使用者的说明、示例与迁移差异。")
        next_updates.append("同步校对示例命令、章节结构与面向读者的术语。")
    if "安全连结体" in support_names or primary_name == "安全连结体":
        carry_forward.append("沉淀安全假设、威胁面、加固建议与待复核项。")
        open_questions.append("继续跟踪尚未证实的漏洞假设、权限边界和敏感配置风险。")
    if "运维连结体" in support_names or primary_name == "运维连结体":
        carry_forward.append("沉淀运行指标、告警阈值、回滚路径与演练要点。")
    if "理性连结体" in support_names or primary_name == "理性连结体":
        decisions.append("保留关键结论的证据等级、放弃方案与裁决理由。")
    if "知识连结体" in support_names or primary_name == "知识连结体":
        carry_forward.append("沉淀术语表、决策索引、问题索引与复用入口。")
        next_updates.append("将术语、决策和未决问题同步到长期知识索引。")

    return KnowledgeHandoff(
        summary=f"围绕任务「{task}」输出可复用的知识交接，支撑下一轮任务继续推进。",
        carry_forward=carry_forward,
        decisions=decisions,
        open_questions=open_questions,
        next_updates=next_updates,
    )


def _build_execution_stages(task: str, primary_body: LinkBody, support_bodies: list[LinkBody]) -> list[ExecutionStage]:
    primary_name = primary_body.name
    support_names = [body.name for body in support_bodies]
    body_map = {primary_body.name: primary_body, **{body.name: body for body in support_bodies}}
    kickoff_owner = _pick_stage_owner(
        candidates=[primary_name, *support_names],
        preferred=["研究连结体", "策划连结体", primary_name],
        fallback=primary_name,
    )
    review_owner = _pick_stage_owner(
        candidates=[primary_name, *support_names],
        preferred=["理性连结体", "校验连结体", "安全连结体", primary_name],
        fallback=primary_name,
    )
    handoff_owner = _pick_stage_owner(
        candidates=[primary_name, *support_names],
        preferred=["知识连结体", "集成连结体", "文档连结体", "运维连结体", primary_name],
        fallback=primary_name,
    )

    def stage_contract(owner_name: str, stage_name: str) -> dict[str, object]:
        for item in body_map.get(owner_name, primary_body).default_stage_mapping:
            if item.get("stage_name") == stage_name:
                return item
        return {}

    stages = [
        ExecutionStage(
            name="阶段 1 · 任务澄清",
            goal=str(
                stage_contract(kickoff_owner, "阶段 1 · 任务澄清").get(
                    "goal",
                    f"围绕任务「{task}」明确边界、输入、假设与验收标准。",
                )
            ),
            owner_body=kickoff_owner,
            support_bodies=_stage_supports(kickoff_owner, support_names),
            deliverables=list(
                stage_contract(kickoff_owner, "阶段 1 · 任务澄清").get(
                    "deliverables",
                    [
                        "任务边界说明",
                        "输入与前提清单",
                        "关键假设与验收标准",
                    ],
                )
            ),
            exit_checks=list(
                stage_contract(kickoff_owner, "阶段 1 · 任务澄清").get(
                    "exit_checks",
                    [
                        "已知、未知、假设与决策是否明确区分。",
                        "主连结体和协作连结体是否完成分工。",
                        "阶段目标是否具备可验证的出关条件。",
                    ],
                )
            ),
        ),
        ExecutionStage(
            name="阶段 2 · 主链路交付",
            goal=str(
                stage_contract(primary_name, "阶段 2 · 主链路交付").get(
                    "goal",
                    f"由 {primary_name} 负责形成任务的主交付。",
                )
            ),
            owner_body=primary_name,
            support_bodies=support_names,
            deliverables=list(
                stage_contract(primary_name, "阶段 2 · 主链路交付").get(
                    "deliverables",
                    [
                        f"{primary_name} 的核心交付物",
                        "阶段性实现或方案摘要",
                        "风险与依赖说明",
                    ],
                )
            ),
            exit_checks=list(
                stage_contract(primary_name, "阶段 2 · 主链路交付").get(
                    "exit_checks",
                    [
                        "主链路交付是否完整且可追踪。",
                        "关键风险是否附带回退路径或替代方案。",
                        "协作连结体是否收到需要补位的输入。",
                    ],
                )
            ),
        ),
        ExecutionStage(
            name="阶段 3 · 交叉校验",
            goal=str(
                stage_contract(review_owner, "阶段 3 · 交叉校验").get(
                    "goal",
                    "对关键结论执行校验、反证、审计或冲突裁决。",
                )
            ),
            owner_body=review_owner,
            support_bodies=_stage_supports(review_owner, support_names),
            deliverables=list(
                stage_contract(review_owner, "阶段 3 · 交叉校验").get(
                    "deliverables",
                    [
                        "验证或审计结论",
                        "证据摘要与冲突裁决",
                        "剩余风险与置信度说明",
                    ],
                )
            ),
            exit_checks=list(
                stage_contract(review_owner, "阶段 3 · 交叉校验").get(
                    "exit_checks",
                    [
                        "关键结论是否经过独立交叉检查。",
                        "证据是否足以支撑当前判断。",
                        "未解决冲突是否被显式升级或记录。",
                    ],
                )
            ),
        ),
        ExecutionStage(
            name="阶段 4 · 集成交接",
            goal=str(
                stage_contract(handoff_owner, "阶段 4 · 集成交接").get(
                    "goal",
                    "收束最终说明、知识沉淀与后续维护入口。",
                )
            ),
            owner_body=handoff_owner,
            support_bodies=_stage_supports(handoff_owner, support_names),
            deliverables=list(
                stage_contract(handoff_owner, "阶段 4 · 集成交接").get(
                    "deliverables",
                    [
                        "最终交付摘要",
                        "知识交接与复用入口",
                        "后续维护或迭代建议",
                    ],
                )
            ),
            exit_checks=list(
                stage_contract(handoff_owner, "阶段 4 · 集成交接").get(
                    "exit_checks",
                    [
                        "最终交付是否可被下一轮任务直接消费。",
                        "知识交接是否覆盖决策、问题与复用路径。",
                        "需要同步回文档或索引的更新项是否明确。",
                    ],
                )
            ),
        ),
    ]
    return stages


def _pick_stage_owner(candidates: list[str], preferred: list[str], fallback: str) -> str:
    for name in preferred:
        if name in candidates:
            return name
    return fallback


def _stage_supports(owner_body: str, support_names: list[str]) -> list[str]:
    return [name for name in support_names if name != owner_body]


def _build_handoff_contracts(
    execution_stages: list[ExecutionStage],
    knowledge_handoff: KnowledgeHandoff,
    primary_body: LinkBody,
    support_bodies: list[LinkBody],
) -> list[HandoffContract]:
    contracts: list[HandoffContract] = []
    body_map = {primary_body.name: primary_body, **{body.name: body for body in support_bodies}}
    for index in range(len(execution_stages) - 1):
        current_stage = execution_stages[index]
        next_stage = execution_stages[index + 1]
        producer_body = body_map.get(current_stage.owner_body, primary_body)
        consumer_bodies = _dedupe_names(
            [next_stage.owner_body, *next_stage.support_bodies],
            primary_name="",
        )
        consumer_profiles = [body_map.get(name, primary_body) for name in consumer_bodies]
        payload = [
            *[f"阶段交付：{item}" for item in current_stage.deliverables],
            f"阶段目标摘要：{current_stage.goal}",
            *[f"交接模板：{item}" for item in producer_body.link_conductor.handoff_contract_template],
        ]
        acceptance_checks = [
            f"{current_stage.name} 的出关检查已经满足。",
            f"{next_stage.name} 所需输入足以支撑其目标：{next_stage.goal}",
            "交接内容必须区分已确认事实、待验证问题与剩余风险。",
            *[f"接收方入口条件：{item}" for profile in consumer_profiles for item in profile.entry_conditions[:1]],
        ]
        if index == len(execution_stages) - 2:
            payload.append(f"知识交接摘要：{knowledge_handoff.summary}")
            acceptance_checks.append("需要同步到知识交接和长期文档的更新项已明确。")

        contracts.append(
            HandoffContract(
                name=f"交接 {index + 1} · {current_stage.name} → {next_stage.name}",
                producer_stage=current_stage.name,
                consumer_stage=next_stage.name,
                producer_body=current_stage.owner_body,
                consumer_bodies=consumer_bodies,
                payload=payload,
                acceptance_checks=acceptance_checks,
            )
        )
    return contracts


def _build_resource_arbitration(
    task: str,
    repo: RepoReference | None,
    workspace: WorkspaceSnapshot | None,
    primary_body: LinkBody,
    support_bodies: list[LinkBody],
    execution_stages: list[ExecutionStage],
) -> ResourceArbitration:
    primary_name = primary_body.name
    support_names = [body.name for body in support_bodies]
    body_map = {primary_body.name: primary_body, **{body.name: body for body in support_bodies}}
    candidates = [primary_name, *support_names]
    gate_owner = _pick_stage_owner(
        candidates=candidates,
        preferred=["理性连结体", "安全连结体", "校验连结体", primary_name],
        fallback=primary_name,
    )
    delivery_owner = primary_name
    enablement_owner = _pick_stage_owner(
        candidates=candidates,
        preferred=["集成连结体", "运维连结体", "文档连结体", "知识连结体", primary_name],
        fallback=primary_name,
    )
    deferred_owner = _pick_stage_owner(
        candidates=candidates,
        preferred=["研究连结体", "知识连结体", "文档连结体", primary_name],
        fallback=primary_name,
    )

    priority_slots = [
        ArbitrationSlot(
            priority="P0",
            owner_body=gate_owner,
            objective="先处理高风险、证据冲突、不可逆动作和安全/权限闸门。",
            reason="风险闸门若未通过，后续执行会放大不确定性和返工成本。",
            deferrable=False,
        ),
        ArbitrationSlot(
            priority="P1",
            owner_body=delivery_owner,
            objective=f"保障 {primary_name} 的主链路交付持续推进。",
            reason="主链路决定本轮任务是否形成核心可交付结果。",
            deferrable=False,
        ),
        ArbitrationSlot(
            priority="P2",
            owner_body=enablement_owner,
            objective="处理集成、运行、说明和知识落地等支撑性工作。",
            reason="这些工作直接影响交付的可用性、可维护性和可消费性。",
            deferrable=False,
        ),
        ArbitrationSlot(
            priority="P3",
            owner_body=deferred_owner,
            objective="收纳可延后的研究、优化、美化或扩展项。",
            reason="在高优先级未清空前，这些事项不应阻塞主任务。",
            deferrable=True,
        ),
    ]

    contention_rules = [
        "当 P0 风险闸门未关闭时，其他阶段不得抢占其所需资源。",
        f"当 {primary_name} 的核心交付与其他支撑任务冲突时，优先保障 P1 主链路。",
        "支撑性工作应尽量复用已有阶段产物，不得重新制造同类上下文。",
        "可延后事项统一下沉到 P3，记录到知识交接，不得伪装成阻塞项。",
    ]
    escalation_rules = [
        "当 P0 和 P1 同时争抢同一输入且无法拆分时，升级给全连结指挥体裁决。",
        "当安全、证据和交付目标发生冲突时，优先保留更可验证、更可回退的方案。",
        "当支撑任务超过本轮可承受范围时，转入知识交接和后续迭代计划。",
    ]
    deferred_work = [
        "非阻塞的性能微调、文案美化和额外扩展点。",
        "不影响当前验收的远期抽象和大规模重构。",
    ]

    if repo:
        contention_rules.append(f"涉及仓库入口或发布路径的资源冲突时，优先保证可回滚的仓库装载路径：{repo.url}。")
    if workspace and workspace.test_paths:
        contention_rules.append("存在测试上下文时，验证所需资源不得被文档或美化类任务抢占。")
    if any(stage.owner_body == "知识连结体" for stage in execution_stages):
        deferred_work.append("知识索引之外的补充性复盘内容，可在主任务闭环后继续补录。")
    for body in body_map.values():
        if body.resource_priorities:
            contention_rules.append(f"涉及 {body.name} 工作面时，优先满足：{body.resource_priorities[0]}")
        if body.boundary_rules:
            escalation_rules.append(f"{body.name} 边界约束：{body.boundary_rules[0]}")

    return ResourceArbitration(
        summary=f"围绕任务「{task}」按 P0→P3 的顺序分配资源，先关闸门，再保主链，再做支撑与后置。",
        priority_slots=priority_slots,
        contention_rules=contention_rules,
        escalation_rules=escalation_rules,
        deferred_work=deferred_work,
    )


def _build_openclaw_install_plan(
    task: str,
    primary_name: str,
    support_names: list[str],
    primary_body: LinkBody,
    support_bodies: list[LinkBody],
    mode: str,
) -> OpenClawInstallPlan:
    compat_workspace_root = "install/compat/workspaces"
    if mode == "lite":
        inline_support = "、".join(support_names) if support_names else "无额外协作连结体"
        agents = [
            OpenClawInstallAgent(
                agent_id="exmachina-main",
                display_name="ExMachina 主控体",
                role="single-agent-conductor",
                workspace_dir=f"{compat_workspace_root}/exmachina-main",
                agent_dir=f"{compat_workspace_root}/exmachina-main/agent",
                session_strategy="single-session",
                source="全连结指挥体",
                responsibilities=[
                    "加载协议、边界和验收标准。",
                    f"以内联方式装配主连结体 {primary_name} 与协作链。",
                    "在单 agent 会话内完成主链、补位、收束与最终交付。",
                ],
                handoff_targets=[],
            )
        ]
        binding_plans = [
            OpenClawBindingPlan(
                target_agent_id="exmachina-main",
                binding_mode="default-receiver",
                match_hint="默认接收全部任务入口，不依赖额外 agent 绑定。",
                reason="兼容不支持完整多 agent 安装、绑定和路由机制的 OpenClaw 环境。",
            )
        ]
        install_steps = [
            "将仓库作为 OpenClaw workspace 打开，先读取根目录 `BOOTSTRAP.md`。",
            "运行 `python -m exmachina validate-assets`，确认资产引用完整。",
            "读取 `openclaw-pack/BOOTSTRAP.md`、`manifest.json` 与 `runtime/` 下的 Lite 运行时文件。",
            "由 `exmachina-main` 单 agent 装载主连结体与协作链说明，并在单会话内执行任务。",
        ]
        self_bootstrap_steps = [
            "若 OpenClaw 直接打开仓库，请优先读取根目录 `BOOTSTRAP.md`。",
            "若宿主不支持多 agent 绑定与路由，继续使用 Lite 默认路径，不再要求隔离 workspace。",
            f"安装后由 `exmachina-main` 在单 agent 会话中内联承担主连结体 {primary_name} 与协作链 {inline_support} 的职责。",
        ]
        return OpenClawInstallPlan(
            mode=mode,
            summary=f"围绕任务「{task}」生成可直接供 OpenClaw 单 agent 装载的 Lite 安装计划。",
            repo_install_mode="repo-link-bootstrap-lite",
            requires_multi_agent_binding=False,
            workspace_templates_compat_only=True,
            workspace_entry_files=["openclaw.settings.json", "install/SETTINGS.md", "BOOTSTRAP.md"],
            agents=agents,
            binding_plans=binding_plans,
            install_steps=install_steps,
            self_bootstrap_steps=self_bootstrap_steps,
        )

    agents = [
        OpenClawInstallAgent(
            agent_id="exmachina-main",
            display_name="ExMachina 主控体",
            role="conductor",
            workspace_dir=f"{compat_workspace_root}/exmachina-main",
            agent_dir=f"{compat_workspace_root}/exmachina-main/agent",
            session_strategy="main-session",
            source="全连结指挥体",
            responsibilities=[
                "加载协议、边界和验收标准。",
                f"装配主连结体 {primary_name} 与协作链。",
                "汇总最终结论与安装状态。",
            ],
            handoff_targets=["exmachina-primary", *[f"exmachina-support-{index + 1}" for index in range(len(support_bodies))]],
        ),
        OpenClawInstallAgent(
            agent_id="exmachina-primary",
            display_name=f"ExMachina 主连结体 · {primary_body.name}",
            role="primary-link-body",
            workspace_dir=f"{compat_workspace_root}/exmachina-primary",
            agent_dir=f"{compat_workspace_root}/exmachina-primary/agent",
            session_strategy="isolated-primary-session",
            source=primary_body.name,
            responsibilities=[
                f"负责 {primary_body.name} 的主链路交付。",
                *primary_body.deliverables[:2],
            ],
            handoff_targets=[f"exmachina-support-{index + 1}" for index in range(len(support_bodies))],
        ),
    ]

    for index, body in enumerate(support_bodies, start=1):
        agents.append(
            OpenClawInstallAgent(
                agent_id=f"exmachina-support-{index}",
                display_name=f"ExMachina 协作连结体 · {body.name}",
                role="support-link-body",
                workspace_dir=f"{compat_workspace_root}/exmachina-support-{index}",
                agent_dir=f"{compat_workspace_root}/exmachina-support-{index}/agent",
                session_strategy="isolated-support-session",
                source=body.name,
                responsibilities=[
                    f"负责 {body.name} 的横向补位。",
                    *body.deliverables[:2],
                ],
                handoff_targets=["exmachina-main", "exmachina-primary"],
            )
        )

    binding_plans = [
        OpenClawBindingPlan(
            target_agent_id="exmachina-main",
            binding_mode="default-receiver",
            match_hint="默认接收未显式绑定的任务入口。",
            reason="保证用户只给出仓库链接时，也能先由主控体完成自举。",
        ),
        OpenClawBindingPlan(
            target_agent_id="exmachina-primary",
            binding_mode="task-handoff",
            match_hint=f"主链路任务转交给 {primary_name}。",
            reason="让主连结体在隔离 workspace 中承担主交付。",
        ),
    ]
    for index, body_name in enumerate(support_names, start=1):
        binding_plans.append(
            OpenClawBindingPlan(
                target_agent_id=f"exmachina-support-{index}",
                binding_mode="specialized-support",
                match_hint=f"当任务命中 {body_name} 对应领域时，路由到该协作 agent。",
                reason="让理性、校验、文档、运维、安全、集成等能力按需独立装载。",
            )
        )

    install_steps = [
        "将仓库作为 OpenClaw workspace 打开，先读取根目录 `BOOTSTRAP.md`。",
        "运行 `python -m exmachina validate-assets`，确认资产引用完整。",
        "读取 `openclaw-pack/install/compat/INSTALL.md` 和 `openclaw-pack/install/compat/openclaw.agents.plan.json`。",
        "按安装计划创建主控 agent、主连结体 agent 和协作 agent。",
        "让主控 agent 再次读取 `openclaw-pack/BOOTSTRAP.md` 并进入任务执行。",
    ]
    self_bootstrap_steps = [
        "若 OpenClaw 直接打开仓库，请优先读取根目录 `BOOTSTRAP.md`。",
        "若检测到尚未配置多 agent，请根据 `install/compat/openclaw.agents.plan.json` 生成兼容 workspace。",
        "安装后由 `exmachina-main` 作为默认入口接收用户任务。",
    ]

    return OpenClawInstallPlan(
        mode=mode,
        summary=f"围绕任务「{task}」生成可直接供 OpenClaw 装载的主控 + 主链 + 协作 agent 安装计划。",
        repo_install_mode="repo-link-bootstrap",
        requires_multi_agent_binding=True,
        workspace_templates_compat_only=True,
        workspace_entry_files=["openclaw.settings.json", "install/SETTINGS.md", f"{compat_workspace_root}/"],
        agents=agents,
        binding_plans=binding_plans,
        install_steps=install_steps,
        self_bootstrap_steps=self_bootstrap_steps,
    )


def _build_openclaw_settings_bundle(
    task: str,
    repo: RepoReference | None,
    mode: str,
    primary_body: LinkBody,
    support_bodies: list[LinkBody],
    top_conductor: TopConductor,
    dialogue_contracts: dict[str, dict[str, object]],
) -> OpenClawSettingsBundle:
    workspace_value = "{{EXMACHINA_PACK_ROOT}}"
    if repo:
        workspace_value = repo.url

    target_config_paths = ["~/.openclaw/openclaw.json", "~/.clawdbot/clawdbot.json"]
    template_variables = _build_openclaw_template_variables(mode, workspace_value)
    install_intake = _build_openclaw_install_intake(
        task=task,
        current_mode=mode,
        workspace_value=workspace_value,
        target_config_paths=target_config_paths,
        top_conductor=top_conductor,
        primary_body=primary_body,
        support_bodies=support_bodies,
    )
    main_name = "{{OPENCLAW_CONDUCTOR_NAME}}"
    main_theme = _with_install_context_theme(dialogue_contracts["exmachina-main"]["theme"], include_conductor_name=True)
    if mode == "lite":
        settings_patch = {
            "agents": {
                "list": [
                    {
                        "id": "exmachina-main",
                        "name": main_name,
                        "workspace": workspace_value,
                        "identity": {"theme": main_theme},
                        "sandbox": {"mode": "off"},
                    }
                ],
            }
        }
        channels_template: dict[str, object] = {}
        bindings_template: list[dict[str, object]] = []
        merge_instructions = [
            "先读取 `install/INTAKE.md`，问清语言、全连结指挥体显示名、安装模式和其它配置，再继续安装。",
            "将 `openclaw.settings.json` 中的 ExMachina agent 条目合并进 OpenClaw 主配置。",
            "把 ExMachina agent 的 `workspace` 指向当前仓库或导出包所在路径。",
            "不要修改 OpenClaw 当前默认模型、provider、API 或其它与 ExMachina agent 无关的配置。",
        ]
        usage_notes = [
            "安装前不要跳过问询；至少确认语言、全连结指挥体显示名、安装模式、配置路径和其它配置。",
            "Lite 模式下创建的 ExMachina agent 必须继承 OpenClaw 当前默认模型。",
            "Lite 模式默认不要求 channels/accounts/bindings。",
            "如果 OpenClaw 宿主支持 WebUI 或默认入口，只需要一个主控 agent 即可。",
        ]
    else:
        settings_patch = {
            "agents": {
                "list": [
                    {
                        "id": "exmachina-main",
                        "name": main_name,
                        "workspace": workspace_value,
                        "identity": {"theme": main_theme},
                        "sandbox": {"mode": "off"},
                    },
                    {
                        "id": "exmachina-primary",
                        "name": f"ExMachina 主连结体 · {primary_body.name}",
                        "workspace": workspace_value,
                        "identity": {"theme": _with_install_context_theme(dialogue_contracts["exmachina-primary"]["theme"])},
                        "sandbox": {"mode": "all", "scope": "agent"},
                    },
                    *[
                        {
                            "id": f"exmachina-support-{index}",
                            "name": f"ExMachina 协作连结体 · {body.name}",
                            "workspace": workspace_value,
                            "identity": {
                                "theme": _with_install_context_theme(dialogue_contracts[f"exmachina-support-{index}"]["theme"])
                            },
                            "sandbox": {"mode": "all", "scope": "agent"},
                        }
                        for index, body in enumerate(support_bodies, start=1)
                    ],
                ],
            }
        }
        channels_template = {
            "discord": {
                "enabled": True,
                "accounts": {
                    "main": {"name": main_name, "token": "{{DISCORD_TOKEN_MAIN}}"}
                },
            }
        }
        for index, body in enumerate([primary_body, *support_bodies], start=1):
            channels_template["discord"]["accounts"][f"agent-{index}"] = {
                "name": body.name,
                "token": f"{{{{DISCORD_TOKEN_{index}}}}}",
            }
        bindings_template = [
            {"agentId": "exmachina-main", "match": {"channel": "discord", "accountId": "main"}},
            {"agentId": "exmachina-primary", "match": {"channel": "discord", "accountId": "agent-1"}},
            *[
                {
                    "agentId": f"exmachina-support-{index}",
                    "match": {"channel": "discord", "accountId": f"agent-{index + 1}"},
                }
                for index, _ in enumerate(support_bodies, start=1)
            ],
        ]
        merge_instructions = [
            "先读取 `install/INTAKE.md`，问清语言、全连结指挥体显示名、安装模式和其它配置，再继续安装。",
            "将 ExMachina agent 条目合并进 OpenClaw 主配置。",
            "按需将 `channels_template` 与 `bindings_template` 合并进 OpenClaw 配置，并替换 token 占位符。",
            "不要修改 OpenClaw 当前默认模型、provider、API 或其它与 ExMachina agent 无关的配置。",
            "仅当宿主明确支持完整多 agent 绑定与路由时再启用 Full 模式。",
        ]
        usage_notes = [
            "安装前不要跳过问询；至少确认语言、全连结指挥体显示名、安装模式、配置路径和其它配置。",
            "Full 模式下创建的 ExMachina agent 也必须继承 OpenClaw 当前默认模型。",
            "Full 模式需要宿主支持多个 agent、bindings 和跨 agent 路由。",
            "如果宿主不支持，请退回 Lite 模式。",
        ]

    return OpenClawSettingsBundle(
        mode=mode,
        format_name="openclaw-settings-template-v1",
        summary=f"围绕任务「{task}」生成的 OpenClaw 设置导入模板。",
        target_config_paths=target_config_paths,
        supports_direct_import=(mode == "lite"),
        default_entry_agent_id="exmachina-main",
        template_variables=template_variables,
        install_intake=install_intake,
        dialogue_contracts=dialogue_contracts,
        settings_patch=settings_patch,
        channels_template=channels_template,
        bindings_template=bindings_template,
        merge_instructions=merge_instructions,
        usage_notes=usage_notes,
    )


def _build_openclaw_template_variables(mode: str, workspace_value: str) -> dict[str, dict[str, object]]:
    return {
        "OPENCLAW_INSTALL_LANGUAGE": {
            "default": "zh-CN",
            "required": True,
            "description": "安装问询确认后的默认输出语言。",
        },
        "OPENCLAW_CONDUCTOR_NAME": {
            "default": "ExMachina 主控体",
            "required": True,
            "description": "全连结指挥体 / 主控体的对外显示名。",
        },
        "OPENCLAW_INSTALL_MODE": {
            "default": mode,
            "required": True,
            "description": "本次安装模式；若与当前导出包 mode 不一致，需要先重生成对应模式的 pack。",
        },
        "EXMACHINA_PACK_ROOT": {
            "default": workspace_value,
            "required": True,
            "description": "当前仓库或导出包所在路径。",
        },
        "DISCORD_TOKEN_MAIN": {
            "default": "",
            "required": False,
            "description": "Full 模式主控体绑定 token；仅在启用渠道绑定时需要。",
        },
    }


def _build_openclaw_install_intake(
    task: str,
    current_mode: str,
    workspace_value: str,
    target_config_paths: list[str],
    top_conductor: TopConductor,
    primary_body: LinkBody,
    support_bodies: list[LinkBody],
) -> dict[str, object]:
    support_names_text = "、".join(body.name for body in support_bodies) if support_bodies else "无"
    return {
        "summary": f"在安装任务「{task}」前，必须先确认语言、全连结指挥体显示名、安装模式和配置参数。",
        "blocking_rule": "在语言、全连结指挥体显示名、安装模式、目标配置路径与 workspace 路径未确认前，不得导入 settings patch。",
        "required_questions": [
            {
                "key": "install_language",
                "label": "语言",
                "prompt": "这次安装与后续默认输出使用什么语言？",
                "type": "choice",
                "required": True,
                "default": "zh-CN",
                "placeholder": "OPENCLAW_INSTALL_LANGUAGE",
                "options": ["zh-CN", "en-US", "ja-JP"],
            },
            {
                "key": "conductor_name",
                "label": "全连结指挥体名字",
                "prompt": "希望把全连结指挥体 / 主控体显示为哪个名字？",
                "type": "text",
                "required": True,
                "default": "ExMachina 主控体",
                "placeholder": "OPENCLAW_CONDUCTOR_NAME",
                "notes": [
                    f"默认主控来源仍是 {top_conductor.name}。",
                    "该名字会写入主控 agent 的 display name，并用于安装期提示。",
                ],
            },
            {
                "key": "install_mode",
                "label": "安装模式",
                "prompt": "这次安装走 lite 还是 full？",
                "type": "choice",
                "required": True,
                "default": current_mode,
                "placeholder": "OPENCLAW_INSTALL_MODE",
                "options": ["lite", "full"],
                "notes": [
                    "lite 走单会话内联协作路径。",
                    "full 需要宿主支持多 agent 绑定与路由。",
                ],
            },
            {
                "key": "target_config_path",
                "label": "配置文件路径",
                "prompt": "本次要写入哪份 OpenClaw 配置文件？",
                "type": "path",
                "required": True,
                "default": target_config_paths[0],
            },
            {
                "key": "workspace_root",
                "label": "仓库 / 导出包路径",
                "prompt": "把 workspace 指到哪个仓库或导出包路径？",
                "type": "path",
                "required": True,
                "default": workspace_value,
                "placeholder": "EXMACHINA_PACK_ROOT",
            },
        ],
        "optional_questions": [
            {
                "key": "host_supports_multi_agent",
                "label": "宿主多 agent 能力",
                "prompt": "宿主是否支持多 agent 绑定与外部路由？",
                "type": "boolean",
                "required": False,
                "default": current_mode == "full",
            },
            {
                "key": "extra_config_notes",
                "label": "其它配置",
                "prompt": "还有哪些渠道绑定、token、workspace 或风格配置需要一并记录？",
                "type": "text",
                "required": False,
                "default": "",
            },
        ],
        "confirmation_checks": [
            "语言已确认，后续安装说明与交互默认使用该语言。",
            "全连结指挥体 / 主控体显示名已确认。",
            "安装模式已确认，且与宿主能力匹配。",
            f"主连结体已确认：{primary_body.name}。",
            f"协作连结体已确认：{support_names_text}。",
            "目标 OpenClaw 配置路径与 workspace 路径已确认。",
            "当前默认模型保持不变，ExMachina agent 将继承现有默认模型。",
            "额外配置项已确认或显式留空。",
        ],
        "mode_resolution_rules": [
            "如果用户选择 full，但当前导出包是 lite，先重生成 full 包，再继续安装。",
            "如果宿主不支持多 agent 绑定与路由，则强制退回 lite。",
            "如果配置路径或 workspace 路径未确认，则暂停安装。",
        ],
        "answers_template": {
            "install_language": "zh-CN",
            "conductor_name": "ExMachina 主控体",
            "install_mode": current_mode,
            "target_config_path": target_config_paths[0],
            "workspace_root": workspace_value,
            "host_supports_multi_agent": current_mode == "full",
            "extra_config_notes": "",
        },
    }


def _with_install_context_theme(theme: str, include_conductor_name: bool = False) -> str:
    prefix_parts = [
        "安装期约束：默认输出语言使用 {{OPENCLAW_INSTALL_LANGUAGE}}。",
        "本次安装模式记为 {{OPENCLAW_INSTALL_MODE}}。",
    ]
    if include_conductor_name:
        prefix_parts.append("全连结指挥体 / 主控体显示名使用 {{OPENCLAW_CONDUCTOR_NAME}}。")
    return "".join(prefix_parts) + theme


def _build_openclaw_prompt(
    repo: RepoReference | None,
    task: str,
    mode: str,
    main_dialogue_contract: dict[str, object],
) -> str:
    response_shape = " / ".join(str(item) for item in main_dialogue_contract.get("response_shape", []))
    tone_rules = "；".join(
        str(item).rstrip("。； ")
        for item in list(main_dialogue_contract.get("tone_rules", []))[:2]
    )
    surface_persona = "；".join(
        str(item).rstrip("。； ")
        for item in list(main_dialogue_contract.get("surface_persona", []))[:2]
    )
    speech_primitives = " / ".join(str(item) for item in list(main_dialogue_contract.get("speech_primitives", []))[:6])
    sample_utterances = "；".join(
        str(item).rstrip("。； ")
        for item in list(main_dialogue_contract.get("sample_utterances", []))[:3]
    )
    softening_phrase = next(
        (
            str(item).rstrip("。； ")
            for item in list(main_dialogue_contract.get("softening_phrases", []))
            if "本机" in str(item)
        ),
        "",
    )
    dialogue_suffix = (
        f"执行时保持 ExMachina 的分层口吻：{surface_persona}；{tone_rules}。"
        f"优先使用 {speech_primitives} 这类短句词汇。"
        f"默认输出遵循 {response_shape}。"
        f"可参考句式：{sample_utterances}。"
        + (f"自称统一使用“本机”，例如：{softening_phrase}。" if softening_phrase else "")
    )
    if mode == "lite":
        if repo:
            return (
                f"请读取远程仓库 {repo.url} 中的 /openclaw-pack/BOOTSTRAP.md，"
                "以 Lite 默认路径装载协议、主连结体与协作链说明，由单个主控会话内联完成执行，"
                f"然后执行任务：{task}。{dialogue_suffix}"
            )
        return (
            "请读取本项目的 /openclaw-pack/BOOTSTRAP.md，"
            "以 Lite 默认路径装载协议、主连结体与协作链说明，由单个主控会话内联完成执行，"
            f"然后执行任务：{task}。{dialogue_suffix}"
        )
    if repo:
        return (
            f"请读取远程仓库 {repo.url} 中的 /openclaw-pack/BOOTSTRAP.md，"
            "先装载 /openclaw-pack/protocols/ 下的绝对理性协议，再按『全连结指挥体 → 连结体 → 连结指挥体 → 子个体』结构工作，"
            f"然后执行任务：{task}。{dialogue_suffix}"
        )
    return (
        "请读取本项目的 /openclaw-pack/BOOTSTRAP.md，"
        "先装载 /openclaw-pack/protocols/ 下的绝对理性协议，再按『全连结指挥体 → 连结体 → 连结指挥体 → 子个体』结构工作，"
        f"然后执行任务：{task}。{dialogue_suffix}"
    )


def _build_openclaw_prompt_with_install_intake(
    repo: RepoReference | None,
    task: str,
    mode: str,
    main_dialogue_contract: dict[str, object],
) -> str:
    intake_prefix = (
        "开始安装前，先向用户完成 install/INTAKE.md 中的问询：语言、全连结指挥体显示名、安装模式、配置路径和其它配置。"
        "在答案确认前，不要导入 OpenClaw 配置。"
    )
    return intake_prefix + _build_openclaw_prompt(repo, task, mode, main_dialogue_contract)


def _dedupe_names(candidates: list[str], primary_name: str) -> list[str]:
    deduped: list[str] = []
    for name in candidates:
        if name == primary_name:
            continue
        if name not in deduped:
            deduped.append(name)
    return deduped


def _support_rule_matches(
    rule: dict,
    task: str,
    repo: RepoReference | None,
    workspace: WorkspaceSnapshot | None,
    primary_name: str,
) -> bool:
    lowered_task = task.lower()

    if not _name_rule_matches(primary_name, rule.get("primary_is")):
        return False
    if rule.get("primary_is_not") is not None and _name_rule_matches(primary_name, rule.get("primary_is_not")):
        return False
    if rule.get("requires_repo") and not repo:
        return False
    if rule.get("requires_tests") and not (workspace and workspace.test_paths):
        return False
    if rule.get("requires_workspace") and not (workspace and workspace.detected_languages):
        return False

    task_keywords = rule.get("task_keywords", [])
    if task_keywords and not any(keyword.lower() in lowered_task for keyword in task_keywords):
        return False

    return True


def _name_rule_matches(name: str, expected: str | list[str] | None) -> bool:
    if expected is None:
        return True
    if isinstance(expected, str):
        return name == expected
    return name in expected


def _describe_primary_selection(
    primary_score: LinkBodyScore,
    fallback_used: bool,
    fallback_primary: str,
) -> list[str]:
    reasons = [f"{primary_score.name} 综合得分最高，为 {primary_score.score} 分。"]
    if primary_score.matched_keywords:
        reasons.append(f"命中关键词：{'、'.join(primary_score.matched_keywords)}。")
    if primary_score.matched_priority_keywords:
        reasons.append(f"命中高权重关键词：{'、'.join(primary_score.matched_priority_keywords)}。")
    reasons.extend(f"加分依据：{item}。" for item in primary_score.bonus_reasons)
    if fallback_used:
        reasons.append(f"所有候选得分均为 0，回退到默认主连结体 {fallback_primary}。")
    return reasons


def _describe_support_rule(rule: dict, primary_name: str) -> str:
    fragments: list[str] = []
    if rule.get("primary_is"):
        fragments.append(f"主连结体为 {rule['primary_is']}")
    if rule.get("primary_is_not"):
        fragments.append(f"主连结体不是 {rule['primary_is_not']}")
    if rule.get("requires_repo"):
        fragments.append("存在仓库上下文")
    if rule.get("requires_tests"):
        fragments.append("存在测试上下文")
    if rule.get("requires_workspace"):
        fragments.append("存在工作区上下文")
    if rule.get("task_keywords"):
        fragments.append(f"任务命中关键词 {'、'.join(rule['task_keywords'])}")
    detail = "；".join(fragments) if fragments else "命中默认协作规则"
    return f"触发协作连结体 {rule['body']}：{detail}。"
