# AI Cookbook

This document provides step-by-step "recipes" for common tasks that AI assistants can perform on this project.

## Recipe: Add a New Validation Script

1. **Create a new Python file**: In the `scripts/validation/` directory, create a new Python file with a descriptive name (e.g., `check_sample_counts.py`).
2. **Add dependencies**: If your script requires any new Python packages, add them to the `pyproject.toml` file, making sure to pin the version.
3. **Write the script**: Your script should connect to the PostgreSQL database, perform the validation, and print a clear "PASS" or "FAIL" message.
4. **Add a Makefile target**: In the `Makefile`, add a new target to run your script (e.g., `validate-sample-counts`).
5. **Update the README**: Add your new validation script to the list of available checks in the `README.md`.

## Recipe: Run a Full Migration

To run a full data migration from DB2 to PostgreSQL, follow these steps:

1. **Extract data from DB2**:
   ```bash
   make extract-data
   ```
2. **Load data into Postgres**:
   ```bash
   make load-target
   ```
3. **Verify the migration**:
   ```bash
   make verify
   ```

## Recipe: Ask Architectural Questions using the Code Graph

1. **Generate/refresh the code graph**:
   ```bash
   make build-graph
   ```
   This writes `graphify-out/graph.json`, `GRAPH_REPORT.md`, and `graph.html`, merged from `loader`, `importer2026`, `exporter2026`, and `sample-service`.

2. **Ask directly** — no manual copy/paste needed. The graph is already exposed as an MCP server (`graphify-sample-service-migration`) in Claude Desktop. Just ask your question:
   > "What are the dependencies of the `LoaderApplication` class?"

   Or query it from the terminal without an assistant in the loop:
   ```bash
   graphify query "LoaderApplication dependencies"
   graphify explain "LoaderApplication"
   ```

See `docs/tool-integration.md` for the full graphify setup and its current limitations (e.g. SQL schema files aren't semantically extracted yet).

## Recipe: Query the Live DB2 Schema

For questions about the *current* DB2 schema/data (not the static graph), use the `db2-biobank-test` MCP server — wired into Claude Code, Copilot CLI, and Antigravity (see `docs/tool-integration.md`). Just ask your question naturally, e.g.:

> "What columns does the CORE.PATIENT table have in the biobank-test DB2 database?"

If DB2 isn't reachable, the server fails fast with a clear error rather than hanging.
