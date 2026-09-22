# DB2 MCP server (biobank-test)

`~/bin/mcp-db2.sh` launches [mcp-alchemy](https://github.com/runekaagaard/mcp-alchemy) against the
`biobank-test` DB2 instance (database `BCDEMO`), giving Claude Code SQL/schema tools for that
database. Credentials are read at runtime from `~/.server/centox-dbowner.conf` — never hardcoded.

Both `mcp-db2.sh` and its setup script live in `~/bin` (not in this repo) since they're personal,
cross-project utilities rather than project-specific tooling.

## Setup

Registered once at Claude Code **user scope**, so it's available in every project on this machine
(no per-project `.mcp.json` needed):

```bash
setup-db2-mcp.sh   # lives in ~/bin, idempotent — re-run any time to re-register
```

Verify with `claude mcp list` / `claude mcp get db2-biobank-test` from any project.

## Gotcha: schema-qualify table names

The connection's `CURRENT SCHEMA` is `DB2INST1` (the login user's default schema), which is
**empty**. The actual data lives in other schemas:

- `BIOBANK3` — the main application/sample schema (the source of truth for sample data):
  `CONTAINER`, `BATCH_SAMPLE_LIST`, `BIOBANK_SAMPLE_PROFILE`, `BIOBANK_VIEW_ALL_SAMPLES`,
  `BCMETA_*` (metadata/forms), `CV_*` (code values/lookups), audit tables, etc.
- `BBVIEW` — application-facing views on top of `BIOBANK3`/other schemas: `PARTICIPANT`, `SAMPLE`,
  `SAMPLE_EVENT`, `CONSENT`, `CONTAINER`, `ALIAS`, `BIOBANKID`, `DNA_EXT`, etc.
- `BCAPP` — app config/audit tables: `APP_CONFIG`, `AUDIT_LOG`, `APPLICATION_LOG`, etc.
- `BBLOG` — access/change logs, Liquibase changelog tables.
- `BACKUP` — ad-hoc backup/snapshot tables from past migrations.

Because of this, mcp-alchemy's `all_table_names` tool returns an **empty list** by default (it only
looks in `CURRENT SCHEMA`). Always fully qualify table names in queries, e.g. `BIOBANK3.CONTAINER`
or `BBVIEW.PARTICIPANT`, not bare `CONTAINER`/`PARTICIPANT`.

To list what actually exists, query the catalog directly instead of relying on `all_table_names`:

```sql
SELECT TABSCHEMA, TABNAME
FROM SYSCAT.TABLES
WHERE TABSCHEMA = 'BIOBANK3'   -- or NOT LIKE 'SYS%' to see all app schemas
FETCH FIRST 50 ROWS ONLY
```
