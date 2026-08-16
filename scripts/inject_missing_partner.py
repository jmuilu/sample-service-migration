import csv
import os

def inject_missing_partner():
    partner_csv = "export/partner.csv"
    project_csv = "export/project.csv"
    membership_csv = "export/project_membership.csv"

    # 1. Ensure Missing Partner is in partner.csv
    if os.path.exists(partner_csv):
        with open(partner_csv, "r", encoding="utf-8") as f:
            content = f.read()
        if "Missing Partner" not in content:
            with open(partner_csv, "a", encoding="utf-8") as f:
                f.write("Missing Partner,migration,2026-07-08 00:00:00,INTERNAL,Missing partner placeholder,ACTIVE,OTHER,\n")
            print("✓ Injected 'Missing Partner' into partner.csv")

    # 2. Read all project abbreviations from project.csv
    abbrevs = []
    if os.path.exists(project_csv):
        with open(project_csv, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if header:
                abbr_idx = -1
                for idx, col in enumerate(header):
                    if col.upper() == "ABBREVIATION":
                        abbr_idx = idx
                        break
                if abbr_idx != -1:
                    for row in reader:
                        if len(row) > abbr_idx:
                            val = row[abbr_idx].strip()
                            if val and val not in abbrevs:
                                abbrevs.append(val)

    # 3. Add memberships for Missing Partner for all projects
    if os.path.exists(membership_csv) and abbrevs:
        existing_memberships = set()
        with open(membership_csv, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            for row in reader:
                if len(row) >= 5:
                    partner = row[3].strip()
                    proj = row[4].strip()
                    existing_memberships.add((partner, proj))

        with open(membership_csv, "a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            for abbr in abbrevs:
                if ("Missing Partner", abbr) not in existing_memberships:
                    writer.writerow(["migration", "2026-07-08 00:00:00", "DEFAULT", "Missing Partner", abbr])
                    print(f"✓ Injected membership: Missing Partner -> {abbr}")

if __name__ == "__main__":
    inject_missing_partner()
