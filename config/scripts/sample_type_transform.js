/**
 * Normalizes and maps sample type abbreviations.
 * @param {string} name - The descriptive name of the sample type (e.g., 'EDTA Whole blood')
 * @param {string} oldAbbr - The legacy abbreviation from DB2 (often numeric, e.g., '10004')
 * @returns {string} The normalized abbreviation
 */
function transformAbbreviation(name, oldAbbr) {
    var ABBREVIATION_MAP = {
        "Master Sample": "MS",
        "DNA": "DNA",
        "EDTA Whole blood": "EWB",
        "Plasma": "PL",
        "Serum": "SR",
        "EDTA cord blood": "ECB",
        "Tissue": "TS",
        "Maternal Whole Blood": "MWB",
        "TestNäyte": "TN",
        "EDTA Plasma": "EDTAPL"
    };

    // 1. Return mapped abbreviation if it exists
    if (ABBREVIATION_MAP[name]) {
        return ABBREVIATION_MAP[name];
    }

    // 2. Keep the old abbreviation if it's non-numeric
    if (oldAbbr && !oldAbbr.match(/^\d+$/)) {
        return oldAbbr;
    }

    // 3. Fallback: generate a clean uppercase alphanumeric slug (max 20 characters)
    var cleaned = name.replace(/[^a-zA-Z0-9]/g, '').toUpperCase();
    if (cleaned.length > 20) {
        cleaned = cleaned.substring(0, 20);
    }
    return cleaned === "" ? "UNKN" : cleaned;
}


/**
 * Maps a sample type name, as carried by the dependent CSVs (samples, profiles, qualities), to the term of
 * sample.cv_sample_type (sample-service ADR 0036). The term is the normalized legacy abbreviation computed by
 * transformAbbreviation, and the dependent columns are foreign keys to it, so there is no id lookup. Only the
 * name is known here: scripts/validation/validate_sample_type_terms.py fails the run if this differs from
 * transformAbbreviation for a legacy type (a non-numeric legacy abbreviation on a name that is not mapped above).
 * @param {string} rawValue - The sample type name (e.g., 'EDTA Plasma')
 * @param {java.util.Map} row - The full CSV row map (unused)
 * @returns {string} The term, or null when the name is blank
 */
function transformSampleTypeTerm(rawValue, row) {
    if (rawValue === null || rawValue === undefined || String(rawValue).trim() === "") {
        return null;
    }
    return transformAbbreviation(String(rawValue), null);
}
