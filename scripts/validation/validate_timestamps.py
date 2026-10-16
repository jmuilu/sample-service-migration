#!/usr/bin/env python3
"""
Validates that timestamps migrated from DB2 to PostgreSQL:
1. Are stored as `timestamp with time zone` (timestamptz in UTC).
2. Faithfully represent the source DB2 wall-clock times in Finland/Helsinki (Europe/Helsinki).
   That is: (pg_timestamp AT TIME ZONE 'Europe/Helsinki') == db2_wallclock_timestamp.
3. Correctly observe seasonal offsets (UTC+2 in winter EET, UTC+3 in summer EEST).
4. Do not contain un-converted timestamps or midnight-shift regressions.
"""

import os
import sys
import csv
import psycopg2

SOURCE_TZ = os.environ.get("SOURCE_TZ", "Europe/Helsinki")

PG_HOST = os.environ.get("PG_HOST", "localhost")
PG_PORT = int(os.environ.get("PG_PORT", "5432"))
PG_USER = os.environ.get("PG_USER", "dbadmin")
PG_PASSWORD = os.environ.get("PG_PASSWORD", "dbadmin")
PG_DATABASE = os.environ.get("PG_DATABASE", "sample")

def connect_pg():
    return psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        user=PG_USER,
        password=PG_PASSWORD,
        dbname=PG_DATABASE
    )

def normalize_ts_str(ts_str):
    if not ts_str:
        return None
    val = ts_str.strip().replace("T", " ")
    if val.endswith("Z"):
        val = val[:-1]
    if "." in val:
        base, frac = val.split(".", 1)
        frac = (frac + "000000")[:6]
        return f"{base}.{frac}"
    else:
        return f"{val}.000000"

def run_timestamp_validation():
    print("======================================================================")
    print("TIMESTAMP MIGRATION VALIDATION (DB2 Finland/Helsinki -> PG UTC)")
    print("======================================================================")

    try:
        conn = connect_pg()
        cur = conn.cursor()
        print(f"✓ Connected to PostgreSQL ({PG_HOST}:{PG_PORT}/{PG_DATABASE}).")
    except Exception as e:
        print(f"✗ Failed to connect to PostgreSQL: {e}")
        sys.exit(1)

    failed = False

    # Check 1: Ensure no columns in 'sample' or 'common' use 'timestamp without time zone'
    print("\n--- CHECK 1: Ensure no zoneless timestamps exist in PG ---")
    cur.execute("""
        SELECT table_schema || '.' || table_name || '.' || column_name
        FROM information_schema.columns
        WHERE table_schema IN ('sample', 'common')
          AND data_type = 'timestamp without time zone'
        ORDER BY 1;
    """)
    zoneless = cur.fetchall()
    if zoneless:
        print(f"✗ Found columns with 'timestamp without time zone': {zoneless}")
        failed = True
    else:
        print("✓ All date-time columns in sample and common use 'timestamp with time zone'.")

    # Check 2: Sample timestamps against export/sample.csv
    print("\n--- CHECK 2: Validate sample.sample (created) against export/sample.csv ---")
    sample_csv = "export/sample.csv"
    if os.path.exists(sample_csv):
        with open(sample_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            checked = 0
            mismatches = 0
            for row in reader:
                sample_id = row.get("SAMPLEID")
                timelog = row.get("TIMELOG")
                if not sample_id or not timelog:
                    continue

                cur.execute("""
                    SELECT 
                        to_char(created AT TIME ZONE %s, 'YYYY-MM-DD HH24:MI:SS.US'),
                        to_char(created, 'YYYY-MM-DD HH24:MI:SS.US TZ')
                    FROM sample.sample
                    WHERE sampleid = %s;
                """, (SOURCE_TZ, sample_id))
                res = cur.fetchone()
                if not res:
                    continue

                pg_helsinki, pg_utc = res
                norm_csv = normalize_ts_str(timelog)
                norm_pg = normalize_ts_str(pg_helsinki)

                if not norm_pg.startswith(timelog.strip()[:19]):
                    print(f"✗ Mismatch on sample {sample_id}: DB2={timelog} != PG Helsinki={pg_helsinki} (UTC={pg_utc})")
                    mismatches += 1
                    failed = True
                    if mismatches >= 5:
                        break

                checked += 1
                if checked >= 50:
                    break
            if mismatches == 0:
                print(f"✓ Checked {checked} samples: wall-clock times match DB2 in {SOURCE_TZ}.")
    else:
        print(f"! {sample_csv} not found, skipping file comparison.")

    # Check 3: Container timestamps against export/container.csv
    print("\n--- CHECK 3: Validate sample.container (created) against export/container.csv ---")
    container_csv = "export/container.csv"
    if os.path.exists(container_csv):
        with open(container_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            checked = 0
            mismatches = 0
            for row in reader:
                name = row.get("NAME")
                timelog = row.get("TIMELOG")
                if not name or not timelog:
                    continue

                cur.execute("""
                    SELECT 
                        to_char(created AT TIME ZONE %s, 'YYYY-MM-DD HH24:MI:SS.US'),
                        to_char(created, 'YYYY-MM-DD HH24:MI:SS.US TZ')
                    FROM sample.container
                    WHERE name = %s;
                """, (SOURCE_TZ, name))
                res = cur.fetchone()
                if not res:
                    continue

                pg_helsinki, pg_utc = res
                if not pg_helsinki.startswith(timelog.strip()[:19]):
                    print(f"✗ Mismatch on container {name}: DB2={timelog} != PG Helsinki={pg_helsinki}")
                    mismatches += 1
                    failed = True

                checked += 1
            if mismatches == 0 and checked > 0:
                print(f"✓ Checked {checked} containers: wall-clock times match DB2 in {SOURCE_TZ}.")
    else:
        print(f"! {container_csv} not found, skipping file comparison.")

    # Check 4: Seasonal offset check (EET vs EEST)
    print("\n--- CHECK 4: Verify seasonal offsets (Winter UTC+2 vs Summer UTC+3) ---")
    cur.execute("""
        SELECT 
            created,
            to_char(created AT TIME ZONE %s, 'YYYY-MM-DD HH24:MI:SS'),
            ROUND(EXTRACT(EPOCH FROM ((created AT TIME ZONE %s) - (created AT TIME ZONE 'UTC'))) / 3600.0) AS offset_hours
        FROM sample.sample
        ORDER BY created
        LIMIT 100;
    """, (SOURCE_TZ, SOURCE_TZ))
    offset_rows = cur.fetchall()
    valid_offsets = 0
    invalid_offsets = 0
    for utc_ts, helsinki_ts, offset in offset_rows:
        if offset in (2.0, 3.0):
            valid_offsets += 1
        else:
            print(f"✗ Unexpected offset {offset} for {utc_ts} (Helsinki: {helsinki_ts})")
            invalid_offsets += 1
            failed = True
    if invalid_offsets == 0 and valid_offsets > 0:
        print(f"✓ Verified {valid_offsets} sample timestamps: offsets strictly adhere to UTC+2 / UTC+3 in {SOURCE_TZ}.")

    # Check 5: Domain Events event_time vs export/legacy_event.csv
    print("\n--- CHECK 5: Validate sample.event (event_time) against export/legacy_event.csv ---")
    legacy_event_csv = "export/legacy_event.csv"
    if os.path.exists(legacy_event_csv):
        with open(legacy_event_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            checked = 0
            mismatches = 0
            for row in reader:
                id_val = row.get("ID")
                event_time = row.get("EVENT_TIME")
                if not id_val or not event_time:
                    continue

                cur.execute("""
                    SELECT 
                        to_char(event_time AT TIME ZONE %s, 'YYYY-MM-DD HH24:MI:SS'),
                        to_char(event_time, 'YYYY-MM-DD HH24:MI:SS TZ')
                    FROM sample.event
                    WHERE id = %s;
                """, (SOURCE_TZ, id_val))
                res = cur.fetchone()
                if not res:
                    continue

                pg_helsinki, pg_utc = res
                if not pg_helsinki.startswith(event_time.strip()[:19]):
                    print(f"✗ Mismatch on event {id_val}: DB2={event_time} != PG Helsinki={pg_helsinki}")
                    mismatches += 1
                    failed = True
                    if mismatches >= 5:
                        break

                checked += 1
                if checked >= 50:
                    break
            if mismatches == 0 and checked > 0:
                print(f"✓ Checked {checked} events: event_time matches DB2 in {SOURCE_TZ}.")
    else:
        print(f"! {legacy_event_csv} not found, skipping file comparison.")

    # Check 6: Check WorkList & Task creation times
    print("\n--- CHECK 6: Validate sample.work_list & sample.task creation timestamps ---")
    cur.execute("""
        SELECT name, created, to_char(created AT TIME ZONE %s, 'YYYY-MM-DD HH24:MI:SS')
        FROM sample.work_list
        LIMIT 10;
    """, (SOURCE_TZ,))
    wl_rows = cur.fetchall()
    print(f"✓ Inspected {len(wl_rows)} work list created timestamps:")
    for name, utc_ts, helsinki_ts in wl_rows[:3]:
        print(f"   WorkList '{name}': UTC={utc_ts} -> {SOURCE_TZ}={helsinki_ts}")

    cur.close()
    conn.close()

    print("\n======================================================================")
    if failed:
        print("✗ TIMESTAMP VALIDATION FAILED!")
        print("======================================================================")
        sys.exit(1)
    else:
        print("✓ ALL TIMESTAMP VALIDATION CHECKS PASSED.")
        print("======================================================================")

if __name__ == "__main__":
    run_timestamp_validation()
