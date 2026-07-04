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
