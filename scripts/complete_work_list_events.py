"""Add the missing terminal lifecycle row of each migrated work list (sample-service todo D51, ADR 0051).

export_work_list_events.py rebuilds a list's lifecycle from BATCH_LIST_AUDIT. A list that was created directly in
its final state (the release lists of the legacy application, entered after the fact with a begin and an end date)
has no update row in the audit, so it gets only a CREATED event. Since ADR 0051 the work_list_event trigger writes
nothing in MIGRATION transactions, so the migration is the only source of these rows.

For every list whose final status maps to COMPLETED or CANCELLED and that has no matching terminal event, this step
appends one at BATCH_LIST.END_TIME, the end time the operator entered. A list without an END_TIME gets no invented
time; it is reported instead. Safe to run again: a list that already has its terminal event is left alone.
"""
import csv
import sys

# Must agree with transformListStatus in config/scripts/work_list_transform.js (checked by the unit test).
COMPLETED_STATUSES = {
    "PICKING_COMPLETED",
    "BATCH_PICKING_FINISHED",
    "BATCH_PROCESSED",
    "BATCH_SENT",
    "BATCH_RECEIVED",
    "SAMPLES_AVAILABLE_FOR_DELIVERY",
    "SAMPLES_DELIVERED",
    "SAMPLE_LIST",
    "BATCH_SAMPLE_LIST",
}
CANCELLED_STATUSES = {"BATCH_CANCELED"}

# The event types that already record the end of a list in the exported lifecycle.
TERMINAL_EVENTS = {"COMPLETED": {"COMPLETED", "DELIVERED"}, "CANCELLED": {"CANCELLED"}}


def terminal_event_type(batch_status):
    status = (batch_status or "").strip().upper()
    if status in COMPLETED_STATUSES:
        return "COMPLETED"
    if status in CANCELLED_STATUSES:
        return "CANCELLED"
    return None


def missing_terminal_events(lists, events):
    """Return (rows to append, names of terminal lists without an END_TIME)."""
    by_list = {}
    for event in events:
        by_list.setdefault(event["BATCH_NAME"], []).append(event)

    added, unresolved = [], []
    for batch in lists:
        event_type = terminal_event_type(batch["BATCH_STATUS"])
        if event_type is None:
            continue
        existing = by_list.get(batch["NAME"], [])
        if any(e["EVENT_TYPE"] in TERMINAL_EVENTS[event_type] for e in existing):
            continue
        end_time = (batch.get("END_TIME") or "").strip()
        if not end_time:
            unresolved.append(batch["NAME"])
            continue
        last = existing[-1] if existing else {}
        added.append({
            "BATCH_ID": last.get("BATCH_ID", ""),
            "BATCH_NAME": batch["NAME"],
            "ISPICK": batch.get("ISPICK", ""),
            "EVENT_TYPE": event_type,
            "FROM_STATUS": last.get("TO_STATUS", ""),
            "TO_STATUS": batch["BATCH_STATUS"],
            "EVENT_TIME": end_time,
            "EVENT_USER": batch.get("USERNAME", ""),
            "PROJECT_ID": batch.get("PROJECT_ID", ""),
            "EVENT_COMMENT": "",
        })
    return added, unresolved


def main(lists_path="export/batch_list.csv", events_path="export/work_list_event.csv"):
    with open(lists_path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if "END_TIME" not in (reader.fieldnames or []):
            sys.exit(f"{lists_path} has no END_TIME column; re-run scripts/export_batch_lists.py")
        lists = list(reader)
    with open(events_path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        events = list(reader)

    added, unresolved = missing_terminal_events(lists, events)
    if added:
        with open(events_path, "a", encoding="utf-8", newline="") as f:
            csv.DictWriter(f, fieldnames=fieldnames).writerows(added)

    print(f"✓ Added {len(added)} terminal work-list events from BATCH_LIST.END_TIME.")
    if unresolved:
        print(f"⚠ {len(unresolved)} finished lists have no END_TIME and keep no terminal event: "
              + ", ".join(unresolved))


if __name__ == "__main__":
    main()
