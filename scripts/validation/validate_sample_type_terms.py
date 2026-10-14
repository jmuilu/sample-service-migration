"""Offline check of the sample type -> term mapping (sample-service ADR 0036, cv_sample_type).

cv_sample_type is keyed by `term`, and every dependent load (sample, sample_type_quality_metadata and the two
profile tables) carries the term, derived from the sample type NAME in its CSV. This script reads the local
exports, runs the real config/scripts/sample_type_transform.js functions under node, and fails (exit 1) if

  * a term is empty, longer than 64 characters or not unique across the legacy types,
  * a type name used by a dependent CSV is not a legacy type (the load would violate the foreign key), or
  * transformSampleTypeTerm(name) differs from transformAbbreviation(name, legacy abbreviation).

Needs no database. Run from the repository root: python3 scripts/validation/validate_sample_type_terms.py
"""
import csv
import json
import os
import subprocess
import sys

TYPES_CSV = "export/samplegroup.csv"
SCRIPT = "config/scripts/sample_type_transform.js"
MAX_TERM = 64

# (file, column holding a legacy sample type name)
USERS = [
    ("export/sample.csv", "SAMPLETYPE"),
    ("export/sample_type_quality_metadata.csv", "SAMPLETYPE"),
    ("export/sample_profile_primary_sample.csv", "SAMPLE_TYPE_NAME"),
    ("export/sample_profile_aliquot_sample_raw.csv", "PRIMARY_SAMPLE_TYPE_NAME"),
    ("export/sample_profile_aliquot_sample_raw.csv", "ALIQUOT_SAMPLE_TYPE_NAME"),
]

NODE_PROGRAM = r"""
const vm = require('vm'), fs = require('fs');
const ctx = {}; vm.createContext(ctx);
vm.runInContext(fs.readFileSync(process.argv[1], 'utf8'), ctx);
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const out = input.map(([name, abbr]) => [
    vm.runInContext('transformAbbreviation', ctx)(name, abbr),
    vm.runInContext('transformSampleTypeTerm', ctx)(name, null)]);
process.stdout.write(JSON.stringify(out));
"""


def read(path):
    with open(path, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main():
    types = read(TYPES_CSV)
    payload = [[t["NAME"].strip(), t["ABBREVIATION"].strip()] for t in types]
    result = subprocess.run(["node", "-e", NODE_PROGRAM, SCRIPT], input=json.dumps(payload),
                            capture_output=True, text=True, check=True)
    pairs = json.loads(result.stdout)

    errors = []
    term_of = {}
    by_term = {}
    for (name, abbr), (term, name_only_term) in zip(payload, pairs):
        if not term:
            errors.append(f"empty term for sample type '{name}'")
        elif len(term) > MAX_TERM:
            errors.append(f"term '{term}' of sample type '{name}' is {len(term)} characters (max {MAX_TERM})")
        if term != name_only_term:
            errors.append(f"'{name}' (legacy abbreviation '{abbr}'): transformAbbreviation gives '{term}', "
                          f"transformSampleTypeTerm gives '{name_only_term}'")
        if name in term_of:
            errors.append(f"duplicate legacy sample type name '{name}'")
        term_of[name] = term
        by_term.setdefault(term, []).append(name)
    for term, names in by_term.items():
        if len(names) > 1:
            errors.append(f"term '{term}' is not unique: {names}")

    print(f"{len(types)} legacy sample types -> {len(by_term)} distinct terms")
    for path, column in USERS:
        if not os.path.exists(path):
            print(f"  skipped {path} (not exported)")
            continue
        used = {}
        for row in read(path):
            name = (row.get(column) or "").strip()
            if name:
                used[name] = used.get(name, 0) + 1
        unknown = sorted(n for n in used if n not in term_of)
        for n in unknown:
            errors.append(f"{path} {column}: '{n}' is not a legacy sample type ({used[n]} rows)")
        print(f"  {path} {column}: {len(used)} distinct types, {sum(used.values())} rows, {len(unknown)} unknown")

    if errors:
        print("FAILED:")
        for e in errors:
            print("  - " + e)
        return 1
    print("OK: every type maps to exactly one unique term (<= 64 characters)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
