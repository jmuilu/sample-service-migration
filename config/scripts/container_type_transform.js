/**
 * Maps and normalizes DB2 CONTAINERTYPE basetype values to Postgres container_type basetype enum:
 * 'SITE', 'FREEZER', 'RACK', 'SHELF', 'BOX', 'PLATE'
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
        "TRASH": "SITE",
        "USED": "SITE",
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
