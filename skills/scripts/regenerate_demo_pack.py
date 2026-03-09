from __future__ import annotations

import argparse
import sys
from pathlib import Path


DEMO_TASK = "沉淀知识交接、术语索引、资源仲裁规则与 README 示例，形成 OpenClaw 协作层"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Regenerate the demo openclaw-pack from source.")
    parser.add_argument("--mode", choices=("lite", "full"), default="lite", help="Export mode for the generated pack.")
    parser.add_argument("--out", default="openclaw-pack", help="Output directory for the generated pack.")
    parser.add_argument("--task", default=DEMO_TASK, help="Task used when generating the demo pack.")
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from exmachina.exporter import export_openclaw_pack
    from exmachina.planner import plan_mission

    plan = plan_mission(task=args.task, workspace_path=".", mode=args.mode)
    export_openclaw_pack(plan, repo_root / args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
