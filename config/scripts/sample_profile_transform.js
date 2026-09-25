/**
 * Normalizes DB2 0/1 flag columns into boolean literals for Postgres boolean columns.
 * @param {string} value - '0', '1', or empty/null
 * @returns {string} 'true' or 'false'
 */
function toBoolean01(value) {
    return value && value.toString().trim() === '1' ? 'true' : 'false';
}
