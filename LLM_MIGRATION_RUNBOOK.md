# LLM Migration Runbook & AI Context Sheet

This document serves as the single source of truth for LLM agents and AI tools to execute, maintain, and extend the biobank database migration from DB2 to PostgreSQL. It is optimized for low token usage and high execution efficiency.

---

## 1. Active Architecture: Generic ETL (Zero-Compile)

The migration is completely decoupled from custom Java application code. Instead, we use pre-compiled generic tools combined with text-based manifests and JavaScript scripts:

```mermaid
graph LR
    DB2[(Source DB2)] -->|1. Extract: exporter2026| RawCSV[Raw CSV]
    RawCSV -->|2. Transform: JS| CleanCSV[Clean CSV]
    CleanCSV -->|3. Load: importer2026| Postgres[(Target PG)]
```

* **Extract:** `exporter2026` runs dynamic JDBC queries against DB2 and flattens PK/FK structures into natural keys in raw CSV files.
* **Transform:** JavaScript scripts (executed dynamically via Java's Nashorn engine inside `importer2026` pipeline) normalize values, map enums, and generate fallback slugs/identifiers.
* **Load:** `importer2026` reads the YAML manifest, executes row transformations, resolves natural keys to target Postgres surrogate IDs (caching queries for performance and self-joins), and bulk-inserts the clean data.

---

## 2. Status of Migrations

* **sample_type**: ✅ **COMPLETE**. Migrated successfully using the generic ETL method with [sample_type_manifest.yaml](file:///Users/muilu/git/others/biobank-solution/sample-service-migration/config/manifests/sample_type_manifest.yaml) and [sample_type_transform.js](file:///Users/muilu/git/others/biobank-solution/sample-service-migration/config/scripts/sample_type_transform.js). Legacy `SampleTypeLoader.java` has been removed.
* **container_type**: ✅ **COMPLETE**. Migrated successfully using the generic ETL method with [container_type_manifest.yaml](file:///Users/muilu/git/others/biobank-solution/sample-service-migration/config/manifests/container_type_manifest.yaml) and [container_type_transform.js](file:///Users/muilu/git/others/biobank-solution/sample-service-migration/config/scripts/container_type_transform.js).
* **container**: ✅ **COMPLETE**. Migrated successfully using the generic ETL method with [container_manifest.yaml](file:///Users/muilu/git/others/biobank-solution/sample-service-migration/config/manifests/container_manifest.yaml). Note: Because containers contain self-referential parent-child relationships, `--sort-self-joins` must be used during import to guarantee correct parent resolution.
* **sample**: ✅ **COMPLETE**. Migrated successfully using the generic ETL method with [sample_manifest.yaml](file:///Users/muilu/git/others/biobank-solution/sample-service-migration/config/manifests/sample_manifest.yaml) and [sample_transform.js](file:///Users/muilu/git/others/biobank-solution/sample-service-migration/config/scripts/sample_transform.js). **(2026-09-23 update: ADR 0015 added native provenance/HL7 columns to `sample.sample` — `source`/`sourceid`/`altid`/`source_file`/`error_remarks` added to this same manifest, sourced directly from `export/sample.csv` which already had the needed DB2 columns; `organ`/`lab_code`/`messageid` investigated and left unmapped, no reliable DB2 source found. See [sample-attributes-migration-plan.md](file:///Users/muilu/git/others/biobank-solution/sample-service-migration/docs/sample-attributes-migration-plan.md) §2.)**
* **sample_property → sample.attributes (DNA)**: ⚠️ **SUPERSEDED, RE-IMPLEMENTED (2026-09-23)**. ADR 0017 deleted the EAV `sample.sample_property` model outright; the DNA-specific migration this repo previously ran into it (`sample_property_manifest.yaml`/`property_transform.js`/`seed_properties.sql`, all now deleted from this repo) has been replaced with [dna_attributes_manifest.yaml](file:///Users/muilu/git/others/biobank-solution/sample-service-migration/config/manifests/dna_attributes_manifest.yaml) + [dna_attributes_transform.js](file:///Users/muilu/git/others/biobank-solution/sample-service-migration/config/scripts/dna_attributes_transform.js), writing directly into `sample.sample.attributes` (jsonb) and the new native `volume_ext` column. Required adding JSON/JSONB column support to `importer2026` itself (user-approved) — see [sample-attributes-migration-plan.md](file:///Users/muilu/git/others/biobank-solution/sample-service-migration/docs/sample-attributes-migration-plan.md) for the full writeup, including the still-open gap for EDTA Whole Blood / TestNäyte (no new attribute registry entries exist for them yet) and the `FACTOR`/`DILUTION_FACTOR` mapping decision. **`PivotHelper.java` is no longer used for DNA** (kept, since it's generic and not EAV-specific at the code level, but nothing currently invokes it).
* **sample_quality**: ✅ **COMPLETE**. Migrated legacy qualities using the generic ETL method. Controlled vocabulary `cv_sample_quality` seeded via [seed_qualities.sql](file:///Users/muilu/git/others/biobank-solution/sample-service-migration/scripts/postgres/seed_qualities.sql), allowed metadata via [sample_type_quality_metadata_manifest.yaml](file:///Users/muilu/git/others/biobank-solution/sample-service-migration/config/manifests/sample_type_quality_metadata_manifest.yaml), and sample quality mappings via [sample_quality_manifest.yaml](file:///Users/muilu/git/others/biobank-solution/sample-service-migration/config/manifests/sample_quality_manifest.yaml). Fully documented in [sample-qualities-migration-plan.md](file:///Users/muilu/git/others/biobank-solution/sample-service-migration/docs/sample-qualities-migration-plan.md). **(2026-09-22 fix: the hand-typed `sample_type_quality_metadata.csv` whitelist rejected real historical `(sample_type, quality)` combinations; it's now generated by [generate_quality_metadata.py](file:///Users/muilu/git/others/biobank-solution/sample-service-migration/scripts/generate_quality_metadata.py), which unions a base whitelist with every pair actually observed in the DB2 export.)**
* **work_list** / **work_list_item**: ✅ **COMPLETE**. Migrated legacy picking lists and batch sample associations successfully using the generic ETL method with [work_list_manifest.yaml](file:///Users/muilu/git/others/biobank-solution/sample-service-migration/config/manifests/work_list_manifest.yaml) and [work_list_item_manifest.yaml](file:///Users/muilu/git/others/biobank-solution/sample-service-migration/config/manifests/work_list_item_manifest.yaml) and [work_list_transform.js](file:///Users/muilu/git/others/biobank-solution/sample-service-migration/config/scripts/work_list_transform.js). Fully documented in [work-lists-migration-plan.md](file:///Users/muilu/git/others/biobank-solution/sample-service-migration/docs/work-lists-migration-plan.md). **(2026-09-22 fix: `work_list_manifest.yaml` mapped `PROJECT_ABBREVIATION`/`PARTNER_NAME` to `project_id`/`partner_id` columns that don't exist on `sample.work_list` and never did — removed; the plan doc always specified `PROJECT_ID` as dropped.)** **(2026-09-25 fix: `work_list_item_manifest.yaml` mapped `completed_by`/`completed_at` onto `sample.work_list_item`, columns that ADR 0018 (2026-09-24) removed from scope — completion is now tracked via `sample.event` PICKED/STORED rows keyed by `task_id`, not columns on the item. Mappings removed; [work-lists-migration-plan.md](file:///Users/muilu/git/others/biobank-solution/sample-service-migration/docs/work-lists-migration-plan.md)'s table for this manifest is now stale on this point.)**
* **event** (legacy sample events): ✅ **COMPLETE**. Migrated `BIOBANK3.EVENT` into `sample.event` using [event_manifest.yaml](file:///Users/muilu/git/others/biobank-solution/sample-service-migration/config/manifests/event_manifest.yaml) with [event_transform.js](file:///Users/muilu/git/others/biobank-solution/sample-service-migration/config/scripts/event_transform.js) for `EVENT_TYPE`/`EVENT_REASON` normalization and [filter_legacy_events.py](file:///Users/muilu/git/others/biobank-solution/sample-service-migration/scripts/filter_legacy_events.py) to exclude picking-list actions that have no target table today. Fully documented in [legacy-events-migration-plan.md](file:///Users/muilu/git/others/biobank-solution/sample-service-migration/docs/legacy-events-migration-plan.md).

---

## 3. Step-by-Step Playbook for Migrating a New Table (Zero-Compile)

When migrating the next table, follow these exact steps to save tokens and avoid redundant research:

### Step 1: Extract (via `exporter2026`)
Run the exporter pointing to the source DB2 table and output directory. Always use absolute paths for the output file:
```bash
# Path: /Users/muilu/git/exporter2026
./gradlew bootRun --args='--table=BIOBANK3.SRC_TABLE --output=/Users/muilu/git/others/biobank-solution/sample-service-migration/export/src_table.csv --spring.datasource.url=jdbc:db2://localhost:50000/BCDEMO --spring.datasource.username=db2inst1 --spring.datasource.password=Adm1Pwd1'
```

### Step 2: Define Transformation Script (JavaScript)
If the table has columns requiring transformation (like enums or string cleanup), create a script at `config/scripts/<target_table>_transform.js`. 
* Keep transformations **stateless/independent** of the database.
* To support relative paths, `importer2026` resolves paths relatively to the manifest file location if they are not found in the current working directory.

### Step 3: Define Manifest & Load (via `importer2026`)
Create `config/manifests/<target_table>_manifest.yaml` mapping the CSV to Postgres.
* **Important:** Always override the driver class name to Postgres when running `importer2026`, as the default in its `application.properties` is DB2: `--spring.datasource.driver-class-name=org.postgresql.Driver`
* If the table contains self-referential parent-child foreign keys (specifically `sample` or `container`), always append the `--sort-self-joins` command-line argument.
* Always use absolute paths for the CSV and manifest parameters when running via Gradle, as the working directory switches to the sibling folder:
```bash
# Path: /Users/muilu/git/others/biobank-solution/sample-service-migration
../../importer2026/gradlew -p ../../importer2026 bootRun --args='--csv=/Users/muilu/git/others/biobank-solution/sample-service-migration/export/src_table.csv --manifest=/Users/muilu/git/others/biobank-solution/sample-service-migration/config/manifests/target_table_manifest.yaml --spring.datasource.url=jdbc:postgresql://localhost:5432/sample --spring.datasource.username=sample --spring.datasource.password=sample --spring.datasource.driver-class-name=org.postgresql.Driver --spring.main.web-application-type=none --sort-self-joins'
```

### Step 4: Verification & Sequence Reset
1. Empty the target table before starting: `TRUNCATE sample.target_table CASCADE;`
   > [!WARNING]
   > `TRUNCATE` is only used during local development, staging tests, and initial clean imports. 
   > In production cutover or delta migrations, do **NOT** run truncate. The loader uses idempotent `UPSERT` (`ON CONFLICT DO UPDATE`) to safely merge changes and allow resuming runs from failures.
2. Run the load step.
3. After loading, reset the database sequence:
   ```sql
   SELECT setval('sample.<table_name>_id_seq', COALESCE((SELECT MAX(id) FROM sample.<table_name>), 1));
   ```
4. Verify row counts and spot-check data integrity.

---

## 4. Sibling Project Paths & Connections

* **Source DB2:** `jdbc:db2://localhost:50000/BCDEMO` (user: `db2inst1`, password: `Adm1Pwd1`).
* **Target Postgres:** `jdbc:postgresql://localhost:5432/sample` (user: `sample`, password: `sample`).
* **Sibling Paths:**
  * Exporter: `/Users/muilu/git/exporter2026`
  * Importer: `/Users/muilu/git/importer2026`
  * Migration workspace: `/Users/muilu/git/others/biobank-solution/sample-service-migration` (this repository)

---

## 5. Summary of importer2026 Capabilities
The generic importer (`importer2026`) has the following features pre-built and ready:
- **Implicit Column Types**: The `type` field in column mappings is optional; if omitted, it is auto-discovered from target database metadata.
- **FK Resolution**: Resolves natural keys to surrogate IDs automatically based on `foreignKey` mapping block in manifest.
- **Self-Joins**: Caches resolved IDs and registers newly inserted rows so that parent-child relationships (like parent containers or parent samples) are resolved in a single pass (assuming parents come before children in the sorted CSV).
- **JavaScript Engine**: Embedded Nashorn engine executes JS transformations natively inside JVM 21, allowing stateless transformations without IPC overhead.
- **Row-by-Row RETURNING id & FK Caching (New)**: The importer inserts rows one-by-one appending `RETURNING id` and registers each successful insert's natural keys + generated ID in the resolver cache. This ensures self-referential rows (e.g. child containers referencing parent containers, or aliquots referencing parent samples) in the same file resolve their parent references dynamically.
- **Nullable FKs (New)**: If all mapped CSV columns for a foreign key are empty/blank, the importer directly assigns a `NULL` target value without throwing "Missing foreign key" errors, supporting optional parent references and unplaced containers/samples.
- **Topological Sorting (`--sort-self-joins`) (New)**: The `--sort-self-joins` command-line argument enables topological sorting of CSV rows prior to import. It constructs a dependency graph using the self-referencing foreign keys defined in the manifest, ensuring parents are imported before children. It falls back gracefully and warns if cyclic dependencies are detected.
- **JSON/JSONB Columns (New, 2026-09-23)**: A column mapping whose `type` (explicit or auto-discovered) contains `JSON` is bound via `SqlDialect.wrapJson(...)` instead of a plain string — `PostgreSqlDialect` wraps the value in a `PGobject` (type `jsonb`), avoiding Postgres's "column is of type jsonb but expression is of type character varying" error. Combine with a `transformScript`/`transformFunction` that returns `JSON.stringify(...)` of an object built from other columns in the row.
- **`operation: UPDATE` fix (2026-09-23)**: previously unused by any manifest in this repo (everything used `UPSERT`) and had a latent arg-ordering bug — `BatchLoader` now reorders bound values to match `generateUpdate`'s `SET ... WHERE ...` column order before executing. Use `UPDATE` (not `UPSERT`) for any manifest that only extends already-migrated rows with new columns and must never insert one itself.
