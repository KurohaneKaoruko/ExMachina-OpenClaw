import unittest

from exmachina.profile import load_profile


class ProfileTests(unittest.TestCase):
    def test_load_profile_resolves_rich_subagent_schema(self) -> None:
        profile = load_profile()
        body = profile["link_bodies"]["实作连结体"]
        child = next(item for item in body["child_agents"] if item["name"] == "编码体")

        self.assertIn("english_alias", child)
        self.assertIn("core_responsibilities", child)
        self.assertIn("output_contract", child)
        self.assertIn("handoff_targets", child)
        self.assertIn("tools_guidance", child)

    def test_load_profile_resolves_rich_conductor_and_skill_binding(self) -> None:
        profile = load_profile()
        body = profile["link_bodies"]["运维连结体"]

        self.assertIn("english_alias", profile["conductor"])
        self.assertIn("core_duties", profile["conductor"])
        self.assertIn("dispatch_rules", body["conductor"])
        self.assertIn("recommended_skill", body)
        self.assertTrue(body["recommended_skill"]["skill_path"].endswith("SKILL.md"))


if __name__ == "__main__":
    unittest.main()
