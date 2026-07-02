# Global Preferences for sample-service-migration

See `/Users/muilu/.claude/CLAUDE.md` for global settings. This file extends or overrides them for this project.

## Migration-specific guidance

- Documentation first: before writing extraction/load scripts, document the schema mapping and transformation strategy in `docs/`.
- Reversibility: every step must be reversible or have a rollback plan.
- Data validation: compare row counts, checksums, and a sample of rows after each step.
- Audit trail: log every extraction, transformation, and load action with timestamps and row counts.

## Development Commands

- Build all: `../../exporter2026/gradlew -p loader build`
- Run loader: `../../exporter2026/gradlew -p loader bootRun`
- Test: `../../exporter2026/gradlew -p loader test`
- Clean: `../../exporter2026/gradlew -p loader clean`
- List dependencies: `../../exporter2026/gradlew -p loader dependencies`
