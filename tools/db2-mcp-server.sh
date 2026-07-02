#!/usr/bin/env bash
# Launches mcp-alchemy against the biobank-test DB2 instance.
# Credentials are read from the conf file at runtime - never hardcoded here.
set -euo pipefail

CONF_FILE="${HOME}/.server/biobank-test.conf"
if [ ! -f "$CONF_FILE" ]; then
    echo "error: credentials file not found at $CONF_FILE" >&2
    exit 1
fi

set -a
# shellcheck source=/dev/null
source "$CONF_FILE"
set +a

DB2_HOST="${DB2_HOST:-localhost}"
DB2_PORT="${DB2_PORT:-50000}"
DB2_DATABASE="${DB2_DATABASE:-BCDEMO}"

# Fail fast and loudly if DB2 isn't reachable, instead of hanging or dying
# deep inside a driver traceback that the calling MCP client can't surface well.
if ! (exec 3<>"/dev/tcp/${DB2_HOST}/${DB2_PORT}") 2>/dev/null; then
    echo "error: cannot reach DB2 at ${DB2_HOST}:${DB2_PORT} - is the tunnel/VPN/service up?" >&2
    exit 1
fi
exec 3<&- 3>&-

export DB_URL="ibm_db_sa://${authid}:${password}@${DB2_HOST}:${DB2_PORT}/${DB2_DATABASE}"
# mcp-alchemy defaults to isolation_level=AUTOCOMMIT, which ibm_db_sa doesn't support.
# Use DB2's standard read isolation level instead.
export DB_ENGINE_OPTIONS='{"isolation_level": "CS"}'

exec uvx --with ibm_db_sa --with ibm_db mcp-alchemy
