package com.bcplatforms.samplemigration;

import lombok.RequiredArgsConstructor;
import lombok.extern.log4j.Log4j2;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;

import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;

@Log4j2
@Component
@RequiredArgsConstructor
public class MigrationRunner implements CommandLineRunner {

    @Override
    public void run(String... args) throws Exception {
        log.info("Starting Migration Runner with arguments: {}", Arrays.toString(args));

        Set<String> targetTables = parseTargetTables(args);
        log.info("Target tables parsed: {}", targetTables);

        if (targetTables.isEmpty()) {
            log.info("No selective tables specified. Running full migration sequence...");
            // Default sequence: load all tables in order
            runSampleTypeMigration();
            // TODO: Hook up containerTypeLoader, containerLoader, sampleLoader here
        } else {
            if (targetTables.contains("sample_type")) {
                runSampleTypeMigration();
            }
            // TODO: Hook up other selective table execution checks here
        }

        log.info("Migration Runner completed execution.");
    }

    private void runSampleTypeMigration() {
        log.info("Sample Type migration is now handled via generic importer2026 with YAML manifests.");
    }

    private Set<String> parseTargetTables(String[] args) {
        Set<String> tables = new HashSet<>();
        for (String arg : args) {
            if (arg.startsWith("--tables=")) {
                String val = arg.substring("--tables=".length());
                if (!val.isBlank()) {
                    tables.addAll(Arrays.asList(val.split(",")));
                }
            }
        }
        return tables;
    }
}
