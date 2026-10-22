/**
 * Normalizes and maps sample status values.
 * @param {string} status - The status value from DB2
 * @returns {string} The normalized status value for PostgreSQL check constraints, or throws error if invalid
 */
function transformStatus(status) {
    if (status === null || status === undefined || status === "") {
        return "PENDING";
    }
    // Clean and normalize status: e.g. "Not available" -> "NOT_AVAILABLE"
    var normalized = status.toString().trim().toUpperCase().replace(/\s+/g, '_');
    
    if (normalized === 'AVAILABLE' || normalized === 'NOT_AVAILABLE' || normalized === 'PENDING') {
        return normalized;
    }
    
    throw new Error("Invalid SAMPLE_STATUS value: '" + status + "' (normalized: '" + normalized + "')");
}

/**
 * Normalizes the legacy SOURCE into a sample.cv_identifier_source term (sample-service ADR 0049, todo D53):
 * trimmed, upper case, inner whitespace as '_', so 'manual' and 'MANUAL' are one source. Blank stays NULL.
 * Must agree with normalize_source in scripts/generate_identifier_sources.py, which builds the vocabulary.
 * @param {string} source - The SOURCE value from DB2
 * @returns {string|null} The identifier source term
 */
function transformIdentifierSource(source) {
    if (source === null || source === undefined) {
        return null;
    }
    var normalized = source.toString().trim().toUpperCase().replace(/\s+/g, '_');
    return normalized === "" ? null : normalized;
}
