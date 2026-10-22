import csv
import sys
import os
import ibm_db
import psycopg2

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from scripts.db2_config import connect_db2

pg_conn_str = "host='{}' port={} dbname='{}' user='{}' password='{}'".format(
    os.environ.get("PG_HOST", "localhost"), os.environ.get("PG_PORT", "5432"),
    os.environ.get("PG_DATABASE", "sample"),
    os.environ.get("PG_USER", "dbadmin"), os.environ.get("PG_PASSWORD", "dbadmin"))
# The prepared input of the work_list_event load: the reconstructed lifecycle plus the terminal events that
# complete_work_list_events.py added from BATCH_LIST.END_TIME (sample-service todo D51).
EVENTS_CSV = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                          "export", "work_list_event.csv")

def run_validation():
    print("======================================================================")
    print("WORK LIST MIGRATION VALIDATION RUNNER")
    print("======================================================================")
    
    # 1. Connect to both databases
    try:
        print("Connecting to DB2...")
        db2_conn = connect_db2()
        print("✓ Connected to DB2.")
    except Exception as e:
        print(f"✗ Failed to connect to DB2: {e}")
        sys.exit(1)
        
    try:
        print("Connecting to PostgreSQL...")
        pg_conn = psycopg2.connect(pg_conn_str)
        pg_cur = pg_conn.cursor()
        print("✓ Connected to PostgreSQL.")
    except Exception as e:
        print(f"✗ Failed to connect to PostgreSQL: {e}")
        ibm_db.close(db2_conn)
        sys.exit(1)

    failed = False
    
    try:
        # --- Check 1: Row Counts ---
        print("\n--- CHECK 1: Row Counts ---")
        
        # DB2 counts
        db2_list_stmt = ibm_db.exec_immediate(db2_conn, "SELECT COUNT(*) FROM BIOBANK3.BATCH_LIST")
        db2_list_cnt = ibm_db.fetch_both(db2_list_stmt)[0]
        
        db2_item_stmt = ibm_db.exec_immediate(db2_conn, "SELECT COUNT(*) FROM BIOBANK3.BATCH_SAMPLE_LIST")
        db2_item_cnt = ibm_db.fetch_both(db2_item_stmt)[0]
        
        # PG counts
        pg_cur.execute("SELECT COUNT(*) FROM sample.work_list")
        pg_list_cnt = pg_cur.fetchone()[0]
        
        pg_cur.execute("SELECT COUNT(*) FROM sample.work_list_item")
        pg_item_cnt = pg_cur.fetchone()[0]
        
        print(f"DB2 BATCH_LIST: {db2_list_cnt} | PG work_list: {pg_list_cnt}")
        if db2_list_cnt == pg_list_cnt:
            print("✓ Work list counts match.")
        else:
            print("✗ Work list counts MISMATCH!")
            failed = True
            
        print(f"DB2 BATCH_SAMPLE_LIST: {db2_item_cnt} | PG work_list_item: {pg_item_cnt}")
        if db2_item_cnt == pg_item_cnt:
            print("✓ Work list item counts match.")
        else:
            print("✗ Work list item counts MISMATCH!")
            failed = True

        # --- Check 2: Event Counts & Details ---
        print("\n--- CHECK 2: Event Counts & Timestamps ---")
        
        # DB2 expected events (derived from view CTE)
        db2_event_query = """
        WITH created_events AS (
            SELECT b.ID, b.BEGIN_TIME FROM BIOBANK3.BATCH_LIST b
        ),
        status_changes AS (
            SELECT a.ID, a.BATCH_STATUS, 
                   COALESCE(LEAD(a.BATCH_STATUS) OVER (PARTITION BY a.ID ORDER BY a.BC_SYS_MODIFIED ASC), b.BATCH_STATUS) as to_status
            FROM BIOBANK3.BATCH_LIST_AUDIT a
            JOIN BIOBANK3.BATCH_LIST b ON a.ID = b.ID
            WHERE a.BC_SYS_OPER = 'U'
        )
        SELECT 
            (SELECT COUNT(*) FROM created_events) + 
            (SELECT COUNT(*) FROM status_changes WHERE BATCH_STATUS <> to_status) as cnt
        FROM SYSIBM.SYSDUMMY1
        """
        db2_event_stmt = ibm_db.exec_immediate(db2_conn, db2_event_query)
        db2_event_cnt = ibm_db.fetch_both(db2_event_stmt)[0]
        
        pg_cur.execute("SELECT COUNT(*) FROM sample.work_list_event")
        pg_event_cnt = pg_cur.fetchone()[0]

        with open(EVENTS_CSV, encoding="utf-8", newline="") as f:
            csv_event_cnt = sum(1 for _ in csv.DictReader(f))
        added_cnt = csv_event_cnt - db2_event_cnt

        print(f"Expected DB2 events (reconstructed): {db2_event_cnt} + terminal events from END_TIME: {added_cnt} "
              f"| prepared CSV: {csv_event_cnt} | PG work_list_event: {pg_event_cnt}")
        if added_cnt >= 0 and csv_event_cnt == pg_event_cnt:
            print("✓ Event counts match.")
        else:
            print("✗ Event counts MISMATCH! (Event migration might not be executed or is incomplete)")
            failed = True
            
        # Check event times in PG - verify they are not all set to a single migration timestamp (default fallback)
        pg_cur.execute("SELECT COUNT(DISTINCT event_time) FROM sample.work_list_event")
        distinct_times = pg_cur.fetchone()[0]
        print(f"Distinct event times in PG: {distinct_times}")
        if distinct_times > 1:
            print("✓ Event timestamps are distinct (historical data preserved).")
        else:
            print("✗ Warning: All event timestamps are identical! Historical timestamps lost.")
            failed = True

        # --- Check 3: Exclusivity Constraint ---
        print("\n--- CHECK 3: Active Picking Exclusivity Constraint ---")
        pg_cur.execute("""
            SELECT sample_id, COUNT(*) 
            FROM sample.work_list_item 
            WHERE is_active_picking = true 
            GROUP BY sample_id 
            HAVING COUNT(*) > 1
        """)
        exclusivity_violations = pg_cur.fetchall()
        if len(exclusivity_violations) == 0:
            print("✓ Exclusivity constraint is valid. No samples are on multiple active picking lists.")
        else:
            print(f"✗ Exclusivity constraint VIOLATED! {len(exclusivity_violations)} samples are double-assigned as active picking.")
            failed = True

        # --- Check 4: Drift Detection View Check ---
        print("\n--- CHECK 4: Drift Detection View Status ---")
        try:
            pg_cur.execute("SELECT COUNT(*) FROM sample.view_work_list_item WHERE is_drifted = true")
            drift_cnt = pg_cur.fetchone()[0]
            print(f"✓ Drift view query succeeded. Number of drifted samples in view: {drift_cnt}")
        except Exception as e:
            print(f"✗ Drift view query failed: {e}")
            failed = True

        # --- Check 5: Parent Work List Mapping ---
        print("\n--- CHECK 5: Parent Work List Mapping ---")
        try:
            db2_parent_stmt = ibm_db.exec_immediate(db2_conn, "SELECT COUNT(*) FROM BIOBANK3.BATCH_LIST WHERE PARENT_ID IS NOT NULL")
            db2_parent_cnt = ibm_db.fetch_both(db2_parent_stmt)[0]
            
            pg_cur.execute("SELECT COUNT(*) FROM sample.work_list WHERE parent_id IS NOT NULL")
            pg_parent_cnt = pg_cur.fetchone()[0]
            
            print(f"DB2 BATCH_LIST with parent: {db2_parent_cnt} | PG work_list with parent: {pg_parent_cnt}")
            if db2_parent_cnt == pg_parent_cnt:
                print("✓ Parent work list mapping counts match.")
                if db2_parent_cnt > 0:
                    # Spot check parent-child relationship by name
                    pg_cur.execute("""
                        SELECT c.name, p.name 
                        FROM sample.work_list c 
                        JOIN sample.work_list p ON c.parent_id = p.id 
                        LIMIT 5
                    """)
                    relations = pg_cur.fetchall()
                    print("Mapped relations spot-check:")
                    for child, parent in relations:
                        print(f"  - {child} derived from {parent}")
            else:
                print("✗ Parent work list mapping counts MISMATCH!")
                failed = True
        except Exception as e:
            print(f"✗ Parent work list validation failed: {e}")
            failed = True

        # --- Check 6: Finished lists have their terminal event (sample-service todo D51) ---
        print("\n--- CHECK 6: Terminal Events of Finished Lists ---")
        pg_cur.execute("""
            SELECT w.name, w.list_status
            FROM sample.work_list w
            WHERE (w.list_status = 'COMPLETED' AND NOT EXISTS (
                       SELECT 1 FROM sample.work_list_event e
                       WHERE e.work_list_id = w.id AND e.event_type IN ('COMPLETED', 'DELIVERED', 'SHIPPED')))
               OR (w.list_status = 'CANCELLED' AND NOT EXISTS (
                       SELECT 1 FROM sample.work_list_event e
                       WHERE e.work_list_id = w.id AND e.event_type = 'CANCELLED'))
        """)
        unfinished = pg_cur.fetchall()
        if not unfinished:
            print("✓ Every completed or cancelled list has its terminal event.")
        else:
            print(f"✗ {len(unfinished)} finished lists have no terminal event: {unfinished}")
            failed = True

        # --- Check 7: Every list belongs to its order (sample-service ADR 0051) ---
        print("\n--- CHECK 7: Work List Task ---")
        pg_cur.execute("""
            SELECT w.name FROM sample.work_list w LEFT JOIN sample.task t ON t.id = w.task_id
            WHERE t.id IS NULL OR t.name <> w.name
        """)
        without_task = pg_cur.fetchall()
        if not without_task:
            print("✓ Every work list has the task loaded from its batch list.")
        else:
            print(f"✗ {len(without_task)} work lists have no matching task: {without_task}")
            failed = True

        # --- Summary ---
        print("\n======================================================================")
        if failed:
            print("VALIDATION STATUS: FAIL")
            print("Please fix the migration anomalies listed above.")
        else:
            print("VALIDATION STATUS: PASS")
            print("All work list migration criteria met successfully.")
        print("======================================================================")
        
    finally:
        pg_cur.close()
        pg_conn.close()
        ibm_db.close(db2_conn)

if __name__ == "__main__":
    run_validation()
