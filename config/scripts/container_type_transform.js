/**
 * Maps and normalizes DB2 CONTAINERTYPE basetype values to a sample.cv_container_basetype term:
 * 'SITE', 'FREEZER', 'RACK', 'SHELF', 'BOX', 'PLATE', and the virtual 'TRASH' and 'USED' (sample-service ADR 0034:
 * legacy Trash holds the legacy 'used' containers Empty, Lost and Picked).
 *
 * @param {string} rawValue - The raw basetype from DB2 (e.g., 'freezer', 'trash', 'no-location')
 * @param {object} rowMap - The entire row context as a map
 * @returns {string} The normalized and mapped basetype
 */
function transformBasetype(rawValue, rowMap) {
    if (!rawValue) {
        return "SITE";
    }

    var baseUpper = rawValue.toUpperCase().trim();

    var REMAP = {
        "FREEZER": "FREEZER",
        "SHELF": "SHELF",
        "RACK": "RACK",
        "DRAWER": "RACK",
        "BOX": "BOX",
        "PLATE": "PLATE",
        "SITE": "SITE",
        "TRASH": "TRASH",
        "USED": "USED",
        "MEGA": "PLATE",
        "ASA": "PLATE",
        "NO-LOCATION": "SITE"
    };

    if (REMAP[baseUpper]) {
        return REMAP[baseUpper];
    }

    // Default fallback if we encounter any other unmapped value
    return "SITE";
}
