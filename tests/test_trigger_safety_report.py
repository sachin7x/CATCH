import json
import tempfile
import unittest
from pathlib import Path

from scripts.benchmark.trigger_safety_report import build_report, load_records


class TriggerSafetyReportTests(unittest.TestCase):
    def test_paired_effect_disagreement_and_adjudication(self):
        rows = [
            {"case_id": "c1", "pair_id": "p1", "condition": "clean",
             "category": "benign", "evaluator_a_safe": True,
             "evaluator_b_safe": True, "adjudicated_safe": True},
            {"case_id": "t1", "pair_id": "p1", "condition": "trigger",
             "category": "benign", "evaluator_a_safe": False,
             "evaluator_b_safe": True, "adjudicated_safe": False},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "records.jsonl"
            path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
            report = build_report(load_records(path), path)
        self.assertEqual(report["paired_trigger_effect"]["evaluator_a"]["n_pairs"], 1)
        self.assertEqual(report["paired_trigger_effect"]["evaluator_a"]["safety_rate_change_pp"], -100.0)
        self.assertEqual(report["evaluator_disagreement"]["count"], 1)
        self.assertEqual(report["adjudication"]["evaluator_a"]["false_negative_unsafe"], 0)
        self.assertEqual(report["adjudication"]["evaluator_a"]["true_positive_unsafe"], 1)

    def test_missing_pairs_are_not_imputed(self):
        row = {"case_id": "c1", "pair_id": "p1", "condition": "clean",
               "category": "benign", "evaluator_a_safe": True,
               "evaluator_b_safe": True}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "records.jsonl"
            path.write_text(json.dumps(row) + "\n")
            report = build_report(load_records(path), path)
        self.assertEqual(report["paired_trigger_effect"]["evaluator_a"]["n_pairs"], 0)


    def test_rejects_duplicate_pair_condition(self):
        row = {"case_id": "c1", "pair_id": "p1", "condition": "clean",
               "category": "benign", "evaluator_a_safe": True,
               "evaluator_b_safe": True}
        duplicate = {**row, "case_id": "c2"}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "records.jsonl"
            path.write_text("\n".join(json.dumps(r) for r in (row, duplicate)) + "\n")
            with self.assertRaisesRegex(ValueError, "duplicate pair/condition"):
                load_records(path)

    def test_rejects_non_string_condition(self):
        row = {"case_id": "c1", "pair_id": "p1", "condition": [],
               "category": "benign", "evaluator_a_safe": True,
               "evaluator_b_safe": True}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "records.jsonl"
            path.write_text(json.dumps(row) + "\n")
            with self.assertRaisesRegex(ValueError, "invalid condition"):
                load_records(path)

    def test_rejects_non_object_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "records.jsonl"
            path.write_text('["not", "a", "record"]\n')
            with self.assertRaisesRegex(ValueError, "must be an object"):
                load_records(path)


if __name__ == "__main__":
    unittest.main()
