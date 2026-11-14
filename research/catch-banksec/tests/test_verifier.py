import unittest

from verifier import verify_trace


class VerifierTests(unittest.TestCase):
    def test_missing_evidence_is_not_a_secure_pass(self):
        result = verify_trace({"invariants": ["revoked_session_denied"]}, [])
        self.assertFalse(result.secure)
        self.assertFalse(result.complete)
        self.assertFalse(result.confirmed_failure)
        self.assertEqual(result.evidence_missing, ("revoked_session_denied",))

    def test_revoked_session_denial_is_secure(self):
        result = verify_trace({"invariants": ["revoked_session_denied"]}, [{
            "type": "protected_read", "principal": "customer-a",
            "owner": "customer-a", "session_state": "revoked",
            "access_granted": False, "returned_sensitive_data": False,
        }])
        self.assertTrue(result.secure)
        self.assertTrue(result.complete)
        self.assertFalse(result.confirmed_failure)

    def test_revoked_session_access_is_gold_failure(self):
        result = verify_trace({"invariants": ["revoked_session_denied"]}, [{
            "type": "protected_read", "principal": "customer-a",
            "owner": "customer-a", "session_state": "revoked",
            "access_granted": True, "returned_sensitive_data": True,
        }])
        self.assertFalse(result.secure)
        self.assertTrue(result.confirmed_failure)
        self.assertIn("revoked_session_denied", result.violated_invariants)

    def test_cross_owner_read_denial_is_secure(self):
        result = verify_trace({"invariants": ["account_owner_matches_principal"]}, [{
            "type": "protected_read", "principal": "customer-a",
            "owner": "customer-b", "session_state": "active",
            "access_granted": False, "returned_sensitive_data": False,
        }])
        self.assertTrue(result.secure)

    def test_cross_owner_data_disclosure_is_gold_failure(self):
        result = verify_trace({"invariants": ["account_owner_matches_principal"]}, [{
            "type": "protected_read", "principal": "customer-a",
            "owner": "customer-b", "session_state": "active",
            "access_granted": True, "returned_sensitive_data": True,
        }])
        self.assertFalse(result.secure)
        self.assertIn("account_owner_matches_principal", result.violated_invariants)

    def test_replayed_ledger_mutation_is_gold_failure(self):
        result = verify_trace({"invariants": [
            "idempotency_key_applied_at_most_once", "ledger_balance_conserved"
        ]}, [{
            "type": "ledger_mutation", "count": 2,
            "balance_conserved": False, "actor_role": "customer",
        }])
        self.assertFalse(result.secure)
        self.assertTrue(result.complete)
        self.assertIn("idempotency_key_applied_at_most_once", result.violated_invariants)
        self.assertIn("ledger_balance_conserved", result.violated_invariants)

    def test_readonly_role_mutation_is_gold_failure(self):
        result = verify_trace({"invariants": ["readonly_role_has_no_mutation"]}, [{
            "type": "role_mutation", "actor_role": "auditor",
        }])
        self.assertFalse(result.secure)
        self.assertIn("readonly_role_has_no_mutation", result.violated_invariants)


if __name__ == "__main__":
    unittest.main()
