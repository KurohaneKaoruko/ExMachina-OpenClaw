from __future__ import annotations

import json
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path
from typing import Any


REQUIRED_TOP_CONDUCTOR_KEYS = {
    "name",
    "mission",
    "principles",
    "english_alias",
    "identity",
    "bilingual_summary",
    "core_duties",
    "operating_rules",
    "handoff_policy",
    "escalation_policy",
    "anti_patterns",
    "quality_bar",
}
REQUIRED_LINK_BODY_KEYS = {
    "entity_type",
    "identity",
    "english_alias",
    "bilingual_summary",
    "member_selection_rule",
    "focus",
    "keywords",
    "reason_template",
    "deliverables",
    "usage_scenarios",
    "entry_conditions",
    "exit_conditions",
    "deliverable_contracts",
    "support_capabilities",
    "collaboration_rules",
    "resource_priorities",
    "boundary_rules",
    "fallback_modes",
    "failure_modes",
    "rationality_obligations",
    "default_stage_mapping",
    "recommended_skill",
    "conductor_file",
    "child_agent_files",
}
REQUIRED_LINK_CONDUCTOR_KEYS = {
    "name",
    "mission",
    "duties",
    "checks",
    "english_alias",
    "identity",
    "bilingual_summary",
    "stage_ownership",
    "dispatch_rules",
    "member_activation_rules",
    "dependency_rules",
    "conflict_resolution_rules",
    "evidence_requirements",
    "handoff_contract_template",
    "reporting_contract",
    "escalation_policy",
    "failure_modes",
    "anti_patterns",
}
REQUIRED_CHILD_AGENT_KEYS = {
    "name",
    "mission",
    "outputs",
    "checks",
    "english_alias",
    "identity",
    "bilingual_summary",
    "core_responsibilities",
    "non_goals",
    "inputs",
    "input_requirements",
    "workflow",
    "reasoning_rules",
    "output_contract",
    "handoff_targets",
    "handoff_payloads",
    "escalation_triggers",
    "failure_modes",
    "anti_patterns",
    "quality_bar",
    "tools_guidance",
}


@dataclass
class AssetValidationResult:
    profile_path: str
    checked_link_bodies: int = 0
    checked_conductors: int = 0
    checked_subagents: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors


def validate_profile_assets(profile_path: str | None = None) -> AssetValidationResult:
    root, raw_profile = _load_raw_profile(profile_path)
    result = AssetValidationResult(profile_path=str(root / "default_profile.json"))

    try:
        from .profile import load_profile

        resolved_profile = load_profile(str(root / "default_profile.json"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        resolved_profile = {"link_bodies": {}}
        result.errors.append(f"加载运行时画像失败：{exc}。")

    _validate_top_conductor(raw_profile, root, result)
    _validate_profile_metadata(raw_profile, root, result)
    _validate_selection_rules(raw_profile, result)
    _validate_link_bodies(raw_profile, resolved_profile, root, result)
    _validate_orphan_assets(raw_profile, root, result)
    return result


def _load_raw_profile(profile_path: str | None) -> tuple[Path, dict[str, Any]]:
    if profile_path:
        profile_file = Path(profile_path)
        root = profile_file.parent
    else:
        root = Path(resources.files("exmachina").joinpath("data"))
        profile_file = root / "default_profile.json"

    raw_profile = json.loads(profile_file.read_text(encoding="utf-8-sig"))
    return root, raw_profile


def _validate_top_conductor(raw_profile: dict[str, Any], root: Path, result: AssetValidationResult) -> None:
    conductor_file = raw_profile.get("conductor_file")
    if not conductor_file:
        result.errors.append("缺少顶层 `conductor_file`。")
        return

    payload = _read_json_file(root, conductor_file, result, "顶层指挥体")
    if payload is None:
        return

    missing = sorted(REQUIRED_TOP_CONDUCTOR_KEYS - payload.keys())
    if missing:
        result.errors.append(f"顶层指挥体缺少字段：{', '.join(missing)}。")
    result.checked_conductors += 1


def _validate_profile_metadata(raw_profile: dict[str, Any], root: Path, result: AssetValidationResult) -> None:
    for key in ("content_policy", "asset_defaults", "validation_policy", "skill_catalog"):
        if key not in raw_profile:
            result.errors.append(f"default_profile.json 缺少顶层字段：{key}。")

    repo_root = root.parent.parent if root.parent.name == "exmachina" else root.parent
    for body_name, skill in raw_profile.get("skill_catalog", {}).items():
        skill_path = skill.get("skill_path")
        if not skill_path:
            result.errors.append(f"skill_catalog 中 `{body_name}` 缺少 `skill_path`。")
            continue
        if not (repo_root / skill_path).exists():
            result.errors.append(f"skill_catalog 中 `{body_name}` 引用了不存在的 skill：{skill_path}。")


def _validate_selection_rules(raw_profile: dict[str, Any], result: AssetValidationResult) -> None:
    link_body_names = set(raw_profile.get("link_bodies", {}).keys())
    selection = raw_profile.get("selection", {})

    fallback_primary = selection.get("fallback_primary")
    if fallback_primary and fallback_primary not in link_body_names:
        result.errors.append(f"`fallback_primary` 引用了不存在的连结体：{fallback_primary}。")

    for rule in selection.get("support_rules", []):
        body_name = rule.get("body")
        if body_name and body_name not in link_body_names:
            result.errors.append(f"`support_rules` 引用了不存在的连结体：{body_name}。")

    for owner, values in selection.get("fallback_supports", {}).items():
        if owner not in link_body_names:
            result.errors.append(f"`fallback_supports` 的键引用了不存在的连结体：{owner}。")
        for body_name in values:
            if body_name not in link_body_names:
                result.errors.append(f"`fallback_supports` 引用了不存在的连结体：{body_name}。")


def _validate_link_bodies(
    raw_profile: dict[str, Any],
    resolved_profile: dict[str, Any],
    root: Path,
    result: AssetValidationResult,
) -> None:
    for body_name, spec in raw_profile.get("link_bodies", {}).items():
        body_file = spec.get("body_file")
        if not body_file:
            result.errors.append(f"连结体 `{body_name}` 缺少 `body_file`。")
            continue

        body_payload = _read_json_file(root, body_file, result, f"连结体 {body_name}")
        if body_payload is None:
            continue

        missing = sorted(REQUIRED_LINK_BODY_KEYS - body_payload.keys())
        if missing:
            result.errors.append(f"连结体 `{body_name}` 缺少字段：{', '.join(missing)}。")
            continue

        conductor_file = body_payload.get("conductor_file")
        conductor_payload = _read_json_file(root, conductor_file, result, f"连结体 {body_name} 的指挥体")
        if conductor_payload is not None:
            missing_conductor = sorted(REQUIRED_LINK_CONDUCTOR_KEYS - conductor_payload.keys())
            if missing_conductor:
                result.errors.append(
                    f"连结体 `{body_name}` 的指挥体缺少字段：{', '.join(missing_conductor)}。"
                )
            result.checked_conductors += 1

        child_files = body_payload.get("child_agent_files", [])
        if not child_files:
            result.errors.append(f"连结体 `{body_name}` 未声明任何 `child_agent_files`。")
        for child_file in child_files:
            child_payload = _read_json_file(root, child_file, result, f"连结体 {body_name} 的子个体")
            if child_payload is None:
                continue
            missing_child = sorted(REQUIRED_CHILD_AGENT_KEYS - child_payload.keys())
            if missing_child:
                result.errors.append(
                    f"子个体文件 `{child_file}` 缺少字段：{', '.join(missing_child)}。"
                )
            result.checked_subagents += 1

        resolved_body = resolved_profile.get("link_bodies", {}).get(body_name, {})
        if resolved_body.get("body_file") != body_file:
            result.errors.append(f"连结体 `{body_name}` 在加载后丢失或改写了 `body_file`。")

        recommended_skill = body_payload.get("recommended_skill", {})
        skill_path = recommended_skill.get("skill_path")
        repo_root = root.parent.parent if root.parent.name == "exmachina" else root.parent
        if not skill_path:
            result.errors.append(f"连结体 `{body_name}` 缺少 `recommended_skill.skill_path`。")
        elif not (repo_root / skill_path).exists():
            result.errors.append(f"连结体 `{body_name}` 引用了不存在的推荐 skill：{skill_path}。")

        result.checked_link_bodies += 1


def _validate_orphan_assets(raw_profile: dict[str, Any], root: Path, result: AssetValidationResult) -> None:
    referenced_body_files = {
        spec.get("body_file")
        for spec in raw_profile.get("link_bodies", {}).values()
        if spec.get("body_file")
    }
    referenced_conductor_files = {raw_profile.get("conductor_file")} if raw_profile.get("conductor_file") else set()
    referenced_subagent_files: set[str] = set()

    for spec in raw_profile.get("link_bodies", {}).values():
        body_file = spec.get("body_file")
        if not body_file:
            continue
        body_payload = json.loads((root / body_file).read_text(encoding="utf-8-sig"))
        if body_payload.get("conductor_file"):
            referenced_conductor_files.add(body_payload["conductor_file"])
        referenced_subagent_files.update(body_payload.get("child_agent_files", []))

    _report_orphans(root / "link_bodies", referenced_body_files, result, "连结体定义")
    _report_orphans(root / "conductors", referenced_conductor_files, result, "指挥体定义")
    _report_orphans(root / "subagents", referenced_subagent_files, result, "子个体定义")


def _report_orphans(directory: Path, referenced_paths: set[str], result: AssetValidationResult, label: str) -> None:
    if not directory.exists():
        return
    actual_paths = {
        str(path.relative_to(directory.parent)).replace("\\", "/")
        for path in directory.glob("*.json")
    }
    orphans = sorted(actual_paths - referenced_paths)
    for orphan in orphans:
        result.errors.append(f"发现未被引用的{label}文件：{orphan}。")


def _read_json_file(root: Path, relative_path: str | None, result: AssetValidationResult, label: str) -> dict[str, Any] | None:
    if not relative_path:
        result.errors.append(f"{label} 缺少引用路径。")
        return None

    target = root / relative_path
    if not target.exists():
        result.errors.append(f"{label} 引用了不存在的文件：{relative_path}。")
        return None

    try:
        return json.loads(target.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        result.errors.append(f"{label} 文件不是有效 JSON：{relative_path}（{exc}）。")
        return None
