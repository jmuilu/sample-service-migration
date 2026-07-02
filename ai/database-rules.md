# Database Rules

## General

- Never assume DB2 and PostgreSQL types are equivalent.
- Always check schema metadata through MCP before generating SQL.
- Do not generate destructive SQL unless explicitly requested.
- Prefer explicit transactions for migrations.
- Include rollback notes for schema changes.

## DB2

- Check DB2 table and column names from schema-context MCP (`db2-biobank-test` — see `docs/tool-integration.md`; connects live to the biobank-test instance).
- Treat DB2 as source/legacy unless task says otherwise.

## PostgreSQL

- Check indexes and foreign keys before query changes.
- For new queries, consider EXPLAIN plan on dev DB only.
- When adding a new column, always create a new Liquibase changeset.
- All new Python scripts must have corresponding unit tests in the `tests/` directory.
