# Global Preferences for sample-service-migration

This file extends or overrides global settings for this project.

## ⚠️ CRITICAL: Read the Runbook First
Always read [LLM_MIGRATION_RUNBOOK.md](file:///Users/muilu/git/others/sample-service-migration/LLM_MIGRATION_RUNBOOK.md) at the start of the session. It contains the active Zero-Compile ETL migration execution playbook, credentials, paths, and status checklist.

## Migration Guidance
- **Zero-Compile ETL:** Do NOT write custom Java loader classes in the `loader/` directory. All migrations must use `exporter2026` + `importer2026` + YAML manifests and JS transformations in `config/`.
- **Status:** `sample_type`, `container_type`, `container` and `sample` migrations are COMPLETE. All 4 core tables are successfully migrated.
- **Notify on Shared Tool Changes:** You MUST notify the user and obtain confirmation before introducing any major architectural changes or large refactorings inside the generic `importer2026` or `exporter2026` projects.
- **Absolute Paths:** When running Gradle `bootRun` tasks for sibling projects, always specify absolute paths for CSV/manifest arguments.
- **Postgres Driver:** Always append `--spring.datasource.driver-class-name=org.postgresql.Driver` to `importer2026` execution commands.

## Development Commands
- Build importer: `../importer2026/gradlew -p ../importer2026 build -x test`
- Test importer: `../importer2026/gradlew -p ../importer2026 test`
- Build legacy loader: `../../exporter2026/gradlew -p loader build`
- Run legacy loader: `../../exporter2026/gradlew -p loader bootRun`
- Clean work files: `make clean`
