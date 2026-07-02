# Tool Integration Guide

This document provides guidance on how and why to use the specific tools included in this project.

## `graphify` (Source Code Analysis)

- **Purpose**: `graphify` is a knowledge-graph tool (CLI `graphify`, PyPI package `graphifyy`) that turns the codebase into a queryable graph of nodes/edges. We use it to understand the relationships between the main `loader` application and the sibling Gradle projects (`importer2026`, `exporter2026`, `sample-service`).
- **Configuration**: There is no YAML config for this tool — `graphify.yml` in the project root is stale and unused; the CLI has no config-file mechanism. Source roots are passed as CLI arguments instead. `.graphifyignore` (excludes `target/`, `build/`, `.git/`, `node_modules/`, `graphify-out/`) is real and does apply.
- **Usage**:
  ```bash
  make build-graph            # extracts all 4 source roots and merges them into graphify-out/graph.json
  make start-graphify-server  # runs build-graph, then starts the MCP stdio server on the merged graph
  ```
  `build-graph` extracts `loader/src/main/java` plus the three sibling repos into scratch dirs under `/tmp/graphify-merge`, merges them with `graphify merge-graphs`, then runs `graphify cluster-only` to (re)generate `graphify-out/graph.json`, `GRAPH_REPORT.md`, and `graph.html`. There is no `graphify build`/`graphify server` command — those don't exist in this CLI version.
  - AST extraction only understands the code languages graphify's tree-sitter grammars support. It does **not** parse SQL DDL, so static schema dump files would extract 0 nodes via AST. We're not going that route for DB2 schema knowledge anyway — see the live MCP server below, which introspects the schema dynamically instead of relying on a static DDL export.
  - MCP access to the graph is already configured in Claude Desktop (`~/Library/Application Support/Claude/claude_desktop_config.json`, server `graphify-sample-service-migration`), pointing at `graphify-out/graph.json` via `python3 -m graphify.serve`.

## DB2 live-schema MCP server (`db2-biobank-test`)

- **Purpose**: separate from the static `graphify` graph — this gives AI tools a *live* connection to the biobank-test DB2 instance for ad-hoc schema/data queries, via [`mcp-alchemy`](https://github.com/runekaagaard/mcp-alchemy) (SQLAlchemy-based) over the `ibm_db_sa` dialect.
- **Launcher**: `tools/db2-mcp-server.sh`
  - Reads `authid`/`password` from `~/.server/biobank-test.conf` at runtime — never hardcoded.
  - Connects to `localhost:50000`, database `BCDEMO` (override via `DB2_HOST`/`DB2_PORT`/`DB2_DATABASE` env vars).
  - Sets `DB_ENGINE_OPTIONS='{"isolation_level": "CS"}'` because mcp-alchemy's default `AUTOCOMMIT` isolation level isn't valid for `ibm_db_sa`.
  - Does a TCP pre-flight check before doing anything else; if DB2 isn't reachable it prints `error: cannot reach DB2 at <host>:<port> - is the tunnel/VPN/service up?` and exits 1, instead of hanging or surfacing a raw driver traceback.
  - Runs the server itself via `uvx --with ibm_db_sa --with ibm_db mcp-alchemy` (versions unpinned — pin with `--with mcp-alchemy==<version>` etc. if reproducibility matters later).
- **Wired into**:
  - **Claude Code**: `.mcp.json` (project scope, checked into the repo).
  - **Copilot CLI**: `~/.copilot/mcp-config.json` (user-level), also auto-discovered from `.mcp.json`.
  - **Antigravity**: `~/.gemini/config/mcp_config.json` — schema used is the standard Gemini-family `mcpServers` format, but **unverified**: there's no `antigravity mcp` subcommand to confirm it, and the file was empty with no reference example. Check this is actually being picked up after restarting Antigravity.
