# Sample Qualities Migration Plan

This document details the strategy and step-by-step execution playbook to migrate legacy DB2 sample qualities (controlled vocabulary and associations) to the new PostgreSQL `sample` schema.

---

## 1. Schema Mapping & Analysis

### Source DB2 Tables
1. **`BIOBANK3.CV_QUALITY`**: Controlled vocabulary containing quality codes (e.g. `CLOUDY`, `HEMOLYTIC`).
   - PK: `QUALITY` `VARCHAR(64)`
2. **`BIOBANK3.SAMPLE_QUALITY`**: Mapping table linking sample records to their quality classifications.
   - PK: `ID` `INTEGER`
   - FK: `SAMPLE_ID` `CHARACTER(13)` references sample subclass tables (`SAMPLE_10002` etc.)
   - FK: `QUALITY` `VARCHAR(64)` references `CV_QUALITY`

### Target PostgreSQL Tables
1. **`sample.cv_sample_quality`**: Harmonized CV schema for sample quality classifications.
   - PK: `term` `VARCHAR(64)`
2. **`sample.sample_type_quality_metadata`**: Metadata defining which qualities are allowed for which sample types.
   - PK: `id` `BIGINT` (auto-sequence)
   - Unique: `(sample_type_id, quality_term)`
3. **`sample.sample_quality`**: Mapping table linking a sample to its quality code(s).
   - PK: `id` `BIGINT` (auto-sequence)
   - FK: `sample_id` `BIGINT` (references `sample.sample`)
   - FK: `quality_term` `VARCHAR(64)` (references `cv_sample_quality.term`)
   - Unique: `(sample_id, quality_term)`
   - Trigger: `tr_validate_sample_quality` executes `tg_validate_sample_quality()` before insert/update to ensure the quality is allowed for the sample's type.

---

## 2. Table Mappings & Transformations

### A. Controlled Vocabulary: `BIOBANK3.CV_QUALITY` → `sample.cv_sample_quality`

| DB2 Column | DB2 Type | Postgres Column | PG Type | Transformation |
|------------|----------|-----------------|---------|----------------|
| `QUALITY` | VARCHAR(64) | `term` | VARCHAR(64) | Direct copy (PK) |
| `DESCRIPTION` | VARCHAR(255) | `name` | VARCHAR(128) | Direct copy (not null) |
| `DESCRIPTION` | VARCHAR(255) | `description` | TEXT | Direct copy (nullable) |
| `RANK` | INTEGER | `rank` | INTEGER | Direct copy |
| `USERNAME` | VARCHAR(128) | `userstamp` | VARCHAR(128) | Direct copy |
| `TIMELOG` | TIMESTAMP | `created` | TIMESTAMP | Direct copy |
| (new) | — | `version` | INTEGER | Hardcode `1` |

*Note: Since `cv_sample_quality` uses `term` as PK and lacks a surrogate `id` column, it cannot be loaded via `importer2026` directly. It must be seeded using a SQL script.*

### B. Metadata: `V_SAMPLE_TYPE_QUALITY_METADATA` → `sample.sample_type_quality_metadata`

To satisfy the target trigger constraint, allowed combinations are derived from actual combinations present in the DB2 source data.

| DB2 Column | DB2 Type | Postgres Column | PG Type | Lookup / Transformation |
|------------|----------|-----------------|---------|-------------------------|
| `SAMPLETYPE` | VARCHAR | `sample_type_id` | BIGINT | **LOOKUP**: `sample_type` name → `id` |
| `QUALITY` | VARCHAR | `quality_term` | VARCHAR(64) | Direct copy (references `cv_sample_quality.term`) |
| (hardcoded)| — | `userstamp` | VARCHAR(128) | Hardcode `'migration'` |
| (hardcoded)| — | `version` | INTEGER | Hardcode `1` |

### C. Sample Qualities: `BIOBANK3.SAMPLE_QUALITY` → `sample.sample_quality`

Since DB2 uses binary keys (`CHARACTER(13)`) to link `SAMPLE_QUALITY` to samples, we join it with the base sample table `SAMPLE_10002` during export to resolve the sample reference to the natural key `SAMPLEID` string.

| DB2 Column | DB2 Type | Postgres Column | PG Type | Lookup / Transformation |
|------------|----------|-----------------|---------|-------------------------|
| (surrogate PK)| INTEGER | (dropped) | — | Do not use; PG auto-generates surrogate `id` |
| `SAMPLE_10002_SAMPLEID` | VARCHAR | `sample_id` | BIGINT | **LOOKUP**: sample `sampleid` → `id` |
| `QUALITY` | VARCHAR | `quality_term` | VARCHAR(64) | Direct copy (no FK lookup needed in manifest) |
| `USERNAME` | VARCHAR(128) | `userstamp` | VARCHAR(128) | Direct copy |
| `TIMELOG` | TIMESTAMP | `created` | TIMESTAMP | Direct copy |

---

## 3. Step-by-Step Migration Playbook

### Step 1: Extract (via `exporter2026` & DDL View)

1. **Extract Controlled Vocabulary**:
   ```bash
   # Path: /Users/muilu/git/exporter2026
   ./gradlew bootRun --args='--table=BIOBANK3.CV_QUALITY --output=/Users/muilu/git/others/sample-service-migration/export/cv_sample_quality.csv --spring.datasource.url=jdbc:db2://localhost:50000/BCDEMO --spring.datasource.username=db2inst1 --spring.datasource.password=Adm1Pwd1'
   ```

2. **Extract Metadata View**:
   Create a temporary view in DB2 to capture existing sample type and quality associations:
   ```sql
   CREATE OR REPLACE VIEW BIOBANK3.V_SAMPLE_TYPE_QUALITY_METADATA AS
   SELECT DISTINCT g.NAME AS SAMPLETYPE, sq.QUALITY
   FROM BIOBANK3.SAMPLE_QUALITY sq
   JOIN BIOBANK3.SAMPLE_10002 s ON s.ID = sq.SAMPLE_ID
   JOIN BIOBANK3.SAMPLEGROUP g ON g.GROUPNR = s.GROUPNR;
   ```
   *(Executes via the MCP query tool or any DB2 client)*.

3. **Export Metadata CSV**:
   Add headers and static audit columns `USERNAME` and `VERSION` to form the CSV file at `export/sample_type_quality_metadata.csv`:
   ```csv
   SAMPLETYPE,QUALITY,USERNAME,VERSION
   DNA,BLOODY,migration,1
   DNA,CENTRIFUGED,migration,1
   DNA,CLOTTED,migration,1
   DNA,TRANSPORT_PROBLEM,migration,1
   EDTA Whole blood,BLOODY,migration,1
   EDTA Whole blood,CENTRIFUGED,migration,1
   EDTA Whole blood,CLOTTED,migration,1
   EDTA Whole blood,CLOUDY,migration,1
   EDTA Whole blood,CONTAMINATED,migration,1
   EDTA Whole blood,HEMOLYTIC,migration,1
   Plasma,CLOTTED,migration,1
   ```

4. **Extract Sample Qualities**:
   ```bash
   # Path: /Users/muilu/git/exporter2026
   ./gradlew bootRun --args='--table=BIOBANK3.SAMPLE_QUALITY --output=/Users/muilu/git/others/sample-service-migration/export/sample_quality.csv --spring.datasource.url=jdbc:db2://localhost:50000/BCDEMO --spring.datasource.username=db2inst1 --spring.datasource.password=Adm1Pwd1'
   ```

### Step 2: Generate Seed Script
Use the python generator to convert `export/cv_sample_quality.csv` into the SQL seeding script `scripts/postgres/seed_qualities.sql`.

### Step 3: Load (Target PostgreSQL Database)

1. **Seed Vocabulary**:
   Execute the generated SQL seed script directly against the Postgres database:
   ```bash
   docker exec -i sample-service-db-1 psql -U sample -d sample < /Users/muilu/git/others/sample-service-migration/scripts/postgres/seed_qualities.sql
   ```

2. **Load Allowed Quality Metadata**:
   Load using `importer2026` with the [sample_type_quality_metadata_manifest.yaml](file:///Users/muilu/git/others/sample-service-migration/config/manifests/sample_type_quality_metadata_manifest.yaml) manifest:
   ```bash
   # Path: /Users/muilu/git/others/sample-service-migration
   ../../importer2026/gradlew -p ../../importer2026 bootRun --args='--csv=/Users/muilu/git/others/sample-service-migration/export/sample_type_quality_metadata.csv --manifest=/Users/muilu/git/others/sample-service-migration/config/manifests/sample_type_quality_metadata_manifest.yaml --spring.datasource.url=jdbc:postgresql://localhost:5432/sample --spring.datasource.username=sample --spring.datasource.password=sample --spring.datasource.driver-class-name=org.postgresql.Driver --spring.main.web-application-type=none'
   ```

3. **Load Sample Quality Mappings**:
   Load using `importer2026` with the [sample_quality_manifest.yaml](file:///Users/muilu/git/others/sample-service-migration/config/manifests/sample_quality_manifest.yaml) manifest:
   ```bash
   # Path: /Users/muilu/git/others/sample-service-migration
   ../../importer2026/gradlew -p ../../importer2026 bootRun --args='--csv=/Users/muilu/git/others/sample-service-migration/export/sample_quality.csv --manifest=/Users/muilu/git/others/sample-service-migration/config/manifests/sample_quality_manifest.yaml --spring.datasource.url=jdbc:postgresql://localhost:5432/sample --spring.datasource.username=sample --spring.datasource.password=sample --spring.datasource.driver-class-name=org.postgresql.Driver --spring.main.web-application-type=none'
   ```

### Step 4: Reset Sequences
Reset sequence counters in Postgres:
```sql
SELECT setval('sample.sample_type_quality_metadata_id_seq', COALESCE((SELECT MAX(id) FROM sample.sample_type_quality_metadata), 1));
SELECT setval('sample.sample_quality_id_seq', COALESCE((SELECT MAX(id) FROM sample.sample_quality), 1));
```

---

## 4. Verification & QA

Run the following validation queries on Postgres to verify correct data load:

1. **Verify Quality Counts**:
   ```sql
   SELECT quality_term, COUNT(*) AS associations_count
   FROM sample.sample_quality
   GROUP BY quality_term
   ORDER BY associations_count DESC;
   ```
   *Expected Outcome*: Total counts must sum up to `493`.

2. **Verify Trigger Constraint Protection**:
   Check if inserting a disallowed quality for a sample type is correctly blocked:
   ```sql
   -- DNA sample type does not allow 'HEMOLYTIC'
   INSERT INTO sample.sample_quality (sample_id, quality_term) 
   VALUES ((SELECT id FROM sample.sample WHERE sample_type_id = (SELECT id FROM sample.sample_type WHERE name = 'DNA') LIMIT 1), 'HEMOLYTIC');
   ```
   *Expected Outcome*: Blocked with error: `Laatukoodi HEMOLYTIC ei ole sallittu näytetyypille...`
