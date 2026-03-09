from __future__ import annotations

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
