import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import json

from exmachina.cli import main
from exmachina.doctor import run_doctor
from exmachina.exporter import export_openclaw_pack
from exmachina.planner import plan_mission


class DoctorTests(unittest.TestCase):
    def test_run_doctor_passes_for_valid_exported_pack(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            pack = Path(tmpdir) / "openclaw-pack"
            workspace.mkdir()
            (workspace / "README.md").write_text("# demo\n", encoding="utf-8")
            (workspace / "tests").mkdir()
            (workspace / "tests" / "test_sample.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")

            plan = plan_mission(task="为 OpenClaw 增强快速上手路径", workspace_path=str(workspace))
            export_openclaw_pack(plan, pack)

            report = run_doctor(workspace_path=str(workspace), pack_path=str(pack))

            self.assertEqual(report.overall_status, "pass")
            self.assertEqual(report.checks[0].status, "pass")
            self.assertEqual(report.checks[2].status, "pass")
            self.assertTrue(any("build --task" in item for item in report.recommended_commands))

    def test_run_doctor_fails_for_invalid_settings_patch_schema(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            pack = Path(tmpdir) / "openclaw-pack"
            workspace.mkdir()
            (workspace / "README.md").write_text("# demo\n", encoding="utf-8")

            plan = plan_mission(task="为 OpenClaw 增强快速上手路径", workspace_path=str(workspace))
            export_openclaw_pack(plan, pack)

            settings_path = pack / "openclaw.settings.json"
            settings_bundle = json.loads(settings_path.read_text(encoding="utf-8"))
            settings_bundle["settings_patch"]["agents"]["list"][0]["metadata"] = {"bad": True}
            settings_path.write_text(json.dumps(settings_bundle, ensure_ascii=False, indent=2), encoding="utf-8")

            report = run_doctor(workspace_path=str(workspace), pack_path=str(pack))

            self.assertEqual(report.overall_status, "fail")
            self.assertEqual(report.checks[2].status, "fail")
            self.assertIn("未知字段", report.checks[2].details[0])

    def test_doctor_command_fails_when_pack_is_missing_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            pack = Path(tmpdir) / "openclaw-pack"
            workspace.mkdir()
            (workspace / "README.md").write_text("# demo\n", encoding="utf-8")

            plan = plan_mission(task="为 OpenClaw 增强快速上手路径", workspace_path=str(workspace))
            export_openclaw_pack(plan, pack)
            (pack / "manifest.json").unlink()

            stdout = StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["doctor", "--workspace", str(workspace), "--pack", str(pack)])

            self.assertEqual(exit_code, 1)
            self.assertIn("[FAIL] Generated Pack", stdout.getvalue())
            self.assertIn("manifest.json", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
