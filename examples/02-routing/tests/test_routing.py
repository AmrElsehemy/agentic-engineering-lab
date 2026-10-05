import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
from routing import FALLBACK, route_request


class RoutingTests(unittest.TestCase):
    def test_each_specialist_is_reachable(self):
        self.assertEqual(route_request("How do we catch a regression?").name, "evaluation")
        self.assertEqual(route_request("How do we secure and observe deployment?").name, "production")
        self.assertEqual(route_request("Show me a tool-calling pattern").name, "agent-pattern")

    def test_unmatched_request_goes_to_human_review(self):
        route = route_request("something unrelated")
        self.assertEqual(route.name, FALLBACK)
        self.assertIn("did not match", route.reason)

    def test_overlapping_matches_use_priority_and_say_so(self):
        route = route_request("How should we evaluate tool selection?")
        self.assertEqual(route.name, "evaluation")
        self.assertIn("also matched: agent-pattern", route.reason)

    def test_keywords_match_word_starts_only(self):
        self.assertEqual(route_request("agentic workflows").name, "agent-pattern")
        self.assertEqual(route_request("evaluating outputs").name, "evaluation")
        self.assertEqual(route_request("team management").name, FALLBACK)
        self.assertEqual(route_request("an insecure habit").name, FALLBACK)

    def test_case_and_whitespace_are_ignored(self):
        self.assertEqual(route_request("  EVALUATE the QUALITY  ").name, "evaluation")

    def test_empty_request_is_rejected(self):
        for blank in ("", "   "):
            with self.assertRaises(ValueError):
                route_request(blank)


if __name__ == "__main__":
    unittest.main()
