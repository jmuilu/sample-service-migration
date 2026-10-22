import csv
import re
import tempfile
import unittest
from pathlib import Path

from scripts.complete_work_list_events import (CANCELLED_STATUSES, COMPLETED_STATUSES, main,
                                               missing_terminal_events)

EVENT_FIELDS = ["BATCH_ID", "BATCH_NAME", "ISPICK", "EVENT_TYPE", "FROM_STATUS", "TO_STATUS",
                "EVENT_TIME", "EVENT_USER", "PROJECT_ID", "EVENT_COMMENT"]


def batch(name, status, end_time="2026-09-08 00:00:00"):
    return dict(NAME=name, BATCH_STATUS=status, END_TIME=end_time, ISPICK="Y", USERNAME="user1", PROJECT_ID="7")


def event(name, kind, to_status, time="2026-09-01 10:00:00"):
    return dict(BATCH_ID="1", BATCH_NAME=name, EVENT_TYPE=kind, TO_STATUS=to_status, EVENT_TIME=time)


class CompleteWorkListEventsTest(unittest.TestCase):
    def test_created_only_completed_list_gets_completion_at_end_time(self):
        added, unresolved = missing_terminal_events(
            [batch("Release", "PICKING_COMPLETED")], [event("Release", "CREATED", "PICKING_COMPLETED")])
        self.assertEqual(unresolved, [])
        self.assertEqual(len(added), 1)
        self.assertEqual(added[0]["EVENT_TYPE"], "COMPLETED")
        self.assertEqual(added[0]["EVENT_TIME"], "2026-09-08 00:00:00")
        self.assertEqual(added[0]["EVENT_USER"], "user1")
        self.assertEqual(added[0]["BATCH_ID"], "1")

    def test_existing_completion_or_delivery_is_kept(self):
        lists = [batch("Picked", "PICKING_COMPLETED"), batch("Delivered", "SAMPLES_DELIVERED")]
        events = [event("Picked", "COMPLETED", "PICKING_COMPLETED"), event("Delivered", "DELIVERED", "SAMPLES_DELIVERED")]
        self.assertEqual(missing_terminal_events(lists, events), ([], []))

    def test_open_lists_are_ignored_and_cancelled_lists_get_cancellation(self):
        added, _ = missing_terminal_events(
            [batch("Open", "PICKING_IN_PROGRESS", ""), batch("Gone", "BATCH_CANCELED")], [])
        self.assertEqual([(a["BATCH_NAME"], a["EVENT_TYPE"]) for a in added], [("Gone", "CANCELLED")])

    def test_no_end_time_is_reported_not_invented(self):
        added, unresolved = missing_terminal_events([batch("NoEnd", "PICKING_COMPLETED", "")], [])
        self.assertEqual((added, unresolved), ([], ["NoEnd"]))

    def test_rerun_adds_nothing(self):
        with tempfile.TemporaryDirectory() as directory:
            lists = Path(directory) / "batch_list.csv"
            events = Path(directory) / "work_list_event.csv"
            with lists.open("w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=list(batch("x", "y")))
                writer.writeheader()
                writer.writerow(batch("Release", "PICKING_COMPLETED"))
            with events.open("w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=EVENT_FIELDS, extrasaction="ignore")
                writer.writeheader()
                writer.writerow(event("Release", "CREATED", "PICKING_COMPLETED"))
            main(lists, events)
            once = events.read_text()
            main(lists, events)
            self.assertEqual(events.read_text(), once)
            self.assertEqual(once.count("COMPLETED,PICKING_COMPLETED"), 1)

    def test_status_sets_match_the_list_status_transform(self):
        script = Path(__file__).resolve().parent.parent / "config/scripts/work_list_transform.js"
        body = script.read_text().split("function transformListStatus", 1)[1].split("\nfunction ", 1)[0]
        mapped = {}
        for block in re.findall(r"((?:case '[A-Z_]+':\s*)+)return '([A-Z]+)'", body):
            for status in re.findall(r"case '([A-Z_]+)'", block[0]):
                mapped[status] = block[1]
        self.assertEqual({s for s, t in mapped.items() if t == "COMPLETED"}, COMPLETED_STATUSES)
        self.assertEqual({s for s, t in mapped.items() if t == "CANCELLED"}, CANCELLED_STATUSES)


if __name__ == "__main__":
    unittest.main()
