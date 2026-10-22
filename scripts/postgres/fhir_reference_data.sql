-- ADR 0049 reference data for the customer's sample types (sample-service todo D53; FHIR alignment proposal WP1, WP2).
--
-- Liquibase maps only the vocabularies it seeds (units, statuses, quality categories, DNA and EWB). The customer's
-- sample types are loaded from DB2, so their mappings and column units are migration reference data. They follow the
-- owner's defaults of 2026-10-21: the proposal's codes where they are confirmed or exported as approximate matches.
-- FFPE is formalin-fixed paraffin-embedded slides (owner, 2026-10-22): a tissue specimen counted in slides.
-- Left out until the terminology owner or the lab answers (docs/plans/fhir-alignment-implementation.md, open
-- questions): fresh tissue (TS), a processing code for the fixation, the MIABIS material types (no confirmed code
-- system), ASSAY and MS (not specimen types), and the unit of amount for TS, swab and cell types.
--
-- A row is written only for a term the load created, so another customer's data simply skips it. Safe to run again.
-- Runs after the sample types are loaded; declared as a migration like the importer's sessions.
\set ON_ERROR_STOP 1
BEGIN;
SELECT common.declare_change('MIGRATION', null, 'DB2-migration: FHIR reference data (ADR 0049)', 'sample-service-migration');

-- 1. Terminology mappings (common.term_mapping). An unverified tube additive is an approximate match (RELATED_TO), as
-- Liquibase does for EWB.
INSERT INTO common.term_mapping (source_table, source_term, target, code_system, code, display, relationship, remarks)
SELECT 'sample.cv_sample_type', m.term, m.target, m.code_system, m.code, m.display, m.relationship, m.remarks
FROM (VALUES
    ('WHOLEBLOOD', 'SPECIMEN_TYPE', 'SNOMED_CT', '258580003', 'Whole blood specimen', 'EQUIVALENT', null),
    ('WHOLEBLOOD', 'SPECIMEN_TYPE', 'HL7_V2_0487', 'BLD', 'Whole blood', 'EQUIVALENT', null),
    ('PL', 'SPECIMEN_TYPE', 'SNOMED_CT', '119361006', 'Plasma specimen', 'EQUIVALENT', null),
    ('PL', 'SPECIMEN_TYPE', 'HL7_V2_0487', 'PLAS', 'Plasma', 'EQUIVALENT', null),
    ('EDTAPL', 'SPECIMEN_TYPE', 'SNOMED_CT', '119361006', 'Plasma specimen', 'SOURCE_IS_NARROWER', 'material only; the additive is a separate mapping'),
    ('EDTAPL', 'CONTAINER_ADDITIVE', 'HL7_V2_0371', 'EDTK', 'Potassium/K EDTA', 'RELATED_TO', 'verify the EDTA salt of the tubes'),
    ('LIHEPARINPLASMA', 'SPECIMEN_TYPE', 'SNOMED_CT', '119361006', 'Plasma specimen', 'SOURCE_IS_NARROWER', 'material only; the additive is a separate mapping'),
    ('LIHEPARINPLASMA', 'CONTAINER_ADDITIVE', 'HL7_V2_0371', 'HEPL', 'Lithium/Li Heparin', 'RELATED_TO', 'verify with the terminology owner'),
    ('MATERNALPLASMA', 'SPECIMEN_TYPE', 'SNOMED_CT', '119361006', 'Plasma specimen', 'SOURCE_IS_NARROWER', 'maternal context belongs to the subject'),
    ('CCFDNAPLASMA', 'SPECIMEN_TYPE', 'SNOMED_CT', '119361006', 'Plasma specimen', 'SOURCE_IS_NARROWER', 'ccfDNA is the intended analysis, not the material'),
    ('SR', 'SPECIMEN_TYPE', 'SNOMED_CT', '119364003', 'Serum specimen', 'EQUIVALENT', null),
    ('SR', 'SPECIMEN_TYPE', 'HL7_V2_0487', 'SER', 'Serum', 'EQUIVALENT', null),
    ('RNA', 'SPECIMEN_TYPE', 'SNOMED_CT', '441673008', 'Ribonucleic acid specimen', 'EQUIVALENT', null),
    ('URINE', 'SPECIMEN_TYPE', 'SNOMED_CT', '122575003', 'Urine specimen', 'EQUIVALENT', null),
    ('SALIVA', 'SPECIMEN_TYPE', 'SNOMED_CT', '119342007', 'Saliva specimen', 'EQUIVALENT', null),
    ('LIKVOR', 'SPECIMEN_TYPE', 'SNOMED_CT', '258450006', 'Cerebrospinal fluid specimen', 'EQUIVALENT', null),
    ('FFPE', 'SPECIMEN_TYPE', 'SNOMED_CT', '119376003', 'Tissue specimen', 'SOURCE_IS_NARROWER', 'formalin-fixed paraffin-embedded slide; the fixation is processing, not material')
) AS m(term, target, code_system, code, display, relationship, remarks)
JOIN sample.cv_sample_type t ON t.term = m.term
ON CONFLICT ON CONSTRAINT uq_term_mapping DO NOTHING;

-- 2. One level-1 specialization per sample type (WP2), the anchor of its units and attributes.
INSERT INTO sample.entity_type_specialization (entity_type, type_value, name)
SELECT 'SAMPLE', t.term, t.name
FROM sample.cv_sample_type t
ON CONFLICT ON CONSTRAINT uq_entity_type_specialization DO NOTHING;

-- 3. Units of the fixed quantity columns: amount in microlitres for the fluid types and in slides for FFPE,
-- concentration in ng/ul for RNA (DNA and EWB come from Liquibase). A type without a unit exports no quantity until
-- the lab names one.
INSERT INTO sample.entity_column_unit_metadata (specialization_id, column_name, unit)
SELECT sp.id, v.column_name, v.unit
FROM (VALUES
    ('WHOLEBLOOD', 'amount', 'UL'),
    ('MWB', 'amount', 'UL'),
    ('CCFDNAWHOLEBLOOD', 'amount', 'UL'),
    ('EDTABUFFY', 'amount', 'UL'),
    ('PL', 'amount', 'UL'),
    ('EDTAPL', 'amount', 'UL'),
    ('LIHEPARINPLASMA', 'amount', 'UL'),
    ('MATERNALPLASMA', 'amount', 'UL'),
    ('CCFDNAPLASMA', 'amount', 'UL'),
    ('SR', 'amount', 'UL'),
    ('MATERNALSERUM', 'amount', 'UL'),
    ('URINE', 'amount', 'UL'),
    ('SALIVA', 'amount', 'UL'),
    ('LIKVOR', 'amount', 'UL'),
    ('LIKVORSUPERNATANT', 'amount', 'UL'),
    ('RNA', 'amount', 'UL'),
    ('RNA', 'concentration', 'NG_PER_UL'),
    ('FFPE', 'amount', 'EA')
) AS v(type_value, column_name, unit)
JOIN sample.entity_type_specialization sp
  ON sp.entity_type = 'SAMPLE' AND sp.parent_id IS NULL AND sp.type_value = v.type_value
ON CONFLICT ON CONSTRAINT uq_entity_column_unit_metadata DO NOTHING;

COMMIT;
