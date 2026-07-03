.PHONY: help plan validate-source extract-data transform-data load-target verify clean check-ai-rules build-graph start-graphify-server

help:
	@echo "sample-service-migration Makefile targets:"
	@echo ""
	@echo "  make plan                   Review migration strategy and schema mapping"
	@echo "  make validate-source        Check DB2 source data integrity"
	@echo "  make extract-data           Export data from DB2"
	@echo "  make transform-data         Convert and prepare data for Postgres"
	@echo "  make load-target            Load data into Postgres"
	@echo "  make verify                 Compare source and target data"
	@echo "  make clean                  Remove extracted/transformed data files"
	@echo "  make check-ai-rules         Run sanity checks for common AI errors"
	@echo "  make build-graph            Build the merged Graphify knowledge graph (loader + importer2026 + exporter2026 + sample-service)"
	@echo "  make start-graphify-server  Build the graph and start the Graphify MCP server"
	@echo ""

plan:
	@echo "Migration planning:"
	@echo "  1. Review docs/schema-mapping.md (DB2 → Postgres mapping)"
	@echo "  2. Review docs/migration-strategy.md (full playbook)"
	@echo "  3. Review docs/data-requirements.md (transformations & validation)"
	@echo ""

validate-source:
	@echo "Validating DB2 source..."
	@echo "TODO: Run DB2 integrity checks (scripts/validation/)"

extract-data:
	@echo "Extracting data from DB2..."
	@echo "TODO: Run DB2 extraction scripts (scripts/db2/)"

transform-data:
	@echo "Transforming data for Postgres..."
	@../../exporter2026/gradlew -p loader build
	@echo "Transformation logic is part of the loader build/process."

load-target:
	@echo "Loading data into Postgres..."
	@../../exporter2026/gradlew -p loader bootRun

verify:
	@echo "Verifying source ↔ target data..."
	@echo "TODO: Run validation scripts (scripts/validation/)"

check-ai-rules:
	@echo "Running AI sanity checks..."
	@echo "  - Checking for unpinned dependencies..."
	@echo "  - Checking for missing test files..."
	@echo "TODO: Implement more sophisticated checks."

build-graph:
	@echo "Building Graphify knowledge graph from all source roots..."
	@rm -rf /tmp/graphify-merge
	@mkdir -p /tmp/graphify-merge
	@graphify extract loader/src/main/java --out /tmp/graphify-merge/loader
	@graphify extract ../../importer2026/src/main/java --out /tmp/graphify-merge/importer2026
	@graphify extract ../../exporter2026/src/main/java --out /tmp/graphify-merge/exporter2026
	@graphify extract ../sample-service/src/main/java --out /tmp/graphify-merge/sample-service
	@graphify merge-graphs \
		/tmp/graphify-merge/loader/graphify-out/graph.json \
		/tmp/graphify-merge/importer2026/graphify-out/graph.json \
		/tmp/graphify-merge/exporter2026/graphify-out/graph.json \
		/tmp/graphify-merge/sample-service/graphify-out/graph.json \
		--out graphify-out/graph.json
	@graphify cluster-only .
	@rm -rf /tmp/graphify-merge

start-graphify-server: build-graph
	@echo "Launching Graphify MCP server. Press Ctrl+C to stop."
	@.venv/bin/python3 -m graphify.serve graphify-out/graph.json


clean:
	@echo "Removing extracted/transformed data files..."
	@find . -name "*.csv" -o -name "*.sql.bak" -o -name "*.tmp" | xargs rm -f
	@echo "Cleaned."
