/**
 * Normalizes and maps batch status values to PostgreSQL task statuses.
 */
function transformTaskStatus(status) {
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
 */
function transformTaskType(ispick) {
    if (ispick === 'Y' || ispick === true || ispick === 'true') {
        return 'SAMPLE_DELIVERY';
    }
    return 'SAMPLE_PROFILE';
}
