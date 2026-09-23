/**
 * Builds the sample.sample.attributes jsonb payload for DNA samples from
 * BIOBANK3.SAMPLE_10003's extension columns, per ADR 0017's registered DNA attribute set
 * (ABS260, ABS280, ABS230, ABS260280, ABS260230, EXTRACTION_METHOD, FACTOR) - the
 * sample.sample_property EAV table this used to be pivoted into no longer exists.
 *
 * Column decisions (none of these DB2 columns have any real data at migration time to
 * verify against - flag to the domain owner if real data ever surfaces that contradicts
 * these):
 * - QUANTITY, EXTRACTIONSITE: no home in the new registry (EXTRACTION_SITE was dropped,
 *   domain-owner-confirmed, see ADR 0017). Not migrated.
 * - ELUTION_VOLUME: promoted to the native sample.sample.volume_ext column by ADR 0015
 *   ("physical eluate/solution volume for a molecular specimen") - handled by this same
 *   manifest's volume_ext column mapping, not here.
 * - FACTOR is sourced from DB2's DILUTION_FACTOR column, not DB2's own FACTOR column:
 *   ADR 0017 describes attributes.FACTOR as "Dilution/concentration factor", matching
 *   DILUTION_FACTOR's old EAV description ("Dilution factor") - DB2's plain FACTOR was a
 *   distinct "Correction factor" concept historically, with no home in the new registry.
 *
 * EXTRACTIONMETHOD is free text in DB2 with no real sample data to build a crosswalk from;
 * best-effort normalized to upper-snake-case so it at least resembles a cv_attribute_choice
 * choice_value. It is NOT validated against the real choice list (SILICA_COLUMN,
 * MAGNETIC_BEADS, ...) since the DB has no CHECK constraint for this (ADR 0014: app-layer
 * validation only, not built yet) - revisit once real EXTRACTIONMETHOD values are available.
 */
function buildDnaAttributes(rawValue, row) {
    var attrs = {};

    addFloat(attrs, "ABS260", row.get("ABS260"));
    addFloat(attrs, "ABS280", row.get("ABS280"));
    addFloat(attrs, "ABS230", row.get("ABS230"));
    addFloat(attrs, "ABS260280", row.get("ABS260280"));
    addFloat(attrs, "ABS260230", row.get("ABS260230"));
    addFloat(attrs, "FACTOR", row.get("DILUTION_FACTOR"));

    var extractionMethod = normalizeChoice(row.get("EXTRACTIONMETHOD"));
    if (extractionMethod !== null) {
        attrs["EXTRACTION_METHOD"] = extractionMethod;
    }

    return JSON.stringify(attrs);
}

function addFloat(attrs, key, rawStr) {
    if (rawStr === null || rawStr === undefined) {
        return;
    }
    var trimmed = String(rawStr).trim();
    if (trimmed === "") {
        return;
    }
    attrs[key] = parseFloat(trimmed);
}

function normalizeChoice(rawStr) {
    if (rawStr === null || rawStr === undefined) {
        return null;
    }
    var trimmed = String(rawStr).trim();
    if (trimmed === "") {
        return null;
    }
    return trimmed.toUpperCase().replace(/[^A-Z0-9]+/g, '_').replace(/^_+|_+$/g, '');
}
