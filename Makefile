.PHONY: help plan validate-source extract-data transform-data load-target verify clean

help:
	@echo "sample-service-migration Makefile targets:"
	@echo ""
	@echo "  make plan               Review migration strategy and schema mapping"
	@echo "  make validate-source    Check DB2 source data integrity"
	@echo "  make extract-data       Export data from DB2"
	@echo "  make transform-data     Convert and prepare data for Postgres"
	@echo "  make load-target        Load data into Postgres"
	@echo "  make verify             Compare source and target data"
	@echo "  make clean              Remove extracted/transformed data files"
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

clean:
	@echo "Removing extracted/transformed data files..."
	@find . -name "*.csv" -o -name "*.sql.bak" -o -name "*.tmp" | xargs rm -f
	@echo "Cleaned."
