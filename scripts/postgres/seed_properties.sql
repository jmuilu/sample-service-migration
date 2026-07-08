-- Seed Controlled Vocabulary of Properties and Metadata
-- Run on target PostgreSQL database:
--   docker exec -i sample-service-db-1 psql -U sample -d sample -f /workspace/scripts/postgres/seed_properties.sql

-- 1. Populate Property Types (Sanasto)
INSERT INTO sample.cv_property_type (term, name, description, data_type, rank, userstamp) VALUES
('abs230', 'Absorbance 230 nm', 'Absorbance at 230 nm', 'FLOAT', 1, 'migration'),
('abs260', 'Absorbance 260 nm', 'Absorbance at 260 nm', 'FLOAT', 1, 'migration'),
('abs260230', 'Absorbance 260/230', 'Absorbance ratio 260/230', 'FLOAT', 1, 'migration'),
('abs260280', 'Absorbance 260/280', 'Absorbance ratio 260/280', 'FLOAT', 1, 'migration'),
('abs280', 'Absorbance 280 nm', 'Absorbance at 280 nm', 'FLOAT', 1, 'migration'),
('dilution_factor', 'Dilution Factor', 'Dilution factor', 'FLOAT', 1, 'migration'),
('elution_volume', 'Elution Volume', 'Elution volume in microliters', 'INTEGER', 1, 'migration'),
('extraction_method', 'Extraction Method', 'Method used for DNA extraction', 'STRING', 1, 'migration'),
('extraction_site', 'Extraction Site', 'Site where extraction was performed', 'STRING', 1, 'migration'),
('factor', 'Factor', 'Correction factor', 'INTEGER', 1, 'migration'),
('quantity', 'Quantity', 'DNA quantity', 'FLOAT', 1, 'migration'),
('liquid_level', 'Liquid Level', 'Liquid level', 'INTEGER', 1, 'migration'),
('plasma_level', 'Plasma Level', 'Plasma level', 'INTEGER', 1, 'migration'),
('separation_level', 'Separation Level', 'Separation level', 'INTEGER', 1, 'migration'),
('lvms', 'LVMS', 'Legacy LVMS property', 'STRING', 1, 'migration')
ON CONFLICT (term) DO UPDATE SET
  name = EXCLUDED.name,
  description = EXCLUDED.description,
  data_type = EXCLUDED.data_type,
  rank = EXCLUDED.rank,
  userstamp = EXCLUDED.userstamp;

-- 2. Populate Property Metadata (Kytkennät Näytetyyppeihin)
INSERT INTO sample.sample_property_metadata (sample_type_id, property_term, is_required, userstamp)
SELECT id, 'abs230', false, 'migration' FROM sample.sample_type WHERE name = 'DNA' UNION ALL
SELECT id, 'abs260', false, 'migration' FROM sample.sample_type WHERE name = 'DNA' UNION ALL
SELECT id, 'abs260230', false, 'migration' FROM sample.sample_type WHERE name = 'DNA' UNION ALL
SELECT id, 'abs260280', false, 'migration' FROM sample.sample_type WHERE name = 'DNA' UNION ALL
SELECT id, 'abs280', false, 'migration' FROM sample.sample_type WHERE name = 'DNA' UNION ALL
SELECT id, 'dilution_factor', false, 'migration' FROM sample.sample_type WHERE name = 'DNA' UNION ALL
SELECT id, 'elution_volume', false, 'migration' FROM sample.sample_type WHERE name = 'DNA' UNION ALL
SELECT id, 'extraction_method', false, 'migration' FROM sample.sample_type WHERE name = 'DNA' UNION ALL
SELECT id, 'extraction_site', false, 'migration' FROM sample.sample_type WHERE name = 'DNA' UNION ALL
SELECT id, 'factor', false, 'migration' FROM sample.sample_type WHERE name = 'DNA' UNION ALL
SELECT id, 'quantity', false, 'migration' FROM sample.sample_type WHERE name = 'DNA' UNION ALL
SELECT id, 'liquid_level', false, 'migration' FROM sample.sample_type WHERE name = 'EDTA Whole blood' UNION ALL
SELECT id, 'plasma_level', false, 'migration' FROM sample.sample_type WHERE name = 'EDTA Whole blood' UNION ALL
SELECT id, 'separation_level', false, 'migration' FROM sample.sample_type WHERE name = 'EDTA Whole blood' UNION ALL
SELECT id, 'lvms', false, 'migration' FROM sample.sample_type WHERE name = 'TestNäyte'
ON CONFLICT (sample_type_id, property_term) DO NOTHING;
