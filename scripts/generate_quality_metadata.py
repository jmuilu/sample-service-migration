import csv
import os

# Baseline (sample_type, quality) whitelist, curated ahead of any specific export.
# Kept even for combinations not observed in a given DB2 export, so the whitelist doesn't
# shrink between migration runs against smaller test datasets.
BASE_PAIRS = [
    ("DNA", "BLOODY"),
    ("DNA", "CENTRIFUGED"),
    ("DNA", "CLOTTED"),
    ("DNA", "TRANSPORT_PROBLEM"),
    ("EDTA Whole blood", "BLOODY"),
    ("EDTA Whole blood", "CENTRIFUGED"),
    ("EDTA Whole blood", "CLOTTED"),
    ("EDTA Whole blood", "CLOUDY"),
    ("EDTA Whole blood", "CONTAMINATED"),
    ("EDTA Whole blood", "HEMOLYTIC"),
    ("EDTA Plasma", "CLOTTED"),
]


def load_sample_types(sample_csv):
    sample_type = {}
    if not os.path.exists(sample_csv):
        return sample_type
    with open(sample_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sample_type[row["SAMPLEID"]] = row["SAMPLETYPE"]
    return sample_type


def load_observed_pairs(sample_quality_csv, sample_type):
    pairs = set()
    if not os.path.exists(sample_quality_csv):
        return pairs
    with open(sample_quality_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sid = row["SAMPLE_10002_SAMPLEID"]
            quality = row["QUALITY"]
            stype = sample_type.get(sid)
            if stype and quality:
                pairs.add((stype, quality))
    return pairs


def generate_quality_metadata():
    sample_type = load_sample_types("export/sample.csv")
    observed = load_observed_pairs("export/sample_quality.csv", sample_type)

    all_pairs = list(BASE_PAIRS)
    seen = set(BASE_PAIRS)
    for pair in sorted(observed):
        if pair not in seen:
            all_pairs.append(pair)
            seen.add(pair)
            print(f"✓ Added observed (sample_type, quality) pair not in base whitelist: {pair}")

    with open("export/sample_type_quality_metadata.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["SAMPLETYPE", "QUALITY", "USERNAME", "VERSION"])
        for sample_type_name, quality in all_pairs:
            writer.writerow([sample_type_name, quality, "migration", 1])


if __name__ == "__main__":
    generate_quality_metadata()
