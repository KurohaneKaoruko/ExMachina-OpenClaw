import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ScriptTests(unittest.TestCase):
    def test_regenerate_demo_pack_supports_full_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "pack"
            script_path = ROOT / "skills" / "scripts" / "regenerate_demo_pack.py"

            completed = subprocess.run(
                [
                    sys.executable,
                    str(script_path),
                    "--mode",
                    "full",
                    "--out",
                    str(output),
                ],
                cwd=ROOT,
                check=True,
            )

            self.assertEqual(completed.returncode, 0)
            self.assertTrue((output / "install" / "compat" / "openclaw.agents.plan.json").exists())
            self.assertTrue((output / "BOOTSTRAP.md").exists())


if __name__ == "__main__":
    unittest.main()
