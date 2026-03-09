from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .validator import validate_profile_assets
from .workspace import scan_workspace


STATUS_ORDER = {"pass": 0, "warn": 1, "fail": 2}
ALLOWED_AGENT_KEYS = {"id", "name", "default", "workspace", "model", "identity", "sandbox"}
ALLOWED_SANDBOX_MODES = {"off", "non-main", "all"}
ALLOWED_SANDBOX_SCOPES = {"session", "agent", "shared"}


@dataclass
class DoctorCheck:
    name: str
    status: str
    summary: str
    details: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DoctorReport:
    overall_status: str
    workspace_root: str
    pack_root: str
    checks: list[DoctorCheck]
    recommended_commands: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall_status": self.overall_status,
            "workspace_root": self.workspace_root,
            "pack_root": self.pack_root,
            "checks": [item.to_dict() for item in self.checks],
            "recommended_commands": self.recommended_commands,
        }


def run_doctor(
    profile_path: str | None = None,
    workspace_path: str | None = None,
    pack_path: str | None = None,
) -> DoctorReport:
    workspace_root = Path(workspace_path).resolve() if workspace_path else Path.cwd().resolve()
    pack_root = Path(pack_path).resolve() if pack_path else (workspace_root / "openclaw-pack").resolve()

    checks = [
        _build_assets_check(profile_path),
        _build_workspace_check(workspace_root),
        _build_pack_check(pack_root),
    ]
    overall_status = _merge_status(check.status for check in checks)
    recommended_commands = _build_recommended_commands(checks, workspace_root, pack_root)

    return DoctorReport(
        overall_status=overall_status,
        workspace_root=str(workspace_root),
        pack_root=str(pack_root),
        checks=checks,
        recommended_commands=recommended_commands,
    )


def render_doctor_report(report: DoctorReport) -> str:
    lines = [
        "ExMachina Doctor",
        f"Status: {report.overall_status.upper()}",
        f"Workspace: {report.workspace_root}",
        f"Pack: {report.pack_root}",
        "",
    ]

    for check in report.checks:
        lines.append(f"[{check.status.upper()}] {check.name}: {check.summary}")
        lines.extend(f"- {detail}" for detail in check.details)
        lines.append("")

    if report.recommended_commands:
        lines.append("Recommended commands:")
        lines.extend(f"- {command}" for command in report.recommended_commands)
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _build_assets_check(profile_path: str | None) -> DoctorCheck:
    result = validate_profile_assets(profile_path)
    if result.is_valid:
        return DoctorCheck(
            name="Source Assets",
            status="pass",
            summary="源资产引用完整，可继续生成任务包。",
            details=[
                f"已校验连接体: {result.checked_link_bodies}",
                f"已校验指挥体: {result.checked_conductors}",
                f"已校验子个体: {result.checked_subagents}",
            ],
        )

    return DoctorCheck(
        name="Source Assets",
        status="fail",
        summary=f"源资产校验失败，共 {len(result.errors)} 项问题。",
        details=result.errors[:10],
    )


def _build_workspace_check(workspace_root: Path) -> DoctorCheck:
    if not workspace_root.exists():
        return DoctorCheck(
            name="Workspace Context",
            status="fail",
            summary="工作区路径不存在。",
            details=[str(workspace_root)],
        )
    if not workspace_root.is_dir():
        return DoctorCheck(
            name="Workspace Context",
            status="fail",
            summary="工作区路径不是目录。",
            details=[str(workspace_root)],
        )

    snapshot = scan_workspace(workspace_root)
    status = "pass" if snapshot.detected_languages else "warn"
    summary = "工作区已识别主要语言与测试入口。" if snapshot.detected_languages else "工作区可读，但未识别主要语言。"
    details = [
        f"语言: {', '.join(snapshot.detected_languages) if snapshot.detected_languages else '未识别'}",
        f"测试目录: {', '.join(snapshot.test_paths) if snapshot.test_paths else '未发现'}",
        f"关键路径: {', '.join(snapshot.notable_paths[:6]) if snapshot.notable_paths else '未发现'}",
    ]
    return DoctorCheck(name="Workspace Context", status=status, summary=summary, details=details)


def _build_pack_check(pack_root: Path) -> DoctorCheck:
    if not pack_root.exists():
        return DoctorCheck(
            name="Generated Pack",
            status="warn",
            summary="未检测到导出包，可先生成或重生 openclaw-pack。",
            details=[str(pack_root)],
        )
    if not pack_root.is_dir():
        return DoctorCheck(
            name="Generated Pack",
            status="fail",
            summary="导出包路径不是目录。",
            details=[str(pack_root)],
        )

    required_files = [
        "BOOTSTRAP.md",
        "README.md",
        "QUICKSTART.md",
        "manifest.json",
        "openclaw.settings.json",
        "install/SETTINGS.md",
        "runtime/README.md",
        "runtime/task-board.json",
    ]
    missing_files = [item for item in required_files if not (pack_root / item).exists()]
    if missing_files:
        return DoctorCheck(
            name="Generated Pack",
            status="fail",
            summary=f"导出包缺少 {len(missing_files)} 个关键文件。",
            details=[f"缺失: {item}" for item in missing_files],
        )

    manifest, manifest_error = _read_json_file(pack_root / "manifest.json")
    settings_bundle, settings_error = _read_json_file(pack_root / "openclaw.settings.json")
    task_board, task_board_error = _read_json_file(pack_root / "runtime" / "task-board.json")
    json_errors = [item for item in (manifest_error, settings_error, task_board_error) if item]
    if json_errors:
        return DoctorCheck(
            name="Generated Pack",
            status="fail",
            summary="导出包中的 JSON 文件无法解析。",
            details=json_errors,
        )

    manifest_mode = str(manifest.get("mode", "")).strip()
    settings_mode = str(settings_bundle.get("mode", "")).strip()
    task_board_mode = str(task_board.get("mode", "")).strip()
    modes = {item for item in (manifest_mode, settings_mode, task_board_mode) if item}
    if len(modes) != 1:
        return DoctorCheck(
            name="Generated Pack",
            status="fail",
            summary="导出包模式不一致，manifest/settings/runtime 未对齐。",
            details=[
                f"manifest.mode = {manifest_mode or '未声明'}",
                f"openclaw.settings.json.mode = {settings_mode or '未声明'}",
                f"runtime/task-board.json.mode = {task_board_mode or '未声明'}",
            ],
        )

    mode = next(iter(modes))
    settings_errors = _validate_settings_patch(settings_bundle)
    if settings_errors:
        return DoctorCheck(
            name="Generated Pack",
            status="fail",
            summary="导出包中的 OpenClaw 设置补丁包含当前 schema 不接受的字段。",
            details=settings_errors,
        )

    compat_plan = pack_root / "install" / "compat" / "openclaw.agents.plan.json"
    if mode == "full" and not compat_plan.exists():
        return DoctorCheck(
            name="Generated Pack",
            status="fail",
            summary="Full 导出包缺少兼容安装计划。",
            details=[str(compat_plan)],
        )

    primary_body = _extract_body_name(manifest.get("primary_link_body"))
    support_bodies = [_extract_body_name(item) for item in manifest.get("support_link_bodies", [])]
    supports_direct_import = bool(settings_bundle.get("supports_direct_import"))
    details = [
        f"模式: {mode}",
        f"主连接体: {primary_body or '未声明'}",
        f"协作连接体: {', '.join(support_bodies) if support_bodies else '无'}",
        f"直接导入设置: {'是' if supports_direct_import else '否'}",
    ]
    if mode == "lite":
        details.append("兼容安装计划: Lite 模式下非必需")
    else:
        details.append(f"兼容安装计划: {compat_plan.relative_to(pack_root)}")

    return DoctorCheck(
        name="Generated Pack",
        status="pass",
        summary="导出包入口、安装说明和运行时任务板齐备。",
        details=details,
    )


def _read_json_file(path: Path) -> tuple[dict[str, Any], str | None]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except json.JSONDecodeError as exc:
        return {}, f"{path}: JSON 解析失败（{exc}）"
    except OSError as exc:
        return {}, f"{path}: 读取失败（{exc}）"


def _extract_body_name(payload: Any) -> str:
    if isinstance(payload, dict):
        return str(payload.get("name", "")).strip()
    if payload is None:
        return ""
    return str(payload).strip()


def _validate_settings_patch(settings_bundle: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    settings_patch = settings_bundle.get("settings_patch", {})
    agents = settings_patch.get("agents", {})

    defaults = agents.get("defaults", {})
    errors.extend(_validate_sandbox(defaults.get("sandbox"), "agents.defaults.sandbox"))

    for index, agent in enumerate(agents.get("list", [])):
        if not isinstance(agent, dict):
            errors.append(f"agents.list[{index}] 不是对象。")
            continue

        unknown_keys = sorted(set(agent.keys()) - ALLOWED_AGENT_KEYS)
        if unknown_keys:
            errors.append(f"agents.list[{index}] 包含未知字段：{', '.join(unknown_keys)}")

        errors.extend(_validate_sandbox(agent.get("sandbox"), f"agents.list[{index}].sandbox"))

    return errors


def _validate_sandbox(payload: Any, label: str) -> list[str]:
    if payload is None:
        return []
    if not isinstance(payload, dict):
        return [f"{label} 不是对象。"]

    errors: list[str] = []
    mode = payload.get("mode")
    scope = payload.get("scope")
    if mode is not None and mode not in ALLOWED_SANDBOX_MODES:
        errors.append(f"{label}.mode = {mode!r} 不在允许值 {sorted(ALLOWED_SANDBOX_MODES)} 内。")
    if scope is not None and scope not in ALLOWED_SANDBOX_SCOPES:
        errors.append(f"{label}.scope = {scope!r} 不在允许值 {sorted(ALLOWED_SANDBOX_SCOPES)} 内。")
    return errors


def _merge_status(statuses: Any) -> str:
    current = "pass"
    for status in statuses:
        if STATUS_ORDER[status] > STATUS_ORDER[current]:
            current = status
    return current


def _build_recommended_commands(checks: list[DoctorCheck], workspace_root: Path, pack_root: Path) -> list[str]:
    commands = ["python -m exmachina validate-assets"]
    pack_check = next(item for item in checks if item.name == "Generated Pack")
    workspace_check = next(item for item in checks if item.name == "Workspace Context")

    if pack_check.status != "pass":
        commands.append("python skills/scripts/regenerate_demo_pack.py")
    if workspace_check.status != "fail":
        commands.append(
            f'python -m exmachina build --task "<你的任务>" --workspace "{workspace_root}" --out "dist/exmachina"'
        )
    commands.append(f'python -m exmachina doctor --workspace "{workspace_root}" --pack "{pack_root}"')

    deduped: list[str] = []
    for command in commands:
        if command not in deduped:
            deduped.append(command)
    return deduped
