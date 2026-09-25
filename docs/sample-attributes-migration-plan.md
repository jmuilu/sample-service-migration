# Migration Plan & Playbook: Sample Native Provenance Columns & DNA Extension Attributes

`sample-service`'s data model changed twice on 2026-09-23:

- [ADR 0015](file:///Users/muilu/git/others/biobank-solution/sample-service/docs/adr/0015-sample-native-provenance-columns.md)
  added native source-provenance/HL7-ingestion columns directly to `sample.sample`
  (`organ`, `source`, `sourceid`, `altid`, `lab_code`, `source_file`, `messageid`,
  `volume_ext`) and renamed `remarks` to `error_remarks`.
- [ADR 0017](file:///Users/muilu/git/others/biobank-solution/sample-service/docs/adr/0017-remove-eav-sample-property-model.md)
  deleted the EAV `sample.sample_property` model outright and registered DNA's
  sample-type-specific extension attributes (`ABS260`, `ABS280`, `ABS230`, `ABS260280`,
  `ABS260230`, `EXTRACTION_METHOD`, `FACTOR`) in [ADR 0014](file:///Users/muilu/git/others/biobank-solution/sample-service/docs/adr/0014-jsonb-extension-attributes.md)'s
  JSONB `sample.sample.attributes` model instead.

This document replaces `docs/sample-properties-migration-plan.md` (deleted; per ADR 0014's
"attribute, never property" naming convention). It supersedes the migration this repo
previously ran into `sample.sample_property` — that table no longer exists.

---

## 1. What changed and why the migration had to change with it

`sample_property` was deleted, not superseded-and-kept, so `config/manifests/sample_property_manifest.yaml`,
`sample_property_metadata_manifest.yaml`, `cv_property_type_manifest.yaml`,
`config/scripts/property_transform.js` and `scripts/postgres/seed_properties.sql` all now
target tables that don't exist and have been removed from this repo. `scripts/PivotHelper.java`
(the generic DB2-subclass-table unpivoter) is kept — it's a generic zero-compile script, not
tied to the EAV shape at the code level — but DNA no longer needs it: the DNA export
(`export/sample_10003.csv`, one row per sample already) is consumed directly by a JS transform
that builds one JSON object per row, not a `SAMPLEID, PROPERTY_TERM, VALUE` unpivot.

### `importer2026` gained JSON/JSONB column support

`sample.sample.attributes` is a `jsonb` column. `importer2026` had no support for it — every
value was bound as a plain string/number, which Postgres rejects for `jsonb`
("column is of type jsonb but expression is of type character varying"). Fixed generically
(not DNA-specific), with the user's explicit sign-off per this project's rule on changes to
the shared `importer2026`/`exporter2026` tools:

- `SqlDialect.wrapJson(String)` (default: pass-through) lets each dialect provide its own
  JDBC binding for a JSON value; `PostgreSqlDialect` wraps it in `org.postgresql.util.PGobject`
  (type `jsonb`). `build.gradle`'s postgres driver dependency moved from `runtimeOnly` to
  `implementation` since `PGobject` is now referenced at compile time.
- `BatchLoader` calls `dialect.wrapJson(...)` for any column whose type (explicit in the
  manifest, or auto-discovered from Postgres metadata) contains `JSON`.
- A real, previously-latent bug was also found and fixed while adding the first manifest to
  actually use `operation: UPDATE`: `SqlDialect#generateUpdate`'s SQL binds non-key (`SET`)
  columns first and natural-key (`WHERE`) columns last, but `BatchLoader` built its args array
  in manifest-declaration order — for any manifest whose natural key isn't listed last in
  `columnMappings`, values landed in the wrong placeholders. No existing "COMPLETE" migration
  had ever used `UPDATE` (all used `UPSERT`, whose column order matches manifest order), so this
  had never been exercised or caught before. `BatchLoader.reorderForUpdate(...)` fixes it.

---

## 2. Native provenance columns — DB2 source investigation

Investigated directly against the live DB2 test instance (`BCDEMO`), not assumed:

| New `sample.sample` column | DB2 source | Notes |
|---|---|---|
| `source` | `SAMPLE_10002.SOURCE` | Direct copy. Already present in `export/sample.csv` (no re-export needed). |
| `sourceid` | `SAMPLE_10002.SOURCEID` | Direct copy. |
| `altid` | `SAMPLE_10002.ALIASID` | Direct copy — DB2's "alias id" is this field's legacy name. |
| `source_file` | `SAMPLE_10002.SOURCE_FILE` | Direct copy. |
| `error_remarks` | `SAMPLE_10002.ERROR_REMARKS` | DB2 already carries `REMARKS` and `ERROR_REMARKS` as two separate columns — the legacy schema already anticipated this split. Old `REMARKS -> remarks` mapping removed (target column renamed away); `REMARKS` is now mapped to the pre-existing, previously-unmapped `comment` column instead (general free text), since DB2's split cleanly matches Postgres's `comment`/`error_remarks` split. Verified no truncation risk: DB2 `REMARKS` max length in this dataset is 88 chars against Postgres `comment varchar(255)`. |
| `volume_ext` | `SAMPLE_10003.ELUTION_VOLUME` (DNA subclass table only) | See §3 — handled by the DNA-specific manifest, not the main sample manifest, since `exporter2026` only joins one level of *FK* relationships and `SAMPLE_10002`/`SAMPLE_10003` share a primary key rather than an FK. |
| `organ` | **none found** | Searched all DB2 schemas for organ/tissue/bodysite/specimen-site columns — none exist. Left unmapped (column is nullable; ADR 0015 already anticipates it applies "only to a sample created ... through an HL7 feed", which this legacy system evidently didn't carry). |
| `lab_code` | **no reliable per-sample source** | `HL7.VIEW_AVAILABLE_LAB_CODE_KIND_SAMPLE` exists and joins to `SAMPLEID`, but it's a many-to-many catalog of lab codes *available* for a sample's kind (2449 rows / 369 distinct `SAMPLEID` in this dataset — e.g. one sample maps to 7 different lab codes), not the single code a specific sample was actually ordered under. Picking one arbitrarily would be a fabricated value, not a migrated one. Left unmapped. |
| `messageid` | **no reliable per-sample source** | `HL7.VIEW_BARE_SAMPLE_ORDER_MESSAGE` exists (has `MESSAGE_CONTROLID`) but keys off `FILLER_ORDER_NUMBER` with `SOURCEID` empty in every sampled row, and the whole HL7 schema's test data is sparse (33 total rows, 1 distinct non-null `SOURCEID`) — not usable as a real per-sample crosswalk in this environment. Left unmapped. |

**Consequence**: `organ`, `lab_code`, `messageid` will be `NULL` for every migrated sample. This
matches ADR 0015's own framing (these columns describe HL7-ingestion provenance a legacy
non-HL7 system wouldn't have populated), but if a *production* DB2 instance's HL7 schema turns
out to carry cleaner per-sample data than this test instance, revisit before assuming these
three columns are permanently unmappable.

Implemented as additions to the existing `config/manifests/sample_manifest.yaml` (still
`UPSERT`, still idempotent) rather than a separate manifest, since the source data was already
present in `export/sample.csv` and the target rows already exist.

---

## 3. DNA extension attributes — DB2 source investigation

`BIOBANK3.SAMPLE_10003` (DNA, group `10003`) columns, and their fate in the new model:

| DB2 column | Type | Real data in this instance? | New home |
|---|---|---|---|
| `ABS260`, `ABS280`, `ABS230`, `ABS260280`, `ABS260230` | REAL | No (0/179 rows) | `attributes.ABS260` etc. (FLOAT), direct copy |
| `EXTRACTIONMETHOD` | VARCHAR | No (0/179) | `attributes.EXTRACTION_METHOD` (MULTICHOICE) — see caveat below |
| `DILUTION_FACTOR` | REAL | No (0/179) | `attributes.FACTOR` (FLOAT) — see decision below |
| `ELUTION_VOLUME` | INT | No (0/179) | native `sample.sample.volume_ext` column (ADR 0015), not an attribute |
| `FACTOR` | INT | No (0/179) | **dropped** — see decision below |
| `QUANTITY` | REAL | No (0/179) | **dropped** — no home in ADR 0017's registered attribute set |
| `EXTRACTIONSITE` | VARCHAR | No (0/179) | **dropped** — domain owner confirmed not needed (ADR 0017) |
| `PROFILE`, `PARENT`, `BATCH`, `USERNAME`, `TIMELOG` | — | — | unused, as before |

**`attributes.FACTOR` decision (user-confirmed, since neither candidate column has any real
data to verify against empirically)**: sourced from DB2's `DILUTION_FACTOR`, not DB2's own
`FACTOR` column. The old EAV seed data (`scripts/postgres/seed_properties.sql`, now deleted)
kept these as two distinct terms with different historical descriptions — `DILUTION_FACTOR`:
"Dilution factor" (FLOAT), `FACTOR`: "Correction factor" (INTEGER) — genuinely different
legacy concepts, not duplicates. ADR 0017 describes the new `attributes.FACTOR` term as
"Dilution/concentration factor", which matches `DILUTION_FACTOR`'s old meaning, not `FACTOR`'s.
DB2's plain `FACTOR` ("correction factor") has no home in the new registry and is dropped, same
as `QUANTITY`. **Flag to the domain owner if real `DILUTION_FACTOR`/`FACTOR` data ever
surfaces that contradicts this.**

**`EXTRACTION_METHOD` caveat**: DB2's `EXTRACTIONMETHOD` is free text with zero real sample
data in this instance to build a crosswalk from. The transform best-effort normalizes it to
upper-snake-case so it at least resembles a `cv_attribute_choice.choice_value`, but does **not**
validate it against the real choice list (`SILICA_COLUMN`, `MAGNETIC_BEADS`, `SALTING_OUT`,
`PHENOL_CHLOROFORM`, `CFDNA_SILICA_COLUMN`, `CFDNA_MAGNETIC_BEADS`, `CFDNA_EXTRACTION`,
`CELL_ISOLATION_GENOMIC_EXTRACTION`) — there's no DB CHECK constraint to catch a mismatch
either (ADR 0014: choice validation is app-layer work, not built yet). Revisit once real
`EXTRACTIONMETHOD` values are available from a populated environment.

### Known gap: EDTA Whole Blood and TestNäyte have no new home

ADR 0017 only registered DNA's seven terms in `cv_attribute_type` (`entity_type = 'SAMPLE'`).
EDTA Whole Blood's `LIQUID_LEVEL`/`PLASMA_LEVEL`/`SEPARATION_LEVEL` (previously real migrated
EAV data — 24 rows across 8 samples, see this repo's memory) and TestNäyte's `LVMS` have **no
registered `cv_attribute_type` entry at all** in the new model. Since `sample_property` is
deleted outright (not kept alongside `attributes`), this data currently has nowhere to land.
This is **not resolved here** — registering new attribute terms for sample types ADR 0017 didn't
cover would need its own domain-owner-reviewed ADR, the same way DNA's term list was. Flagging
for the domain owner rather than inventing unauthorized `cv_attribute_type` rows.

### Pipeline

```
BIOBANK3.SAMPLE_10003 (DNA subclass, exporter2026 auto-joins to SAMPLE_10002 for
SAMPLE_10002_SAMPLEID since SAMPLE_10003.ID -> SAMPLE_10002.ID is a real FK)
        |
        v
export/sample_10003.csv  (already exported — one row per DNA sample)
        |
        v
config/scripts/dna_attributes_transform.js (buildDnaAttributes: builds one JSON object
per row from ABS260/280/230/260280/260230, DILUTION_FACTOR, normalized EXTRACTIONMETHOD)
        |
        v
config/manifests/dna_attributes_manifest.yaml (importer2026, operation: UPDATE,
naturalKeys: [sampleid]) -> UPDATE sample.sample SET volume_ext = ELUTION_VOLUME,
attributes = <built JSON> WHERE sampleid = SAMPLE_10002_SAMPLEID
```

`UPDATE`, not `UPSERT`: this manifest only ever extends `sample.sample` rows the (already
`COMPLETE`) `sample` migration created — it must never insert a row itself.

```bash
../../importer2026/gradlew -p ../../importer2026 bootRun --args='--csv=/Users/muilu/git/others/biobank-solution/sample-service-migration/export/sample_10003.csv --manifest=/Users/muilu/git/others/biobank-solution/sample-service-migration/config/manifests/dna_attributes_manifest.yaml --spring.datasource.url=jdbc:postgresql://localhost:5432/sample --spring.datasource.username=dbadmin --spring.datasource.password=dbadmin --spring.datasource.driver-class-name=org.postgresql.Driver --spring.main.web-application-type=none'
```

Since every DNA extension column is currently `NULL` for all 179 rows in this DB2 instance,
running this today is an idempotent no-op (`volume_ext` stays `NULL`, `attributes` stays `{}`,
both already the column defaults) — it exercises the pipeline correctly without changing any
data. It becomes meaningful the moment a populated environment has real values.

---

## 4. Validation

```sql
-- attributes must always be a JSON object, never null/array/scalar (DB CHECK already enforces
-- this, but confirm no manifest bug produced something the CHECK somehow let through)
SELECT sampleid, attributes FROM sample.sample
WHERE sample_type_id = (SELECT id FROM sample.sample_type WHERE abbreviation = 'DNA')
  AND attributes != '{}'::jsonb;

-- volume_ext should only be populated for DNA samples in this dataset
SELECT st.abbreviation, count(*) FILTER (WHERE s.volume_ext IS NOT NULL) AS with_volume_ext
FROM sample.sample s JOIN sample.sample_type st ON st.id = s.sample_type_id
GROUP BY st.abbreviation;

-- new provenance columns: spot-check coverage
SELECT count(*) FILTER (WHERE source IS NOT NULL) AS with_source,
       count(*) FILTER (WHERE sourceid IS NOT NULL) AS with_sourceid,
       count(*) FILTER (WHERE altid IS NOT NULL) AS with_altid,
       count(*) FILTER (WHERE source_file IS NOT NULL) AS with_source_file,
       count(*) FILTER (WHERE error_remarks IS NOT NULL) AS with_error_remarks,
       count(*) FILTER (WHERE comment IS NOT NULL) AS with_comment
FROM sample.sample;
```
