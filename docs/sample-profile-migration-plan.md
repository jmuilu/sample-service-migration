# Migration Plan & Playbook: Sample Profiles

Migrates DB2's sample-profile tables into `sample-service`'s `sample.sample_profile*` tables
(schema: [v009-sample-profile.sql](file:///Users/muilu/git/others/biobank-solution/sample-service/src/main/resources/db/scripts/sample/v009-sample-profile.sql),
status **DRAFT** — see [schema-status.md](file:///Users/muilu/git/others/biobank-solution/sample-service/docs/reference/schema-status.md).
`sample-service` already has full entity/repository/service/controller code and a passing
`SampleProfileIntegrationTest` for this feature — this is a pure data migration, not new backend
work).

All row counts and column values below were verified live against the running `db2-biobank-test`
DB2 instance and the target Postgres (`sample-service-db-1`), not assumed from documentation.

## 1. Source → target table mapping

| DB2 Table | Rows | Target Table |
|---|---|---|
| `BIOBANK3.BIOBANK_SAMPLE_PROFILE` | 10 | `sample.sample_profile` |
| `BIOBANK3.PROFILE_PRIMARY_SAMPLE_TYPE` + `BIOBANK3.PROFILE_SAMPLE_AMOUNT` (1:1 join) | 15 | `sample.sample_profile_primary_sample` |
| `BIOBANK3.PROFILE_ALIQUOT_SAMPLE` | 29 | `sample.sample_profile_aliquot_sample` |
| `BIOBANK3.BIOBANK_SAMPLE_PROFILE_SAMPLE_COLUMN` | 40 (4 rows × 10 distinct column names) | `sample.sample_profile_sample_column` (only the `SOURCE` rows — see §3) |

Unused DB2 tables (0 rows, confirmed live): `BIOBANK_SAMPLE_PROFILE_PROJECT_EVENT`,
`PROFILE_PRIMARY_SAMPLE_PROPERTY`, `PROFILE_ALIQUOT_SAMPLE_PROPERTY`, `PROFILE_SAMPLE_FIELD`,
`PROFILE_SAMPLE_ID_TEMPLATE`. Not migrated.

All natural-key joins (sample type by `SAMPLEGROUP.NAME`, container type by
`CONTAINERTYPE`-style code) resolve cleanly against already-migrated Postgres reference data —
verified 0 mismatches for every sample type / container type referenced by any profile row.

## 2. Column mapping & intentionally dropped columns

### `sample_profile`

| DB2 Column | Destination | Notes |
|---|---|---|
| `NAME` | `name` | Natural key (`UNIQUE`) |
| `IS_DEFAULT_SAMPLE_CREATION` | `is_default` | 0/1 → boolean |
| `USERNAME` | `userstamp` | |
| `TIMELOG` | `created` | |
| `LAB_PACKAGE_CODE` | *(dropped)* | Real values (`BIOBANK`, `BIOBANK2`) on 2/10 profiles |
| `ENABLE_KIT_CREATION` | *(dropped)* | `Y` on 2/10 profiles — real workflow toggle |
| `ENABLE_LAB_REQUEST` | *(dropped)* | `Y` on 2/10 profiles — real workflow toggle |
| `ENABLE_SAMPLE_CREATION` | *(dropped)* | Always `Y` — uninformative |
| `AUTO_ASSIGN`, `IS_DEFAULT_KIT`, `IS_AUTO_ID_GENERATION`, `SIMPLE_AUTO_ASSIGN` | *(dropped)* | Always `0` across all 10 profiles — dead data |

**Decision (2026-09-25): drop LAB_PACKAGE_CODE / ENABLE_KIT_CREATION / ENABLE_LAB_REQUEST,
document only, no schema change.** `sample.sample_profile` has no destination for kit-creation
workflow, lab-request workflow, or lab package code today. This is real, non-default legacy
configuration (not merely cosmetic UI state) that is lost by this migration — a conscious,
approved trade-off, not silent data loss. If kit-creation/lab-request workflows are needed later,
they require a schema change to this DRAFT table plus product input on the intended behavior,
tracked as a future follow-up, not part of this migration.

### `sample_profile_primary_sample` (from `PROFILE_PRIMARY_SAMPLE_TYPE` ⋈ `PROFILE_SAMPLE_AMOUNT`)

| DB2 Column | Destination | Notes |
|---|---|---|
| `BIOBANK_SAMPLE_PROFILE_ID` → profile `NAME` | `sample_profile_id` (FK by name) | |
| `SAMPLE_GROUPNR` → `SAMPLEGROUP.NAME` | `sample_type_id` (FK by name) | |
| `RANK` | `"order"` | |
| `AMOUNT` | `amount` | |
| `CONTAINER_TYPE` | `container_type_id` (FK by name) | Nullable — some rows have no container type |
| `SIMPLE_AUTO_ASSIGN` | `auto_assign` | See ambiguity note below |
| `USERNAME` / `TIMELOG` | `userstamp` / `created` | |
| `PRODUCT_CODE` | *(dropped)* | Real values on 3/15 rows (lab product codes), no destination |
| `MARK_AS_EMPTY` | *(dropped)* | `1` on 2/15 rows, no destination |

**`AUTO_ASSIGN` vs `SIMPLE_AUTO_ASSIGN` ambiguity (resolved):** the target schema has a single
`auto_assign` boolean per row, but `PROFILE_ALIQUOT_SAMPLE` carries both DB2 columns. Live data:
`AUTO_ASSIGN` is `0` for all 29 aliquot rows; `SIMPLE_AUTO_ASSIGN` is `1` for 3 of them. `AUTO_ASSIGN`
is dead at the profile level — `SIMPLE_AUTO_ASSIGN` is the real signal and is what both the primary
and aliquot manifests map to `auto_assign`. (`PROFILE_SAMPLE_AMOUNT`, the primary-sample side, only
has `SIMPLE_AUTO_ASSIGN` in the first place — no ambiguity there.)

**`PRODUCT_CODE` / `MARK_AS_EMPTY` decision (2026-09-25): same as §2's `sample_profile` columns —
drop, document only.**

### `sample_profile_aliquot_sample` (from `PROFILE_ALIQUOT_SAMPLE`)

Same shape as primary sample: `ALIQUOT_SAMPLE_GROUPNR` → `sample_type_id` (FK by name), `NUM` →
`count`, `RANK` → `"order"`, `AMOUNT` → `amount`, `CONTAINER_TYPE` → `container_type_id` (FK,
nullable), `SIMPLE_AUTO_ASSIGN` → `auto_assign`. Parent link
(`sample_profile_primary_sample_id`) resolved via a composite key — see §4.

### `sample_profile_sample_column`

Only 1 of the 10 distinct `SAMPLE_COLUMN` values across the 40 source rows has a destination:

| DB2 `SAMPLE_COLUMN` | Rows | Destination |
|---|---|---|
| `SOURCE` | 4 | `sample.source` (text, exists) |
| `COLLECTION_ID`, `FASTING`, `PIC_TYPE`, `PROJECT_ID`, `SAMPLE_RECEIVED_TEMP`, `SHOW_ORIGINAL_ID`, `TEMP`, `TEMP_BEFORE_STORAGE`, `VISIT_ID` | 36 (9 × 4) | *(dropped — no matching column)* |

Verified live against `sample.view_sample_profile_available_columns` (the catalog view
`sample_profile_sample_column.column_name` is validated against — see
[sample-profile-columns.md](file:///Users/muilu/git/others/biobank-solution/sample-service/docs/reference/sample-profile-columns.md)):
none of the 9 dropped names exist as a real column on `sample.sample` today, including
`PROJECT_ID` — there is no `project_id` FK column on `sample.sample`, so it cannot use the
FK-reference half of `sample_profile_sample_column`'s type-safe design either. All 4 migrated rows
are plain text-literal defaults (`is_fk_reference = false`); no source row in this migration needs
the FK-reference path.

This mirrors the precedent set for ADR 0017's dropped EAV attributes (documented, not silently
lost) — same treatment here, decided 2026-09-25.

## 3. `sample_profile` seed row

The DRAFT schema ships a Liquibase-seeded placeholder row, `'Default Profile'` (`is_default =
true`), inserted once by `v009-sample-profile.sql` and not re-created by this migration's
`clear-target`/`load-target` cycle (Liquibase changesets don't re-run once applied). None of the
10 DB2 profiles are named `'Default Profile'`, so there's no name collision — but
`clear-target`'s `TRUNCATE ... CASCADE` (dev-only, per the runbook) does delete it, and it is not
re-inserted. This is **intentional, not a regression**: one of the 10 migrated profiles,
`WB-PROFILE`, already has `IS_DEFAULT_SAMPLE_CREATION = 1` in DB2, so after migration
`sample.sample_profile` still has exactly one row with `is_default = true` — the real migrated
default, superseding the placeholder.

## 4. Why `sample_profile_primary_sample` / `sample_profile_aliquot_sample` need one extra step

`importer2026`'s generic FK resolver (`foreignKey.parentNaturalKey`) matches a child row's FK
column against **literal columns on the parent table** (e.g. `container.name`,
`sample_profile.name`) — every existing manifest in this repo uses that shape. But
`sample.sample_profile_primary_sample` has no literal business-key column of its own; its only
identity is the composite `(sample_profile_id, sample_type_id, "order")` — itself made of two FK
columns. `parentNaturalKey` can match against those literal integer/FK columns directly, but only
if the CSV already carries the exact resolved integer values, which requires a lookup against
Postgres that can only happen *after* `sample_profile` and `sample_profile_primary_sample` are
loaded.

[`scripts/enrich_sample_profile_aliquots.py`](file:///Users/muilu/git/others/biobank-solution/sample-service-migration/scripts/enrich_sample_profile_aliquots.py)
bridges this one hop: after `sample_profile` + `sample_profile_primary_sample` are loaded, it
resolves `sample_profile.id` and `sample_type.id` by name via `psycopg2` (already a project
dependency) and writes them as literal `PRIMARY_PROFILE_ID` / `PRIMARY_SAMPLE_TYPE_ID` columns
into `export/sample_profile_aliquot_sample.csv`. The aliquot manifest's FK block then matches
those, plus the untouched `PRIMARY_RANK`, against `sample_profile_primary_sample`'s own
`(sample_profile_id, sample_type_id, "order")` — a 3-column composite `parentNaturalKey`, the same
mechanism `project_membership_manifest.yaml` already uses for its two simple FKs, just extended to
one more level.

This is a small **read-only** script, not a departure from Zero-Compile ETL: `importer2026` still
performs every actual write and FK/UPSERT resolution; nothing here writes to Postgres directly or
touches the shared `importer2026`/`exporter2026` tools.

Verified live: `(BIOBANK_SAMPLE_PROFILE_ID, SAMPLE_GROUPNR, RANK)` is unique across all 15
`PROFILE_PRIMARY_SAMPLE_TYPE` rows, and `(PROFILE_PRIMARY_SAMPLE_TYPE_ID, ALIQUOT_SAMPLE_GROUPNR,
RANK)` is unique across all 29 `PROFILE_ALIQUOT_SAMPLE` rows — so the composite keys used here are
real, not coincidental.

## 5. Implementation notes from actually running this

Verified end-to-end on 2026-09-25 (`make verify` afterward, full suite, still passes — see §5 of
[`LLM_MIGRATION_RUNBOOK.md`](file:///Users/muilu/git/others/biobank-solution/sample-service-migration/LLM_MIGRATION_RUNBOOK.md)
for the up-to-date list of `importer2026` capabilities/fixes referenced below):

- `sample_profile_primary_sample` / `sample_profile_aliquot_sample` use `operation: "INSERT"`,
  not `UPSERT`: neither table has a real unique constraint matching its natural key (unlike
  `sample_type_quality_metadata`'s `uq_sample_type_quality`), and Postgres's `ON CONFLICT` needs
  one. `naturalKeys` is still declared and still useful (FK caching / self-join row registration).
- Hit and fixed (user-approved) three small, generic gaps in `importer2026` along the way:
  no boolean-column support, no identifier quoting (broke on the reserved-word column `"order"`,
  in two separate places — `PostgreSqlDialect` and `ForeignKeyResolver`). None of this repo's
  prior manifests had exercised these paths.
- Own bug, not `importer2026`'s: the export script must format `TIMELOG` as whole-second
  `yyyy-MM-dd HH:mm:ss` (matching `exporter2026`'s convention) — `importer2026`'s date parser
  rejects Python's default microsecond-precision `datetime` string.

## 6. Running it

```bash
make extract-data   # DB2 -> export/sample_profile*.csv (incl. the *_raw aliquot CSV)
make clear-target   # dev-only: truncates sample_profile* along with everything else
make load-target    # loads sample_profile -> primary_sample -> [enrich] -> aliquot -> sample_column
make verify          # row counts: sample_profile=10, primary_sample=15, aliquot_sample=29, sample_column=4
```

Or `make migrate-all` for the full cycle (as with every other table in this repo).

## 7. See also

- [`sample-profile-columns.md`](file:///Users/muilu/git/others/biobank-solution/sample-service/docs/reference/sample-profile-columns.md) — target schema's type-safe column-default design (text vs. FK-reference)
- [`sample-attributes-migration-plan.md`](file:///Users/muilu/git/others/biobank-solution/sample-service-migration/docs/sample-attributes-migration-plan.md) — precedent for documenting dropped legacy columns instead of silently losing them
- [`LLM_MIGRATION_RUNBOOK.md`](file:///Users/muilu/git/others/biobank-solution/sample-service-migration/LLM_MIGRATION_RUNBOOK.md) — overall ETL architecture and per-table status
