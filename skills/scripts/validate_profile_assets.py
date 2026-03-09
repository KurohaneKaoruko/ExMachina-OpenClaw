from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    command = [sys.executable, "-m", "exmachina", "validate-assets"]
    subprocess.run(command, cwd=repo_root, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
