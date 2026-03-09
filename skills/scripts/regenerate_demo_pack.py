from __future__ import annotations

import subprocess
import sys
from pathlib import Path


DEMO_TASK = "沉淀知识交接、术语索引、资源仲裁规则与 README 示例，形成 OpenClaw 协作层"


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    command = [
        sys.executable,
        "-m",
        "exmachina",
        "export-pack",
        "--task",
        DEMO_TASK,
        "--workspace",
        ".",
        "--out",
        "openclaw-pack",
    ]
    subprocess.run(command, cwd=repo_root, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

