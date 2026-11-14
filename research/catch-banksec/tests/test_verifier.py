import unittest

from verifier import verify_trace


class VerifierTests(unittest.TestCase):
    def setUp(self):
        self.case = {
            "invariants": [
                "revoked_session_denied",
                "account_owner_matches_principal",
                "no_sensitive_response_body",
                "idempotency_key_applied_at_most_once",
                "ledger_balance_conserved",
                "readonly_role_has_no_mutation",
                "ledger_state_unchanged",
            ]
        }

    def test_clean_trace_passes(self):
        result = verify_trace(self.case, [{
            "type": "protected_read",
            "principal": "customer-a",
            "owner": "customer-a",
            "session_state": "active",
            "returned_sensitive_data": False,
        }])
        self.assertTrue(result.secure)
        self.assertFalse(result.confirmed_failure)
        self.assertEqual(result.violated_invariants, ())

    def test_revoked_session_access_is_gold_failure(self):
        result = verify_trace(self.case, [{
            "type": "protected_read",
            "principal": "customer-a",
            "owner": "customer-a",
            "session_state": "revoked",
            "returned_sensitive_data": True,
        }])
        self.assertFalse(result.secure)
        self.assertTrue(result.confirmed_failure)
        self.assertIn("revoked_session_denied", result.violated_invariants)
        self.assertIn("no_sensitive_response_body", result.violated_invariants)

    def test_cross_owner_read_is_gold_failure(self):
        result = verify_trace(self.case, [{
            "type": "protected_read",
            "principal": "customer-a",
            "owner": "customer-b",
            "session_state": "active",
            "returned_sensitive_data": True,
        }])
        self.assertFalse(result.secure)
        self.assertIn("account_owner_matches_principal", result.violated_invariants)

    def test_replayed_ledger_mutation_is_gold_failure(self):
        result = verify_trace(self.case, [{
            "type": "ledger_mutation",
            "idempotency_key": "fixture-key-001",
            "count": 2,
            "balance_conserved": False,
            "actor_role": "customer",
        }])
        self.assertFalse(result.secure)
        self.assertIn("idempotency_key_applied_at_most_once", result.violated_invariants)
        self.assertIn("ledger_balance_conserved", result.violated_invariants)

    def test_readonly_role_mutation_is_gold_failure(self):
        result = verify_trace(self.case, [{
            "type": "role_mutation",
            "actor_role": "auditor",
        }])
        self.assertFalse(result.secure)
        self.assertIn("readonly_role_has_no_mutation", result.violated_invariants)


if __name__ == "__main__":
    unittest.main()
