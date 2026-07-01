package com.bcplatforms.samplemigration.csv;

import com.opencsv.CSVParser;
import com.opencsv.CSVParserBuilder;
import com.opencsv.CSVReader;
import com.opencsv.CSVReaderBuilder;
import lombok.extern.log4j.Log4j2;

import java.io.Reader;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.stream.Stream;
import java.util.stream.StreamSupport;

@Log4j2
public class CsvStreamReader {

    private static final String TIMESTAMP_FORMAT = "yyyy-MM-dd HH:mm:ss";
    private static final DateTimeFormatter TIMESTAMP_FORMATTER = DateTimeFormatter.ofPattern(TIMESTAMP_FORMAT);

    private final CSVReader csvReader;
    private final String[] headers;

    public CsvStreamReader(Reader reader) {
        CSVParser parser = new CSVParserBuilder().build();
        this.csvReader = new CSVReaderBuilder(reader)
                .withCSVParser(parser)
                .build();
        try {
            this.headers = csvReader.readNext();
            if (this.headers == null) {
                throw new IllegalArgumentException("CSV file is empty");
            }
        } catch (Exception e) {
            throw new RuntimeException("Failed to read CSV headers", e);
        }
    }

    public String[] getHeaders() {
        return headers;
    }

    public Stream<Map<String, String>> stream() {
        Iterable<String[]> iterable = () -> csvReader.iterator();
        return StreamSupport.stream(iterable.spliterator(), false)
                .map(this::toMap);
    }

    private Map<String, String> toMap(String[] row) {
        Map<String, String> map = new LinkedHashMap<>();
        for (int i = 0; i < headers.length && i < row.length; i++) {
            String value = (i < row.length && row[i] != null) ? row[i].trim() : "";
            map.put(headers[i], value);
        }
        return map;
    }

    public static String getString(Map<String, String> row, String key) {
        String val = row.get(key);
        return (val == null || val.isEmpty()) ? null : val;
    }

    public static Long getLong(Map<String, String> row, String key) {
        String val = getString(row, key);
        return (val == null) ? null : Long.parseLong(val);
    }

    public static Integer getInteger(Map<String, String> row, String key) {
        String val = getString(row, key);
        return (val == null) ? null : Integer.parseInt(val);
    }

    public static Double getDouble(Map<String, String> row, String key) {
        String val = getString(row, key);
        return (val == null) ? null : Double.parseDouble(val);
    }

    public static LocalDateTime getTimestamp(Map<String, String> row, String key) {
        String val = getString(row, key);
        return (val == null) ? null : LocalDateTime.parse(val, TIMESTAMP_FORMATTER);
    }

    public void close() {
        try {
            csvReader.close();
        } catch (Exception e) {
            log.warn("Failed to close CSV reader", e);
        }
    }
}
