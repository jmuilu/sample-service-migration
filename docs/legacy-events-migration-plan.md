# Legacy Sample Events Migration Plan (DB2 ↔ Postgres)

Covers migrating `BIOBANK3.EVENT` (joined to `SAMPLE_10002` for the natural sample key) into
`sample.event`, using the **Generic ETL (Zero-Compile)** approach: `scripts/export_legacy_events.py`
extracts the raw rows, `scripts/filter_legacy_events.py` and
[event_transform.js](file:///Users/muilu/git/others/biobank-solution/sample-service-migration/config/scripts/event_transform.js)
normalize them, and `importer2026` loads them via
[event_manifest.yaml](file:///Users/muilu/git/others/biobank-solution/sample-service-migration/config/manifests/event_manifest.yaml).

## EVENT_TYPE mapping

`sample.cv_event_type` models sample **state** transitions only (`AVAILABLE`, `CHANGED`, `FROZEN`,
`NOT_AVAILABLE`, `PROCESSED`, `SAMPLE_RECEIVED`, `SAMPLE_TAKEN`, `THAWED`), narrower than DB2's
`BIOBANK3.EVENT.EVENT_TYPE`, which also recorded picking-list actions in the same table. Decision
(2026-09-22, confirmed with the repo owner):

| DB2 `EVENT_TYPE` | Target `event_type` | Rationale |
|:---|:---|:---|
| `SAMPLE_TAKEN`, `PROCESSED`, `SAMPLE_RECEIVED`, `CHANGED` | (same) | Exact vocabulary match. |
| `FREEZING_TIME` | `FROZEN` | "Sample placed into cold storage"; row carries a `TEMPERATURE` value like `THAWED`/`FROZEN` events. |
| `DISCARDED` | `NOT_AVAILABLE` | `NOT_AVAILABLE`'s own description explicitly lists "disposed, depleted, discarded". |
| `REVERTED` | `AVAILABLE` | `AVAILABLE`'s description covers "corrected/re-evaluated from unavailable". |
| `PLATE_PROCESSING` | `PROCESSED` | Matches "physical preprocessing or isolation... finished". |
| `ADDED_TO_LIST`, `PICKED`, `SHIPPING`, `RETURNED_TO_PICKING`, `RELEASED_FROM_PICKING` | **excluded** | Picking-list item actions, not sample-state events. `sample.work_list_event` only tracks header-level `CREATED`/`ACTIVATED`/`COMPLETED` transitions, not per-sample picking history — there is currently no target table for these. Filtered out by `filter_legacy_events.py` into `export/legacy_event_excluded_picking.csv` for manual follow-up rather than silently dropped. |

The remap is applied in `event_transform.js::transformEventType`; the exclusion happens earlier,
in `filter_legacy_events.py`, since the importer's FK-skip mechanism only works against parent
tables with a surrogate `id` column and `cv_event_type` is keyed by `term`.

## Follow-up

`export/legacy_event_excluded_picking.csv` (not migrated) should be reviewed if/when the schema
grows a home for per-sample picking-item history — e.g. an extension of `work_list_item` or a new
event-log table scoped to `work_list_item`.
