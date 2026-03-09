from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = REPO_ROOT / "exmachina" / "data"
SUBAGENT_ROOT = DATA_ROOT / "subagents"
CONDUCTOR_ROOT = DATA_ROOT / "conductors"
LINK_BODY_ROOT = DATA_ROOT / "link_bodies"
SKILLS_ROOT = REPO_ROOT / "skills"

DEFAULT_CHILD_OUTPUT_CONTRACT = [
    "背景事实",
    "关键观察或证据",
    "当前结论或产出",
    "风险与边界",
    "建议交接对象",
]

DEFAULT_CONDUCTOR_REPORTING_CONTRACT = [
    "当前阶段状态",
    "关键证据或阻塞",
    "是否需要升级",
    "下一步行动建议",
]

DEFAULT_BODY_EXIT_CONTRACT = [
    "交付物可被下游直接消费",
    "风险、未知和边界已明确",
    "后续交接对象和下一步已明确",
]

SUBAGENT_CATEGORY_MAP = {
    "上下文体": "research",
    "侦察体": "planning",
    "侦查体": "implementation",
    "假设体": "research",
    "决策体": "knowledge",
    "加固体": "security",
    "反证体": "rationality",
    "发布体": "integration",
    "合规体": "security",
    "告警体": "operations",
    "回归体": "validation",
    "回滚体": "operations",
    "复现体": "validation",
    "威胁体": "security",
    "审核体": "implementation",
    "审计体": "security",
    "拆解体": "planning",
    "接口体": "architecture",
    "接驳体": "integration",
    "文档体": "integration",
    "断言体": "validation",
    "术语体": "knowledge",
    "校准体": "rationality",
    "校订体": "documentation",
    "比对体": "research",
    "汇报体": "common",
    "溯源体": "research",
    "演练体": "operations",
    "盘点体": "documentation",
    "示例体": "documentation",
    "索引体": "knowledge",
    "约束体": "planning",
    "结构体": "documentation",
    "编码体": "implementation",
    "落图体": "architecture",
    "裁决体": "rationality",
    "观测体": "operations",
    "证据体": "rationality",
    "路线体": "planning",
    "边界体": "architecture",
    "配置体": "integration",
    "问题体": "knowledge",
    "风控体": "architecture",
}

CATEGORY_REASONING_RULES = {
    "planning": ["先澄清任务边界，再讨论路线与执行顺序。", "所有计划都必须显式列出前提、风险和退出条件。", "不把愿景口号误当作可执行计划。"],
    "research": ["先收集现状事实，再给出解释、假设或比较。", "所有推断都必须保留证据来源和置信度。", "发现信息缺口时优先输出缺口，不编造结论。"],
    "architecture": ["先拆边界和依赖，再做接口与结构判断。", "任何结构建议都要说明适用边界和风险。", "优先选择可测试、可回退、可演化的结构。"],
    "implementation": ["先找最小可行改动，再考虑扩展和清理。", "所有实现都必须明确入口、影响面和回退方式。", "不为未来假设提前引入复杂抽象。"],
    "validation": ["先定义验证口径，再收集复现实验和断言结果。", "验证失败时优先输出可复现步骤和观测。", "不把一次通过误判为全面正确。"],
    "integration": ["先梳理入口和依赖，再安排接入、配置和交付。", "任何发布或集成建议都要有回退路径。", "不把隐性前置条件留给下游猜。"],
    "documentation": ["先盘点读者视角和现有资料，再整理结构与示例。", "文档必须对齐真实实现和导出结构。", "不以优美措辞掩盖事实缺口。"],
    "operations": ["先识别运行面风险，再定义观测、告警和回退。", "所有稳定性判断都必须指向具体观测点。", "不在无回退预案时推进不可逆发布动作。"],
    "security": ["先识别攻击面、权限边界和敏感数据，再下判断。", "所有风险判断都必须区分已证实问题和待验证假设。", "优先选择更可验证、更可回退的安全处置方案。"],
    "knowledge": ["先沉淀事实与决策，再组织索引和复用入口。", "所有知识条目都必须可追溯到路径、命令或结论来源。", "不把临时猜测写进长期规范。"],
    "rationality": ["先分级证据，再比较推理链和风险。", "主动寻找反证和冲突，不追求表面一致。", "无法裁决时必须升级而不是主观拍板。"],
    "common": ["先归并事实上游结果，再压缩成可消费总结。", "总结必须保留风险、未知和下一步，不只写亮点。", "不替上游角色篡改其结论含义。"],
}

CATEGORY_TOOLS_GUIDANCE = {
    "planning": ["优先读取需求、README、issue、上游交接和现有流程文件。", "涉及执行路线时必须给出阶段划分和验收口径。"],
    "research": ["优先阅读源代码、文档、配置、测试、日志和历史决策记录。", "所有研究结论都应附带路径、命令或证据引用。"],
    "architecture": ["优先分析模块目录、接口定义、配置边界和依赖方向。", "涉及抽象设计时必须同时说明约束和非目标。"],
    "implementation": ["优先使用现有工具链、已有模式和可运行验证。", "改动前后都要保留可复核的命令、路径和结果。"],
    "validation": ["优先使用测试、命令复现、日志和直接证据。", "断言必须具体到条件、输入和期望行为。"],
    "integration": ["优先检查启动入口、部署配置、目录结构和交付文档。", "接入说明必须可复用、可复制、可回滚。"],
    "documentation": ["优先对照 README、示例、命令和真实文件结构。", "示例必须能追溯到实际命令、路径或配置。"],
    "operations": ["优先分析运行入口、日志、监控、部署路径和历史事故信息。", "演练和回滚策略都要明确触发条件与执行步骤。"],
    "security": ["优先检查权限、密钥、配置、输入边界和日志泄露。", "所有安全结论都应保留证据来源和复核建议。"],
    "knowledge": ["优先读取决策记录、文档、目录结构和输出产物。", "术语与索引必须服务下轮任务消费。"],
    "rationality": ["优先汇总代码、测试、日志、命令输出和上游交接中的直接证据。", "所有裁决都要保留证据等级、放弃原因和置信度。"],
    "common": ["优先消费结构化交接和已确认结论。", "总结中必须保留来源角色和下游消费方式。"],
}

BODY_META = {
    "策划连结体": ("10_策划连结体.json", "10_策划连结指挥体.json", "planning-link-body", "Planning Link Body", "需求澄清、任务拆解、约束收束与路线规划", "阶段 1 · 任务澄清", "阶段 2 · 主链路交付"),
    "研究连结体": ("11_研究连结体.json", "11_研究连结指挥体.json", "research-link-body", "Research Link Body", "现状分析、上下文补齐、候选方案比对与来源追踪", "阶段 1 · 任务澄清", "阶段 2 · 主链路交付"),
    "架构连结体": ("12_架构连结体.json", "12_架构连结指挥体.json", "architecture-link-body", "Architecture Link Body", "边界划分、接口契约、风险前置与结构落图", "阶段 2 · 主链路交付", "阶段 1 · 任务澄清"),
    "实作连结体": ("13_实作连结体.json", "13_实作连结指挥体.json", "implementation-link-body", "Implementation Link Body", "代码实现、关键入口落地、最小可行交付与实现质量收束", "阶段 2 · 主链路交付", "阶段 3 · 交叉校验"),
    "校验连结体": ("14_校验连结体.json", "14_校验连结指挥体.json", "validation-link-body", "Validation Link Body", "复现、断言、证据收集与回归验证", "阶段 3 · 交叉校验", "阶段 2 · 主链路交付"),
    "集成连结体": ("15_集成连结体.json", "15_集成连结指挥体.json", "integration-link-body", "Integration Link Body", "接入路径、配置收束、发布入口和交付说明", "阶段 4 · 集成交接", "阶段 2 · 主链路交付"),
    "文档连结体": ("16_文档连结体.json", "16_文档连结指挥体.json", "documentation-link-body", "Documentation Link Body", "资料盘点、结构整理、示例编写和校订发布", "阶段 4 · 集成交接", "阶段 2 · 主链路交付"),
    "运维连结体": ("17_运维连结体.json", "17_运维连结指挥体.json", "operations-link-body", "Operations Link Body", "运行稳定性、监控告警、回滚预案和演练设计", "阶段 2 · 主链路交付", "阶段 3 · 交叉校验"),
    "安全连结体": ("18_安全连结体.json", "18_安全连结指挥体.json", "security-link-body", "Security Link Body", "威胁建模、权限审计、加固建议与合规收束", "阶段 3 · 交叉校验", "阶段 2 · 主链路交付"),
    "知识连结体": ("19_知识连结体.json", "19_知识连结指挥体.json", "knowledge-link-body", "Knowledge Link Body", "术语统一、决策沉淀、索引组织和问题归档", "阶段 4 · 集成交接", "阶段 1 · 任务澄清"),
    "理性连结体": ("20_理性连结体.json", "20_理性连结指挥体.json", "rationality-link-body", "Rationality Link Body", "证据分级、反证搜索、冲突裁决与置信度校准", "阶段 3 · 交叉校验", "阶段 1 · 任务澄清"),
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_subagent_memberships() -> dict[str, list[str]]:
    memberships: dict[str, list[str]] = {}
    for path in sorted(LINK_BODY_ROOT.glob("*.json")):
        body = load_json(path)
        conductor_name = Path(body["conductor_file"]).stem.split("_", 1)[1]
        for child_file in body["child_agent_files"]:
            child_name = Path(child_file).stem.split("_", 1)[1]
            memberships.setdefault(child_name, [])
            if conductor_name not in memberships[child_name]:
                memberships[child_name].append(conductor_name)
    for child_name in list(memberships):
        if child_name != "汇报体" and "汇报体" not in memberships[child_name]:
            memberships[child_name].append("汇报体")
    memberships["汇报体"] = ["各连结指挥体", "全连结指挥体"]
    return memberships


def regenerate_subagents() -> None:
    memberships = build_subagent_memberships()
    for path in sorted(SUBAGENT_ROOT.glob("*.json")):
        subagent = load_json(path)
        name = subagent["name"]
        category = SUBAGENT_CATEGORY_MAP[name]
        focus = subagent["mission"].rstrip("。")
        role_id = path.stem.split("_", 1)[0]
        handoff_targets = memberships.get(name, ["汇报体"])
        subagent.update(
            {
                "english_alias": f"subagent-{role_id}",
                "identity": f"{name} 是负责「{focus}」的原子执行角色，只交付本职责范围内的结论、证据与交接输入。",
                "bilingual_summary": f"负责：{focus}。 / Role: {focus}.",
                "core_responsibilities": [
                    f"围绕「{focus}」收集事实、结构化产出和可交接结果。",
                    f"识别与「{focus}」相关的关键风险、依赖和信息缺口。",
                    f"将「{focus}」结果压缩成可供下游直接消费的交接内容。",
                ],
                "non_goals": ["不越权替代连结指挥体进行最终裁决。", "不在证据不足时冒充确定性结论。", "不替其他角色承担其专业工作面。"],
                "inputs": ["当前阶段目标", "上游交接物", "仓库、工作区或文档中的直接事实", f"与「{focus}」相关的补充上下文"],
                "input_requirements": ["输入必须能追溯到任务、路径、命令、文档或上游交接。", "输入若不足以支撑执行，必须先输出缺口和补齐建议。", "涉及结论判断时必须带上证据来源或验证计划。"],
                "workflow": ["确认当前阶段目标、边界和验收口径。", f"执行与「{focus}」直接相关的分析、整理或实施动作。", "把结果整理成结构化输出并显式标记风险、未知和下一步。", "按交接契约提交给下游对象或汇报体。"],
                "reasoning_rules": CATEGORY_REASONING_RULES[category],
                "output_contract": DEFAULT_CHILD_OUTPUT_CONTRACT,
                "handoff_targets": handoff_targets,
                "handoff_payloads": list(subagent.get("outputs", [])),
                "escalation_triggers": ["关键输入缺失且无法自行补齐。", "出现高风险、不可逆或越权动作。", f"围绕「{focus}」的证据冲突导致无法继续推进。"],
                "failure_modes": [f"只给出「{focus}」结论，未附证据和边界。", "没有完成结构化交接就提前结束。", "把局部观察误写成全局结论。"],
                "anti_patterns": ["把推断伪装成事实。", "绕过交接对象直接扩散结论。", "为了看起来完整而补写不存在的信息。"],
                "quality_bar": [f"输出可直接服务 {handoff_targets[0]} 或其他下游角色。", "关键判断具备证据引用或明确验证路径。", "风险、未知和下一步清晰可读。"],
                "tools_guidance": CATEGORY_TOOLS_GUIDANCE[category],
            }
        )
        write_json(path, subagent)


def regenerate_bodies_and_conductors() -> None:
    for body_name, (body_file, conductor_file, skill_id, skill_label, focus, owner_stage, support_stage) in BODY_META.items():
        body_path = LINK_BODY_ROOT / body_file
        conductor_path = CONDUCTOR_ROOT / conductor_file
        body = load_json(body_path)
        conductor = load_json(conductor_path)
        child_names = [Path(item).stem.split("_", 1)[1] for item in body["child_agent_files"]]

        body.update(
            {
                "english_alias": skill_id,
                "bilingual_summary": f"负责{focus}。 / Handles {focus}.",
                "usage_scenarios": [f"当任务需要 {focus} 时启用。", f"当 {body_name} 需要作为主链或协作链补位时启用。"],
                "entry_conditions": ["任务边界已经明确需要该工作面参与。", "存在足够输入供该连结体工作。"],
                "exit_conditions": DEFAULT_BODY_EXIT_CONTRACT,
                "deliverable_contracts": [f"交付必须覆盖：{item}" for item in body.get("deliverables", [])],
                "support_capabilities": [f"为其他连结体提供与{focus}相关的补位输入。", "在主链路需要时提供结构化阶段交接和风险说明。", "把局部专业判断收束为可消费的工作面结论。"],
                "collaboration_rules": ["优先复用上游阶段产物，不重复制造上下文。", "跨连结体结论必须通过连结指挥体或 handoff 契约传递。", "若发现越权、冲突或高风险动作，先升级再继续。"],
                "resource_priorities": [f"优先保障 {body_name} 的核心交付和必要验证。", f"涉及 {focus} 的关键输入不得被非阻塞工作抢占。"],
                "boundary_rules": [f"{body_name} 只处理 {focus} 对应的工作面。", "需要跨域裁决时必须交给上游指挥体或主控体。"],
                "fallback_modes": ["输入不足时退回最小可验证结论和缺口清单。", "依赖未满足时输出阻塞、风险和补齐建议。"],
                "failure_modes": ["成员间重复劳动或职责重叠。", "交付缺少明确契约、边界或交接对象。", "越权替代其他连结体判断。"],
                "default_stage_mapping": [
                    {
                        "stage_name": owner_stage,
                        "goal": f"由 {body_name} 主责完成 {focus} 的核心交付。",
                        "deliverables": list(body.get("deliverables", [])),
                        "exit_checks": [f"{body_name} 的关键交付已形成结构化结果。", "风险、边界和后续动作已经明确。", "交接物可直接被下游消费。"],
                    },
                    {
                        "stage_name": support_stage,
                        "goal": f"由 {body_name} 为其他工作面提供 {focus} 的补位输入。",
                        "deliverables": [f"面向主责连结体的 {focus} 补位结论", "风险与边界提醒"],
                        "exit_checks": ["补位输入已经按 handoff 契约交付给 owner。", "补位结论没有越过本连结体职责边界。"],
                    },
                ],
                "recommended_skill": {"skill_id": skill_id, "skill_path": f"skills/{skill_id}/SKILL.md", "purpose": f"在任务主要命中 {body_name} 工作面时，提供对应的流程、边界和交接模板。"},
            }
        )
        write_json(body_path, body)

        conductor.update(
            {
                "english_alias": f"{skill_id}-conductor",
                "identity": f"负责 {body_name} 内部成员调度、依赖管理、阶段收束与升级判断。",
                "bilingual_summary": f"负责 {body_name} 的内部调度与收束。 / Coordinates and closes work inside {body_name}.",
                "stage_ownership": [owner_stage, support_stage],
                "dispatch_rules": [f"优先激活最能支撑 {focus} 的关键子个体。", "先明确 owner/support，再安排执行顺序。", "阶段输入不足时先输出缺口，不盲目推进。"],
                "member_activation_rules": [f"默认按 {', '.join(child_names)} 的顺序激活关键成员。", "补位成员只在需要时拉起，避免无效并发。"],
                "dependency_rules": ["未收到上游明确交接前，不得假设前置条件已满足。", "共享输入必须统一语义、版本和交接格式。"],
                "conflict_resolution_rules": ["先比较证据等级、输入来源和适用边界。", "冲突无法收敛时升级给理性连结体或全连结指挥体。"],
                "evidence_requirements": ["关键阶段结论必须引用代码、测试、日志、配置或明确输入。", "所有建议都要说明风险、边界和置信度。"],
                "handoff_contract_template": ["当前阶段目标与完成度", "结构化交付物摘要", "风险、未知与下游待续工作"],
                "reporting_contract": DEFAULT_CONDUCTOR_REPORTING_CONTRACT,
                "escalation_policy": ["出现高风险不可逆动作时必须升级。", "发现证据冲突、越权动作或关键依赖缺失时必须升级。"],
                "failure_modes": ["成员顺序错乱导致返工或结论冲突。", "交接信息不完整导致下游无法消费。", "在边界未收束前放任任务扩散。"],
                "anti_patterns": ["越过成员输入直接编造细节。", "用口头统一替代结构化收束。", "跳过升级或 handoff 契约。"],
            }
        )
        write_json(conductor_path, conductor)


def regenerate_top_conductor() -> None:
    path = CONDUCTOR_ROOT / "00_全连结指挥体.json"
    conductor = load_json(path)
    conductor.update(
        {
            "english_alias": "global-conductor",
            "identity": "负责统筹任务边界、验收标准、主链与协作链装配、升级裁决与最终收束的顶层指挥体。",
            "bilingual_summary": "负责统筹全局边界、验收和升级裁决。 / Coordinates global boundaries, acceptance, and escalations.",
            "core_duties": ["确认任务边界、验收标准和主连结体选型。", "在需要时拉起协作连结体并控制跨链路交接。", "统一汇总最终交付、风险、升级决策与后续动作。"],
            "operating_rules": ["先加载理性协议，再加载角色和运行时文件。", "先收束边界和证据，再做跨链路派发。", "所有升级都必须附带当前事实、风险和候选路径。"],
            "handoff_policy": ["所有跨连结体交接都必须可追踪、可回收、可升级。", "主控体必须保留最终汇总的统一口径。"],
            "escalation_policy": ["证据冲突、权限风险和不可逆动作统一升级到主控体。", "任一连结体无法判断边界时不得擅自继续推进。"],
            "anti_patterns": ["跳过协议直接派发任务。", "忽略升级信号或遮蔽风险。", "在主线未收束前扩散过多并发工作。"],
            "quality_bar": ["全局边界、验收、升级路径始终清晰。", "最终输出包含证据、结论、风险、置信度和下一步。"],
        }
    )
    write_json(path, conductor)


def regenerate_default_profile() -> None:
    path = DATA_ROOT / "default_profile.json"
    profile = load_json(path)
    profile["content_policy"] = {
        "primary_language": "zh-CN",
        "secondary_language": "en",
        "style": "structured-role-prompts",
        "allow_inspiration_reference_in_readme_only": True,
    }
    profile["asset_defaults"] = {
        "child_output_contract": DEFAULT_CHILD_OUTPUT_CONTRACT,
        "conductor_reporting_contract": DEFAULT_CONDUCTOR_REPORTING_CONTRACT,
        "body_exit_contract": DEFAULT_BODY_EXIT_CONTRACT,
    }
    profile["validation_policy"] = {
        "strict_mode": True,
        "require_bilingual_summary": True,
        "require_skill_binding": True,
    }
    profile["skill_catalog"] = {
        body_name: {"skill_id": skill_id, "skill_path": f"skills/{skill_id}/SKILL.md", "display_name": skill_label}
        for body_name, (_, _, skill_id, skill_label, _, _, _) in BODY_META.items()
    }
    write_json(path, profile)


def regenerate_skills() -> None:
    (SKILLS_ROOT / "SKILL.md").write_text(
        """---
name: exmachina-project-maintainer
description: Use when extending or maintaining the ExMachina repository: evolving role assets, planner/runtime/exporter schemas, repo-local skills, tests, and the generated OpenClaw pack.
---

# ExMachina Project Maintainer

English summary: Maintains ExMachina schemas, role assets, runtime exports, skills, tests, and the demo pack.

## Workflow

1. Read `references/file-map.md` to locate the change surface.
2. If the task changes role assets, start from `skills/scripts/regenerate_role_assets.py` and `exmachina/data/default_profile.json`.
3. If the task changes exported structure, keep `exmachina/models.py`, `exmachina/planner.py`, `exmachina/runtime.py`, and `exmachina/exporter.py` in sync.
4. If the task changes repo-local skills, update both `skills/SKILL.md` and the affected `skills/<link-body-skill>/SKILL.md` files.
5. If the task changes user-facing structure, update `README.md` and `docs/ARCHITECTURE.md`.
6. Regenerate role assets with `python skills/scripts/regenerate_role_assets.py`.
7. Regenerate the demo pack with `python skills/scripts/regenerate_demo_pack.py`.
8. Run `python -m exmachina validate-assets` and `python -m unittest discover -s tests -p "test_*.py"` before finishing.

## Rules

- Do not change one schema/output surface in isolation; models, planner, runtime, exporter, assets, and tests move together.
- Keep `recommended_skill` and `skill_catalog` aligned with the actual `skills/<skill-id>/SKILL.md` files.
- Keep inspiration-related wording out of non-README files.
""",
        encoding="utf-8",
    )

    for body_name, (_, _, skill_id, _, focus, _, _) in BODY_META.items():
        skill_dir = SKILLS_ROOT / skill_id
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(
            f"""---
name: {skill_id}
description: Use when the task is primarily owned by {body_name} and needs its role-specific workflow, boundaries, and handoff expectations.
---

# {body_name} Skill

English summary: Use this skill when the task is primarily about {focus}.

## When to use

- 当任务主要命中 {body_name} 对应工作面时。
- 当你需要围绕 {focus} 组织主链路或协作补位时。
- 当你需要按该连结体的阶段、交接和升级契约稳定推进任务时。

## Boundaries

- 只处理 {body_name} 负责的工作面，不替其他连结体做最终裁决。
- 发现跨域依赖、证据冲突或不可逆风险时，立即升级给主控体或理性链路。
- 所有输出都必须写清事实、判断、风险、边界和下一步。

## Workflow

1. 读取当前阶段目标、边界、交接契约和 runtime queue。
2. 激活最能支撑 {focus} 的关键子个体。
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
""",
            encoding="utf-8",
        )


def main() -> int:
    regenerate_subagents()
    regenerate_bodies_and_conductors()
    regenerate_top_conductor()
    regenerate_default_profile()
    regenerate_skills()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
