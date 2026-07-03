# Migration Strategy: DB2 → PostgreSQL

High-level plan for migrating the biobank sample database from DB2 to PostgreSQL.

## Phase 1 — Preparation (Before cutover)

### 1.1 Schema analysis & validation
- [ ] Document full DB2 schema (tables, columns, constraints, sequences)
- [ ] Map to Postgres schema (see `schema-mapping.md`)
- [ ] Identify transformations needed (data type changes, normalization, etc.)
- [ ] Validate all data is mappable without loss

### 1.2 Extract sample data
- [ ] Extract 1–5% of data from DB2 (representative sample by date range)
- [ ] Transform sample data to Postgres format
- [ ] Load into staging Postgres instance
- [ ] Run validation checks (row counts, checksums, data spot-checks)
- [ ] Iterate on transformation logic until sample validates

### 1.3 Build extraction/load scripts
- [ ] DB2 extraction scripts (SQL, bulk unload, or ODBC dumps)
- [ ] Data transformation manifests and JavaScript/SpEL scripts (stored in `config/`)
- [ ] Generic `importer2026` load configurations and schemas
- [ ] Validation queries (compare source/target row counts, checksums, sample rows)
- [ ] Rollback procedures (documented, tested)

### 1.4 Test full extraction & load
- [ ] Run full extraction against full DB2 database
- [ ] Run full transformation
- [ ] Load into second staging Postgres instance (separate from sample validation)
- [ ] Run full validation (all tables, all rows)
- [ ] Document any data issues found and resolutions

## Phase 2 — Cutover (Migration day)

### 2.1 Pre-cutover
- [ ] Backup DB2 database
- [ ] Backup existing Postgres production database (if any)
- [ ] Notify stakeholders of maintenance window
- [ ] Freeze writes to DB2 (read-only mode or application shutdown)

### 2.2 Execute migration
- [ ] Extract all data from DB2
- [ ] Transform data
- [ ] Load into target Postgres database
- [ ] Run validation queries
- [ ] Verify audit triggers are installed and working (insert test row, check `*_audit` table)

### 2.3 Verify & smoke test
- [ ] Check row counts for all tables
- [ ] Spot-check data integrity (sample rows, business rules)
- [ ] Verify no corruption, orphaned FKs, or constraint violations
- [ ] Confirm Postgres audit/version triggers are capturing changes
- [ ] Test read-only on sample-service against new Postgres DB

### 2.4 Cutover application
- [ ] Point sample-service to new Postgres database
- [ ] Run smoke tests against live application
- [ ] Monitor error logs and metrics

### 2.5 Post-cutover
- [ ] Keep DB2 online in read-only mode for N days (fallback)
- [ ] Decommission DB2 database after verification window closes

## Phase 3 — Validation & wrap-up (After cutover)

### 3.1 Extended validation
- [ ] Monitor sample-service for errors (logs, metrics, alerts)
- [ ] Verify audit trail is capturing all writes correctly
- [ ] Spot-check data with sample-service queries
- [ ] Check optimistic locking behavior (test concurrent updates)

### 3.2 Cleanup
- [ ] Decommission DB2
- [ ] Clean up staging Postgres instances
- [ ] Document final migration report (timing, issues, resolutions)

## Timeline estimate

- **Preparation**: 1–2 weeks (depends on schema complexity and data size)
- **Cutover**: 2–4 hours (downtime)
- **Validation**: 1 week (post-cutover monitoring)
- **Total**: 3–4 weeks

## Risk & rollback

**Worst-case rollback**: Keep DB2 online in read-only mode for 1 week post-cutover. If critical data loss is discovered, can switch sample-service back to DB2 and re-plan.

**Mitigation**: Thorough validation at each phase, including full-database load test before cutover.

## Next steps

1. Review schema mapping (`schema-mapping.md`)
2. Finalize data requirements (`data-requirements.md`)
3. Extract data from DB2 using `exporter2026` (see `export/tables.md`)
4. Apply transformations via project-specific JS/SpEL scripts and load data into Postgres using the generic `importer2026` tool (see `config/`)
5. Run validation queries (compare source/target)
6. Run Phase 1 testing against staging Postgres
7. Schedule cutover window
