package com.bcplatforms.samplemigration.enums;

import lombok.extern.log4j.Log4j2;

import java.util.Map;

@Log4j2
public class ContainerBaseTypeMapper {

    private static final Map<String, String> REMAP = Map.of(
            "SITE", "SITE",
            "FREEZER", "FREEZER",
            "RACK", "RACK",
            "SHELF", "SHELF",
            "BOX", "BOX",
            "PLATE", "PLATE"
    );

    public static String map(String dbValue) {
        if (dbValue == null || dbValue.isEmpty()) {
            throw new IllegalArgumentException("BASETYPE cannot be null or empty");
        }

        String mapped = REMAP.get(dbValue.toUpperCase());
        if (mapped == null) {
            throw new IllegalArgumentException("Unmapped CONTAINER_BASETYPE value: " + dbValue +
                    ". Valid values: " + REMAP.keySet());
        }
        return mapped;
    }
}
