import json
import tempfile
import unittest
from pathlib import Path

from exmachina.validator import validate_profile_assets


class ValidatorTests(unittest.TestCase):
    def test_validate_profile_assets_default_profile(self) -> None:
        result = validate_profile_assets()
        self.assertTrue(result.is_valid)
        self.assertGreater(result.checked_link_bodies, 0)
        self.assertGreater(result.checked_conductors, 0)
        self.assertGreater(result.checked_subagents, 0)

    def test_validate_profile_assets_reports_missing_rich_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "conductors").mkdir()
            (root / "link_bodies").mkdir()
            (root / "subagents").mkdir()
            (root / "skills" / "implementation-link-body").mkdir(parents=True)
            (root / "skills" / "implementation-link-body" / "SKILL.md").write_text("# skill\n", encoding="utf-8")
            (root / "conductors" / "00_global.json").write_text(json.dumps({"name": "全连结指挥体", "mission": "m", "principles": ["p"]}, ensure_ascii=False), encoding="utf-8")
            (root / "conductors" / "13_impl.json").write_text(json.dumps({"name": "实作连结指挥体", "mission": "m", "duties": ["d"], "checks": ["c"]}, ensure_ascii=False), encoding="utf-8")
            (root / "subagents" / "34_code.json").write_text(json.dumps({"name": "编码体", "mission": "m", "outputs": ["o"], "checks": ["c"]}, ensure_ascii=False), encoding="utf-8")
            (root / "link_bodies" / "13_impl.json").write_text(json.dumps({"entity_type": "连结体", "identity": "i", "member_selection_rule": "r", "focus": "f", "keywords": ["实现"], "reason_template": "t", "deliverables": ["d"], "rationality_obligations": ["o"], "conductor_file": "conductors/13_impl.json", "child_agent_files": ["subagents/34_code.json"], "recommended_skill": {"skill_path": "skills/implementation-link-body/SKILL.md"}}, ensure_ascii=False), encoding="utf-8")
            (root / "default_profile.json").write_text(json.dumps({"rationality": {}, "selection": {"support_rules": [], "fallback_supports": {}}, "content_policy": {}, "asset_defaults": {}, "validation_policy": {}, "skill_catalog": {"实作连结体": {"skill_path": "skills/implementation-link-body/SKILL.md"}}, "conductor_file": "conductors/00_global.json", "link_bodies": {"实作连结体": {"body_file": "link_bodies/13_impl.json"}}}, ensure_ascii=False), encoding="utf-8")
            result = validate_profile_assets(str(root / "default_profile.json"))

        self.assertFalse(result.is_valid)
        self.assertTrue(any("缺少字段" in item for item in result.errors))


if __name__ == "__main__":
    unittest.main()
