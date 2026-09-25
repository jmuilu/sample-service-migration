# sample-service-migration

Tools and scripts for migrating biobank sample database from DB2 to PostgreSQL (targeting the new `sample-service` simplified schema).

## Overview

This project contains:
- **Schema mapping documentation** — how DB2 tables/columns map to the new Postgres `sample-service` schema
- **Data extraction via `exporter2026`** — reuses the complete, tested DB2→CSV tool
- **Generic loader via `importer2026`** — reuses the generic importer tool with project-specific YAML manifests and JS/SpEL transformation scripts
- **Validation tools** — compare source/target row counts, check FK/unique-constraint integrity
- **Migration playbook** — step-by-step runbook for the actual cutover

## Key design decisions

- **Reuse `exporter2026` for extraction**: The org's purpose-built DB2→CSV exporter (already complete, tested) handles JDBC metadata introspection and FK→natural-key resolution. No custom extraction code needed.
- **Leverage generic loading with scriptable transformations**: Use the generic `importer2026` tool. Project-specific mappings are configured in YAML manifests, and complex transformation logic (abbreviation mappings, enum remapping) is executed via external JavaScript/SpEL scripts loaded dynamically by `importer2026`. This keeps the Java importer generic and reusable for other databases.
- **Current location only**: Migrate only current `container_id`/`placecode` columns, not synthetic audit history. DB2 location history is reconstructed from `EVENT` rows (out of scope).
- **Scope**: see [`LLM_MIGRATION_RUNBOOK.md`](LLM_MIGRATION_RUNBOOK.md) §2 for the current per-table migration status — `sample_type`, `container_type`, `container`, `sample`, `sample_quality`, `work_list`/`work_list_item`, `event`, and `sample_profile*` are all complete; ID generators and consent/participant remain deferred until `sample-service` implements those entities.

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
├── config/                        # Project-specific migration configurations
│   ├── manifests/                 # YAML manifests defining column mapping & FK resolution rules
│   └── scripts/                   # JS/SpEL scripts for data transformations (abbreviations, enums)
└── Makefile                       # Targets: export, load, validate, clean
```

## Prerequisites

Before you begin, ensure you have the following installed and configured:

- **Java 21**: Sibling projects are built with Java 21.
- **PostgreSQL**: A running PostgreSQL instance is required for `importer2026` to connect to. The connection details are configured in `importer2026/src/main/resources/application.properties` or overridden via CLI.
- **Sibling Project Paths**: You must have `exporter2026` and `importer2026` projects cloned and located correctly in sibling directories relative to this project root.
- **DB2 Access**: For the data extraction step (`make extract-data`), you will need access to the source DB2 database.

## Quick start

1. **Review the schema mapping**: `docs/schema-mapping.md`
2. **Extract from DB2**: `make extract-data` (uses `exporter2026`; see `export/tables.md` for CLI details)
3. **Load into Postgres**: `make load-target` (runs `importer2026` with config manifests and scripts)
4. **Validate**: `make validate-source` or `make verify` (row counts, FKs, enums, spot-checks)

See `docs/migration-strategy.md` for the full 3-phase runbook and rollback plan.

## Executing the Load step with importer2026

The migration uses the generic `importer2026` application. Run it using its Gradle tasks, pointing to the CSV files and project-specific manifests:

```bash
# Run the generic importer with project-specific manifest
../../importer2026/gradlew -p ../../importer2026 bootRun --args='--csv=export/samplegroup.csv --manifest=config/manifests/sample-type-manifest.yaml'
```

## Python Environment Setup

This project uses `uv` for Python package management. To get started with the Python scripts for validation and data analysis, follow these steps:

1. **Install `uv`**:
   If you don't have `uv` installed, run the following command:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Create a virtual environment**:
   ```bash
   uv venv
   ```

3. **Activate the virtual environment**:
   ```bash
   source .venv/bin/activate
   ```

4. **Install dependencies**:
   ```bash
   uv pip install -e .
   ```

Now you can run any Python scripts in the `scripts/` directory.

## DB2 connectivity

The DB2 database is available on `localhost` (port `50000`), with database name `BCDEMO` accessed as user `db2inst1`. Credentials for the test environment are stored in `.server/biobank-test.conf`.

A local connection is available, and you can interact with it via the `db2-biobank-test` MCP server.

### Source Database Statistics
Current counts from the DB2 source database:
- **Total Participants** (`BBVIEW.PARTICIPANT`): **806,265**
- **Insight Project Participants** (`BCPROJECT.INSIGHT_PROJECT_PARTICIPANT`): **2,022**
- **Subjects** (`BCDEMO.SUBJECTS`): **29**
- **Subjects 2** (`BCDEMO.SUBJECTS2`): **764**

### Next Steps
1. Confirm `BIOBANK3.VIEW_SAMPLE_MASTER` column list (flattened FKs)
2. Run `exporter2026` against the live DB2 instance
3. Feed output CSVs into the loader

