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
./gradlew bootRun --args='--table=BIOBANK3.VIEW_SAMPLE_MASTER --output=sample.csv'
```

**Expected columns**: `SAMPLEID`, `SUBJECT`, `SAMPLETYPE`, `SAMPLE_STATUS`, `AMOUNT`, `CONCENTRATION`, `REMARKS`, `COMMENT`, `CONTAINER_NAME`, `PLACECODE`, `PARENT_SAMPLEID`, `USERNAME`, `TIMELOG`

**Critical note**: The exact column list depends on what `VIEW_SAMPLE_MASTER` exposes. If the view does not already flatten the foreign keys (e.g. `CONTAINER_ID` instead of `CONTAINER_NAME`, `SAMPLE_TYPE_ID` instead of `SAMPLETYPE` name), the export will fail or produce incorrect output. **Requires live DB2 connection to confirm.**

If the view doesn't flatten FKs correctly, a custom query may be needed. Use `--sql-output` to inspect the generated SQL and adjust accordingly.

## Loader Input

The loader app expects 4 CSV files in a configurable input directory:
- `samplegroup.csv` → loaded into `sample.sample_type`
- `containertype.csv` → loaded into `sample.container_type`
- `container.csv` → loaded into `sample.container`
- `sample.csv` → loaded into `sample.sample`

See the loader app's README for configuration and run instructions.
