import csv
import os
import psycopg2

# sample.sample_profile_primary_sample has no literal business-key column of its
# own (only FK/computed columns: sample_profile_id, sample_type_id, "order") —
# importer2026's foreignKey.parentNaturalKey can only match literal parent
# columns, so it can't resolve sample_profile_aliquot_sample.sample_profile_
# primary_sample_id directly from names. This script bridges that one hop: it
# resolves PROFILE_NAME -> sample_profile.id and PRIMARY_SAMPLE_TYPE_NAME ->
# sample_type.id (both already-loaded, static-or-just-loaded reference data) and
# writes them as literal integer columns the aliquot manifest can then match
# against sample_profile_primary_sample's own (sample_profile_id, sample_type_id,
# "order") composite key. Must run after sample_profile + sample_profile_primary_
# sample are loaded, before sample_profile_aliquot_sample is loaded.
# See docs/sample-profile-migration-plan.md for the full rationale.

PG_DSN = {
    "host": os.environ.get("PG_HOST", "localhost"),
    "port": os.environ.get("PG_PORT", "5432"),
    "dbname": os.environ.get("PG_DATABASE", "sample"),
    "user": os.environ.get("PG_USER", "dbadmin"),
    "password": os.environ.get("PG_PASSWORD", "dbadmin"),
}

RAW_CSV = "export/sample_profile_aliquot_sample_raw.csv"
OUTPUT_CSV = "export/sample_profile_aliquot_sample.csv"


def main():
    conn = psycopg2.connect(**PG_DSN)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT name, id FROM sample.sample_profile")
            profile_ids = {name: id_ for name, id_ in cur.fetchall()}
            cur.execute("SELECT name, id FROM sample.sample_type")
            sample_type_ids = {name: id_ for name, id_ in cur.fetchall()}

        with open(RAW_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        missing = set()
        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                list(reader.fieldnames) + ["PRIMARY_PROFILE_ID", "PRIMARY_SAMPLE_TYPE_ID"]
            )
            count = 0
            for row in rows:
                profile_id = profile_ids.get(row["PROFILE_NAME"])
                type_id = sample_type_ids.get(row["PRIMARY_SAMPLE_TYPE_NAME"])
                if profile_id is None:
                    missing.add(("profile", row["PROFILE_NAME"]))
                if type_id is None:
                    missing.add(("sample_type", row["PRIMARY_SAMPLE_TYPE_NAME"]))
                writer.writerow(list(row.values()) + [profile_id, type_id])
                count += 1

        if missing:
            print(f"⚠ {len(missing)} unresolved lookups (rows will fail FK resolution on load): {sorted(missing)}")
        print(f"✓ Enriched {count} aliquot rows -> {OUTPUT_CSV}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
