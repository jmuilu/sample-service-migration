import csv
import sys
import os
import ibm_db

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.db2_config import connect_db2

# See docs/sample-profile-migration-plan.md for the full column-mapping rationale,
# including which DB2 columns have no destination and are intentionally dropped here.

PROFILE_QUERY = """
SELECT ID, NAME, IS_DEFAULT_SAMPLE_CREATION, USERNAME, TIMELOG
FROM BIOBANK3.BIOBANK_SAMPLE_PROFILE
ORDER BY ID
"""

PRIMARY_SAMPLE_QUERY = """
SELECT
    p.BIOBANK_SAMPLE_PROFILE_ID,
    prof.NAME AS PROFILE_NAME,
    g.NAME AS SAMPLE_TYPE_NAME,
    a.AMOUNT,
    p.RANK,
    a.CONTAINER_TYPE,
    a.SIMPLE_AUTO_ASSIGN,
    p.USERNAME,
    p.TIMELOG
FROM BIOBANK3.PROFILE_PRIMARY_SAMPLE_TYPE p
JOIN BIOBANK3.BIOBANK_SAMPLE_PROFILE prof ON p.BIOBANK_SAMPLE_PROFILE_ID = prof.ID
JOIN BIOBANK3.SAMPLEGROUP g ON p.SAMPLE_GROUPNR = g.GROUPNR
JOIN BIOBANK3.PROFILE_SAMPLE_AMOUNT a ON a.PROFILE_PRIMARY_SAMPLE_TYPE_ID = p.ID
ORDER BY p.ID
"""

# Raw = not yet enriched with the Postgres-side sample_profile_id / sample_type_id
# needed to resolve the parent sample_profile_primary_sample row (composite key,
# see scripts/enrich_sample_profile_aliquots.py — that script produces the final
# export/sample_profile_aliquot_sample.csv consumed by the importer).
ALIQUOT_SAMPLE_RAW_QUERY = """
SELECT
    prof.NAME AS PROFILE_NAME,
    primary_g.NAME AS PRIMARY_SAMPLE_TYPE_NAME,
    p.RANK AS PRIMARY_RANK,
    aliquot_g.NAME AS ALIQUOT_SAMPLE_TYPE_NAME,
    al.AMOUNT,
    al.NUM,
    al.RANK,
    al.CONTAINER_TYPE,
    al.SIMPLE_AUTO_ASSIGN,
    al.USERNAME,
    al.TIMELOG
FROM BIOBANK3.PROFILE_ALIQUOT_SAMPLE al
JOIN BIOBANK3.PROFILE_PRIMARY_SAMPLE_TYPE p ON al.PROFILE_PRIMARY_SAMPLE_TYPE_ID = p.ID
JOIN BIOBANK3.BIOBANK_SAMPLE_PROFILE prof ON p.BIOBANK_SAMPLE_PROFILE_ID = prof.ID
JOIN BIOBANK3.SAMPLEGROUP primary_g ON p.SAMPLE_GROUPNR = primary_g.GROUPNR
JOIN BIOBANK3.SAMPLEGROUP aliquot_g ON al.ALIQUOT_SAMPLE_GROUPNR = aliquot_g.GROUPNR
ORDER BY al.ID
"""

# Only SAMPLE_COLUMN = 'SOURCE' has a destination column on sample.sample today
# (verified live against sample.view_sample_profile_available_columns). The other
# 9 distinct legacy fields (COLLECTION_ID, FASTING, PIC_TYPE, PROJECT_ID,
# SAMPLE_RECEIVED_TEMP, SHOW_ORIGINAL_ID, TEMP, TEMP_BEFORE_STORAGE, VISIT_ID —
# 36 of the 40 source rows) are dropped; see the migration plan doc.
SAMPLE_COLUMN_QUERY = """
SELECT
    prof.NAME AS PROFILE_NAME,
    c.DEFAULT_VALUE,
    c.IS_VISIBLE,
    c.IS_FIXED,
    c.USERNAME,
    c.TIMELOG
FROM BIOBANK3.BIOBANK_SAMPLE_PROFILE_SAMPLE_COLUMN c
JOIN BIOBANK3.BIOBANK_SAMPLE_PROFILE prof ON c.BIOBANK_SAMPLE_PROFILE_ID = prof.ID
WHERE c.SAMPLE_COLUMN = 'SOURCE'
ORDER BY prof.ID
"""


def strip(v):
    # Match exporter2026's whole-second timestamp formatting (no fractional seconds) -
    # importer2026's BatchLoader date parser doesn't accept microseconds.
    if hasattr(v, "strftime"):
        return v.strftime("%Y-%m-%d %H:%M:%S")
    return v.strip() if isinstance(v, str) else v


def export_query(conn, query, headers, row_fn, output_path):
    print(f"Executing query for {output_path}...")
    stmt = ibm_db.exec_immediate(conn, query)
    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        count = 0
        row = ibm_db.fetch_assoc(stmt)
        while row:
            row_upper = {k.upper(): strip(v) for k, v in row.items()}
            writer.writerow(row_fn(row_upper))
            count += 1
            row = ibm_db.fetch_assoc(stmt)
    print(f"✓ Exported {count} rows to {output_path}")


def main():
    os.makedirs("export", exist_ok=True)
    print("Connecting to DB2 database...")
    conn = connect_db2()
    try:
        export_query(
            conn,
            PROFILE_QUERY,
            ["NAME", "IS_DEFAULT", "USERNAME", "TIMELOG"],
            lambda r: [
                r["NAME"],
                1 if r["IS_DEFAULT_SAMPLE_CREATION"] else 0,
                r["USERNAME"],
                r["TIMELOG"],
            ],
            "export/sample_profile.csv",
        )

        export_query(
            conn,
            PRIMARY_SAMPLE_QUERY,
            ["PROFILE_NAME", "SAMPLE_TYPE_NAME", "AMOUNT", "ORDER", "CONTAINER_TYPE", "AUTO_ASSIGN", "USERNAME", "TIMELOG"],
            lambda r: [
                r["PROFILE_NAME"],
                r["SAMPLE_TYPE_NAME"],
                r["AMOUNT"],
                r["RANK"],
                r["CONTAINER_TYPE"],
                1 if r["SIMPLE_AUTO_ASSIGN"] else 0,
                r["USERNAME"],
                r["TIMELOG"],
            ],
            "export/sample_profile_primary_sample.csv",
        )

        export_query(
            conn,
            ALIQUOT_SAMPLE_RAW_QUERY,
            [
                "PROFILE_NAME", "PRIMARY_SAMPLE_TYPE_NAME", "PRIMARY_RANK",
                "ALIQUOT_SAMPLE_TYPE_NAME", "AMOUNT", "COUNT", "ORDER",
                "CONTAINER_TYPE", "AUTO_ASSIGN", "USERNAME", "TIMELOG",
            ],
            lambda r: [
                r["PROFILE_NAME"],
                r["PRIMARY_SAMPLE_TYPE_NAME"],
                r["PRIMARY_RANK"],
                r["ALIQUOT_SAMPLE_TYPE_NAME"],
                r["AMOUNT"],
                r["NUM"],
                r["RANK"],
                r["CONTAINER_TYPE"],
                1 if r["SIMPLE_AUTO_ASSIGN"] else 0,
                r["USERNAME"],
                r["TIMELOG"],
            ],
            "export/sample_profile_aliquot_sample_raw.csv",
        )

        export_query(
            conn,
            SAMPLE_COLUMN_QUERY,
            ["PROFILE_NAME", "COLUMN_NAME", "DEFAULT_VALUE", "IS_VISIBLE", "IS_FIXED", "USERNAME", "TIMELOG"],
            lambda r: [
                r["PROFILE_NAME"],
                "source",
                r["DEFAULT_VALUE"],
                1 if r["IS_VISIBLE"] else 0,
                1 if r["IS_FIXED"] else 0,
                r["USERNAME"],
                r["TIMELOG"],
            ],
            "export/sample_profile_sample_column.csv",
        )
    finally:
        ibm_db.close(conn)


if __name__ == "__main__":
    main()
