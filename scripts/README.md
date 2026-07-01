# Migration Scripts

Organized by phase and target database.

## Directory structure

- **`db2/`** — Extract data from DB2 (SQL queries, unload scripts, ODBC dumps)
- **`postgres/`** — Load data into PostgreSQL (SQL scripts, CSV loaders, constraints)
- **`transformation/`** — Convert DB2 data to Postgres format (Python/SQL/bash scripts)
- **`validation/`** — Compare source ↔ target, verify integrity (SQL queries, Python validation)

## Naming convention

- Extract scripts: `extract_<tablename>.sql` or `extract_<tablename>.py`
- Load scripts: `load_<tablename>.sql` or `load_<tablename>.py`
- Validation: `validate_<aspect>.sql` (e.g., `validate_foreign_keys.sql`, `validate_row_counts.sql`)
- Transformation: `transform_<stage>.py` (e.g., `transform_dates.py`, `transform_enums.py`)

## Execution order

1. **Extract** (scripts/db2/) — export all tables from DB2
2. **Transform** (scripts/transformation/) — prepare data for Postgres
3. **Load** (scripts/postgres/) — insert into target Postgres database
4. **Validate** (scripts/validation/) — verify integrity post-load

See `docs/migration-strategy.md` for the full timeline.
