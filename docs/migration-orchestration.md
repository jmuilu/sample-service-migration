# Migration Orchestration: Table-by-Table & Idempotency Playbook

> [!IMPORTANT]
> This document contains legacy design references to a custom Java 'loader' application. The project has migrated to a generic, script-based ETL model using `exporter2026`, `importer2026`, and JS/SpEL manifests. Refer to [LLM_MIGRATION_RUNBOOK.md](file:///Users/muilu/git/others/sample-service-migration/LLM_MIGRATION_RUNBOOK.md) for the active design and execution playbook.

This document describes how to orchestrate the migration process to enable table-by-table execution, rollback control, and incremental/resume capabilities in case of failures.

---

## 1. Core Architecture for Orchestration

To run a safe, repeatable, and table-by-table migration, the custom `loader` application must implement three principles:
1. **Idempotency (UPSERT)**: Any insert must be safe to rerun without causing duplicate key errors or duplicating data.
2. **Selective Execution Flags**: Command-line flags to target specific tables.
3. **Multi-Pass Hierarchical Transactions**: Commit self-referential levels in separate transactions to ensure progress is saved.

---

## 2. Table-by-Table Selective Execution

The `loader` application should accept a `--tables` command-line argument. This allows operators to isolate runs and debug specific tables:

```bash
# Example executions:
# Run only metadata tables
./gradlew bootRun --args='--tables=sample_type,container_type'

# Run only container structure (after verifying metadata matches)
./gradlew bootRun --args='--tables=container'

# Run only sample loading
./gradlew bootRun --args='--tables=sample'
```

### Implementation Pattern in Java (`LoaderApplication.java`):
Using Spring Boot's `CommandLineRunner`, parse the arguments:
```java
@Component
public class MigrationRunner implements CommandLineRunner {
    private final SampleTypeLoader sampleTypeLoader;
    private final ContainerTypeLoader containerTypeLoader;
    private final ContainerLoader containerLoader;
    private final SampleLoader sampleLoader;

    @Override
    public void run(String... args) throws Exception {
        Set<String> targetTables = parseTargetTables(args); // e.g. ["sample_type", "container"]
        
        if (targetTables.contains("sample_type")) {
            sampleTypeLoader.load();
        }
        if (targetTables.contains("container_type")) {
            containerTypeLoader.load();
        }
        if (targetTables.contains("container")) {
            containerLoader.load();
        }
        if (targetTables.contains("sample")) {
            sampleLoader.load();
        }
    }
}
```

---

## 3. Designing for Idempotency (UPSERT)

If the loader crashes mid-migration (due to a database constraint, network error, or server out-of-memory), the operator should be able to simply rerun the command.
To enable this, we use PostgreSQL's `ON CONFLICT` SQL clause.

### A. For `sample_type` and `container_type`
If the record exists, we can either skip it (`DO NOTHING`) or update mutable fields:
```sql
INSERT INTO sample.sample_type (name, abbreviation, description, userstamp, created, version)
VALUES (?, ?, ?, ?, ?, 1)
ON CONFLICT (name) 
DO UPDATE SET 
    abbreviation = EXCLUDED.abbreviation,
    description = EXCLUDED.description,
    userstamp = EXCLUDED.userstamp,
    version = sample.sample_type.version + 1; -- Increment version on modification
```

### B. For `container`
Since `container.name` (barcode) is the unique business key:
```sql
INSERT INTO sample.container (name, description, container_type_id, parent_container_id, placecode, userstamp, created, version)
VALUES (?, ?, ?, ?, ?, ?, ?, 1)
ON CONFLICT (name)
DO UPDATE SET
    description = EXCLUDED.description,
    container_type_id = EXCLUDED.container_type_id,
    parent_container_id = EXCLUDED.parent_container_id,
    placecode = EXCLUDED.placecode,
    userstamp = EXCLUDED.userstamp,
    version = sample.container.version + 1;
```

### C. For `sample`
Unique key is `sampleid`:
```sql
INSERT INTO sample.sample (sampleid, subjectid, sample_type_id, sample_status, amount, concentration, remarks, comment, container_id, placecode, parent_id, userstamp, created, version)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
ON CONFLICT (sampleid)
DO UPDATE SET
    sample_status = EXCLUDED.sample_status,
    amount = EXCLUDED.amount,
    concentration = EXCLUDED.concentration,
    remarks = EXCLUDED.remarks,
    comment = EXCLUDED.comment,
    container_id = EXCLUDED.container_id,
    placecode = EXCLUDED.placecode,
    parent_id = EXCLUDED.parent_id,
    userstamp = EXCLUDED.userstamp,
    version = sample.sample.version + 1;
```

---

## 4. Hierarchy Checkpointing (Resume from Failure)

Since `container` and `sample` tables have self-referential relationships, they are loaded in sequential "depth passes".
To make the migration resumable:
1. **Pass-level Transactions**: Run each depth pass in its own database transaction (`@Transactional(propagation = Propagation.REQUIRES_NEW)`).
2. If Pass 1 (e.g. parent containers) succeeds and is committed, but Pass 2 (child shelves/boxes) fails, the parent containers are saved.
3. Rerunning the loader will skip Pass 1 inserts (handled by `ON CONFLICT DO NOTHING`) and resume processing at Pass 2.

---

## 5. Incremental Synchronization (Optional Delta Extraction)

If there is a significant lag between extraction and the final cutover, we can run an incremental delta sync.
1. **Delta Query on DB2**:
   Modify the DB2 query in `exporter2026` to filter by modification time:
   ```sql
   SELECT * FROM BIOBANK3.VIEW_SAMPLE_MASTER 
   WHERE TIMELOG > ?
   ```
   *Note: In the live DB2 database, the `TIMELOG` timestamp tracks when a row was last updated.*
2. The exporter generates `sample_delta.csv` which is processed by the loader. The loader uses the `UPSERT` statements above to apply modifications and insert new records seamlessly.
