# Global Preferences for sample-service-migration

See `/Users/muilu/.claude/CLAUDE.md` for global settings. This file extends or overrides them for this project.

## Migration-specific guidance

- Documentation first: before writing extraction/load scripts, document the schema mapping and transformation strategy in `docs/`.
- Reversibility: every step must be reversible or have a rollback plan.
- Data validation: compare row counts, checksums, and a sample of rows after each step.
- Audit trail: log every extraction, transformation, and load action with timestamps and row counts.
