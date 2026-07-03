# Migration Design Analysis: File-Based vs. Direct Direct ETL

> [!IMPORTANT]
> This document contains legacy design references to a custom Java 'loader' application. The project has migrated to a generic, script-based ETL model using `exporter2026`, `importer2026`, and JS/SpEL manifests. Refer to [LLM_MIGRATION_RUNBOOK.md](file:///Users/muilu/git/others/sample-service-migration/LLM_MIGRATION_RUNBOOK.md) for the active design and execution playbook.

This document explains the rationale behind the file-based migration design (DB2 → CSV → Postgres) and evaluates its alignment with industry best practices for database migrations.

---

## 1. The Chosen Approach
The migration uses a **File-Based intermediate stage (CSV)**:
1. **Export**: `exporter2026` extracts DB2 data into raw, schema-mapped CSV files.
2. **Load**: The `loader` Java application reads, validates, transforms, and loads these CSVs into PostgreSQL.

---

## 2. Rationale & Best Practices Evaluation

Yes, this approach aligns with industry best practices for **offline/non-realtime system migrations**. Below is an analysis comparing this approach to direct database-to-database streaming.

### A. Security & Decoupling (Best Practice: Minimizing DB Access)
* **File-Based**: The live DB2 source and the target Postgres database never need to be connected to the same network or host. This is a critical security practice when migrating across different infrastructure zones (e.g., legacy on-prem DB2 to cloud-hosted Postgres).
* **Direct ETL**: A direct migration requires open network paths between both databases concurrently, increasing security vulnerability risks.

### B. Reproducibility & Testing (Best Practice: Repeatable Trials)
* **File-Based**: The exported CSVs represent a **frozen snapshot** of the source data. The migration team can run the loader app, identify a bug (e.g., unmapped status value), fix the code, clear the target schema, and run it again using the exact same source dataset.
* **Direct ETL**: Repeatedly querying the source DB2 database for trial migrations adds unnecessary load, risk of network timeouts, and variable data if the source is active.

### C. Validation & Audit Trail (Best Practice: Immutable Source of Truth)
* **File-Based**: CSV files can be statically analyzed before being loaded. We can compute checksums, verify row counts, and check encoding (UTF-8). The CSV files act as a physical audit trail verifying the data was not modified.
* **Direct ETL**: If a count mismatch occurs in direct streaming, it is much harder to determine whether the issue occurred during extraction, transit, transformation, or insertion.

### D. Component Reuse (Best Practice: Don't Reinvent the Wheel)
* Reusing the organization's existing, tested `exporter2026` tool drastically minimizes the chance of extraction bugs. Writing custom DB2 extraction scripts would require duplicating metadata mapping logic and testing it from scratch.

---

## 3. Potential Drawbacks & Mitigations

While the file-based approach is highly recommended, we must manage the following factors:

| Risk | Mitigation |
| :--- | :--- |
| **Large Disk Storage Requirements** | Ensure the migration host has sufficient temporary disk space to hold the uncompressed CSV files (specifically for the larger `sample` dataset). |
| **File I/O Overhead** | Use buffered readers (`CsvStreamReader`) and batch inserts in the loader app to ensure disk I/O does not become the bottleneck. |
| **Sensitive Data Exposure** | CSV files are stored as plain text. Ensure the extraction directory has restrictive file system permissions (`chmod 600`) and that files are securely wiped after validation. |
