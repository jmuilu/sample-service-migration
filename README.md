# sample-service-migration

Tools and scripts for migrating biobank sample database from DB2 to PostgreSQL.

## Overview

This project contains:
- **Schema mapping documentation** — how DB2 tables/columns map to PostgreSQL
- **Data extraction scripts** — export data from DB2
- **Transformation scripts** — convert and validate data for PostgreSQL
- **Validation tools** — compare source and target data, check integrity
- **Migration playbook** — step-by-step runbook for the actual migration

## Project structure

```
.
├── docs/                          # Documentation
│   ├── schema-mapping.md          # DB2 ↔ Postgres schema translation
│   ├── migration-strategy.md      # Overall approach, timeline, rollback
│   └── data-requirements.md       # Data types, transformations, validation
├── scripts/
│   ├── db2/                       # DB2 extraction (SQL, etc.)
│   ├── postgres/                  # Postgres load scripts (SQL, etc.)
│   └── validation/                # Data comparison & integrity checks
├── tools/                         # Utility scripts (Python/bash/Java)
└── tests/                         # Validation tests
```

## Development

```bash
make help          # Show all targets
make plan          # Review migration strategy
```

See `Makefile` for common tasks.

## Quick start (when migration begins)

```bash
make validate-source     # Check DB2 source data
make extract-data        # Export from DB2
make transform-data      # Prepare for Postgres
make load-target         # Load into Postgres
make verify              # Compare source ↔ target
```

See `docs/migration-strategy.md` for the full playbook.
