import csv

# EVENT_TYPE codes from BIOBANK3.EVENT that describe picking-list actions, not sample-state
# transitions. sample.cv_event_type only models sample state (see docs/legacy-events-migration-plan.md);
# there is no target table for per-sample picking-item history today. These rows are excluded from
# sample.event and written to a side file for manual follow-up instead of being silently dropped.
EXCLUDED_EVENT_TYPES = {
    "ADDED_TO_LIST",
    "PICKED",
    "SHIPPING",
    "RETURNED_TO_PICKING",
    "RELEASED_FROM_PICKING",
}


def filter_legacy_events():
    input_path = "export/legacy_event.csv"
    excluded_path = "export/legacy_event_excluded_picking.csv"

    with open(input_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    kept = [r for r in rows if r["EVENT_TYPE"] not in EXCLUDED_EVENT_TYPES]
    excluded = [r for r in rows if r["EVENT_TYPE"] in EXCLUDED_EVENT_TYPES]

    with open(input_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(kept)

    with open(excluded_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(excluded)

    print(f"✓ Kept {len(kept)} legacy events, excluded {len(excluded)} picking-list events "
          f"(written to {excluded_path} for follow-up).")


if __name__ == "__main__":
    filter_legacy_events()
