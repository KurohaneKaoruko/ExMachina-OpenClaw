from __future__ import annotations

import argparse
from pathlib import Path

from .exporter import export_openclaw_pack, write_bundle, write_plan_files
from .planner import plan_mission
from .validator import validate_profile_assets


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="exmachina",
        description="为 OpenClaw 生成协议化的多智能体协作结构。",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name in ("plan", "build", "export-pack"):
        subparser = subparsers.add_parser(name)
        subparser.add_argument("--task", required=True, help="需要编排的大任务。")
        subparser.add_argument("--repo", help="远程仓库链接。")
        subparser.add_argument("--workspace", help="本地工作区目录，用于生成定制化编排。")
        subparser.add_argument("--title", help="自定义任务标题。")
        subparser.add_argument("--profile", help="自定义 JSON 体系配置路径。")
        subparser.add_argument(
            "--mode",
            choices=("lite", "full"),
            default="lite",
            help="导出模式：lite 为默认单 agent 兼容模式，full 为完整多 agent 模式。",
        )
        subparser.add_argument("--out", required=True, help="输出目录。")

    validate_parser = subparsers.add_parser("validate-assets")
    validate_parser.add_argument("--profile", help="要校验的 JSON 画像入口，默认使用内置 default_profile.json。")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "validate-assets":
        result = validate_profile_assets(profile_path=args.profile)
        if result.is_valid:
            print(
                f"资产校验通过：{result.checked_link_bodies} 个连结体，"
                f"{result.checked_conductors} 个指挥体，{result.checked_subagents} 个子个体。"
            )
            return 0

        for item in result.errors:
            print(item)
        return 1

    plan = plan_mission(
        task=args.task,
        repo_url=args.repo,
        workspace_path=args.workspace,
        title=args.title,
        profile_path=args.profile,
        mode=args.mode,
    )

    out_path = Path(args.out)
    if args.command == "plan":
        write_plan_files(plan, out_path)
        print(f"已输出 ExMachina 任务编排：{out_path}")
        return 0

    if args.command == "export-pack":
        export_openclaw_pack(plan, out_path)
        print(f"已导出 ExMachina 应用包：{out_path}")
        return 0

    write_bundle(plan, out_path)
    print(f"已生成 ExMachina 完整任务包：{out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
