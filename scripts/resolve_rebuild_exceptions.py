"""Apply explicitly approved rebuild exceptions; retain original rows for reconciliation."""
import argparse
import csv
from pathlib import Path
import shutil

EVENT_TYPES = {"FREEZING_TIME": "FROZEN", "DISCARDED": "NOT_AVAILABLE",
               "REVERTED": "AVAILABLE", "PLATE_PROCESSING": "PROCESSED"}


def move_orphans_to_trash(rows):
    exceptions = []
    for row in rows:
        if row["PLACECODE"].strip() and not row["CONTAINER_NAME"].strip():
            exceptions.append(dict(row))
            row["CONTAINER_NAME"] = "Trash"
            row["PLACECODE"] = ""
            row["SAMPLE_STATUS"] = "Not available"
    return rows, exceptions


def deduplicate_events(rows):
    # Align with event_transform.js before enforcing the target composite key.
    retained = {}
    excluded = []
    for row in sorted(rows, key=lambda r: int(r["ID"])):
        raw = row["EVENT_TYPE"].strip().upper()
        key = (row["SAMPLEID"], EVENT_TYPES.get(raw, raw), row["EVENT_TIME"])
        if key in retained:
            excluded.append(row)
        else:
            retained[key] = row
    ids = {r["ID"] for r in retained.values()}
    return [r for r in rows if r["ID"] in ids], excluded


def apply(path, report_dir, transform, report_name):
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames
        rows = list(reader)
    kept, exceptions = transform(rows)
    if not exceptions:
        return 0  # A rerun must not erase the original exception evidence.
    report_dir.mkdir(parents=True, exist_ok=True)
    original = report_dir / (path.stem + "_original.csv")
    report = report_dir / report_name
    if original.exists() or report.exists():
        raise ValueError("Report already exists; choose a fresh report directory for a new export")
    shutil.copy2(path, original)
    original.chmod(0o600)
    for target, records in [(report, exceptions), (path, kept)]:
        with target.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(records)
        target.chmod(0o600)
    return len(exceptions)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-dir", type=Path, default=Path("export"))
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument("--move-orphan-locations-to-trash", action="store_true")
    parser.add_argument("--keep-lowest-event-id", action="store_true")
    args = parser.parse_args()
    if args.move_orphan_locations_to_trash:
        print("Samples moved to Trash and marked unavailable:", apply(
            args.export_dir / "sample.csv", args.report_dir, move_orphans_to_trash,
            "sample_orphan_locations.csv"))
    if args.keep_lowest_event_id:
        print("Duplicate events quarantined:", apply(
            args.export_dir / "legacy_event.csv", args.report_dir, deduplicate_events,
            "legacy_event_duplicate_keys.csv"))


if __name__ == "__main__":
    main()
