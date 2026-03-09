# File Map

## Core runtime files

- `exmachina/data/default_profile.json`: Primary profile index; stores selection rules and file references to link-body, conductor, and subagent definitions.
- `exmachina/data/link_bodies/`: Source-of-truth link-body definitions used by the profile loader.
- `exmachina/data/conductors/`: Source-of-truth conductor definitions used by the profile loader.
- `exmachina/data/subagents/`: Source-of-truth subagent prompt definitions used by the profile loader.
- `exmachina/validator.py`: Strict asset validation for richer prompt fields and skill bindings.
- `exmachina/models.py`: Structured output schema for plans and exported packs.
- `exmachina/planner.py`: Planning logic, selection trace, stages, contracts, knowledge handoff, and arbitration.
- `exmachina/runtime.py`: Runtime topology compiler for agent specs, assignments, routes, and shared artifacts.
- `exmachina/exporter.py`: `mission.json`, `mission.md`, `openclaw-pack/`, and runtime document generation.
- `exmachina/cli.py`: CLI entrypoints.

## Validation

- `tests/`: Unit and export validation suite for planner, assets, runtime, and exporter.
- `skills/scripts/regenerate_role_assets.py`: Regenerates richer role assets and repo-local body skills.

## Documentation

- `README.md`: Single-entry project overview and role catalog.
- `docs/ARCHITECTURE.md`: Detailed architecture diagrams and file flow.
- `openclaw-pack/`: Regenerated demo pack tracked in the repo.

## Skills

- `skills/`: Repo-local maintainer skill plus per-link-body execution skills.
