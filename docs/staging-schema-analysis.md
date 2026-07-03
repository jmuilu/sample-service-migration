# Migration Design Analysis: Staging Schema vs. Application-Based ETL

> [!IMPORTANT]
> This document contains legacy design references to a custom Java 'loader' application. The project has migrated to a generic, script-based ETL model using `exporter2026`, `importer2026`, and JS/SpEL manifests. Refer to [LLM_MIGRATION_RUNBOOK.md](file:///Users/muilu/git/others/sample-service-migration/LLM_MIGRATION_RUNBOOK.md) for the active design and execution playbook.

This document analyzes whether it makes sense to copy the source DB2 database directly into a staging schema within PostgreSQL and perform the migration transformations entirely in-database (ELT/SQL), compared to using the custom Java loader application.

---

## 1. Staging Schema (In-Database ELT) Overview
In this approach:
1. **Extract/Load (as-is)**: The source DB2 tables are replicated directly into a temporary staging schema (e.g., `stage_db2`) in the target PostgreSQL instance.
2. **Transform (SQL)**: SQL scripts, CTEs, and views are used to transform, clean, and insert the data from the staging schema to the final `sample` schema.

---

## 2. Comparative Analysis

| Dimension | Application-Based Loader (Current Design) | Staging Schema (In-Database ELT) |
| :--- | :--- | :--- |
| **Performance** | Good for M1+M2. Can be slower on massive datasets (millions of rows) due to row-by-row Java/Spring batch overhead. | **Excellent**. The database performs bulk joins and inserts natively in-memory (C-level), bypassing JDBC roundtrips. |
| **Logic & Testing** | **Excellent**. Business rules (enum mapping, abbreviation normalization, parent-child depth sorting) are written in Java with full support for unit/integration tests (Testcontainers). | **Complex**. Complex conditional logic and recursive lookups require writing database-specific SQL, stored procedures, or `PL/pgSQL` functions, which are harder to unit test. |
| **Existing Code Reuse** | **Excellent**. Reuses the organization's existing, tested components (`exporter2026` and `importer2026`) via a composite Gradle build. | **None**. Replaces Java code with SQL scripts, requiring all extraction and transformation logic to be rewritten from scratch in Postgres dialect. |
| **Cross-Database Dialect Issues**| **Minimal**. The Java app bridges the gap between DB2 dialect and Postgres. | **Significant**. DB2 data types (e.g., CLOBs, specific timestamp formats, system audit columns) must be mapped to Postgres counterparts during staging schema creation. |

---

## 3. Does it make sense for this project?

### Why it is NOT recommended for this migration:
1. **Heavy Reuse of Tested Java Components**: Since the org already has `exporter2026` and `importer2026` complete and tested, throwing them away to write custom PL/pgSQL scripts adds new development risk and code churn.
2. **Complex Self-Referential Tree Resolution**: Both the `container` and `sample` tables have hierarchical, self-referential relationships (containers inside containers, aliquots inside samples). Resolving these hierarchy depths dynamically in SQL is complex (requiring recursive CTEs/recursive queries), whereas it is straightforward to handle in Java loops or staging passes.
3. **Data Size**: The database statistics show ~800,000 participant records, but the sample service schema is restricted to 4 tables (M1+M2). The active sample count is small enough to be easily processed in batches by the Java `loader` without performance bottlenecks.

### When it WOULD make sense:
- If the dataset grows to tens of millions of rows, where JDBC batch inserts become a severe bottleneck.
- If the target Java codebase was not already written or composite build dependencies were unavailable.
- If you wanted to decommission the Java loader entirely and manage the migration solely via database administration scripts.
