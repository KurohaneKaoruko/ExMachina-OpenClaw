from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from pathlib import Path


ALLOWED_PATCH_KEYS = {"agents"}
ALLOWED_AGENT_SECTION_KEYS = {"list"}
ALLOWED_AGENT_KEYS = {"id", "name", "default", "workspace", "identity", "sandbox"}
ALLOWED_SANDBOX_MODES = {"off", "non-main", "all"}
ALLOWED_SANDBOX_SCOPES = {"session", "agent", "shared"}
ANSWER_KEY_TO_VAR = {
    "install_language": "OPENCLAW_INSTALL_LANGUAGE",
    "conductor_name": "OPENCLAW_CONDUCTOR_NAME",
    "install_mode": "OPENCLAW_INSTALL_MODE",
    "workspace_root": "EXMACHINA_PACK_ROOT",
}
PLACEHOLDER_PATTERN = re.compile(r"{{([A-Z0-9_]+)}}")


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
    unknown_patch_keys = sorted(set(patch.keys()) - ALLOWED_PATCH_KEYS)
    if unknown_patch_keys:
        errors.append(f"settings_patch 包含未允许的顶层字段：{', '.join(unknown_patch_keys)}")

    agents = patch.get("agents", {})
    unknown_agent_section_keys = sorted(set(agents.keys()) - ALLOWED_AGENT_SECTION_KEYS)
    if unknown_agent_section_keys:
        errors.append(f"settings_patch.agents 包含未允许的字段：{', '.join(unknown_agent_section_keys)}")

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


def load_answers(answers_path: str | None) -> dict:
    if not answers_path:
        return {}
    return json.loads(Path(answers_path).expanduser().resolve().read_text(encoding="utf-8"))


def build_replacements(settings_bundle: dict, args: argparse.Namespace) -> dict[str, object]:
    variable_specs = settings_bundle.get("template_variables", {})
    replacements = {
        name: spec.get("default", "")
        for name, spec in variable_specs.items()
        if isinstance(spec, dict)
    }

    for key, value in load_answers(args.answers).items():
        normalized_key = ANSWER_KEY_TO_VAR.get(key, key)
        if value is not None:
            replacements[normalized_key] = value

    cli_overrides = {
        "OPENCLAW_INSTALL_LANGUAGE": args.language,
        "OPENCLAW_CONDUCTOR_NAME": args.conductor_name,
        "OPENCLAW_INSTALL_MODE": args.install_mode,
        "EXMACHINA_PACK_ROOT": args.workspace_value,
    }
    for key, value in cli_overrides.items():
        if value is not None:
            replacements[key] = value

    return replacements


def substitute_placeholders(payload: object, replacements: dict[str, object]) -> object:
    if isinstance(payload, str):
        return PLACEHOLDER_PATTERN.sub(
            lambda match: str(replacements.get(match.group(1), match.group(0))),
            payload,
        )
    if isinstance(payload, list):
        return [substitute_placeholders(item, replacements) for item in payload]
    if isinstance(payload, dict):
        return {key: substitute_placeholders(value, replacements) for key, value in payload.items()}
    return payload


def collect_unresolved_placeholders(payload: object) -> list[str]:
    unresolved = []
    if isinstance(payload, str):
        unresolved.extend(match.group(1) for match in PLACEHOLDER_PATTERN.finditer(payload))
    elif isinstance(payload, list):
        for item in payload:
            unresolved.extend(collect_unresolved_placeholders(item))
    elif isinstance(payload, dict):
        for value in payload.values():
            unresolved.extend(collect_unresolved_placeholders(value))
    return sorted(set(unresolved))


def validate_selected_mode(settings_bundle: dict, replacements: dict[str, object]) -> list[str]:
    bundle_mode = str(settings_bundle.get("mode", "")).strip()
    selected_mode = str(replacements.get("OPENCLAW_INSTALL_MODE", bundle_mode)).strip()
    if not bundle_mode or not selected_mode or bundle_mode == selected_mode:
        return []

    return [
        f"当前 settings bundle 是 {bundle_mode}，但安装问询选择了 {selected_mode}。",
        "请先重生成对应模式的 pack，再继续安装。",
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge ExMachina OpenClaw settings template into an existing OpenClaw config.")
    parser.add_argument("--config", required=True, help="Target OpenClaw config path, e.g. ~/.openclaw/openclaw.json")
    parser.add_argument("--settings", default="openclaw.settings.json", help="Path to the exported ExMachina settings template")
    parser.add_argument("--answers", help="Path to the install intake answers JSON")
    parser.add_argument("--language", help="Preferred install/output language")
    parser.add_argument("--conductor-name", help="Display name for the top conductor / main agent")
    parser.add_argument("--mode", dest="install_mode", choices=("lite", "full"), help="Selected install mode from intake")
    parser.add_argument("--workspace-value", help="Workspace path that should replace {{EXMACHINA_PACK_ROOT}}")
    args = parser.parse_args()

    config_path = Path(args.config).expanduser().resolve()
    settings_path = Path(args.settings).expanduser().resolve()

    settings_bundle = json.loads(settings_path.read_text(encoding="utf-8"))
    patch = settings_bundle.get("settings_patch", {})
    replacements = build_replacements(settings_bundle, args)

    validation_errors = validate_selected_mode(settings_bundle, replacements)
    validation_errors.extend(validate_patch(patch))
    if validation_errors:
        for item in validation_errors:
            print(item)
        return 1

    patch = substitute_placeholders(patch, replacements)
    unresolved = collect_unresolved_placeholders(patch)
    if unresolved:
        for item in unresolved:
            print(f"仍有未填充的模板变量：{item}")
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
        config_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
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
