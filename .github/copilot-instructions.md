# Copilot Instructions - Sample Service Migration

DB2 to PostgreSQL migration project using a Zero-Compile ETL architecture (exporter2026 → CSV → importer2026).

## Quick Reference

- **Runbook**: [LLM_MIGRATION_RUNBOOK.md](../LLM_MIGRATION_RUNBOOK.md) - Complete migration playbook
- **Schema Mapping**: [docs/schema-mapping.md](../docs/schema-mapping.md) - DB2 ↔ PostgreSQL mappings
- **Sibling Projects**: `../../exporter2026/`, `../../importer2026/`

## Migration Architecture

Zero-Compile ETL - no custom Java loaders, only YAML manifests + JS transforms:

```
DB2 → [exporter2026] → CSV → [JS transforms] → [importer2026 + YAML manifests] → PostgreSQL
```

Config location:
- **Manifests**: `config/manifests/*.yaml` - column mappings, FK resolution
- **Transforms**: `config/scripts/*.js` - stateless data transformations

## Build & Run Commands

### Python Setup
```bash
uv venv && source .venv/bin/activate && uv pip install -e .
```

### Makefile Targets
```bash
make help          # View all targets
make extract-data  # Export from DB2
make load-target   # Import to PostgreSQL
make verify        # Validate migration
```

### Importer2026 Execution

**Critical**: Use absolute paths (Gradle changes working directory)

```bash
../../importer2026/gradlew -p ../../importer2026 bootRun --args='\
  --csv=/Users/muilu/git/others/sample-service-migration/export/sample.csv \
  --manifest=/Users/muilu/git/others/sample-service-migration/config/manifests/sample_manifest.yaml \
  --spring.datasource.url=jdbc:postgresql://localhost:5432/sample \
  --spring.datasource.username=sample \
  --spring.datasource.password=sample \
  --spring.datasource.driver-class-name=org.postgresql.Driver \
  --spring.main.web-application-type=none \
  --sort-self-joins'
```

Required flags:
- `--spring.datasource.driver-class-name=org.postgresql.Driver` (PostgreSQL override)
- `--sort-self-joins` (for self-referential tables: `sample`, `container`)

## Architecture Overview

### Database Connections
- **Source**: DB2 at `localhost:50000/BCDEMO` (user: `db2inst1`)
- **Target**: PostgreSQL at `localhost:5432/sample` (schema: `sample`)

### Project Paths
```
/Users/muilu/git/
├── exporter2026/          # Generic extraction tool
├── importer2026/          # Generic loading tool
└── others/sample-service-migration/
    ├── config/manifests/  # YAML mappings
    ├── config/scripts/    # JS transforms
    └── export/            # CSV files
```

### Migration Scope (M1+M2)

4 core tables - manifests configured, CSV files exported:
1. `sample_type`: SAMPLEGROUP → sample.sample_type
2. `container_type`: CONTAINERTYPE → sample.container_type  
3. `container`: CONTAINER → sample.container (self-referential)
4. `sample`: VIEW_SAMPLE_MASTER → sample.sample (self-referential)

## Key Conventions

### YAML Manifest Pattern
See existing manifests in `config/manifests/` for complete examples. Key structure:

```yaml
import:
  targetTable: "sample.table_name"
  operation: "UPSERT"
  naturalKeys: ["business_key"]
  columnMappings:
    - csv: "SOURCE_COL"
      column: "target_col"
      foreignKey:                    # FK resolution
        parentTable: "sample.parent"
        parentNaturalKey:
          - csv: "SOURCE_COL"
            column: "parent_key"
    - csv: "ENUM_COL"
      column: "target_col"
      transformScript: "config/scripts/transform.js"
      transformFunction: "transformEnum"
```

### JavaScript Transforms
Nashorn engine (JVM 21). Example in `config/scripts/`:

```javascript
function transformEnum(value) {
    var map = {'A': 'ACTIVE', 'I': 'INACTIVE'};
    return map[value] || value;
}
```

### Self-Referential Tables
For parent-child relationships (`sample`, `container`):
- Use `--sort-self-joins` flag
- Importer sorts rows topologically (parents before children)
- IDs cached dynamically during insert

### Post-Load Sequence Reset
Always run after migration:
```sql
SELECT setval('sample.table_name_id_seq', 
              COALESCE((SELECT MAX(id) FROM sample.table_name), 1));
```

## Important Rules

1. **No custom Java loaders** - use YAML manifests + JS transforms only
2. **Absolute paths required** - Gradle changes working directory
3. **Notify before shared tool changes** - `importer2026`/`exporter2026` are shared across projects
4. **PostgreSQL driver override** - always add `--spring.datasource.driver-class-name=org.postgresql.Driver`
