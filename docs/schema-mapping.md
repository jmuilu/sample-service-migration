# DB2 ↔ Postgres Schema Mapping

Maps the existing DB2 schema to the new PostgreSQL schema defined in `sample-service`.

## Overview

| Aspect | DB2 | Postgres |
|--------|-----|----------|
| Database | `BIOBANK` | `bcsystem` (schema: `sample`) |
| Character set | EBCDIC/ASCII | UTF-8 |
| Date/Time | DB2 DATE/TIME/TIMESTAMP | PostgreSQL timestamp |
| Numeric | DECIMAL, INTEGER | NUMERIC, BIGINT |
| String | VARCHAR, CHAR | VARCHAR, TEXT |
| Sequences | SEQUENCE | sequence (compatible) |
| Constraints | FK, UK, CK | Same (fully compatible) |

## Tables & Column Mappings

### SAMPLE table

| DB2 Column | Type | → | Postgres Column | Type | Notes |
|-----------|------|---|-----------------|------|-------|
| SAMPLE_ID | BIGINT | → | id | BIGINT (PK) | Rename to `id`, generate via sequence |
| SAMPLE_NUM | VARCHAR(64) | → | sampleid | VARCHAR(64) (UK) | Business ID, e.g. `OBB-2025-1` |
| SUBJECT_ID | VARCHAR(64) | → | subjectid | VARCHAR(64) | Loose reference (no FK in either) |
| SAMPLE_TYPE_ID | BIGINT | → | sample_type_id | BIGINT (FK) | Reference to SAMPLE_TYPE |
| PARENT_SAMPLE_ID | BIGINT | → | parent_id | BIGINT (FK, self) | Aliquot parent |
| STATUS | CHAR(32) | → | sample_status | VARCHAR(32) | Enum-backed, values: PENDING/AVAILABLE/NOT_AVAILABLE |
| AMOUNT | DECIMAL(10,2) | → | amount | INTEGER | Unit: microliters (integer, no decimals) |
| ... (more columns) | ... | → | ... | ... | See `sample-service` entity for full list |
| (audit) | — | → | userstamp, created, version | VARCHAR(128), TIMESTAMP, INTEGER | Added by Postgres schema |

### (Continue mapping for other core tables...)

- **SAMPLE_TYPE** — 1:1 mapping, add audit columns
- **CONTAINER** — new location model (container_id/placecode instead of location_id)
- **CONTAINER_TYPE** — new, basetype enum
- (Other tables — to be detailed as schema stabilizes)

## Key differences

1. **Location model**: DB2 uses a discrete location_id FK; Postgres uses `container_id`/`placecode` pair — see `sample-service` ADR 0001.
2. **Audit columns**: DB2 may not have `userstamp`/`created`/`version`; Postgres requires all three.
3. **ID generation**: DB2 may use triggers; Postgres uses sequences with `@GeneratedValue(strategy = SEQUENCE)`.
4. **Enums**: DB2 CHARs with check constraints; Postgres uses VARCHAR + check constraint matching Java enum values.

## Validation checklist

- [ ] All DB2 tables identified and mapped
- [ ] All column types confirmed to have Postgres equivalents
- [ ] Null/non-null constraints documented
- [ ] Unique constraints mapped
- [ ] Foreign key relationships verified
- [ ] Sequence/ID generation strategy aligned
- [ ] Audit column strategy confirmed (backfill vs. trigger defaults)
- [ ] Sample of real data extracted and type-checked in Postgres

## Next step

→ See `docs/migration-strategy.md` for the execution plan.
