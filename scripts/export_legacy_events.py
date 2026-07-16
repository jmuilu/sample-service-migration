import csv
import ibm_db

# Connection configuration
dsn = "DATABASE=BCDEMO;HOSTNAME=localhost;PORT=50000;PROTOCOL=TCPIP;UID=db2inst1;PWD=Adm1Pwd1;"

sql_query = """
SELECT 
    e.ID,
    s.SAMPLEID,
    e.EVENT_TYPE,
    e.START_TIME,
    e.TEMPERATURE,
    e.CHANGE_REASON,
    e.COMMENT,
    e.USERNAME
FROM BIOBANK3.EVENT e
JOIN BIOBANK3.SAMPLE_10002 s ON e.MASTER_ID = s.ID
ORDER BY e.ID
"""

print("Connecting to DB2 database...")
conn = ibm_db.connect(dsn, "", "")

try:
    print("Executing legacy events export query...")
    stmt = ibm_db.exec_immediate(conn, sql_query)
    
    output_path = "export/legacy_event.csv"
    print(f"Writing output to {output_path}...")
    
    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        # Write headers
        writer.writerow([
            "ID", "SAMPLEID", "EVENT_TYPE", "EVENT_TIME", 
            "TEMPERATURE", "EVENT_REASON", "COMMENT", "USERNAME", "TASK_NAME"
        ])
        
        row_count = 0
        row = ibm_db.fetch_assoc(stmt)
        while row:
            row_upper = {k.upper(): v for k, v in row.items()}
            
            id_val = row_upper.get("ID")
            sampleid = row_upper.get("SAMPLEID")
            event_type = row_upper.get("EVENT_TYPE")
            start_time = row_upper.get("START_TIME")
            temperature = row_upper.get("TEMPERATURE")
            change_reason = row_upper.get("CHANGE_REASON")
            comment = row_upper.get("COMMENT")
            username = row_upper.get("USERNAME")
            
            if sampleid: sampleid = sampleid.strip()
            if event_type: event_type = event_type.strip()
            if comment: comment = comment.strip()
            if username: username = username.strip()
            
            # Map change reason to cv_event_reason terms
            event_reason = 'NA'
            if change_reason:
                cr_str = change_reason.strip()
                if cr_str == "parent - aliquot inheritance":
                    event_reason = 'ALIQUOT_INHERITANCE'
                elif cr_str != "" and cr_str.upper() != "NULL":
                    event_reason = cr_str
            
            # Clean start time timestamp format
            event_time = start_time
            if event_time:
                event_time = str(event_time).replace('T', ' ').strip()
                if '.' in event_time:
                    event_time = event_time.split('.')[0]
            
            # Always route to SYSTEM-DEFAULT task
            task_name = 'SYSTEM-DEFAULT'
            
            writer.writerow([
                id_val, sampleid, event_type, event_time,
                temperature, event_reason, comment, username, task_name
            ])
            row_count += 1
            row = ibm_db.fetch_assoc(stmt)
            
    print(f"✓ Exported {row_count} legacy events successfully.")

finally:
    ibm_db.close(conn)
