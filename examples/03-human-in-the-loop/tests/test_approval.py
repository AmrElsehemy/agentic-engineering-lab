import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
from approval import ApprovalRequest, Decision


class ApprovalTests(unittest.TestCase):
    def setUp(self):
        self.request = ApprovalRequest("send a report", "user asked for a weekly summary")

    def test_a_new_request_is_pending_and_cannot_execute(self):
        self.assertIs(self.request.decision, Decision.PENDING)
        self.assertFalse(self.request.can_execute())

    def test_approval_allows_execution(self):
        self.request.decide(Decision.APPROVED)
        self.assertTrue(self.request.can_execute())

    def test_rejection_is_a_safe_terminal_state(self):
        self.request.decide(Decision.REJECTED)
        self.assertFalse(self.request.can_execute())

    def test_a_decision_cannot_be_changed(self):
        self.request.decide(Decision.REJECTED)
        with self.assertRaises(ValueError):
            self.request.decide(Decision.APPROVED)
        self.assertFalse(self.request.can_execute())

    def test_pending_is_not_a_valid_decision(self):
        with self.assertRaises(ValueError):
            self.request.decide(Decision.PENDING)
        self.assertIs(self.request.decision, Decision.PENDING)

    def test_the_proposed_action_and_reason_are_kept_with_the_decision(self):
        self.request.decide(Decision.APPROVED)
        self.assertEqual((self.request.action, self.request.reason), ("send a report", "user asked for a weekly summary"))


if __name__ == "__main__":
    unittest.main()
