import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
import agent
from scripted_client import ScriptedClient, text, tool_call, tool_calls

GOOD = {"goal": "HYROX preparation", "days_available": 3}


def run(responses, **kwargs):
    client = ScriptedClient(responses)
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        answer = agent.run_agent(client, "m", kwargs.pop("goal", "plan please"), **kwargs)
    events = [json.loads(l) for l in out.getvalue().splitlines() if l.startswith("{")]
    return client, answer, events


class EnvFileTests(unittest.TestCase):
    def test_parse_and_precedence(self):
        import os
        import envfile
        parsed = envfile.parse("# c\nexport A=1\nB='two words'\nC=\"x=y\"\n\nbad line\n")
        self.assertEqual(parsed, {"A": "1", "B": "two words", "C": "x=y"})
        path = Path(tempfile.mkdtemp()) / "t.env"
        path.write_text("LAB_TEST_A=file\nLAB_TEST_B=file\n")
        os.environ["LAB_TEST_A"] = "real"
        os.environ["LAB_ENV_FILE"] = str(path)
        try:
            envfile.load_env()
            self.assertEqual(os.environ["LAB_TEST_A"], "real")
            self.assertEqual(os.environ["LAB_TEST_B"], "file")
        finally:
            for k in ("LAB_TEST_A", "LAB_TEST_B", "LAB_ENV_FILE"):
                os.environ.pop(k, None)


class LiveEvaluatorTests(unittest.TestCase):
    """The live evaluator's assertions, checked against synthetic traces (no network)."""

    def setUp(self):
        sys.path.insert(0, str(Path(__file__).parents[3]))
        import evaluate_live
        self.check = evaluate_live.check
        self.store = Path(tempfile.mkdtemp()) / "plans.jsonl"

    PLAN = [
        {"event": "model_response", "step": 1, "tool_calls": [{"name": "get_training_plan"}]},
        {"event": "tool_executed", "tool": "get_training_plan", "outcome": "ok"},
        {"event": "model_response", "step": 2, "tool_calls": []},
        {"event": "quality_check", "passed": True},
    ]

    def test_trailing_quality_check_event_is_not_a_failure(self):
        self.assertEqual(self.check("plan", self.PLAN, self.store), [])

    def test_plan_without_tool_fails(self):
        events = [{"event": "model_response", "step": 1, "tool_calls": []}]
        self.assertTrue(self.check("plan", events, self.store))

    def test_denied_scenario_is_inconclusive_if_save_never_attempted(self):
        events = [{"event": "model_response", "step": 1, "tool_calls": []}]
        self.assertTrue(any("not exercised" in p for p in self.check("denied", events, self.store)))

    def test_denied_scenario_passes_when_attempt_was_denied(self):
        events = [
            {"event": "model_response", "step": 1, "tool_calls": [{"name": "save_plan"}]},
            {"event": "approval", "tool": "save_plan", "approved": False},
            {"event": "tool_executed", "tool": "save_plan", "outcome": "denied"},
            {"event": "model_response", "step": 2, "tool_calls": []},
        ]
        self.assertEqual(self.check("denied", events, self.store), [])


class TracingTests(unittest.TestCase):
    def test_tool_execution_gets_a_span_with_the_tool_name(self):
        recorded = []

        class FakeSpan:
            def set_attribute(self, key, value):
                recorded.append((key, value))

        class FakeTracer:
            def start_as_current_span(self, name):
                recorded.append(("span", name))
                return contextlib.nullcontext(FakeSpan())

        client = ScriptedClient([tool_call("get_training_plan", GOOD), text("done")])
        with contextlib.redirect_stdout(io.StringIO()):
            agent.run_agent(client, "m", "plan please", tracer=FakeTracer())
        self.assertIn(("span", "agent.tool_execution"), recorded)
        self.assertIn(("agent.tool", "get_training_plan"), recorded)
        self.assertIn(("span", "agent.model_response"), recorded)


class ToolTests(unittest.TestCase):
    def test_sessions_match_days(self):
        for days in range(1, 8):
            self.assertEqual(len(agent.get_training_plan("g", days)["sessions"]), days)

    def test_rejects_bad_days(self):
        for bad in (0, 8, -1, True, "3", None, 2.5):
            with self.assertRaises(ValueError, msg=repr(bad)):
                agent.get_training_plan("g", bad)

    def test_rejects_long_goal(self):
        with self.assertRaises(ValueError):
            agent.get_training_plan("x" * 501, 3)


class LoopTests(unittest.TestCase):
    def setUp(self):
        self.store = Path(tempfile.mkdtemp()) / "plans.jsonl"

    def test_model_may_choose_no_tool(self):
        client, answer, events = run([text("HYROX is a fitness race.")], store=self.store)
        self.assertEqual(answer, "HYROX is a fitness race.")
        self.assertEqual(client.calls[0]["tool_choice"], "auto")
        self.assertFalse([e for e in events if e["event"] == "tool_executed"])

    def test_tool_result_reaches_model(self):
        client, answer, _ = run([tool_call("get_training_plan", GOOD), text("done")], store=self.store)
        self.assertEqual(answer, "done")
        tool_message = client.calls[1]["messages"][-1]
        self.assertEqual(tool_message["role"], "tool")
        self.assertEqual(json.loads(tool_message["content"])["days_available"], 3)

    def test_missing_days_is_not_invented(self):
        client, _, events = run(
            [tool_call("get_training_plan", {"goal": "HYROX"}), text("How many days can you train?")],
            store=self.store,
        )
        self.assertIn("error", json.loads(client.calls[1]["messages"][-1]["content"]))
        self.assertEqual([e["outcome"] for e in events if e["event"] == "tool_executed"], ["invalid_arguments"])

    def test_bad_arguments_return_errors_instead_of_crashing(self):
        for raw in ("{not json", "[1]", json.dumps({**GOOD, "athlete": "x"}), json.dumps({**GOOD, "days_available": 99})):
            client, _, _ = run([tool_call("get_training_plan", raw), text("ok")], store=self.store)
            self.assertIn("error", json.loads(client.calls[1]["messages"][-1]["content"]), raw)

    def test_unknown_tool_blocked(self):
        client, _, events = run([tool_call("delete_everything", {}), text("ok")], store=self.store)
        self.assertIn("error", json.loads(client.calls[1]["messages"][-1]["content"]))
        self.assertEqual([e["outcome"] for e in events if e["event"] == "tool_executed"], ["blocked"])

    def test_only_first_tool_call_runs(self):
        _, _, events = run(
            [tool_calls(("get_training_plan", GOOD), ("get_training_plan", GOOD)), text("ok")], store=self.store
        )
        self.assertEqual([e["outcome"] for e in events if e["event"] == "tool_executed"], ["ok", "skipped"])

    def test_side_effect_denied_by_default(self):
        _, _, events = run([tool_call("save_plan", GOOD), text("ok")], store=self.store)
        self.assertFalse(self.store.exists())
        self.assertEqual([e["outcome"] for e in events if e["event"] == "tool_executed"], ["denied"])

    def test_side_effect_runs_once_when_approved(self):
        run([tool_call("save_plan", GOOD), text("ok")], approver=agent.approve_all, store=self.store)
        lines = self.store.read_text().splitlines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(json.loads(lines[0])["days_available"], 3)

    def test_repeated_approved_save_is_idempotent(self):
        for _ in range(3):
            run([tool_call("save_plan", GOOD), text("ok")], approver=agent.approve_all, store=self.store)
        self.assertEqual(len(self.store.read_text().splitlines()), 1)
        self.assertTrue(agent.save_plan(GOOD["goal"], GOOD["days_available"], self.store)["already_saved"])

    def test_different_plan_is_saved_separately(self):
        agent.save_plan("HYROX", 3, self.store)
        self.assertFalse(agent.save_plan("HYROX", 4, self.store)["already_saved"])
        self.assertEqual(len(self.store.read_text().splitlines()), 2)

    def test_invalid_save_never_asks_for_approval(self):
        asked = []
        def approver(name, arguments):
            asked.append(name)
            return True
        run([tool_call("save_plan", {"goal": "g", "days_available": 99}), text("ok")], approver=approver, store=self.store)
        self.assertEqual(asked, [])
        self.assertFalse(self.store.exists())

    def test_loop_is_bounded_and_last_call_has_no_tools(self):
        responses = [tool_call("get_training_plan", GOOD, f"c{i}") for i in range(3)] + [text("final")]
        client, answer, _ = run(responses, store=self.store)
        self.assertEqual(len(client.calls), 4)
        self.assertEqual(client.calls[-1]["tool_choice"], "none")
        self.assertEqual(answer, "final")

    def test_contradictory_final_answer_fails_the_run(self):
        with self.assertRaises(RuntimeError):
            run([tool_call("get_training_plan", GOOD), text("Here is your 5-day plan.")], store=self.store)

    def test_consistent_final_answer_passes_quality_check(self):
        _, _, events = run([tool_call("get_training_plan", GOOD), text("Here is your 3-day plan.")], store=self.store)
        self.assertTrue([e for e in events if e["event"] == "quality_check"][0]["passed"])

    def test_long_goal_rejected_before_any_model_call(self):
        client = ScriptedClient([])
        with self.assertRaises(ValueError):
            agent.run_agent(client, "m", "x" * 501)
        self.assertEqual(client.calls, [])

    def test_trace_is_redacted_by_default(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            agent.run_agent(ScriptedClient([tool_call("get_training_plan", GOOD), text("secret answer")]), "m", "private goal")
        for leaked in ("HYROX preparation", "secret answer", "private goal", "sessions"):
            self.assertNotIn(leaked, out.getvalue())


if __name__ == "__main__":
    unittest.main()
