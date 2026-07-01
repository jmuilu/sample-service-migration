package com.bcplatforms.samplemigration.enums;

import lombok.extern.log4j.Log4j2;

import java.util.Map;

@Log4j2
public class SampleStatusMapper {

    private static final Map<String, String> REMAP = Map.of(
            "AVAILABLE", "AVAILABLE",
            "NOT_AVAILABLE", "NOT_AVAILABLE",
            "PENDING", "PENDING"
    );

    public static String map(String dbValue) {
        if (dbValue == null || dbValue.isEmpty()) {
            return null;
        }

        String mapped = REMAP.get(dbValue.toUpperCase());
        if (mapped == null) {
            throw new IllegalArgumentException("Unmapped SAMPLE_STATUS value: " + dbValue +
                    ". Valid values: " + REMAP.keySet());
        }
        return mapped;
    }
}
