"""Build the identifier-source vocabulary from the legacy SOURCE values (sample-service ADR 0049, todo D53).

Since ADR 0049 sample.sample.source is a foreign key to sample.cv_identifier_source, whose system_uri is the FHIR
Identifier.system of sourceid. Liquibase seeds only the system terms (BIOBANK, TUBE_BARCODE); the customer's sources
(importers, robots, hospital systems) are reference data from the legacy samples. Each distinct SOURCE becomes one
term, normalized as transformIdentifierSource in config/scripts/sample_transform.js does, so 'manual' and 'MANUAL'
are one source. The URIs are placeholders until the terminology owner names the real namespaces.

Writes export/cv_identifier_source.csv, loaded by cv_identifier_source_manifest.yaml before the samples.
"""
import csv
import re
import sys

TERM_MAX_LENGTH = 64
URI_PREFIX = "urn:placeholder:source:"


def normalize_source(value):
    """Trimmed, upper case, inner whitespace as '_'; blank is None. Must agree with transformIdentifierSource."""
    normalized = re.sub(r"\s+", "_", (value or "").strip().upper())
    return normalized or None


def identifier_sources(values):
    """Distinct normalized terms of the given SOURCE values, as vocabulary rows in term order."""
    terms = sorted({t for t in (normalize_source(v) for v in values) if t})
    too_long = [t for t in terms if len(t) > TERM_MAX_LENGTH]
    if too_long:
        raise ValueError(f"identifier source terms longer than {TERM_MAX_LENGTH}: {too_long}")
    return [{"TERM": t, "NAME": t, "SYSTEM_URI": URI_PREFIX + t.lower(),
             "DESCRIPTION": "Legacy DB2 sample source; placeholder system URI"} for t in terms]


def main(samples_path="export/sample.csv", output_path="export/cv_identifier_source.csv"):
    with open(samples_path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if "SOURCE" not in (reader.fieldnames or []):
            sys.exit(f"{samples_path} has no SOURCE column")
        rows = identifier_sources(row["SOURCE"] for row in reader)
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["TERM", "NAME", "SYSTEM_URI", "DESCRIPTION"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"✓ Wrote {len(rows)} identifier sources to {output_path}: " + ", ".join(r["TERM"] for r in rows))


if __name__ == "__main__":
    main()
