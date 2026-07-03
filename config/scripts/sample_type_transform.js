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
