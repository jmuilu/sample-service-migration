# AGENTS.md — sample-service-migration

Before work, read the umbrella [AGENTS.md](../AGENTS.md), including its shared
coordination protocol, then this repository’s task documentation. Local domain rules
below specialize the umbrella; tool adapters contain no separate policy.

Read [LLM_MIGRATION_RUNBOOK.md](LLM_MIGRATION_RUNBOOK.md) for the ETL architecture,
execution procedures and current migration status. Read [ai/database-rules.md](ai/database-rules.md)
for database inspection and validation rules. These are task references, not tool-specific copies.

- Per-table work uses the runbook's generic exporter/importer pipeline, manifests and JS
  transforms; do not reintroduce custom Java loaders.
- Major architectural changes or large refactorings to the shared `importer2026` or
  `exporter2026` tools require the user's confirmation before implementation, unless the
  current request already explicitly authorizes that change.
- The target domain/schema belongs to [sample-service](../sample-service/AGENTS.md).
  Read its current rules before changing mappings; old draft-schema guidance is historical.
- Keep execution flags, sequence-reset procedures, paths and completion status in the
  runbook only. Check the actual command and target before executing it.
