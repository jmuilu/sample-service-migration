import csv

# sample-service ADR 0036 (v029): only a container of a FREEZER type has a temperature; a database trigger
# rejects the row otherwise. DB2 CONTAINER.TEMPERATURE is free-form, so a temperature on a container whose type
# is not a freezer is blanked here and reported instead of failing the load. A freezer type is one whose
# BASETYPE is 'freezer' (config/scripts/container_type_transform.js maps nothing else to FREEZER).
# sample.container_type.temperature is not loaded at all: it stays NULL (the customer sets it).
FREEZER_BASETYPE = "FREEZER"


def filter_container_temperature():
    types_path = "export/containertype.csv"
    containers_path = "export/container.csv"

    with open(types_path, "r", encoding="utf-8", newline="") as f:
        freezer_types = {r["NAME"] for r in csv.DictReader(f)
                         if (r["BASETYPE"] or "").strip().upper() == FREEZER_BASETYPE}

    with open(containers_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    blanked = []
    for r in rows:
        if (r.get("TEMPERATURE") or "").strip() and r["TYPE"] not in freezer_types:
            blanked.append((r["NAME"], r["TYPE"], r["TEMPERATURE"]))
            r["TEMPERATURE"] = ""

    with open(containers_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"✓ Blanked the temperature of {len(blanked)} containers whose type is not a freezer "
          f"(sample.container.temperature is freezer-only).")
    for name, type_name, temperature in blanked:
        print(f"  {name} (type {type_name}): {temperature}")


if __name__ == "__main__":
    filter_container_temperature()
