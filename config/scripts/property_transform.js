/**
 * Nashorn script for dynamic properties routing.
 * Inspects row property term and routes values to appropriate type columns.
 * 
 * Each function receives the raw string value and the full row map.
 * It returns the value if the term maps to this type, or null otherwise.
 */

function getStringValue(value, row) {
    var term = String(row.get("PROPERTY_TERM"));
    var type = getDataType(term);
    return type === 'STRING' ? value : null;
}

function getIntegerValue(value, row) {
    var term = String(row.get("PROPERTY_TERM"));
    var type = getDataType(term);
    return type === 'INTEGER' ? value : null;
}

function getFloatValue(value, row) {
    var term = String(row.get("PROPERTY_TERM"));
    var type = getDataType(term);
    return type === 'FLOAT' ? value : null;
}

function getChoiceValue(value, row) {
    var term = String(row.get("PROPERTY_TERM"));
    var type = getDataType(term);
    return type === 'MULTICHOICE' ? value : null;
}

/**
 * Returns the expected data type for a property term.
 * Handled terms are defined here to route values to the correct database column.
 */
function getDataType(term) {
    var types = {
        // DNA Properties (SAMPLE_10003)
        "abs230": "FLOAT",
        "abs260": "FLOAT",
        "abs260230": "FLOAT",
        "abs260280": "FLOAT",
        "abs280": "FLOAT",
        "dilution_factor": "FLOAT",
        "elution_volume": "INTEGER",
        "extraction_method": "STRING",
        "extraction_site": "STRING",
        "factor": "INTEGER",
        "quantity": "FLOAT",
        
        // EDTA Whole Blood Properties (SAMPLE_10004)
        "liquid_level": "INTEGER",
        "plasma_level": "INTEGER",
        "separation_level": "INTEGER"
    };
    return types[term.toLowerCase()] || "STRING";
}
