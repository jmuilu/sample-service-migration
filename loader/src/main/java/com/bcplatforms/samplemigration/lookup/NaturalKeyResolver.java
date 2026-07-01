package com.bcplatforms.samplemigration.lookup;

import lombok.RequiredArgsConstructor;
import lombok.extern.log4j.Log4j2;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

import java.util.HashMap;
import java.util.Map;
import java.util.Objects;

@Log4j2
@Component
@RequiredArgsConstructor
public class NaturalKeyResolver {

    private final JdbcTemplate jdbcTemplate;

    // Caches to avoid repeated lookups
    private final Map<String, Long> sampleTypeCache = new HashMap<>();
    private final Map<String, Long> containerTypeCache = new HashMap<>();
    private final Map<String, Long> containerCache = new HashMap<>();
    private final Map<String, Long> sampleCache = new HashMap<>();

    public Long resolveSampleTypeId(String name, String abbreviation) {
        String key = name + "|" + abbreviation;
        return sampleTypeCache.computeIfAbsent(key, k -> {
            String sql = "SELECT id FROM sample.sample_type WHERE name = ? AND abbreviation = ?";
            var result = jdbcTemplate.queryForList(sql, Long.class, name, abbreviation);
            if (result.isEmpty()) {
                throw new IllegalArgumentException("Sample type not found: name=" + name + ", abbr=" + abbreviation);
            }
            if (result.size() > 1) {
                throw new IllegalArgumentException("Multiple sample types found: name=" + name + ", abbr=" + abbreviation);
            }
            return result.get(0);
        });
    }

    public Long resolveContainerTypeId(String name) {
        return containerTypeCache.computeIfAbsent(name, k -> {
            String sql = "SELECT id FROM sample.container_type WHERE name = ?";
            var result = jdbcTemplate.queryForList(sql, Long.class, name);
            if (result.isEmpty()) {
                throw new IllegalArgumentException("Container type not found: " + name);
            }
            if (result.size() > 1) {
                throw new IllegalArgumentException("Multiple container types found: " + name);
            }
            return result.get(0);
        });
    }

    public Long resolveContainerId(String name) {
        return containerCache.computeIfAbsent(name, k -> {
            String sql = "SELECT id FROM sample.container WHERE name = ?";
            var result = jdbcTemplate.queryForList(sql, Long.class, name);
            if (result.isEmpty()) {
                return null; // nullable FK — unplaced samples
            }
            if (result.size() > 1) {
                throw new IllegalArgumentException("Multiple containers found with name: " + name);
            }
            return result.get(0);
        });
    }

    public Long resolveSampleId(String sampleid) {
        return sampleCache.computeIfAbsent(sampleid, k -> {
            String sql = "SELECT id FROM sample.sample WHERE sampleid = ?";
            var result = jdbcTemplate.queryForList(sql, Long.class, sampleid);
            if (result.isEmpty()) {
                return null; // nullable self-FK — non-aliquots
            }
            if (result.size() > 1) {
                throw new IllegalArgumentException("Multiple samples found with sampleid: " + sampleid);
            }
            return result.get(0);
        });
    }

    public void clearCache() {
        sampleTypeCache.clear();
        containerTypeCache.clear();
        containerCache.clear();
        sampleCache.clear();
    }
}
