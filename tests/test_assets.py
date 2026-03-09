import unittest
from pathlib import Path

from exmachina.profile import load_profile


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_TERMS = ("机凯种", "Ex-Machina", "灵感来源", "群体连结", "共享推理", "高理性协作")
SKILL_REQUIRED_SECTIONS = (
    "## When to use",
    "## Boundaries",
    "## Workflow",
    "## Handoff Template",
    "## Quality Bar",
)


class AssetIntegrityTests(unittest.TestCase):
    def test_all_link_bodies_have_rich_prompt_fields(self) -> None:
        profile = load_profile()

        self.assertEqual(set(profile["skill_catalog"].keys()), set(profile["link_bodies"].keys()))
        for body_name, body in profile["link_bodies"].items():
            self.assertTrue(body["usage_scenarios"], body_name)
            self.assertTrue(body["entry_conditions"], body_name)
            self.assertTrue(body["exit_conditions"], body_name)
            self.assertTrue(body["deliverable_contracts"], body_name)
            self.assertTrue(body["support_capabilities"], body_name)
            self.assertTrue(body["collaboration_rules"], body_name)
            self.assertTrue(body["boundary_rules"], body_name)
            self.assertTrue(body["fallback_modes"], body_name)
            self.assertTrue(body["failure_modes"], body_name)
            self.assertTrue(body["default_stage_mapping"], body_name)
            self.assertTrue(body["recommended_skill"]["skill_path"].endswith("SKILL.md"), body_name)
            self.assertTrue(body["conductor"]["dispatch_rules"], body_name)
            self.assertTrue(body["conductor"]["handoff_contract_template"], body_name)

            for child in body["child_agents"]:
                self.assertTrue(child["core_responsibilities"], child["name"])
                self.assertTrue(child["inputs"], child["name"])
                self.assertTrue(child["workflow"], child["name"])
                self.assertTrue(child["output_contract"], child["name"])
                self.assertTrue(child["handoff_targets"], child["name"])
                self.assertTrue(child["escalation_triggers"], child["name"])
                self.assertTrue(child["failure_modes"], child["name"])
                self.assertTrue(child["quality_bar"], child["name"])
                self.assertTrue(child["tools_guidance"], child["name"])

    def test_all_repo_local_body_skills_exist_and_have_required_sections(self) -> None:
        profile = load_profile()

        for body_name, skill in profile["skill_catalog"].items():
            skill_path = ROOT / skill["skill_path"]
            self.assertTrue(skill_path.exists(), body_name)
            text = skill_path.read_text(encoding="utf-8")
            for section in SKILL_REQUIRED_SECTIONS:
                self.assertIn(section, text, f"{body_name} missing {section}")

    def test_forbidden_inspiration_terms_only_live_in_readme(self) -> None:
        for path in ROOT.rglob("*"):
            if not path.is_file():
                continue
            if path.name == "README.md":
                continue
            if "tests" in path.parts:
                continue
            if path.suffix.lower() not in {".md", ".json", ".py"}:
                continue

            text = path.read_text(encoding="utf-8-sig")
            for term in FORBIDDEN_TERMS:
                self.assertNotIn(term, text, f"{path} contains forbidden term: {term}")


if __name__ == "__main__":
    unittest.main()
