import csv
import ibm_db

# Connection configuration
dsn = "DATABASE=BCDEMO;HOSTNAME=localhost;PORT=50000;PROTOCOL=TCPIP;UID=db2inst1;PWD=Adm1Pwd1;"

sql_query = """
SELECT 
    b.NAME,
    b.BEGIN_TIME,
    b.END_TIME,
    p.ABBREVIATION AS PROJECT_ABBREVIATION,
    b.BATCH_STATUS,
    b.COMMENT,
    b.TIMELOG,
    b.ISPICK,
    b.USERNAME
FROM BIOBANK3.BATCH_LIST b
LEFT JOIN BCPROJECT.PROJECT p ON b.PROJECT_ID = p.ID
ORDER BY b.ID
"""

print("Connecting to DB2 database...")
conn = ibm_db.connect(dsn, "", "")

try:
    print("Executing batch list export query...")
    stmt = ibm_db.exec_immediate(conn, sql_query)
    
    output_path = "export/batch_list.csv"
    print(f"Writing output to {output_path}...")
    
    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        # Write headers matching work_list_manifest and task_manifest requirements
        writer.writerow([
            "NAME", "BEGIN_TIME", "PROJECT_ABBREVIATION", 
            "BATCH_STATUS", "COMMENT", "ISPICK", "PARTNER_NAME", "USERNAME"
        ])
        
        row_count = 0
        row = ibm_db.fetch_assoc(stmt)
        while row:
            row_upper = {k.upper(): v for k, v in row.items()}
            
            name = row_upper.get("NAME")
            begin_time = row_upper.get("BEGIN_TIME")
            project_abbrev = row_upper.get("PROJECT_ABBREVIATION")
            batch_status = row_upper.get("BATCH_STATUS")
            comment = row_upper.get("COMMENT")
            ispick = row_upper.get("ISPICK")
            username = row_upper.get("USERNAME")
            
            if name: name = name.strip()
            if project_abbrev: project_abbrev = project_abbrev.strip()
            if batch_status: batch_status = batch_status.strip()
            if comment: comment = comment.strip()
            if ispick: ispick = ispick.strip()
            if username: username = username.strip()
            
            # Since partner_id in batch_list is always null in DB2, partner_name is empty.
            # The JS transform transforms empty string to 'Missing Partner' which resolves correctly.
            partner_name = ""
                
            writer.writerow([
                name, begin_time, project_abbrev,
                batch_status, comment, ispick, partner_name, username
            ])
            row_count += 1
            row = ibm_db.fetch_assoc(stmt)
            
    print(f"✓ Exported {row_count} batch lists successfully.")

finally:
    ibm_db.close(conn)
