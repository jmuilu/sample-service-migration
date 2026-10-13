/**
 * Normalizes and maps batch status values to PostgreSQL work list statuses.
 * @param {string} status - The legacy batch status from DB2
 * @returns {string} The normalized work list status ('DRAFT', 'ACTIVE', 'COMPLETED', 'CANCELLED')
 */
function transformListStatus(status) {
    if (!status) return 'DRAFT';
    var normalized = status.toString().trim().toUpperCase();
    switch (normalized) {
        case 'READY_FOR_PICKING':
        case 'BATCH_PICKING_TO_DO':
        case 'BATCH_CREATE':
            return 'DRAFT';
        case 'PICKING_IN_PROGRESS':
        case 'BATCH_PICKING_IN_PROGRESS':
        case 'BATCH_PROCESSING':
        case 'BATCH_UNDER_PROCESSING':
        case 'BATCH_ORIGINAL_SAMPLES':
        case 'BATCH_ALIQUOT_FOR_DNA':
        case 'BATCH_DNA_SAMPLES':
            return 'ACTIVE';
        case 'PICKING_COMPLETED':
        case 'BATCH_PICKING_FINISHED':
        case 'BATCH_PROCESSED':
        case 'BATCH_SENT':
        case 'BATCH_RECEIVED':
        case 'SAMPLES_AVAILABLE_FOR_DELIVERY':
        case 'SAMPLES_DELIVERED':
        case 'SAMPLE_LIST':
        case 'BATCH_SAMPLE_LIST':
            return 'COMPLETED';
        case 'BATCH_CANCELED':
            return 'CANCELLED';
        default:
            return 'DRAFT';
    }
}

/**
 * Normalizes and maps batch type.
 * @param {string} ispick - 'Y' or 'N' indicating picking list status
 * @returns {string} The work list type ('PICKING' or 'ANALYSIS')
 */
function transformListType(ispick) {
    if (ispick === 'Y' || ispick === true || ispick === 'true') {
        return 'PICKING';
    }
    return 'ANALYSIS';
}

/**
 * Normalizes and maps batch sample status values.
 * @param {string} rawValue - The legacy batch sample status from DB2 ('COLLECTED', 'NOT_COLLECTED', etc.)
 * @param {java.util.Map} row - The full CSV row map
 * @returns {string} The work list item status ('PENDING', 'COMPLETED', 'FAILED', 'EXCLUDED')
 */
function transformItemStatus(rawValue, row) {
    if (rawValue === 'COLLECTED' || rawValue === 'PROCESSED') {
        return 'COMPLETED';
    }
    if (rawValue === 'DOES_NOT_EXIST') {
        return 'FAILED';
    }
    
    // Look up the parent batch status from the denormalized CSV row to route NOT_COLLECTED / NOT_PROCESSED
    var batchStatus = row.get("BATCH_STATUS");
    var listStatus = transformListStatus(batchStatus);
    
    if (listStatus === 'COMPLETED' || listStatus === 'CANCELLED') {
        return 'FAILED';
    }
    return 'PENDING';
}

/**
 * Normalizes and formats timestamp to 'yyyy-MM-dd HH:mm:ss' to prevent PostgreSQL varying char errors.
 */
function transformCreated(rawValue) {
    if (!rawValue) return null;
    var valStr = rawValue.toString().trim();
    if (valStr.toUpperCase() === 'NULL' || valStr === '') return null;
    valStr = valStr.replace('T', ' ');
    if (valStr.indexOf('.') !== -1) {
        valStr = valStr.split('.')[0];
    }
    return valStr;
}
