# Data Extraction (exporter2026 CLI invocations)

This document lists the CLI commands to extract data from DB2 using the `exporter2026` tool.

## Prerequisites

- `exporter2026` cloned and built at `/Users/muilu/git/exporter2026`
- DB2 connection available (hostname, port, database, credentials)
- DB2 credentials in `~/.server/centox-dbowner.conf` (or override via CLI)

## Extraction Commands

Run these in order (dependency order for FK lookups to work correctly):

### 1. Sample Type

```bash
cd /Users/muilu/git/exporter2026
./gradlew bootRun --args='--table=BIOBANK3.SAMPLEGROUP --output=samplegroup.csv'
```

**Expected columns**: `NAME`, `ABBREVIATION`, `DESCRIPTION`, `USERNAME`, `TIMELOG`
(GROUPNR surrogate PK will be excluded by exporter2026)

### 2. Container Type

```bash
./gradlew bootRun --args='--table=BIOBANK3.CONTAINERTYPE --output=containertype.csv'
```

**Expected columns**: `NAME`, `BASETYPE`, `X`, `Y`, `DESCRIPTION`, `USERNAME`, `TIMELOG`

### 3. Container

```bash
./gradlew bootRun --args='--table=BIOBANK3.CONTAINER --output=container.csv'
```

**Expected columns**: `NAME`, `DESCRIPTION`, `TYPE`, `PARENT`, `PARENT_NAME` (if exporter2026 handles self-ref join), `PLACECODE`, `USERNAME`, `TIMELOG`

**Note**: If `PARENT` (self-FK) is not flattened to `PARENT_NAME` by exporter2026, a custom `--sql-output` may be needed:

```bash
./gradlew bootRun --args='--table=BIOBANK3.CONTAINER --sql-output=container-query.sql'
```

Then inspect `container-query.sql` and adjust if needed.

### 4. Sample

```bash
./gradlew bootRun --args='--table=BIOBANK3.VIEW_SAMPLE_MASTER --output=/Users/muilu/git/others/sample-service-migration/export/sample.csv --spring.datasource.url=jdbc:db2://localhost:50000/BCDEMO --spring.datasource.username=db2inst1 --spring.datasource.password=Adm1Pwd1'
```

**Expected columns**: `SAMPLEID`, `SUBJECT`, `SAMPLETYPE`, `SAMPLE_STATUS`, `AMOUNT`, `CONCENTRATION`, `REMARKS`, `COMMENT`, `CONTAINER_NAME`, `PLACECODE`, `PARENT_SAMPLEID`, `USERNAME`, `TIMELOG`

**Note (Verified)**: The exact column list of `VIEW_SAMPLE_MASTER` has been confirmed via live DB2 database inspection. It successfully exposes `CONTAINER_NAME`, `SAMPLETYPE`, and `PARENT_SAMPLEID` as flattened natural key strings, matching the loader's requirements perfectly. No custom queries are needed for extraction.


## Loader Input

The loader app expects 4 CSV files in a configurable input directory:
- `samplegroup.csv` → loaded into `sample.sample_type`
- `containertype.csv` → loaded into `sample.container_type`
- `container.csv` → loaded into `sample.container`
- `sample.csv` → loaded into `sample.sample`

See the loader app's README for configuration and run instructions.
