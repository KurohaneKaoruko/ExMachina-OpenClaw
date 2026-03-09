import tempfile
import unittest
from pathlib import Path

from exmachina.planner import plan_mission


class PlannerTests(unittest.TestCase):
    def test_plan_mission_builds_rich_role_models_in_lite_mode_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            (workspace / "README.md").write_text("# demo\n", encoding="utf-8")
            (workspace / "tests").mkdir()
            (workspace / "tests" / "test_runtime.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
            plan = plan_mission(
                task="为线上发布补充监控、告警与回滚演练方案",
                repo_url="https://code.example.com/example/exmachina",
                workspace_path=tmpdir,
            )

        self.assertEqual(plan.mode, "lite")
        self.assertTrue(plan.conductor_profile.core_duties)
        self.assertTrue(plan.primary_link_body.entry_conditions)
        self.assertTrue(plan.primary_link_body.recommended_skill)
        self.assertTrue(plan.primary_link_body.link_conductor.dispatch_rules)
        self.assertTrue(plan.primary_link_body.child_agents[0].workflow)
        self.assertFalse(plan.openclaw_install_plan.requires_multi_agent_binding)
        self.assertFalse(plan.runtime_topology.requires_external_routing)
        self.assertEqual(len(plan.openclaw_install_plan.agents), 1)
        self.assertEqual(plan.openclaw_settings_bundle.mode, "lite")
        self.assertTrue(plan.openclaw_settings_bundle.supports_direct_import)
        self.assertEqual(plan.openclaw_settings_bundle.default_entry_agent_id, "exmachina-main")
        self.assertIn("OPENCLAW_INSTALL_LANGUAGE", plan.openclaw_settings_bundle.template_variables)
        self.assertIn("install_mode", plan.openclaw_settings_bundle.install_intake["answers_template"])
        required_keys = {item["key"] for item in plan.openclaw_settings_bundle.install_intake["required_questions"]}
        self.assertTrue(
            {"install_language", "conductor_name", "install_mode", "target_config_path", "workspace_root"}.issubset(
                required_keys
            )
        )
        main_agent = plan.openclaw_settings_bundle.settings_patch["agents"]["list"][0]
        self.assertNotIn("metadata", main_agent)
        self.assertNotIn("model", main_agent)
        self.assertEqual(main_agent["sandbox"]["mode"], "off")
        self.assertEqual(main_agent["name"], "{{OPENCLAW_CONDUCTOR_NAME}}")
        self.assertIn("{{OPENCLAW_INSTALL_LANGUAGE}}", main_agent["identity"]["theme"])
        self.assertIn("子个体", main_agent["identity"]["theme"])
        self.assertIn("少女式终端", main_agent["identity"]["theme"])
        self.assertIn("已接收", main_agent["identity"]["theme"])
        self.assertIn("本机", main_agent["identity"]["theme"])
        self.assertNotIn("我会继续", main_agent["identity"]["theme"])
        self.assertEqual(plan.openclaw_settings_bundle.dialogue_contracts["exmachina-main"]["role_name"], "主控体")

    def test_plan_mission_builds_lite_runtime_topology_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            (workspace / "README.md").write_text("# demo\n", encoding="utf-8")
            plan = plan_mission(task="沉淀术语索引、关键决策和未决问题", workspace_path=tmpdir)

        self.assertEqual(plan.runtime_topology.mode, "lite")
        self.assertEqual(plan.runtime_topology.coordination_mode, "single-agent-inline-support")
        self.assertFalse(plan.runtime_topology.routes)
        self.assertEqual(len(plan.runtime_topology.agent_specs), 1)
        self.assertEqual(plan.runtime_topology.agent_specs[0].agent_id, "exmachina-main")
        self.assertTrue(plan.runtime_topology.agent_specs[0].recommended_skill)
        self.assertIn("agents", plan.openclaw_settings_bundle.settings_patch)
        self.assertIn("少女式终端", plan.openclaw_install_prompt)
        self.assertIn("可参考句式", plan.openclaw_install_prompt)
        self.assertIn("本机", plan.openclaw_install_prompt)
        self.assertIn("install/INTAKE.md", plan.openclaw_install_prompt)

    def test_plan_mission_builds_full_runtime_topology_when_requested(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            (workspace / "README.md").write_text("# demo\n", encoding="utf-8")
            (workspace / "tests").mkdir()
            (workspace / "tests" / "test_runtime.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
            plan = plan_mission(task="沉淀术语索引、关键决策和未决问题", workspace_path=tmpdir, mode="full")

        self.assertEqual(plan.mode, "full")
        self.assertTrue(plan.runtime_topology.routes)
        self.assertTrue(all(route.guidance for route in plan.runtime_topology.routes))
        self.assertTrue(all(route.escalation_triggers for route in plan.runtime_topology.routes))
        self.assertTrue(all(assignment.guidance for assignment in plan.runtime_topology.assignments))
        self.assertTrue(plan.openclaw_install_plan.requires_multi_agent_binding)
        self.assertTrue(plan.runtime_topology.requires_external_routing)
        self.assertGreater(len(plan.openclaw_install_plan.agents), 1)
        self.assertFalse(plan.openclaw_settings_bundle.supports_direct_import)
        self.assertTrue(plan.openclaw_settings_bundle.bindings_template)
        self.assertNotIn("defaults", plan.openclaw_settings_bundle.settings_patch["agents"])
        for agent in plan.openclaw_settings_bundle.settings_patch["agents"]["list"]:
            self.assertNotIn("metadata", agent)
            self.assertNotIn("model", agent)
            self.assertIn(agent["sandbox"]["mode"], {"off", "all"})
            self.assertEqual(agent["workspace"], "{{EXMACHINA_PACK_ROOT}}")
            self.assertIn("对话口吻要求", agent["identity"]["theme"])
            self.assertIn("优先词汇", agent["identity"]["theme"])
            self.assertIn("{{OPENCLAW_INSTALL_LANGUAGE}}", agent["identity"]["theme"])
        self.assertEqual(plan.openclaw_settings_bundle.dialogue_contracts["exmachina-primary"]["role_name"], "主连结体")


if __name__ == "__main__":
    unittest.main()
