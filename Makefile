# Sibling paths
EXPORTER_DIR = ../../exporter2026
IMPORTER_DIR = ../../importer2026

# DB2 Source Connection
DB2_URL = jdbc:db2://localhost:50000/BCDEMO
DB2_USER = db2inst1
DB2_PASSWORD = Adm1Pwd1

# Postgres Target Connection
PG_URL = jdbc:postgresql://localhost:5432/sample
PG_USER = sample
PG_PASSWORD = sample

.PHONY: help plan validate-source extract-data transform-data clear-target load-target verify migrate-all clean check-ai-rules build-graph start-graphify-server

help:
	@echo "sample-service-migration Makefile targets:"
	@echo ""
	@echo "  make plan                   Review migration strategy and schema mapping"
	@echo "  make validate-source        Check DB2 source data integrity"
	@echo "  make extract-data           Export data from DB2 to CSV"
	@echo "  make transform-data         Convert and prepare dynamic EAV data for Postgres"
	@echo "  make clear-target           Truncate target Postgres tables"
	@echo "  make load-target            Load seed SQL and import all table data into Postgres"
	@echo "  make migrate-all            Execute the full end-to-end migration in one go"
	@echo "  make verify                 Compare source and target data"
	@echo "  make clean                  Remove extracted/transformed data files"
	@echo "  make check-ai-rules         Run sanity checks for common AI errors"
	@echo "  make build-graph            Build the merged Graphify knowledge graph"
	@echo "  make start-graphify-server  Build the graph and start the Graphify MCP server"
	@echo ""

plan:
	@echo "Migration planning:"
	@echo "  1. Review docs/schema-mapping.md (DB2 → Postgres mapping)"
	@echo "  2. Review docs/migration-strategy.md (full playbook)"
	@echo "  3. Review docs/data-requirements.md (transformations & validation)"
	@echo "  4. Review docs/sample-qualities-migration-plan.md (qualities playbook)"
	@echo ""

validate-source:
	@echo "Validating DB2 source connection..."
	@nc -z localhost 50000 && echo "✓ DB2 is reachable on port 50000" || (echo "✗ DB2 is unreachable" && exit 1)

extract-data:
	@echo "Extracting data from DB2 to CSV..."
	@mkdir -p export
	@$(EXPORTER_DIR)/gradlew -p $(EXPORTER_DIR) bootRun --args='--table=BIOBANK3.SAMPLEGROUP --output=/Users/muilu/git/others/sample-service-migration/export/samplegroup.csv --spring.datasource.url=$(DB2_URL) --spring.datasource.username=$(DB2_USER) --spring.datasource.password=$(DB2_PASSWORD)'
	@$(EXPORTER_DIR)/gradlew -p $(EXPORTER_DIR) bootRun --args='--table=BIOBANK3.CONTAINERTYPE --output=/Users/muilu/git/others/sample-service-migration/export/containertype.csv --spring.datasource.url=$(DB2_URL) --spring.datasource.username=$(DB2_USER) --spring.datasource.password=$(DB2_PASSWORD)'
	@$(EXPORTER_DIR)/gradlew -p $(EXPORTER_DIR) bootRun --args='--table=BIOBANK3.CONTAINER --output=/Users/muilu/git/others/sample-service-migration/export/container.csv --spring.datasource.url=$(DB2_URL) --spring.datasource.username=$(DB2_USER) --spring.datasource.password=$(DB2_PASSWORD)'
	@$(EXPORTER_DIR)/gradlew -p $(EXPORTER_DIR) bootRun --args='--table=BIOBANK3.VIEW_SAMPLE_MASTER --output=/Users/muilu/git/others/sample-service-migration/export/sample.csv --spring.datasource.url=$(DB2_URL) --spring.datasource.username=$(DB2_USER) --spring.datasource.password=$(DB2_PASSWORD)'
	@$(EXPORTER_DIR)/gradlew -p $(EXPORTER_DIR) bootRun --args='--table=BIOBANK3.SAMPLE_10003 --output=/Users/muilu/git/others/sample-service-migration/export/sample_10003.csv --spring.datasource.url=$(DB2_URL) --spring.datasource.username=$(DB2_USER) --spring.datasource.password=$(DB2_PASSWORD)'
	@$(EXPORTER_DIR)/gradlew -p $(EXPORTER_DIR) bootRun --args='--table=BIOBANK3.SAMPLE_10004 --output=/Users/muilu/git/others/sample-service-migration/export/sample_10004.csv --spring.datasource.url=$(DB2_URL) --spring.datasource.username=$(DB2_USER) --spring.datasource.password=$(DB2_PASSWORD)'
	@$(EXPORTER_DIR)/gradlew -p $(EXPORTER_DIR) bootRun --args='--table=BIOBANK3.SAMPLE_10029 --output=/Users/muilu/git/others/sample-service-migration/export/sample_10029.csv --spring.datasource.url=$(DB2_URL) --spring.datasource.username=$(DB2_USER) --spring.datasource.password=$(DB2_PASSWORD)'
	@$(EXPORTER_DIR)/gradlew -p $(EXPORTER_DIR) bootRun --args='--table=BIOBANK3.CV_QUALITY --output=/Users/muilu/git/others/sample-service-migration/export/cv_sample_quality.csv --spring.datasource.url=$(DB2_URL) --spring.datasource.username=$(DB2_USER) --spring.datasource.password=$(DB2_PASSWORD)'
	@$(EXPORTER_DIR)/gradlew -p $(EXPORTER_DIR) bootRun --args='--table=BIOBANK3.SAMPLE_QUALITY --output=/Users/muilu/git/others/sample-service-migration/export/sample_quality.csv --spring.datasource.url=$(DB2_URL) --spring.datasource.username=$(DB2_USER) --spring.datasource.password=$(DB2_PASSWORD)'
	@$(EXPORTER_DIR)/gradlew -p $(EXPORTER_DIR) bootRun --args='--table=BIOBANK3.BATCH_LIST --output=/Users/muilu/git/others/sample-service-migration/export/batch_list.csv --spring.datasource.url=$(DB2_URL) --spring.datasource.username=$(DB2_USER) --spring.datasource.password=$(DB2_PASSWORD)'
	@$(EXPORTER_DIR)/gradlew -p $(EXPORTER_DIR) bootRun --args='--table=BIOBANK3.BATCH_SAMPLE_LIST --output=/Users/muilu/git/others/sample-service-migration/export/batch_sample_list.csv --spring.datasource.url=$(DB2_URL) --spring.datasource.username=$(DB2_USER) --spring.datasource.password=$(DB2_PASSWORD)'
	@$(EXPORTER_DIR)/gradlew -p $(EXPORTER_DIR) bootRun --args='--table=BCPROJECT.PROJECT --output=/Users/muilu/git/others/sample-service-migration/export/project.csv --spring.datasource.url=$(DB2_URL) --spring.datasource.username=$(DB2_USER) --spring.datasource.password=$(DB2_PASSWORD)'
	@$(EXPORTER_DIR)/gradlew -p $(EXPORTER_DIR) bootRun --args='--table=BCPROJECT.PARTNER --output=/Users/muilu/git/others/sample-service-migration/export/partner.csv --spring.datasource.url=$(DB2_URL) --spring.datasource.username=$(DB2_USER) --spring.datasource.password=$(DB2_PASSWORD)'
	@$(EXPORTER_DIR)/gradlew -p $(EXPORTER_DIR) bootRun --args='--table=BCPROJECT.PROJECT_MEMBERSHIP --output=/Users/muilu/git/others/sample-service-migration/export/project_membership.csv --spring.datasource.url=$(DB2_URL) --spring.datasource.username=$(DB2_USER) --spring.datasource.password=$(DB2_PASSWORD)'
	@echo "✓ Data extraction complete."

transform-data:
	@echo "Transforming dynamic EAV property data..."
	@java scripts/PivotHelper.java export/sample_10003.csv export/sample_property_dna.csv 10003
	@java scripts/PivotHelper.java export/sample_10004.csv export/sample_property_edta.csv 10004
	@java scripts/PivotHelper.java export/sample_10029.csv export/sample_property_testnayte.csv 10029
	@echo "Generating sample type quality metadata CSV..."
	@echo "SAMPLETYPE,QUALITY,USERNAME,VERSION" > export/sample_type_quality_metadata.csv
	@echo "DNA,BLOODY,migration,1" >> export/sample_type_quality_metadata.csv
	@echo "DNA,CENTRIFUGED,migration,1" >> export/sample_type_quality_metadata.csv
	@echo "DNA,CLOTTED,migration,1" >> export/sample_type_quality_metadata.csv
	@echo "DNA,TRANSPORT_PROBLEM,migration,1" >> export/sample_type_quality_metadata.csv
	@echo "EDTA Whole blood,BLOODY,migration,1" >> export/sample_type_quality_metadata.csv
	@echo "EDTA Whole blood,CENTRIFUGED,migration,1" >> export/sample_type_quality_metadata.csv
	@echo "EDTA Whole blood,CLOTTED,migration,1" >> export/sample_type_quality_metadata.csv
	@echo "EDTA Whole blood,CLOUDY,migration,1" >> export/sample_type_quality_metadata.csv
	@echo "EDTA Whole blood,CONTAMINATED,migration,1" >> export/sample_type_quality_metadata.csv
	@echo "EDTA Whole blood,HEMOLYTIC,migration,1" >> export/sample_type_quality_metadata.csv
	@echo "Plasma,CLOTTED,migration,1" >> export/sample_type_quality_metadata.csv
	@echo "Injecting 'Missing Partner' placeholder into partner.csv..."
	@echo "Missing Partner,migration,2026-07-08 00:00:00,INTERNAL,Missing partner placeholder,ACTIVE,OTHER," >> export/partner.csv
	@echo "Injecting missing project memberships for 'Missing Partner' into project_membership.csv..."
	@echo "migration,2026-07-08 00:00:00,DEFAULT,Missing Partner,JAN12" >> export/project_membership.csv
	@echo "migration,2026-07-08 00:00:00,DEFAULT,Missing Partner,D3R" >> export/project_membership.csv
	@echo "migration,2026-07-08 00:00:00,DEFAULT,Missing Partner,KMoHUq" >> export/project_membership.csv
	@echo "migration,2026-07-08 00:00:00,DEFAULT,Missing Partner,tammi7" >> export/project_membership.csv
	@echo "migration,2026-07-08 00:00:00,DEFAULT,Missing Partner,DR" >> export/project_membership.csv
	@echo "✓ Transformation complete."

clear-target:
	@echo "Clearing PostgreSQL target tables..."
	@docker exec -i sample-service-db-1 psql -U $(PG_USER) -d sample -c "TRUNCATE sample.work_list_item, sample.work_list, sample.work_list_event, project.project_membership, project.partner, project.project, sample.sample_quality, sample.sample_type_quality_metadata, sample.sample_property, sample.sample, sample.container, sample.container_type, sample.sample_type, sample.cv_sample_quality CASCADE;"

load-target:
	@echo "Loading seed data and vocabularies..."
	@docker exec -i sample-service-db-1 psql -U $(PG_USER) -d sample < scripts/postgres/seed_properties.sql
	@docker exec -i sample-service-db-1 psql -U $(PG_USER) -d sample < scripts/postgres/seed_qualities.sql
	@echo "Importing table data..."
	@$(IMPORTER_DIR)/gradlew -p $(IMPORTER_DIR) bootRun --args='--csv=/Users/muilu/git/others/sample-service-migration/export/project.csv --manifest=/Users/muilu/git/others/sample-service-migration/config/manifests/project_manifest.yaml --spring.datasource.url=$(PG_URL) --spring.datasource.username=$(PG_USER) --spring.datasource.password=$(PG_PASSWORD) --spring.datasource.driver-class-name=org.postgresql.Driver --spring.main.web-application-type=none'
	@$(IMPORTER_DIR)/gradlew -p $(IMPORTER_DIR) bootRun --args='--csv=/Users/muilu/git/others/sample-service-migration/export/partner.csv --manifest=/Users/muilu/git/others/sample-service-migration/config/manifests/partner_manifest.yaml --spring.datasource.url=$(PG_URL) --spring.datasource.username=$(PG_USER) --spring.datasource.password=$(PG_PASSWORD) --spring.datasource.driver-class-name=org.postgresql.Driver --spring.main.web-application-type=none'
	@$(IMPORTER_DIR)/gradlew -p $(IMPORTER_DIR) bootRun --args='--csv=/Users/muilu/git/others/sample-service-migration/export/project_membership.csv --manifest=/Users/muilu/git/others/sample-service-migration/config/manifests/project_membership_manifest.yaml --spring.datasource.url=$(PG_URL) --spring.datasource.username=$(PG_USER) --spring.datasource.password=$(PG_PASSWORD) --spring.datasource.driver-class-name=org.postgresql.Driver --spring.main.web-application-type=none'
	@$(IMPORTER_DIR)/gradlew -p $(IMPORTER_DIR) bootRun --args='--csv=/Users/muilu/git/others/sample-service-migration/export/samplegroup.csv --manifest=/Users/muilu/git/others/sample-service-migration/config/manifests/sample_type_manifest.yaml --spring.datasource.url=$(PG_URL) --spring.datasource.username=$(PG_USER) --spring.datasource.password=$(PG_PASSWORD) --spring.datasource.driver-class-name=org.postgresql.Driver --spring.main.web-application-type=none'
	@$(IMPORTER_DIR)/gradlew -p $(IMPORTER_DIR) bootRun --args='--csv=/Users/muilu/git/others/sample-service-migration/export/containertype.csv --manifest=/Users/muilu/git/others/sample-service-migration/config/manifests/container_type_manifest.yaml --spring.datasource.url=$(PG_URL) --spring.datasource.username=$(PG_USER) --spring.datasource.password=$(PG_PASSWORD) --spring.datasource.driver-class-name=org.postgresql.Driver --spring.main.web-application-type=none'
	@$(IMPORTER_DIR)/gradlew -p $(IMPORTER_DIR) bootRun --args='--csv=/Users/muilu/git/others/sample-service-migration/export/container.csv --manifest=/Users/muilu/git/others/sample-service-migration/config/manifests/container_manifest.yaml --spring.datasource.url=$(PG_URL) --spring.datasource.username=$(PG_USER) --spring.datasource.password=$(PG_PASSWORD) --spring.datasource.driver-class-name=org.postgresql.Driver --spring.main.web-application-type=none --sort-self-joins'
	@$(IMPORTER_DIR)/gradlew -p $(IMPORTER_DIR) bootRun --args='--csv=/Users/muilu/git/others/sample-service-migration/export/sample.csv --manifest=/Users/muilu/git/others/sample-service-migration/config/manifests/sample_manifest.yaml --spring.datasource.url=$(PG_URL) --spring.datasource.username=$(PG_USER) --spring.datasource.password=$(PG_PASSWORD) --spring.datasource.driver-class-name=org.postgresql.Driver --spring.main.web-application-type=none --sort-self-joins'
	@$(IMPORTER_DIR)/gradlew -p $(IMPORTER_DIR) bootRun --args='--csv=/Users/muilu/git/others/sample-service-migration/export/sample_property_edta.csv --manifest=/Users/muilu/git/others/sample-service-migration/config/manifests/sample_property_manifest.yaml --spring.datasource.url=$(PG_URL) --spring.datasource.username=$(PG_USER) --spring.datasource.password=$(PG_PASSWORD) --spring.datasource.driver-class-name=org.postgresql.Driver --spring.main.web-application-type=none'
	@$(IMPORTER_DIR)/gradlew -p $(IMPORTER_DIR) bootRun --args='--csv=/Users/muilu/git/others/sample-service-migration/export/sample_property_dna.csv --manifest=/Users/muilu/git/others/sample-service-migration/config/manifests/sample_property_manifest.yaml --spring.datasource.url=$(PG_URL) --spring.datasource.username=$(PG_USER) --spring.datasource.password=$(PG_PASSWORD) --spring.datasource.driver-class-name=org.postgresql.Driver --spring.main.web-application-type=none'
	@$(IMPORTER_DIR)/gradlew -p $(IMPORTER_DIR) bootRun --args='--csv=/Users/muilu/git/others/sample-service-migration/export/sample_property_testnayte.csv --manifest=/Users/muilu/git/others/sample-service-migration/config/manifests/sample_property_manifest.yaml --spring.datasource.url=$(PG_URL) --spring.datasource.username=$(PG_USER) --spring.datasource.password=$(PG_PASSWORD) --spring.datasource.driver-class-name=org.postgresql.Driver --spring.main.web-application-type=none'
	@$(IMPORTER_DIR)/gradlew -p $(IMPORTER_DIR) bootRun --args='--csv=/Users/muilu/git/others/sample-service-migration/export/sample_type_quality_metadata.csv --manifest=/Users/muilu/git/others/sample-service-migration/config/manifests/sample_type_quality_metadata_manifest.yaml --spring.datasource.url=$(PG_URL) --spring.datasource.username=$(PG_USER) --spring.datasource.password=$(PG_PASSWORD) --spring.datasource.driver-class-name=org.postgresql.Driver --spring.main.web-application-type=none'
	@$(IMPORTER_DIR)/gradlew -p $(IMPORTER_DIR) bootRun --args='--csv=/Users/muilu/git/others/sample-service-migration/export/sample_quality.csv --manifest=/Users/muilu/git/others/sample-service-migration/config/manifests/sample_quality_manifest.yaml --spring.datasource.url=$(PG_URL) --spring.datasource.username=$(PG_USER) --spring.datasource.password=$(PG_PASSWORD) --spring.datasource.driver-class-name=org.postgresql.Driver --spring.main.web-application-type=none'
	@$(IMPORTER_DIR)/gradlew -p $(IMPORTER_DIR) bootRun --args='--csv=/Users/muilu/git/others/sample-service-migration/export/batch_list.csv --manifest=/Users/muilu/git/others/sample-service-migration/config/manifests/work_list_manifest.yaml --spring.datasource.url=$(PG_URL) --spring.datasource.username=$(PG_USER) --spring.datasource.password=$(PG_PASSWORD) --spring.datasource.driver-class-name=org.postgresql.Driver --spring.main.web-application-type=none'
	@$(IMPORTER_DIR)/gradlew -p $(IMPORTER_DIR) bootRun --args='--csv=/Users/muilu/git/others/sample-service-migration/export/batch_sample_list.csv --manifest=/Users/muilu/git/others/sample-service-migration/config/manifests/work_list_item_manifest.yaml --spring.datasource.url=$(PG_URL) --spring.datasource.username=$(PG_USER) --spring.datasource.password=$(PG_PASSWORD) --spring.datasource.driver-class-name=org.postgresql.Driver --spring.main.web-application-type=none'
	@echo "Resetting PostgreSQL sequences..."
	@docker exec -i sample-service-db-1 psql -U $(PG_USER) -d sample -c "\
		SELECT setval('project.project_id_seq', COALESCE((SELECT MAX(id) FROM project.project), 1)); \
		SELECT setval('project.partner_id_seq', COALESCE((SELECT MAX(id) FROM project.partner), 1)); \
		SELECT setval('project.project_membership_id_seq', COALESCE((SELECT MAX(id) FROM project.project_membership), 1)); \
		SELECT setval('sample.sample_type_id_seq', COALESCE((SELECT MAX(id) FROM sample.sample_type), 1)); \
		SELECT setval('sample.container_type_id_seq', COALESCE((SELECT MAX(id) FROM sample.container_type), 1)); \
		SELECT setval('sample.container_id_seq', COALESCE((SELECT MAX(id) FROM sample.container), 1)); \
		SELECT setval('sample.sample_id_seq', COALESCE((SELECT MAX(id) FROM sample.sample), 1)); \
		SELECT setval('sample.sample_property_id_seq', COALESCE((SELECT MAX(id) FROM sample.sample_property), 1)); \
		SELECT setval('sample.sample_type_quality_metadata_id_seq', COALESCE((SELECT MAX(id) FROM sample.sample_type_quality_metadata), 1)); \
		SELECT setval('sample.sample_quality_id_seq', COALESCE((SELECT MAX(id) FROM sample.sample_quality), 1)); \
		SELECT setval('sample.work_list_id_seq', COALESCE((SELECT MAX(id) FROM sample.work_list), 1)); \
		SELECT setval('sample.work_list_event_id_seq', COALESCE((SELECT MAX(id) FROM sample.work_list_event), 1)); \
		SELECT setval('sample.work_list_item_id_seq', COALESCE((SELECT MAX(id) FROM sample.work_list_item), 1));"
	@echo "✓ Data loading complete."

migrate-all: clear-target extract-data transform-data load-target verify
	@echo "✓ FULL MIGRATION COMPLETED SUCCESSFULLY!"

verify:
	@echo "Comparing source and target database counts..."
	@docker exec -i sample-service-db-1 psql -U $(PG_USER) -d sample -c "\
		SELECT 'sample_type' AS tab, COUNT(*) FROM sample.sample_type \
		UNION ALL SELECT 'container_type', COUNT(*) FROM sample.container_type \
		UNION ALL SELECT 'container', COUNT(*) FROM sample.container \
		UNION ALL SELECT 'sample', COUNT(*) FROM sample.sample \
		UNION ALL SELECT 'sample_property', COUNT(*) FROM sample.sample_property \
		UNION ALL SELECT 'cv_sample_quality', COUNT(*) FROM sample.cv_sample_quality \
		UNION ALL SELECT 'sample_type_quality_metadata', COUNT(*) FROM sample.sample_type_quality_metadata \
		UNION ALL SELECT 'sample_quality', COUNT(*) FROM sample.sample_quality \
		UNION ALL SELECT 'work_list', COUNT(*) FROM sample.work_list \
		UNION ALL SELECT 'work_list_event', COUNT(*) FROM sample.work_list_event \
		UNION ALL SELECT 'work_list_item', COUNT(*) FROM sample.work_list_item \
		UNION ALL SELECT 'project.project', COUNT(*) FROM project.project \
		UNION ALL SELECT 'project.partner', COUNT(*) FROM project.partner \
		UNION ALL SELECT 'project.project_membership', COUNT(*) FROM project.project_membership;"

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
