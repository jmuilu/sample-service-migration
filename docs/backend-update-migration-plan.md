# Backend Schema Update Migration Plan & Concept/Value Mapping Analysis

**Target Repositories:**
- Destination Schema: [sample-service](file:///Users/muilu/git/others/sample-service) (PostgreSQL)
- Migration Workspace: [sample-service-migration](file:///Users/muilu/git/others/sample-service-migration)
- Extraction & Loading Engines: `exporter2026` & `importer2026`

---

## 1. Executive Summary & Context

The backend data model in `sample-service` has evolved to align with **HL7 FHIR**, **MIABIS 2.0**, and **ISBER** biobanking standards (ADR 0012, ADR 0013, v001–v009 SQL migrations). 

These architectural refinements require updates to the migration configuration, export scripts, and transformation pipelines before executing the next end-to-end data load:
1. **CV Tables & Shared Metadata Architecture**: The `ontology` column was removed across all `sample.cv_*` tables. External ontology terms (LOINC, SNOMED CT, NCIT, SPREC) are now managed via a shared metadata catalog (`common.cv_term_metadata`).
2. **Work List & Task Separation**: `sample.work_list` has been normalized into an operational specimen execution list; `project_id` and `partner_id` foreign keys have been moved exclusively to `sample.task`.
3. **Event Type & Reason Canonicalization**: `sample.cv_event_type` was reduced from 26 raw values to 8 canonical lifecycle events. Historical DB2 events must be cleanly mapped to the 8 canonical terms and legacy reasons mapped into `sample.cv_event_reason`.
4. **Pre-analytical Quality & Properties Expansion**: Canonical SPREC properties (`FREEZE_THAW_COUNT`, `WARM_ISCHEMIA_TIME_MIN`, etc.) are now pre-seeded in `sample.cv_property_type`.

---

## 2. Detailed Concept & Value Mapping Investigation

### 2.1 Event Types & Event Reasons Mapping (Critical)

In the legacy DB2 database (`BIOBANK3.EVENT`), 18 distinct `EVENT_TYPE` strings exist across 11,471 records. Target PostgreSQL table `sample.cv_event_type` strictly allows only **8 canonical event terms**.

Below is the verified value mapping matrix between DB2 source events and PostgreSQL canonical events and reasons:

| DB2 Source `EVENT_TYPE` | Count | Target `cv_event_type` | Target `cv_event_reason` | Remarks / Comment Handling |
|---|---|---|---|---|
| `SAMPLE_TAKEN` | 2,817 | `SAMPLE_TAKEN` | `NA` | Initial specimen collection timestamp. |
| `PROCESSED` | 1,622 | `PROCESSED` | `NA` | General laboratory processing. |
| `SAMPLE_RECEIVED` | 968 | `SAMPLE_RECEIVED` | `NA` | Accessioning into laboratory custody. |
| `FREEZING_TIME` | 764 | `FROZEN` | `NA` | Transition into cold storage. |
| `THAWED` | 10 | `THAWED` | `NA` | Thermal transition (temperature logged). |
| `DISCARDED` | 93 | `NOT_AVAILABLE` | `DISCARDED` | Sample destroyed or disposed. |
| `CHANGED` | 352 | `CHANGED` | `NA` | Metadata or attribute modification. |
| `VOLUME_CHANGE` | 5 | `CHANGED` | `NA` | Prefix comment: `[VOLUME_CHANGE]`. |
| `SAMPLE_TYPE_CHANGE` | 2 | `CHANGED` | `WRONG_SAMPLE_TYPE` | Sample type classification updated. |
| `REVERTED` | 3 | `CHANGED` | `CORRECTION` | Action roll-back / administrative fix. |
| `POOLED` | 270 | `PROCESSED` | `N10` | Whole blood or aliquot pooling. |
| `ADDED_TO_LIST` | 1,449 | `CHANGED` | `NA` | Allocated to picking/processing work list. |
| `ADDED_TO_SAMPLE_LIST`| 1 | `CHANGED` | `NA` | Added to generic sample list. |
| `PICKED` | 1,422 | `CHANGED` | `NA` | Retrieved from storage slot during picking. |
| `RELEASED_FROM_PICKING`| 200 | `CHANGED` | `N08` | Sample released / returned after picking. |
| `RETURNED_TO_PICKING` | 56 | `CHANGED` | `NA` | Re-queued for picking. |
| `PLATE_PROCESSING` | 344 | `PROCESSED` | `NA` | Microplate transfer or assay prep. |
| `SHIPPING` | 1,093 | `NOT_AVAILABLE` | `SAMPLE_USED` | Dispatched to external partner/facility. |

#### Source `CHANGE_REASON` to `cv_event_reason` Mapping
- Empty / Null / `'NA'` -> `'NA'`
- `'parent - aliquot inheritance'` -> `'ALIQUOT_INHERITANCE'`
- Legacy codes (`'N00'` through `'N17'`, `'NX'`, `'NXCONF'`, `'USED'`, `'HL7C'`, `'ALIQUOT'`, `'EXTRACTED'`) -> Preserved as-is (all exist in `cv_event_reason`).

---

### 2.2 Work Lists vs. Tasks Separation

* **DB2 Source Table**: `BIOBANK3.BATCH_LIST`
* **Target Table 1**: `sample.task` (High-level project workflow context)
  - Retains `project_id` and `partner_id` (foreign keys to `project.project_membership`).
  - Maps `ISPICK = 'Y'` -> `task_type = 'SAMPLE_DELIVERY'`, `ISPICK = 'N'` -> `task_type = 'SAMPLE_PROFILE'`.
* **Target Table 2**: `sample.work_list` (Operational execution list)
  - `project_id` and `partner_id` columns **removed**.
  - Retains `list_type` (`'PICKING'` vs `'ANALYSIS'`), `list_status` (`'DRAFT'`, `'ACTIVE'`, `'COMPLETED'`, `'CANCELLED'`), `assigned_to`, `parent_id`, and `priority`.

---

### 2.3 Sample Status Mapping

Source column `BIOBANK3.VIEW_SAMPLE_MASTER.SAMPLE_STATUS`:
- `'Available'` -> `'AVAILABLE'`
- `'Not available'` -> `'NOT_AVAILABLE'`
- `'Pending'` -> `'PENDING'`
- Empty / `NULL` -> `'AVAILABLE'` (Default fallback)

---

### 2.4 Controlled Vocabularies & Metadata Removal

The `ontology` column has been deleted from:
- `sample.cv_property_type`
- `sample.cv_sample_quality`
- `sample.cv_container_basetype`
- `sample.cv_container_type`
- `sample.cv_sample_type`
- `sample.cv_work_list_type`, `cv_work_list_status`, `cv_work_list_item_status`
- `sample.cv_task_type`, `cv_task_status`, `cv_event_type`, `cv_event_reason`

Any manifest, SQL seed script, or CSV export referencing `ontology` on these tables must be updated to omit the column.

---

## 3. Required File Modifications in `sample-service-migration`

| File | Target Component | Modification Description |
|---|---|---|
| [config/manifests/work_list_manifest.yaml](file:///Users/muilu/git/others/sample-service-migration/config/manifests/work_list_manifest.yaml) | Manifest | Remove `project_id` and `partner_id` column mappings and `foreignKey` blocks. |
| [config/manifests/cv_property_type_manifest.yaml](file:///Users/muilu/git/others/sample-service-migration/config/manifests/cv_property_type_manifest.yaml) | Manifest | Remove `ontology` column mapping. |
| [scripts/export_legacy_events.py](file:///Users/muilu/git/others/sample-service-migration/scripts/export_legacy_events.py) | Python ETL | Implement canonical 8-event mapping table and event reason resolver. |
| [config/scripts/work_list_transform.js](file:///Users/muilu/git/others/sample-service-migration/config/scripts/work_list_transform.js) | JS Transform | Clean up unused `transformPartnerName` function. |
| [scripts/postgres/seed_properties.sql](file:///Users/muilu/git/others/sample-service-migration/scripts/postgres/seed_properties.sql) | SQL Seed | Remove `ontology` references; add SPREC canonical property definitions. |
| [scripts/postgres/seed_qualities.sql](file:///Users/muilu/git/others/sample-service-migration/scripts/postgres/seed_qualities.sql) | SQL Seed | Remove `ontology` references. |
| [Makefile](file:///Users/muilu/git/others/sample-service-migration/Makefile) | Automation | Verify table sequences, truncation order, and post-migration verification query. |
| [LLM_MIGRATION_RUNBOOK.md](file:///Users/muilu/git/others/sample-service-migration/LLM_MIGRATION_RUNBOOK.md) | Documentation | Update runbook with the new schema mappings and rules. |

---

## 4. Execution Plan for the Migration Session

When ready to execute the migration in a separate session, follow this sequence:

### Step 1: Environment & Dependency Verification
```bash
# 1. Verify DB2 container/service on port 50000
nc -z localhost 50000

# 2. Verify PostgreSQL container on port 5432
nc -z localhost 5432

# 3. Verify backend schema migrations are up-to-date in PostgreSQL
docker exec -i sample-service-db-1 psql -U sample -d sample -c "\dt sample.*"
```

### Step 2: Apply Script and Manifest Changes
Apply the updates outlined in Section 3 to [work_list_manifest.yaml](file:///Users/muilu/git/others/sample-service-migration/config/manifests/work_list_manifest.yaml), [cv_property_type_manifest.yaml](file:///Users/muilu/git/others/sample-service-migration/config/manifests/cv_property_type_manifest.yaml), [export_legacy_events.py](file:///Users/muilu/git/others/sample-service-migration/scripts/export_legacy_events.py), and [seed_properties.sql](file:///Users/muilu/git/others/sample-service-migration/scripts/postgres/seed_properties.sql).

### Step 3: Run Full End-to-End Migration
```bash
cd /Users/muilu/git/others/sample-service-migration
make migrate-all
```
This target executes:
1. `make clear-target`: Truncates all target Postgres tables in foreign-key safe order.
2. `make extract-data`: Exports fresh data from DB2 into `export/*.csv` (including updated legacy events).
3. `make transform-data`: Dynamic EAV unpivoting and placeholder generation.
4. `make load-target`: Seeds CVs, imports all CSVs via `importer2026`, and resets database sequences.
5. `make verify`: Compares row counts and validates referential integrity.

### Step 4: Verification Checks
```sql
-- Verify table row counts in PostgreSQL
SELECT 'sample_type' AS tab, COUNT(*) FROM sample.sample_type
UNION ALL SELECT 'container_type', COUNT(*) FROM sample.container_type
UNION ALL SELECT 'container', COUNT(*) FROM sample.container
UNION ALL SELECT 'sample', COUNT(*) FROM sample.sample
UNION ALL SELECT 'sample_property', COUNT(*) FROM sample.sample_property
UNION ALL SELECT 'sample_quality', COUNT(*) FROM sample.sample_quality
UNION ALL SELECT 'task', COUNT(*) FROM sample.task
UNION ALL SELECT 'work_list', COUNT(*) FROM sample.work_list
UNION ALL SELECT 'work_list_item', COUNT(*) FROM sample.work_list_item
UNION ALL SELECT 'work_list_event', COUNT(*) FROM sample.work_list_event
UNION ALL SELECT 'event', COUNT(*) FROM sample.event;

-- Verify event type distribution strictly matches canonical vocabulary
SELECT e.event_type, COUNT(*) 
FROM sample.event e 
GROUP BY e.event_type 
ORDER BY COUNT(*) DESC;

-- Verify zero orphaned foreign keys in sample.event
SELECT COUNT(*) 
FROM sample.event e 
LEFT JOIN sample.cv_event_type c ON e.event_type = c.term 
WHERE c.term IS NULL;
```
