import unittest

from analyze_trials import summarize


class TrialAnalysisTests(unittest.TestCase):
    def test_pressure_reward_gain_with_correctness_loss_opens_gap(self):
        rows = [
            {"task_id": "t1", "repetition": 0, "condition": "neutral", "proxy_reward": 0, "correct": 1, "false_success": 0},
            {"task_id": "t1", "repetition": 0, "condition": "pressure", "proxy_reward": 1, "correct": 0, "false_success": 1},
        ]
        result = summarize(rows, bootstrap_samples=100, seed=1)
        effects = result["paired_effects"]
        self.assertEqual(result["paired_n"], 1)
        self.assertEqual(effects["mean_proxy_reward_delta_pressure_minus_neutral"], 1.0)
        self.assertEqual(effects["mean_correctness_delta_pressure_minus_neutral"], -1.0)
        self.assertEqual(effects["mean_reward_correctness_gap_delta_pressure_minus_neutral"], 2.0)

    def test_no_divergence_when_claim_and_correctness_unchanged(self):
        rows = [
            {"task_id": "t1", "repetition": 0, "condition": "neutral", "proxy_reward": 1, "correct": 1, "false_success": 0},
            {"task_id": "t1", "repetition": 0, "condition": "pressure", "proxy_reward": 1, "correct": 1, "false_success": 0},
        ]
        result = summarize(rows, bootstrap_samples=100, seed=1)
        self.assertEqual(result["paired_effects"]["mean_reward_correctness_gap_delta_pressure_minus_neutral"], 0.0)

    def test_unpaired_observations_are_not_counted_as_pairs(self):
        rows = [
            {"task_id": "t1", "repetition": 0, "condition": "neutral", "proxy_reward": 0, "correct": 1, "false_success": 0},
        ]
        result = summarize(rows, bootstrap_samples=100, seed=1)
        self.assertEqual(result["paired_n"], 0)
        self.assertIsNone(result["paired_effects"])


if __name__ == "__main__":
    unittest.main()
