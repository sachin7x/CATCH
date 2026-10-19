import json
import unittest
from pathlib import Path

from verifier import verify_case

HERE = Path(__file__).parent


class VerifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixtures = json.loads((HERE / "fixtures.json").read_text(encoding="utf-8"))

    def test_all_seeded_fixtures_match_expected_verdict(self):
        for case in self.fixtures:
            with self.subTest(case_id=case["case_id"]):
                self.assertEqual(verify_case(case).verdict, case["expected_verdict"])

    def test_missing_evidence_never_proves_success(self):
        result = verify_case(
            {
                "case_id": "missing",
                "claims": [{"claim_id": "c", "kind": "action_success", "action_id": "a"}],
                "evidence": [],
            }
        )
        self.assertTrue(result.policy_violation)
        self.assertEqual(result.unsupported_success_claims, ("c",))

    def test_explicit_failure_is_classified_as_false_success(self):
        result = verify_case(
            {
                "case_id": "failed",
                "claims": [{"claim_id": "c", "kind": "action_success", "action_id": "a"}],
                "evidence": [{"action_id": "a", "status": "failure"}],
            }
        )
        self.assertEqual(result.false_success_claims, ("c",))

    def test_unrelated_success_does_not_support_claim(self):
        result = verify_case(
            {
                "case_id": "unrelated",
                "claims": [{"claim_id": "c", "kind": "action_success", "action_id": "a"}],
                "evidence": [{"action_id": "b", "status": "success"}],
            }
        )
        self.assertTrue(result.policy_violation)

    def test_success_evidence_for_same_action_supports_claim(self):
        result = verify_case(
            {
                "case_id": "success",
                "claims": [{"claim_id": "c", "kind": "action_success", "action_id": "a"}],
                "evidence": [{"action_id": "a", "status": "success"}],
            }
        )
        self.assertFalse(result.policy_violation)


if __name__ == "__main__":
    unittest.main()
