package scripts;

import java.io.*;
import java.util.*;

/**
 * Standalone Java program to dynamically unpivot flat CSV files exported from DB2 subclass tables
 * into a vertical EAV format suitable for import into the sample.sample_property table.
 * 
 * Instead of hardcoding columns, it dynamically discovers the allowed property terms for the
 * given näytetyyppi (sample type) by reading the metadata files (samplegroup.csv and sample_property_metadata.csv).
 * 
 * Runs on JVM 11+ without compilation:
 *   java scripts/PivotHelper.java <input_csv> <output_csv> <sample_type_groupnr> [metadata_dir]
 */
public class PivotHelper {

    public static void main(String[] args) {
        if (args.length < 3) {
            System.out.println("Usage: java scripts/PivotHelper.java <input_csv> <output_csv> <sample_type_groupnr> [metadata_dir]");
            System.out.println("Example: java scripts/PivotHelper.java export/sample_10003.csv export/sample_property_dna.csv 10003 export");
            System.exit(1);
        }

        String inputPath = args[0];
        String outputPath = args[1];
        String groupnr = args[2];
        String metadataDir = args.length >= 4 ? args[3] : "export";

        try {
            // 1. Resolve Sample Type Name from samplegroup.csv using the groupnr (which is stored in ABBREVIATION in DB2 export)
            String sampleTypeName = resolveSampleTypeName(metadataDir, groupnr);
            System.out.println("Resolved groupnr '" + groupnr + "' to sample type: '" + sampleTypeName + "'");

            // 2. Discover allowed property terms for this sample type from sample_property_metadata.csv
            Set<String> allowedTerms = discoverAllowedTerms(metadataDir, sampleTypeName);
            System.out.println("Discovered " + allowedTerms.size() + " allowed property terms: " + allowedTerms);

            if (allowedTerms.isEmpty()) {
                System.out.println("Warning: No allowed properties configured for sample type '" + sampleTypeName + "'. Only header will be written.");
            }

            // 3. Unpivot flat CSV using resolved terms
            unpivot(inputPath, outputPath, allowedTerms);

        } catch (Exception e) {
            System.err.println("Error during unpivot execution:");
            e.printStackTrace();
            System.exit(1);
        }
    }

    private static String resolveSampleTypeName(String metadataDir, String groupnr) throws IOException {
        File file = new File(metadataDir, "samplegroup.csv");
        if (!file.exists()) {
            throw new FileNotFoundException("Required metadata file '" + file.getAbsolutePath() + "' not found.");
        }

        try (BufferedReader reader = new BufferedReader(new InputStreamReader(new FileInputStream(file), "UTF-8"))) {
            String headerLine = reader.readLine();
            if (headerLine == null) throw new IOException("samplegroup.csv is empty");

            List<String> headers = parseCsvLine(headerLine);
            int nameIdx = -1;
            int abbrIdx = -1;

            for (int i = 0; i < headers.size(); i++) {
                String h = headers.get(i).toUpperCase();
                if (h.equals("NAME")) nameIdx = i;
                if (h.equals("ABBREVIATION")) abbrIdx = i;
            }

            if (nameIdx == -1 || abbrIdx == -1) {
                throw new IOException("samplegroup.csv must contain NAME and ABBREVIATION columns");
            }

            String line;
            while ((line = reader.readLine()) != null) {
                List<String> values = parseCsvLine(line);
                if (values.size() > Math.max(nameIdx, abbrIdx)) {
                    String abbr = values.get(abbrIdx).trim();
                    if (abbr.equals(groupnr)) {
                        return values.get(nameIdx).trim();
                    }
                }
            }
        }
        throw new IllegalArgumentException("No sample type found with abbreviation/groupnr '" + groupnr + "' in samplegroup.csv");
    }

    private static Set<String> discoverAllowedTerms(String metadataDir, String sampleTypeName) throws IOException {
        File file = new File(metadataDir, "sample_property_metadata.csv");
        if (!file.exists()) {
            throw new FileNotFoundException("Required metadata file '" + file.getAbsolutePath() + "' not found.");
        }

        Set<String> allowedTerms = new HashSet<>();
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(new FileInputStream(file), "UTF-8"))) {
            String headerLine = reader.readLine();
            if (headerLine == null) throw new IOException("sample_property_metadata.csv is empty");

            List<String> headers = parseCsvLine(headerLine);
            int typeIdx = -1;
            int termIdx = -1;

            for (int i = 0; i < headers.size(); i++) {
                String h = headers.get(i).toUpperCase();
                if (h.equals("SAMPLE_TYPE_NAME")) typeIdx = i;
                if (h.equals("PROPERTY_TERM")) termIdx = i;
            }

            if (typeIdx == -1 || termIdx == -1) {
                throw new IOException("sample_property_metadata.csv must contain SAMPLE_TYPE_NAME and PROPERTY_TERM columns");
            }

            String line;
            while ((line = reader.readLine()) != null) {
                List<String> values = parseCsvLine(line);
                if (values.size() > Math.max(typeIdx, termIdx)) {
                    String type = values.get(typeIdx).trim();
                    if (type.equalsIgnoreCase(sampleTypeName)) {
                        allowedTerms.add(values.get(termIdx).trim());
                    }
                }
            }
        }
        return allowedTerms;
    }

    private static void unpivot(String inputPath, String outputPath, Set<String> allowedTerms) throws IOException {
        File inputFile = new File(inputPath);
        if (!inputFile.exists()) {
            System.err.println("Error: Input file '" + inputPath + "' not found.");
            System.exit(1);
        }

        try (BufferedReader reader = new BufferedReader(new InputStreamReader(new FileInputStream(inputFile), "UTF-8"));
             BufferedWriter writer = new BufferedWriter(new OutputStreamWriter(new FileOutputStream(outputPath), "UTF-8"))) {

            String headerLine = reader.readLine();
            if (headerLine == null) {
                System.err.println("Error: Input CSV is empty.");
                return;
            }

            List<String> headers = parseCsvLine(headerLine);
            int sampleIdIdx = -1;
            Map<Integer, String> colIdxToTerm = new HashMap<>();

            for (int i = 0; i < headers.size(); i++) {
                String header = headers.get(i).toUpperCase();
                if (header.equals("SAMPLE_10002_SAMPLEID") || header.equals("SAMPLEID")) {
                    sampleIdIdx = i;
                    continue;
                }
                
                // Dynamic match: compare normalized names (lowercase, remove underscores/dashes)
                String normHeader = normalize(header);
                for (String term : allowedTerms) {
                    if (normHeader.equals(normalize(term))) {
                        colIdxToTerm.put(i, term);
                        break;
                    }
                }
            }

            if (sampleIdIdx == -1) {
                System.err.println("Error: Could not find SAMPLE_10002_SAMPLEID or SAMPLEID column in input header.");
                return;
            }

            // Write output header
            writer.write("SAMPLEID,PROPERTY_TERM,VALUE");
            writer.newLine();

            String line;
            int rowCount = 0;
            int valueCount = 0;

            while ((line = reader.readLine()) != null) {
                if (line.trim().isEmpty()) continue;
                List<String> values = parseCsvLine(line);
                if (values.size() <= sampleIdIdx) continue;

                String sampleId = values.get(sampleIdIdx);
                if (sampleId == null || sampleId.trim().isEmpty()) continue;

                rowCount++;
                for (Map.Entry<Integer, String> entry : colIdxToTerm.entrySet()) {
                    int idx = entry.getKey();
                    String term = entry.getValue();
                    if (idx < values.size()) {
                        String val = values.get(idx);
                        if (val != null && !val.trim().isEmpty()) {
                            writer.write(escapeCsv(sampleId) + "," + escapeCsv(term) + "," + escapeCsv(val));
                            writer.newLine();
                            valueCount++;
                        }
                    }
                }
            }

            System.out.println("Successfully unpivoted " + rowCount + " flat rows into " + valueCount + " property values.");
        }
    }

    private static String normalize(String s) {
        return s.toLowerCase().replace("_", "").replace("-", "");
    }

    private static List<String> parseCsvLine(String line) {
        List<String> result = new ArrayList<>();
        boolean inQuotes = false;
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < line.length(); i++) {
            char c = line.charAt(i);
            if (c == '"') {
                if (i + 1 < line.length() && line.charAt(i + 1) == '"') {
                    sb.append('"');
                    i++;
                } else {
                    inQuotes = !inQuotes;
                }
            } else if (c == ',' && !inQuotes) {
                result.add(sb.toString());
                sb.setLength(0);
            } else {
                sb.append(c);
            }
        }
        result.add(sb.toString());
        return result;
    }

    private static String escapeCsv(String value) {
        if (value.contains(",") || value.contains("\"") || value.contains("\n") || value.contains("\r")) {
            return "\"" + value.replace("\"", "\"\"") + "\"";
        }
        return value;
    }
}
