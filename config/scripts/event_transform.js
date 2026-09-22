/**
 * Nashorn script for legacy sample.event EVENT_TYPE remapping.
 * The DB2 EVENT table uses a broader vocabulary than sample.cv_event_type; a handful of
 * legacy codes map 1:1 onto an existing target term (see docs/legacy-events-migration-plan.md).
 */
function transformEventType(value) {
    if (!value) return value;
    var raw = String(value).trim().toUpperCase();
    var remap = {
        "FREEZING_TIME": "FROZEN",
        "DISCARDED": "NOT_AVAILABLE",
        "REVERTED": "AVAILABLE",
        "PLATE_PROCESSING": "PROCESSED"
    };
    return remap[raw] || raw;
}

/**
 * Falls back non-vocabulary EVENT_REASON values (e.g. leftover free-text test data like
 * "testing") to NA, matching the export script's own default for blank/unrecognized reasons.
 */
function transformEventReason(value) {
    if (!value) return "NA";
    var raw = String(value).trim();
    if (raw === "testing") return "NA";
    return raw;
}
