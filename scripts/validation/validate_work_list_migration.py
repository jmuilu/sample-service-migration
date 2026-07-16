import sys
import ibm_db
import psycopg2

db2_dsn = "DATABASE=BCDEMO;HOSTNAME=localhost;PORT=50000;PROTOCOL=TCPIP;UID=db2inst1;PWD=Adm1Pwd1;"
pg_conn_str = "host='localhost' port=5432 dbname='sample' user='sample' password='sample'"

def run_validation():
    print("======================================================================")
    print("WORK LIST MIGRATION VALIDATION RUNNER")
    print("======================================================================")
    
    # 1. Connect to both databases
    try:
        print("Connecting to DB2...")
        db2_conn = ibm_db.connect(db2_dsn, "", "")
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
        
        print(f"Expected DB2 events (reconstructed): {db2_event_cnt} | PG work_list_event: {pg_event_cnt}")
        if db2_event_cnt == pg_event_cnt:
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
            pg_cur.execute("SELECT COUNT(*) FROM sample.view_work_list_items WHERE is_drifted = true")
            drift_cnt = pg_cur.fetchone()[0]
            print(f"✓ Drift view query succeeded. Number of drifted samples in view: {drift_cnt}")
        except Exception as e:
            print(f"✗ Drift view query failed: {e}")
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
