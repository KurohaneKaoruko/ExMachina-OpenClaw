---
name: exmachina-project-maintainer
description: Use when extending or maintaining the ExMachina repository: evolving role assets, planner/runtime/exporter schemas, repo-local skills, tests, and the generated OpenClaw pack.
---

# ExMachina Project Maintainer

English summary: Maintains ExMachina schemas, role assets, runtime exports, skills, tests, and the demo pack.

## Workflow

1. Read `references/file-map.md` to locate the change surface.
2. If the task changes role assets, start from `skills/scripts/regenerate_role_assets.py` and `exmachina/data/default_profile.json`.
3. If the task changes exported structure, keep `exmachina/models.py`, `exmachina/planner.py`, `exmachina/runtime.py`, and `exmachina/exporter.py` in sync.
4. If the task changes repo-local skills, update both `skills/SKILL.md` and the affected `skills/<link-body-skill>/SKILL.md` files.
5. If the task changes user-facing structure, update `README.md` and `docs/ARCHITECTURE.md`.
6. Regenerate role assets with `python skills/scripts/regenerate_role_assets.py`.
7. Regenerate the demo pack with `python skills/scripts/regenerate_demo_pack.py`.
8. Run `python -m exmachina validate-assets` and `python -m unittest discover -s tests -p "test_*.py"` before finishing.

## Rules

- Do not change one schema/output surface in isolation; models, planner, runtime, exporter, assets, and tests move together.
- Keep `recommended_skill` and `skill_catalog` aligned with the actual `skills/<skill-id>/SKILL.md` files.
- Keep inspiration-related wording out of non-README files.
