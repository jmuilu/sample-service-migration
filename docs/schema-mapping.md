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

| DB2 value | → | Postgres check value | Notes |
|-----------|---|---|---|
| `AVAILABLE` | → | `AVAILABLE` | Direct |
| `NOT_AVAILABLE` | → | `NOT_AVAILABLE` | Direct |
| `PENDING` | → | `PENDING` | Direct |
| *(any other)* | → | **FAIL** | Log unmapped value, halt migration — do not silently drop |

### CONTAINER_BASETYPE

| DB2 value | → | Postgres check value | Notes |
|-----------|---|---|---|
| `SITE` | → | `SITE` | Direct |
| `FREEZER` | → | `FREEZER` | Direct |
| `RACK` | → | `RACK` | Direct |
| `SHELF` | → | `SHELF` | Direct |
| `BOX` | → | `BOX` | Direct |
| `PLATE` | → | `PLATE` | Direct |
| *(any other)* | → | **FAIL** | Log unmapped value, halt migration |

## Natural Key Resolution (FK Lookups)

The loader will resolve all FKs via **natural keys**, not surrogate IDs:

1. **`sample_type_id`**: lookup `sample_type` by `(name, abbreviation)` — both columns uniquely identify a row
2. **`container_type_id`**: lookup `container_type` by `name`
3. **`container_id`** (on sample): lookup `container` by `name` (barcode)
4. **`parent_container_id`** (self): lookup `container` by `name` (barcode)
5. **`parent_id`** (self on sample): lookup `sample` by `sampleid`

All lookups happen **against the target Postgres schema**, which is assumed to be pre-populated or created by `sample-service`'s Liquibase migrations.

## Open Items

1. **`BIOBANK3.VIEW_SAMPLE_MASTER` column list**: confirm exact columns and whether `CONTAINER_NAME`, `SAMPLETYPE` (name), `PARENT_SAMPLEID` are already flattened or need custom export SQL. Requires live DB2 connection.
2. **Unmapped BASETYPE/SAMPLE_STATUS values**: if legacy DB2 data contains values not in the remap tables above, the migration will fail loudly. Consult stakeholders to determine correct mapping for any new values.

## Next step

→ See `docs/migration-strategy.md` for the execution plan.
