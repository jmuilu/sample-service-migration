import csv
import ibm_db

# Connection configuration
dsn = "DATABASE=BCDEMO;HOSTNAME=localhost;PORT=50000;PROTOCOL=TCPIP;UID=db2inst1;PWD=Adm1Pwd1;"

sql_query = """
WITH created_events AS (
    SELECT
        b.ID                              AS batch_id,
        b.NAME                            AS batch_name,
        b.ISPICK                          AS ispick,
        'CREATED'                         AS event_type,
        CAST(NULL AS VARCHAR(40))         AS from_status,
        CASE
            WHEN EXISTS (
                SELECT 1 FROM BIOBANK3.BATCH_LIST_AUDIT a2
                WHERE a2.ID = b.ID AND a2.BC_SYS_OPER = 'U'
            )
            THEN (
                SELECT a3.BATCH_STATUS
                FROM BIOBANK3.BATCH_LIST_AUDIT a3
                WHERE a3.ID = b.ID AND a3.BC_SYS_OPER = 'U'
                ORDER BY a3.BC_SYS_MODIFIED ASC
                FETCH FIRST 1 ROW ONLY
            )
            ELSE b.BATCH_STATUS
        END                               AS to_status,
        b.BEGIN_TIME                      AS event_time,
        b.USERNAME                        AS event_user,
        b.PROJECT_ID                      AS project_id,
        b.COMMENT                         AS event_comment
    FROM BIOBANK3.BATCH_LIST b
),
status_changes AS (
    SELECT
        a.ID                              AS batch_id,
        b.NAME                            AS batch_name,
        b.ISPICK                          AS ispick,
        b.PROJECT_ID                      AS project_id,
        a.BATCH_STATUS                    AS from_status,
        COALESCE(
            LEAD(a.BATCH_STATUS) OVER (
                PARTITION BY a.ID ORDER BY a.BC_SYS_MODIFIED ASC
            ),
            b.BATCH_STATUS
        )                                 AS to_status,
        a.BC_SYS_MODIFIED                 AS event_time,
        a.BC_SYS_MODIFIED_BY              AS event_user,
        a.COMMENT                         AS event_comment
    FROM BIOBANK3.BATCH_LIST_AUDIT a
    JOIN BIOBANK3.BATCH_LIST b ON a.ID = b.ID
    WHERE a.BC_SYS_OPER = 'U'
),
all_events AS (
    SELECT batch_id, batch_name, ispick, event_type,
           from_status, to_status, event_time, event_user, project_id, event_comment
    FROM created_events

    UNION ALL

    SELECT batch_id, batch_name, ispick,
        CASE
            WHEN to_status = 'PICKING_IN_PROGRESS'           THEN 'ACTIVATED'
            WHEN to_status = 'PICKING_COMPLETED'              THEN 'COMPLETED'
            WHEN to_status = 'SAMPLES_AVAILABLE_FOR_DELIVERY' THEN 'COMPLETED'
            WHEN to_status = 'SAMPLES_DELIVERED'              THEN 'DELIVERED'
            WHEN to_status = 'DATA_FOR_SAMPLES_RECEIVED'      THEN 'COMPLETED'
            WHEN to_status = 'BATCH_RECEIVED'                 THEN 'COMPLETED'
            WHEN to_status = 'READY_FOR_PICKING'              THEN 'CREATED'
            ELSE 'ACTIVATED'
        END AS event_type,
        from_status, to_status, event_time, event_user, project_id, event_comment
    FROM status_changes
    WHERE from_status <> to_status
)
SELECT batch_id, batch_name, ispick, event_type, from_status, to_status, event_time, event_user, project_id, event_comment
FROM all_events
ORDER BY batch_id, event_time
"""

print("Connecting to DB2 database...")
conn = ibm_db.connect(dsn, "", "")

try:
    print("Executing event reconstruction query...")
    stmt = ibm_db.exec_immediate(conn, sql_query)
    
    output_path = "export/work_list_event.csv"
    print(f"Writing output to {output_path}...")
    
    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        # Write headers
        writer.writerow([
            "BATCH_ID", "BATCH_NAME", "ISPICK", "EVENT_TYPE", 
            "FROM_STATUS", "TO_STATUS", "EVENT_TIME", "EVENT_USER", 
            "PROJECT_ID", "EVENT_COMMENT"
        ])
        
        row_count = 0
        row = ibm_db.fetch_assoc(stmt)
        while row:
            # Clean spaces from char fields (like USERNAME which might have padding)
            event_user = row["BATCH_NAME"]  # Wait, check keys returned by fetch_assoc (usually uppercase or matching SELECT)
            # Standard ibm_db fetch_assoc keys are uppercase or matching column name depending on driver
            # Let's inspect the row keys on first iteration
            if row_count == 0:
                print("Keys returned by DB2 query:", list(row.keys()))
            
            # Map keys case-insensitively
            row_upper = {k.upper(): v for k, v in row.items()}
            
            batch_id = row_upper.get("BATCH_ID")
            batch_name = row_upper.get("BATCH_NAME")
            ispick = row_upper.get("ISPICK")
            event_type = row_upper.get("EVENT_TYPE")
            from_status = row_upper.get("FROM_STATUS")
            to_status = row_upper.get("TO_STATUS")
            event_time = row_upper.get("EVENT_TIME")
            event_user = row_upper.get("EVENT_USER")
            project_id = row_upper.get("PROJECT_ID")
            event_comment = row_upper.get("EVENT_COMMENT")
            
            if batch_name:
                batch_name = batch_name.strip()
            if event_user:
                event_user = event_user.strip()
            if event_comment:
                event_comment = event_comment.strip()
                
            writer.writerow([
                batch_id, batch_name, ispick, event_type,
                from_status, to_status, event_time, event_user,
                project_id, event_comment
            ])
            row_count += 1
            row = ibm_db.fetch_assoc(stmt)
            
    print(f"✓ Exported {row_count} events successfully.")

finally:
    ibm_db.close(conn)
