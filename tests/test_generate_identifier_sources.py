import csv
import tempfile
import unittest
from pathlib import Path

from scripts.generate_identifier_sources import identifier_sources, main, normalize_source


class GenerateIdentifierSourcesTest(unittest.TestCase):
    def test_normalize(self):
        self.assertEqual(normalize_source(" manual "), "MANUAL")
        self.assertEqual(normalize_source("Hospital  lab"), "HOSPITAL_LAB")
        self.assertEqual(normalize_source("ALIQUOT-IMPORTER"), "ALIQUOT-IMPORTER")
        self.assertIsNone(normalize_source(""))
        self.assertIsNone(normalize_source(None))

    def test_case_variants_are_one_term_and_blanks_are_dropped(self):
        rows = identifier_sources(["MANUAL", "manual", "", "HAMILTON", None])
        self.assertEqual([r["TERM"] for r in rows], ["HAMILTON", "MANUAL"])
        self.assertEqual(rows[1]["SYSTEM_URI"], "urn:placeholder:source:manual")

    def test_overlong_term_fails(self):
        with self.assertRaises(ValueError):
            identifier_sources(["X" * 65])

    def test_writes_vocabulary_csv(self):
        with tempfile.TemporaryDirectory() as directory:
            samples = Path(directory) / "sample.csv"
            samples.write_text("SAMPLEID,SOURCE\ns1,manual\ns2,MANUAL\ns3,\n")
            output = Path(directory) / "cv_identifier_source.csv"
            main(samples, output)
            rows = list(csv.DictReader(output.open()))
            self.assertEqual([(r["TERM"], r["NAME"]) for r in rows], [("MANUAL", "MANUAL")])


if __name__ == "__main__":
    unittest.main()
