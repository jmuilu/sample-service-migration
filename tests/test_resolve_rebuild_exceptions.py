import csv
import tempfile
import unittest
from pathlib import Path

from scripts.resolve_rebuild_exceptions import apply, deduplicate_events, move_orphans_to_trash


class RebuildExceptionsTest(unittest.TestCase):
    def test_trash_only_orphans_and_preserve_original(self):
        rows = [dict(PLACECODE="A1", CONTAINER_NAME="", SAMPLE_STATUS="Available"),
                dict(PLACECODE="A2", CONTAINER_NAME="Box", SAMPLE_STATUS="Available"),
                dict(PLACECODE="", CONTAINER_NAME="", SAMPLE_STATUS="Pending")]
        kept, exceptions = move_orphans_to_trash(rows)
        self.assertEqual(len(exceptions), 1)
        self.assertEqual(exceptions[0]["PLACECODE"], "A1")
        self.assertEqual(kept[0], dict(PLACECODE="", CONTAINER_NAME="Trash", SAMPLE_STATUS="Not available"))
        self.assertEqual(kept[1]["CONTAINER_NAME"], "Box")
        self.assertEqual(kept[2]["SAMPLE_STATUS"], "Pending")

    def test_lowest_numeric_id_and_normalized_type(self):
        def event(i, kind, comment):
            return dict(ID=str(i), SAMPLEID="test", EVENT_TYPE=kind, EVENT_TIME="2026-01-01", COMMENT=comment)
        kept, rejected = deduplicate_events([event(10, "DISCARDED", "ten"),
                                            event(2, "NOT_AVAILABLE", "two"),
                                            event(3, "AVAILABLE", "three")])
        self.assertEqual([r["ID"] for r in kept], ["2", "3"])
        self.assertEqual(rejected[0]["COMMENT"], "ten")

    def test_reports_and_original_survive_rerun(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.csv"
            path.write_text("PLACECODE,CONTAINER_NAME,SAMPLE_STATUS\nA1,,Available\n")
            reports = Path(directory) / "reports"
            self.assertEqual(apply(path, reports, move_orphans_to_trash, "exceptions.csv"), 1)
            evidence = (reports / "exceptions.csv").read_bytes()
            self.assertEqual(apply(path, reports, move_orphans_to_trash, "exceptions.csv"), 0)
            self.assertEqual((reports / "exceptions.csv").read_bytes(), evidence)
            self.assertIn("A1,,Available", (reports / "sample_original.csv").read_text())
