# Work List & Project Membership Migration Report

This report summarizes the implementation, data cleaning, and execution results of the `work_list` and project membership migration from DB2 to PostgreSQL.

## 1. Migration Architecture
The migration was completed utilizing the generic zero-compile `importer2026` ETL framework. No custom Java code or external scripting (like Python) was introduced. Instead, YAML manifests and embedded JavaScript (GraalJS/Nashorn inside the JVM) are used for dynamic transformations and cleanups.

> [!NOTE]
> All documentation files are maintained directly within the repository in Markdown format; there is no need to generate separate PDF documents.

### Manifest Files Used:
* [project_manifest.yaml](file:///Users/muilu/git/others/sample-service-migration/config/manifests/project_manifest.yaml)
* [partner_manifest.yaml](file:///Users/muilu/git/others/sample-service-migration/config/manifests/partner_manifest.yaml)
* [project_membership_manifest.yaml](file:///Users/muilu/git/others/sample-service-migration/config/manifests/project_membership_manifest.yaml)
* [work_list_manifest.yaml](file:///Users/muilu/git/others/sample-service-migration/config/manifests/work_list_manifest.yaml)
* [work_list_item_manifest.yaml](file:///Users/muilu/git/others/sample-service-migration/config/manifests/work_list_item_manifest.yaml)

---

## 2. Dynamic Missing Partner & Timestamp Resolution
During source DB2 database analysis, it was identified that out of 71 batch lists (`BIOBANK3.BATCH_LIST`), **11 rows had missing partner information** (both `PARTNER_ID` and `PROJECT_MEMBERSHIP_ID` were `NULL`). Additionally, some timestamps contained microseconds format incompatible with standard Postgres timestamp mapping.

To resolve these issues cleanly without extra tools or connection logic on the customer's server:
1. **Dynamic Partner Cache initialization**: In [work_list_transform.js](file:///Users/muilu/git/others/sample-service-migration/config/scripts/work_list_transform.js), Java NIO APIs are leveraged to read and index `export/project_membership.csv` in memory during first-row execution.
2. **Auto-Resolution Rule (JavaScript)**: If a project associated with a batch has *exactly one* active project membership, the partner is auto-resolved to that partner.
3. **Fallback Placeholder Rule (JavaScript)**: If a project has zero or multiple memberships, the partner is resolved to a synthetic **"Missing Partner"** fallback placeholder.
4. **Timestamp normalization (JavaScript)**: Formats any microsecond-precision DB2 timestamps to the standard `'yyyy-MM-dd HH:mm:ss'` format expected by PostgreSQL.
5. To maintain foreign key integrity, the synthetic `"Missing Partner"` partner and the corresponding memberships are dynamically injected during the `transform-data` phase.

---

## 3. Database Schema Fixes
To support seamless UPSERT operations and foreign key lookups inside `importer2026`:
1. **`project.partner` schema fix**: Added a `UNIQUE` constraint to the `name` column.
2. **`project.project_membership` schema fix**: Created an autoincrementing surrogate `id` column (`project_membership_id_seq`) and added a `UNIQUE` constraint to `(project_id, partner_id)` to allow proper `RETURNING id` query support during CSV load.

All schema changes were done directly in the database scripts:
* [v001b-project.sql](file:///Users/muilu/git/others/sample-service/src/main/resources/db/scripts/sample/v001b-project.sql)

---

## 4. Migration Execution Verification
The full migration pipeline was successfully executed using `make migrate-all`. The final row counts in the target PostgreSQL database matched expectations:

| Target Table | Row Count | Description |
| :--- | :--- | :--- |
| `project.project` | 642 | All projects successfully migrated |
| `project.partner` | 603 | Partners migrated + "Missing Partner" placeholder |
| `project.project_membership` | 598 | Project memberships + injected placeholder links |
| `sample.sample_type` | 29 | Fully verified |
| `sample.container_type` | 19 | Fully verified |
| `sample.container` | 129 | Fully verified |
| `sample.sample` | 2,822 | Fully verified |
| `sample.sample_property` | 239 | EAV properties pivoted |
| `sample.cv_sample_quality` | 40 | Fully verified |
| `sample.sample_type_quality_metadata` | 11 | Fully verified |
| `sample.sample_quality` | 493 | Fully verified |
| `sample.work_list` | 71 | All batches successfully migrated |
| `sample.work_list_event` | 71 | Sync status event log triggers executed |
| `sample.work_list_item` | 1,253 | Work list lines successfully matched and migrated |

**Verification Status: PASS**
