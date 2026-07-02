# sample-service-migration

Tools and scripts for migrating biobank sample database from DB2 to PostgreSQL (targeting the new `sample-service` simplified schema).

## Overview

This project contains:
- **Schema mapping documentation** — how DB2 tables/columns map to the new Postgres `sample-service` schema
- **Data extraction via `exporter2026`** — reuses the complete, tested DB2→CSV tool
- **Custom loader** — Java/Spring Boot app that transforms and loads CSVs into the target Postgres schema
- **Validation tools** — compare source/target row counts, check FK/unique-constraint integrity
- **Migration playbook** — step-by-step runbook for the actual cutover

## Key design decisions

- **Reuse `exporter2026` for extraction**: The org's purpose-built DB2→CSV exporter (already complete, tested) handles JDBC metadata introspection and FK→natural-key resolution. No custom extraction code needed.
- **Leverage local services for loading**: The custom `loader` app leverages `importer2026` and `exporter2026` libraries via a Gradle composite build to transform and load CSV data into the target Postgres schema. The target schema requires complex transformation logic (consolidating legacy per-sample-group DB2 tables, enum remapping, sequence ID generation, explicit audit-column backfill) that are handled in the `loader` module while reusing shared components.
- **Current location only**: Migrate only current `container_id`/`placecode` columns, not synthetic audit history. DB2 location history is reconstructed from `EVENT` rows (out of scope).
- **Scope: 4 tables only**: `sample_type`, `container_type`, `container`, `sample` (matching `sample-service` M1+M2). Everything else (`EVENT`, `TASK`, annotations, batch lists, sample profiles, ID generators, consent/participant) is deferred until `sample-service` M3+ implements those entities.

## Project structure

```
.
├── README.md                      (this file)
├── docs/
│   ├── schema-mapping.md          # DB2 ↔ sample-service Postgres mapping, detailed transformations
│   ├── migration-strategy.md      # 3-phase cutover plan, timeline, rollback
│   └── data-requirements.md       # Data type conversions, enum remapping rules, validation checklist
├── export/
│   └── tables.md                  # exporter2026 CLI invocations (one per source table/view)
├── loader/                        # Custom loader app (Java 21 / Spring Boot / Gradle)
│   ├── build.gradle.kts           # Kotlin DSL build script
│   ├── settings.gradle.kts        # Composite build configuration
│   ├── src/main/java/com/bcplatforms/samplemigration/
│   │   ├── LoaderApplication.java
│   │   ├── csv/            # CsvStreamReader (lift pattern from importer2026)
│   │   ├── lookup/         # NaturalKeyResolver (queries target Postgres)
│   │   ├── enums/          # SampleStatusMapper, ContainerBaseTypeMapper
│   │   └── load/           # Entity loaders (ordered by FK dependency)
│   └── src/test/java/...   # Testcontainers integration tests
└── Makefile                       # Targets: export, load, validate, clean
```

## Quick start

1. **Review the schema mapping**: `docs/schema-mapping.md`
2. **Extract from DB2**: `make extract-data` (uses `exporter2026`; see `export/tables.md` for CLI details)
3. **Load into Postgres**: `make load-target` (runs the loader app against CSVs)
4. **Validate**: `make validate-source` or `make verify` (row counts, FKs, enums, spot-checks)

See `docs/migration-strategy.md` for the full 3-phase runbook and rollback plan.

## Building the loader app

The `loader` project uses a composite build to include `exporter2026`, `importer2026`, and `sample-service` as local dependencies. Since `loader` does not have its own Gradle wrapper, use the one from a sibling project or a local Gradle installation.

```bash
# Using sibling gradlew
../../exporter2026/gradlew -p loader build

# Run the loader
../../exporter2026/gradlew -p loader bootRun
```

## DB2 connectivity

The DB2 database is available on port `50000`. Credentials for the test environment are stored in `.server/biobank-test.conf`.

This machine doesn't have DB2 access. Once a DB2 connection is available:
1. Confirm `BIOBANK3.VIEW_SAMPLE_MASTER` column list (flattened FKs)
2. Run `exporter2026` against the live DB2 instance
3. Feed output CSVs into the loader
