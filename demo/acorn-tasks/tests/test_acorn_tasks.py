import importlib.util
import json
from pathlib import Path
import unittest


MODULE = Path(__file__).resolve().parents[1] / "src" / "acorn_tasks.py"
SPEC = importlib.util.spec_from_file_location("acorn_tasks", MODULE)
acorn_tasks = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(acorn_tasks)


class TaskInboxTests(unittest.TestCase):
    def test_submit_returns_pending_task_and_list_exposes_it(self):
        inbox = acorn_tasks.TaskInbox()
        self.assertEqual(inbox.submit("  Water the paper fern  "), {
            "id": "task-001", "title": "Water the paper fern", "status": "pending"
        })
        self.assertEqual(inbox.list_tasks(), [{
            "id": "task-001", "title": "Water the paper fern", "status": "pending"
        }])

    def test_complete_changes_visible_state_and_duplicate_completion_is_safe(self):
        inbox = acorn_tasks.TaskInbox()
        inbox.submit("Sort the wooden stars")
        self.assertEqual(inbox.complete("task-001")["status"], "complete")
        self.assertEqual(inbox.complete("task-001")["status"], "complete")
        self.assertEqual(len(inbox.list_tasks()), 1)

    def test_unknown_task_cannot_change_another_task(self):
        inbox = acorn_tasks.TaskInbox()
        inbox.submit("Fold a blue kite")
        with self.assertRaises(KeyError):
            inbox.complete("task-999")
        self.assertEqual(inbox.list_tasks()[0]["status"], "pending")

    def test_empty_submission_does_not_allocate_an_id(self):
        inbox = acorn_tasks.TaskInbox()
        with self.assertRaises(ValueError):
            inbox.submit("  ")
        self.assertEqual(inbox.submit("Draw a tiny moon")["id"], "task-001")

    def test_duplicate_submission_creates_separate_tasks(self):
        inbox = acorn_tasks.TaskInbox()
        inbox.submit("Count the toy acorns")
        inbox.submit("Count the toy acorns")
        self.assertEqual([task["id"] for task in inbox.list_tasks()], ["task-001", "task-002"])

    def test_restart_starts_an_empty_inbox(self):
        inbox = acorn_tasks.TaskInbox()
        inbox.submit("Draw a tiny moon")
        self.assertEqual(acorn_tasks.TaskInbox().list_tasks(), [])

    def test_returned_data_cannot_mutate_inbox(self):
        inbox = acorn_tasks.TaskInbox()
        submitted = inbox.submit("Fold a blue kite")
        submitted["status"] = "complete"
        tasks = inbox.list_tasks()
        tasks[0]["title"] = "Different title"
        self.assertEqual(inbox.list_tasks(), [{
            "id": "task-001", "title": "Fold a blue kite", "status": "pending"
        }])

    def test_fictional_runtime_effects_match_executable_actions(self):
        path = MODULE.parents[1] / "runtime" / "sample-run.json"
        record = json.loads(path.read_text())
        self.assertTrue(record["synthetic"])
        self.assertIsNone(record["acceptance"])
        inbox = acorn_tasks.TaskInbox()
        for event in record["events"]:
            if event["action"] == "submit":
                result = inbox.submit(event["input"]["title"])
            elif event["action"] == "complete":
                result = inbox.complete(event["input"]["id"])
            else:
                self.assertEqual(event["action"], "list_tasks")
                result = inbox.list_tasks()
            self.assertEqual(result, event["output"])

    def test_runtime_record_contains_only_public_synthetic_values(self):
        text = (MODULE.parents[1] / "runtime" / "sample-run.json").read_text()
        self.assertNotRegex(text, r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
        self.assertNotRegex(text, r"/Users/|/home/|https?://|(?:access[_ -]?token|api[_ -]?key|secret|signature)\s*[\"=:]")
        record = json.loads(text)
        self.assertRegex(record["run_id"], r"^demo-run-\d{3}$")
        for event in record["events"]:
            for value in (event["input"], event["output"]):
                tasks = value if isinstance(value, list) else [value]
                for task in tasks:
                    if "id" in task:
                        self.assertRegex(task["id"], r"^task-\d{3}$")


if __name__ == "__main__":
    unittest.main()
