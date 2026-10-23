import json
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
from routing import FALLBACK, route_request


# Golden cases: any change to routing rules must update this table on purpose.
GOLDEN = (
    ("How do we catch a regression?", "evaluation"),
    ("How should we evaluate tool selection?", "evaluation"),
    ("Is output quality getting worse?", "evaluation"),
    ("How do we secure and observe deployment?", "production"),
    ("Which identity should the agent run as?", "production"),
    ("Show me a tool-calling pattern", "agent-pattern"),
    ("Explain function calling", "agent-pattern"),
    ("how do we know it still works?", FALLBACK),
    ("team management", FALLBACK),
    ("hello", FALLBACK),
)


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

    def test_golden_cases(self):
        for request, expected in GOLDEN:
            with self.subTest(request=request):
                self.assertEqual(route_request(request).name, expected)

    def test_every_route_has_a_reason(self):
        for request, _ in GOLDEN:
            self.assertTrue(route_request(request).reason)

    def test_non_string_request_is_rejected(self):
        for bad in (None, 3, ["tool"]):
            with self.assertRaises(TypeError):
                route_request(bad)

    def test_routing_is_deterministic(self):
        first = route_request("evaluate tool security")
        self.assertEqual([route_request("evaluate tool security") for _ in range(5)], [first] * 5)

    def test_cli_prints_json_route(self):
        out = subprocess.run(
            [sys.executable, str(Path(__file__).parents[1] / "routing.py"), "Show me a tool pattern"],
            capture_output=True, text=True, check=True,
        ).stdout
        self.assertEqual(json.loads(out)["name"], "agent-pattern")


if __name__ == "__main__":
    unittest.main()
