# DB2 ↔ Postgres Schema Mapping

Maps the existing DB2 schema (schemas `BIOBANK3`, `BCPROJECT`, `CORE`) to the new PostgreSQL `sample-service` schema (schema `sample`, 4 tables only).

## Overview

| Aspect | DB2 | Postgres |
|--------|-----|----------|
| Databases & schemas | `BIOBANK`, `BCPROJECT`, `CORE`, `BCSUBJECT` | `bcsystem` (schema: `sample`; schema: `bcapp` for audit procedures) |
| Character set | ASCII/EBCDIC | UTF-8 |
| Date/Time | DB2 DATE/TIME/TIMESTAMP | PostgreSQL timestamp |
| Numeric | DECIMAL, INTEGER | NUMERIC, BIGINT |
| String | VARCHAR, CHAR | VARCHAR, TEXT |
| Sequences | `nextval('seq_name')` | `nextval('seq_name')` — compatible |
| Constraints | FK, UK, CK | Same — fully compatible |

## Core Table Mappings

### 1. SAMPLE_TYPE: `BIOBANK3.SAMPLEGROUP` → `sample.sample_type`

| DB2 Column | DB2 Type | Postgres Column | PG Type | Transformation |
|-----------|----------|-----------------|---------|---|
| GROUPNR | BIGINT | (dropped) | — | Do not use; new `id` auto-generated via `sample.sample_type_id_seq` |
| NAME | VARCHAR(128) | name | VARCHAR(128) | Direct copy; UNIQUE constraint |
| ABBREVIATION | VARCHAR(5) | abbreviation | VARCHAR(20) | Direct copy; UNIQUE constraint |
| DESCRIPTION | TEXT | description | TEXT | Direct copy, nullable |
| USERNAME | VARCHAR(128) | userstamp | VARCHAR(128) | Preserve original; DB2 audit value |
| TIMELOG | TIMESTAMP | created | TIMESTAMP | Preserve original; DB2 audit value |
| (new) | — | version | INTEGER | Hardcode `1` for all migrated rows |

### 2. CONTAINER_TYPE: `BIOBANK3.CONTAINERTYPE` → `sample.container_type`

| DB2 Column | DB2 Type | Postgres Column | PG Type | Transformation |
|-----------|----------|-----------------|---------|---|
| (surrogate PK) | BIGINT | (dropped) | — | Do not use; new `id` auto-generated via `sample.container_type_id_seq` |
| NAME | VARCHAR(64) | name | VARCHAR(64) | Direct copy; UNIQUE constraint |
| BASETYPE | VARCHAR(32) | basetype | VARCHAR(32) | **ENUM REMAP**: lookup value in remap table; CHECK `IN ('SITE','FREEZER','RACK','SHELF','BOX','PLATE')` |
| X | INTEGER | x | INTEGER | Direct copy; grid columns (0 = no grid) |
| Y | INTEGER | y | INTEGER | Direct copy; grid rows (0 = no grid) |
| DESCRIPTION | TEXT | description | TEXT | Direct copy, nullable |
| USERNAME | VARCHAR(128) | userstamp | VARCHAR(128) | Preserve original |
| TIMELOG | TIMESTAMP | created | TIMESTAMP | Preserve original |
| (new) | — | version | INTEGER | Hardcode `1` |

### 3. CONTAINER: `BIOBANK3.CONTAINER` → `sample.container`

| DB2 Column | DB2 Type | Postgres Column | PG Type | Transformation |
|-----------|----------|-----------------|---------|---|
| ID | BIGINT | (dropped) | — | Do not use; new `id` auto-generated via `sample.container_id_seq` |
| NAME | VARCHAR(64) | name | VARCHAR(64) | Direct copy; **barcode** — UNIQUE constraint |
| DESCRIPTION | TEXT | description | TEXT | Direct copy, nullable |
| TYPE | VARCHAR(64) | container_type_id | BIGINT (FK) | **LOOKUP**: `TYPE` → `sample.container_type.name` → new `id` |
| PARENT | BIGINT (self-FK) | parent_container_id | BIGINT (FK, self) | **SELF-REF LOOKUP**: `PARENT` → `CONTAINER.NAME` → new `id` in `sample.container`; nullable |
| PLACECODE | VARCHAR(64) | placecode | VARCHAR(30) | Direct copy; nullable; part of UNIQUE `(parent_container_id, placecode)` |
| USERNAME | VARCHAR(128) | userstamp | VARCHAR(128) | Preserve original |
| TIMELOG | TIMESTAMP | created | TIMESTAMP | Preserve original |
| (new) | — | version | INTEGER | Hardcode `1` |

**Note**: DB2 `CONTAINER` also has `X`, `Y` (grid dims) at the row level. New schema stores these only in `CONTAINER_TYPE`, not per container.

### 4. SAMPLE: `BIOBANK3.VIEW_SAMPLE_MASTER` (consolidates `SAMPLE_10002`, `SAMPLE_10003`, ...) → `sample.sample`

| DB2 Column | DB2 Type | Postgres Column | PG Type | Transformation |
|-----------|----------|-----------------|---------|---|
| (surrogate PK) | BIGINT | (dropped) | — | Do not use; new `id` auto-generated via `sample.sample_id_seq` |
| SAMPLEID | VARCHAR(64) | sampleid | VARCHAR(64) | Direct copy; **business ID** — UNIQUE constraint |
| SUBJECT | VARCHAR(64) | subjectid | VARCHAR(64) | Direct copy; loose reference (no FK), nullable |
| SAMPLETYPE | VARCHAR(128) | sample_type_id | BIGINT (FK) | **LOOKUP**: `SAMPLETYPE` name → `sample.sample_type.name` → new `id` |
| SAMPLE_STATUS | VARCHAR(32) | sample_status | VARCHAR(32) | **ENUM REMAP**: lookup in remap table; CHECK `IN ('PENDING','AVAILABLE','NOT_AVAILABLE')` |
| AMOUNT | INTEGER | amount | INTEGER | Direct copy; nullable; unit: microliters |
| CONCENTRATION | REAL | concentration | REAL | Direct copy; nullable |
| REMARKS | VARCHAR(2000) | remarks | TEXT | Direct copy; nullable |
| COMMENT | VARCHAR(255) | comment | VARCHAR(255) | Direct copy; nullable |
| CONTAINER_NAME | VARCHAR(64) | container_id | BIGINT (FK) | **LOOKUP**: `CONTAINER_NAME` → `sample.container.name` → new `id`; nullable (samples may be unplaced) |
| PLACECODE | VARCHAR(64) | placecode | VARCHAR(30) | Direct copy; nullable; part of UNIQUE `(container_id, placecode)` |
| PARENT_SAMPLEID | VARCHAR(64) | parent_id | BIGINT (FK, self) | **SELF-REF LOOKUP**: `PARENT_SAMPLEID` → `sample.sample.sampleid` → new `id` in `sample.sample`; nullable (non-aliquots) |
| USERNAME | VARCHAR(128) | userstamp | VARCHAR(128) | Preserve original |
| TIMELOG | TIMESTAMP | created | TIMESTAMP | Preserve original |
| (new) | — | version | INTEGER | Hardcode `1` |

**Note**: DB2 uses multiple sample tables (`SAMPLE_10002`, `SAMPLE_10003`, ...) unified via `VIEW_SAMPLE_MASTER`. Export must target the view or an equivalent join that flattens parent/sibling/container references to natural-key strings.

## Enum Remapping

### SAMPLE_STATUS

Actual distinct values in DB2 `BIOBANK3.VIEW_SAMPLE_MASTER` are title-case/mixed-case. Normalization is required during migration (converting to uppercase and replacing spaces with underscores) before checking against Postgres constraints:

| DB2 value | → | Normalized DB2 | → | Postgres value | Notes |
|-----------|---|----------------|---|----------------|-------|
| `Available` | → | `AVAILABLE` | → | `AVAILABLE` | Case normalization |
| `Not available` | → | `NOT_AVAILABLE` | → | `NOT_AVAILABLE` | Space replaced with underscore |
| `Pending` | → | `PENDING` | → | `PENDING` | Case normalization |
| `NULL` | → | `NULL` | → | `NULL` | Nullable column |
| *(any other)* | → | — | → | **FAIL** | Log unmapped value, halt migration |

### CONTAINER_BASETYPE

Actual distinct values in DB2 `CONTAINERTYPE` include several legacy/specialty values. Postgres `sample.container_type` strictly enforces the check constraint `IN ('SITE','FREEZER','RACK','SHELF','BOX','PLATE')`.

| DB2 value | → | Postgres value | Status & Notes |
|-----------|---|----------------|----------------|
| `site` | → | `SITE` | Case normalization |
| `freezer` | → | `FREEZER` | Case normalization |
| `rack` | → | `RACK` | Case normalization |
| `shelf` | → | `SHELF` | Case normalization |
| `box` | → | `BOX` | Case normalization |
| `plate` | → | `PLATE` | Case normalization |
| `no-location` | → | **FAIL / TBD** | Used by 2 containers. Needs mapping strategy (e.g. map to `SITE` or exclude). |
| `trash` | → | **FAIL / TBD** | Used by 1 container (`Trash`). Needs mapping strategy. |
| `used` | → | **FAIL / TBD** | Used by 3 containers (`Empty`, `Lost`, `Picked`). Needs mapping strategy. |
| `ASA`, `drawer`, `MEGA` | → | **FAIL** | Defined in `CONTAINERTYPE` but currently used by 0 containers. |

---

## Resolved Open Items

1. **`BIOBANK3.VIEW_SAMPLE_MASTER` columns verified (Resolved)**:
   A live database query confirmed that the view `BIOBANK3.VIEW_SAMPLE_MASTER` exists and contains the necessary columns:
   - `CONTAINER_NAME` (VARCHAR 64, nullable) — ready for natural key resolution.
   - `SAMPLETYPE` (VARCHAR 128, non-null) — ready for mapping to `sample_type_id`.
   - `PARENT_SAMPLEID` (VARCHAR 64, nullable) — ready for self-referential lookup.
   - `SAMPLEID` (VARCHAR 64), `SUBJECT` (VARCHAR 64), `AMOUNT` (INTEGER), `CONCENTRATION` (REAL), `USERNAME` (VARCHAR 128), and `TIMELOG` (TIMESTAMP).

2. **Unmapped BASETYPE/SAMPLE_STATUS values verified (Resolved)**:
   - **`SAMPLE_STATUS`**: The values are `'Available'`, `'Not available'`, and `'Pending'`. Normalization is handled via JavaScript/SpEL scripts in the `importer2026` pipeline (e.g. converting space to underscore and uppercase).
   - **`CONTAINER_BASETYPE`**: Legacy containers exist with basetypes `'no-location'`, `'trash'`, and `'used'`. These are mapped to standard types (e.g. `SITE`) using script-based rules during import.

## Natural Key Resolution (FK Lookups)

The `importer2026` application resolves all FKs via **natural keys**, not surrogate IDs, as defined in the YAML manifest files.

1. **`sample_type_id`**: lookup `sample_type` by `(name, abbreviation)` — both columns uniquely identify a row
2. **`container_type_id`**: lookup `container_type` by `name`
3. **`container_id`** (on sample): lookup `container` by `name` (barcode)
4. **`parent_container_id`** (self): lookup `container` by `name` (barcode)
5. **`parent_id`** (self on sample): lookup `sample` by `sampleid`

All lookups happen **against the target Postgres schema**, which is assumed to be pre-populated or created by `sample-service`'s Liquibase migrations.


## Next step

→ See `docs/migration-strategy.md` for the execution plan.
