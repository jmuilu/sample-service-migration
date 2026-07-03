# Sample Type Migration Plan: DB2 ↔ PostgreSQL

> [!IMPORTANT]
> This document contains legacy design references to a custom Java 'loader' application. The project has migrated to a generic, script-based ETL model using `exporter2026`, `importer2026`, and JS/SpEL manifests. Refer to [LLM_MIGRATION_RUNBOOK.md](file:///Users/muilu/git/others/sample-service-migration/LLM_MIGRATION_RUNBOOK.md) for the active design and execution playbook.

This plan outlines the steps, mappings, rules, and validations required to migrate **Sample Types** from the legacy DB2 database (table `BIOBANK3.SAMPLEGROUP`) to the target PostgreSQL `sample-service` database (table `sample.sample_type`).

---

## 1. Schema Analysis

### Source Database (DB2: `BIOBANK3.SAMPLEGROUP`)
The source table represents classifications of biological samples. 

| Column Name | Data Type | Nullable | Description / Usage |
| :--- | :--- | :--- | :--- |
| `GROUPNR` | `BIGINT` | No | Legacy surrogate primary key (IDs range from `10002` to `10030`) |
| `NAME` | `VARCHAR(128)` | No | Full descriptive name of the sample type (e.g., `'DNA'`, `'Serum'`) |
| `ABBREVIATION`| `VARCHAR(5)` | No | Character abbreviation (mostly legacy numeric strings or `'MS'`) |
| `DESCRIPTION` | `VARCHAR(1000)`| Yes | Optional longer description / detail |
| `USERNAME` | `VARCHAR(128)` | No | User stamp of who last modified the row |
| `TIMELOG` | `TIMESTAMP` | No | Timestamp of the last update / creation |
| `STATUS` | `INTEGER` | No | Operational status (1 = Active, 2 = Inactive/Locked) |
| `FORMXML` | `CLOB` | Yes | Legacy XML metadata template (Not used in the new schema, will be dropped) |
| `FOLDERNAME` | `VARCHAR(50)` | Yes | Legacy grouping folder (Not used, will be dropped) |
| `OWNER` | `VARCHAR(128)` | Yes | Owner namespace (Not used, will be dropped) |

### Target Database (PostgreSQL: `sample.sample_type`)
The target table contains the simplified schema for sample types.

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `BIGINT` | `PRIMARY KEY` (seq auto-generated) | New surrogate ID generated via `sample.sample_type_id_seq` |
| `name` | `VARCHAR(128)` | `NOT NULL`, `UNIQUE` | Distinct sample type name |
| `abbreviation`| `VARCHAR(20)` | `NOT NULL`, `UNIQUE` | Normalized, readable short code |
| `description` | `TEXT` | `NULL` | Detailed description |
| `userstamp` | `VARCHAR(128)` | `NOT NULL` | Username of modification/migration |
| `created` | `TIMESTAMP` | `NOT NULL` | Creation timestamp |
| `version` | `INTEGER` | `NOT NULL`, `DEFAULT 1` | Optimistic locking version |

---

## 2. Source Data Analysis & Observations

A live inspection of the source `BIOBANK3.SAMPLEGROUP` table shows 29 rows. We observed two important details:

1. **Abbreviation Redundancy**: 
   Almost all abbreviations (except for `'Master Sample'` which uses `'MS'`) are stored as their `GROUPNR` string representation (e.g., `'10003'`, `'10004'`). These numeric codes do not act as helpful abbreviations for application users.
2. **In-Use Sample Types**:
   A query on the sample table (`BIOBANK3.VIEW_SAMPLE_MASTER`) shows that **only 9 of the 29 defined sample types are actually referenced by active samples**.
   The in-use sample types are:
   - `DNA`
   - `EDTA Whole blood`
   - `Plasma`
   - `Serum`
   - `EDTA cord blood`
   - `Tissue`
   - `Maternal Whole Blood`
   - `TestNäyte`
   - `EDTA Plasma`

---

## 3. Key Migration Rules & Transformations

### A. Abbreviation Normalization
To prevent legacy numeric strings (like `'10003'`) from polluting the new database, we should normalize the abbreviations. Since `abbreviation` has a `UNIQUE` constraint, each mapped abbreviation must be distinct.

We propose two strategies for the migration:
* **Option 1 (Direct Copy)**: Keep the abbreviations exactly as they are in DB2. (Simplest, but preserves ugly `'10003'` abbreviations).
* **Option 2 (Recommended - Remapping Table)**: Remap abbreviations to clean, standard values. If no mapping exists, normalize the `NAME` or use `DESCRIPTION` if short.

#### Recommended Abbreviation Remapping Table
For the 9 active sample types, the recommended mapping is:

| DB2 Name | Old Abbreviation | Recommended New Abbreviation | Source / Justification |
| :--- | :--- | :--- | :--- |
| `Master Sample` | `MS` | `MS` | Direct copy |
| `DNA` | `10003` | `DNA` | Description |
| `EDTA Whole blood`| `10004` | `EWB` | Description / EDTA Whole Blood |
| `Plasma` | `10008` | `PL` | Standard short code |
| `Serum` | `10010` | `SR` | Standard short code |
| `EDTA cord blood` | `10012` | `ECB` | EDTA Cord Blood |
| `Tissue` | `10014` | `TS` | Standard short code |
| `Maternal Whole Blood` | `10027` | `MWB` | Maternal Whole Blood |
| `TestNäyte` | `10029` | `TN` | Test Näyte |
| `EDTA Plasma` | `10030` | `EDTAPL` | EDTA Plasma |

For other inactive sample types, a fallback algorithm will convert the name to a clean, uppercase slug (e.g., `'Buccal swab'` → `'BS'`, `'Urine'` → `'URINE'`), checking for uniqueness.

### B. ID Generation
* **Rule**: Drop DB2 `GROUPNR`. Let Postgres automatically assign sequence-based IDs using `sample.sample_type_id_seq`.
* **Reason**: Prevents future sequence gap problems and follows the target schema design where `sample-service` manages sequence primary keys.

### C. Audit Columns
* `userstamp`: Directly map from DB2 `USERNAME` column.
* `created`: Directly map from DB2 `TIMELOG` timestamp.
* `version`: Set to `1` for all rows.

---

## 4. Implementation Steps

### Step 4.1: Export Data from DB2
Generate `samplegroup.csv` containing the raw DB2 columns.
```bash
cd /Users/muilu/git/exporter2026
./gradlew bootRun --args='--table=BIOBANK3.SAMPLEGROUP --output=samplegroup.csv'
```
Copy `samplegroup.csv` to the loader's configured input directory.

### Step 4.2: Implement `SampleTypeLoader` in the Loader App
Create a new class `com.bcplatforms.samplemigration.load.SampleTypeLoader` under `loader/src/main/java/com/bcplatforms/samplemigration/load/` to process the CSV rows:
1. Parse `samplegroup.csv` using the existing `CsvStreamReader`.
2. Apply abbreviation normalization mappings.
3. Construct and run SQL `INSERT` statements using `JdbcTemplate`. Use a transactional batch save for efficiency.
4. Update the DB sequence status afterwards:
   ```sql
   SELECT setval('sample.sample_type_id_seq', COALESCE((SELECT MAX(id) FROM sample.sample_type), 1));
   ```

### Step 4.3: Verify & Hook into `LoaderApplication`
In `LoaderApplication.java`, wire the `SampleTypeLoader` to run on startup or via a task trigger. Make sure it runs first in the loader chain (before `ContainerTypeLoader`, `ContainerLoader`, and `SampleLoader`), as all samples have a dependency on `sample_type_id`.

---

## 5. Validation Plan

### SQL 5.1: Row Count Check
Verify that all 29 records from the source database are loaded.
```sql
-- Postgres
SELECT COUNT(*) FROM sample.sample_type;
-- Expected: 29
```

### SQL 5.2: Constraint Verification
Verify there are no null values or duplicate constraints violated:
```sql
-- Check for NULL name or abbreviation
SELECT * FROM sample.sample_type WHERE name IS NULL OR abbreviation IS NULL;

-- Check for duplicate names
SELECT name, COUNT(*) FROM sample.sample_type GROUP BY name HAVING COUNT(*) > 1;

-- Check for duplicate abbreviations
SELECT abbreviation, COUNT(*) FROM sample.sample_type GROUP BY abbreviation HAVING COUNT(*) > 1;
```

### SQL 5.3: Referential Verification
Ensure that all sample types used in the samples table can be resolved correctly:
```sql
-- After samples are loaded, run this to check for orphaned/unresolved sample types
SELECT DISTINCT s.sampletype 
FROM sample.sample s 
WHERE s.sample_type_id IS NULL;
-- Expected: 0 rows returned
```
