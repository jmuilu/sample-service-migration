-- Seed Controlled Vocabulary of Properties and Metadata
-- Run on target PostgreSQL database:
--   docker exec -i sample-service-db-1 psql -U sample -d sample -f /workspace/scripts/postgres/seed_properties.sql

-- 1. Populate Property Types (Sanasto)
-- Terms are UPPER_SNAKE_CASE per sample-service ADR 0014 (chk_property_type_term:
-- term ~ '^[A-Z][A-Z0-9_]*$'), which keeps cv_property_type.term in lockstep with
-- cv_attribute_type.term's naming convention.
INSERT INTO sample.cv_property_type (term, name, description, data_type, rank, userstamp) VALUES
('ABS230', 'Absorbance 230 nm', 'Absorbance at 230 nm', 'FLOAT', 1, 'migration'),
('ABS260', 'Absorbance 260 nm', 'Absorbance at 260 nm', 'FLOAT', 1, 'migration'),
('ABS260230', 'Absorbance 260/230', 'Absorbance ratio 260/230', 'FLOAT', 1, 'migration'),
('ABS260280', 'Absorbance 260/280', 'Absorbance ratio 260/280', 'FLOAT', 1, 'migration'),
('ABS280', 'Absorbance 280 nm', 'Absorbance at 280 nm', 'FLOAT', 1, 'migration'),
('DILUTION_FACTOR', 'Dilution Factor', 'Dilution factor', 'FLOAT', 1, 'migration'),
('ELUTION_VOLUME', 'Elution Volume', 'Elution volume in microliters', 'INTEGER', 1, 'migration'),
('EXTRACTION_METHOD', 'Extraction Method', 'Method used for DNA extraction', 'STRING', 1, 'migration'),
('EXTRACTION_SITE', 'Extraction Site', 'Site where extraction was performed', 'STRING', 1, 'migration'),
('FACTOR', 'Factor', 'Correction factor', 'INTEGER', 1, 'migration'),
('QUANTITY', 'Quantity', 'DNA quantity', 'FLOAT', 1, 'migration'),
('LIQUID_LEVEL', 'Liquid Level', 'Liquid level', 'INTEGER', 1, 'migration'),
('PLASMA_LEVEL', 'Plasma Level', 'Plasma level', 'INTEGER', 1, 'migration'),
('SEPARATION_LEVEL', 'Separation Level', 'Separation level', 'INTEGER', 1, 'migration'),
('LVMS', 'LVMS', 'Legacy LVMS property', 'STRING', 1, 'migration')
ON CONFLICT (term) DO UPDATE SET
  name = EXCLUDED.name,
  description = EXCLUDED.description,
  data_type = EXCLUDED.data_type,
  rank = EXCLUDED.rank,
  userstamp = EXCLUDED.userstamp;

-- 2. Populate Property Metadata (Kytkennät Näytetyyppeihin)
INSERT INTO sample.sample_property_metadata (sample_type_id, property_term, is_required, userstamp)
SELECT id, 'ABS230', false, 'migration' FROM sample.sample_type WHERE name = 'DNA' UNION ALL
SELECT id, 'ABS260', false, 'migration' FROM sample.sample_type WHERE name = 'DNA' UNION ALL
SELECT id, 'ABS260230', false, 'migration' FROM sample.sample_type WHERE name = 'DNA' UNION ALL
SELECT id, 'ABS260280', false, 'migration' FROM sample.sample_type WHERE name = 'DNA' UNION ALL
SELECT id, 'ABS280', false, 'migration' FROM sample.sample_type WHERE name = 'DNA' UNION ALL
SELECT id, 'DILUTION_FACTOR', false, 'migration' FROM sample.sample_type WHERE name = 'DNA' UNION ALL
SELECT id, 'ELUTION_VOLUME', false, 'migration' FROM sample.sample_type WHERE name = 'DNA' UNION ALL
SELECT id, 'EXTRACTION_METHOD', false, 'migration' FROM sample.sample_type WHERE name = 'DNA' UNION ALL
SELECT id, 'EXTRACTION_SITE', false, 'migration' FROM sample.sample_type WHERE name = 'DNA' UNION ALL
SELECT id, 'FACTOR', false, 'migration' FROM sample.sample_type WHERE name = 'DNA' UNION ALL
SELECT id, 'QUANTITY', false, 'migration' FROM sample.sample_type WHERE name = 'DNA' UNION ALL
SELECT id, 'LIQUID_LEVEL', false, 'migration' FROM sample.sample_type WHERE name = 'EDTA Whole blood' UNION ALL
SELECT id, 'PLASMA_LEVEL', false, 'migration' FROM sample.sample_type WHERE name = 'EDTA Whole blood' UNION ALL
SELECT id, 'SEPARATION_LEVEL', false, 'migration' FROM sample.sample_type WHERE name = 'EDTA Whole blood' UNION ALL
SELECT id, 'LVMS', false, 'migration' FROM sample.sample_type WHERE name = 'TestNäyte'
ON CONFLICT (sample_type_id, property_term) DO NOTHING;
