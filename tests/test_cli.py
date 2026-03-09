import json
import tempfile
import unittest
from pathlib import Path

from exmachina.cli import main


class CliTests(unittest.TestCase):
    def test_build_command_exports_lite_pack_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            output = Path(tmpdir) / "out"
            workspace.mkdir()
            (workspace / "README.md").write_text("# demo\n", encoding="utf-8")
            (workspace / "tests").mkdir()
            (workspace / "tests" / "test_sample.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")

            exit_code = main(
                [
                    "build",
                    "--task",
                    "为 OpenClaw 补充运行时拓扑与详细角色契约",
                    "--repo",
                    "https://code.example.com/example/exmachina",
                    "--workspace",
                    str(workspace),
                    "--out",
                    str(output),
                ]
            )

            self.assertEqual(exit_code, 0)
            manifest = json.loads((output / "openclaw-pack" / "manifest.json").read_text(encoding="utf-8"))
            mission = json.loads((output / "mission.json").read_text(encoding="utf-8"))
            runtime_spec = json.loads(
                (output / "openclaw-pack" / "runtime" / "agents" / "exmachina-main" / "spec.json").read_text(
                    encoding="utf-8"
                )
            )
            install_plan = json.loads(
                (output / "openclaw-pack" / "install" / "openclaw.agents.plan.json").read_text(encoding="utf-8")
            )
            task_board = json.loads((output / "openclaw-pack" / "runtime" / "task-board.json").read_text(encoding="utf-8"))
            child_doc = next((output / "openclaw-pack" / "subagents").glob("*.md")).read_text(encoding="utf-8")

            self.assertEqual(mission["mode"], "lite")
            self.assertEqual(manifest["mode"], "lite")
            self.assertFalse(manifest["compatibility"]["requires_multi_agent_binding"])
            self.assertFalse(manifest["compatibility"]["requires_external_routing"])
            self.assertIn("openclaw_directive", manifest)
            self.assertTrue(manifest["openclaw_directive"]["quick_start"])
            self.assertEqual(len(install_plan["agents"]), 1)
            self.assertEqual(runtime_spec["runtime_role"], "single-agent-conductor")
            self.assertIn("ordered_execution_steps", task_board)
            self.assertTrue(task_board["ordered_execution_steps"])
            self.assertIn("single_session_brief", task_board)
            self.assertIn("recommended_skill", runtime_spec)
            self.assertIn("## 工作流", child_doc)
            self.assertIn("## 输出契约", child_doc)

    def test_build_command_exports_full_pack_when_requested(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            output = Path(tmpdir) / "out"
            workspace.mkdir()
            (workspace / "README.md").write_text("# demo\n", encoding="utf-8")
            (workspace / "tests").mkdir()
            (workspace / "tests" / "test_sample.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")

            exit_code = main(
                [
                    "build",
                    "--mode",
                    "full",
                    "--task",
                    "为 OpenClaw 补充运行时拓扑与详细角色契约",
                    "--repo",
                    "https://code.example.com/example/exmachina",
                    "--workspace",
                    str(workspace),
                    "--out",
                    str(output),
                ]
            )

            self.assertEqual(exit_code, 0)
            manifest = json.loads((output / "openclaw-pack" / "manifest.json").read_text(encoding="utf-8"))
            install_plan = json.loads(
                (output / "openclaw-pack" / "install" / "openclaw.agents.plan.json").read_text(encoding="utf-8")
            )
            topology = json.loads((output / "openclaw-pack" / "runtime" / "topology.json").read_text(encoding="utf-8"))

            self.assertEqual(manifest["mode"], "full")
            self.assertTrue(manifest["compatibility"]["requires_multi_agent_binding"])
            self.assertTrue(manifest["compatibility"]["requires_external_routing"])
            self.assertGreater(len(install_plan["agents"]), 1)
            self.assertTrue(topology["routes"])


if __name__ == "__main__":
    unittest.main()
