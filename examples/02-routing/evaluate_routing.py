"""Score the router against the labelled set in golden.json. No model or credentials needed.

Metrics: accuracy, fallback rate, and wrong-route rate (a request sent to the wrong specialist).
Cases marked known_gap are documented paraphrase misses: they are reported but excluded from the
thresholds. A wrong route is worse than a fallback, so it has the tightest threshold.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from routing import FALLBACK, route_request

MIN_ACCURACY = 0.9
MAX_WRONG_ROUTE_RATE = 0.0


def score(cases: list[dict]) -> dict:
    gaps = [c for c in cases if c.get("known_gap")]
    cases = [c for c in cases if not c.get("known_gap")]
    results = [(c, route_request(c["request"]).name) for c in cases]
    correct = sum(1 for c, got in results if got == c["route"])
    wrong = [c["request"] for c, got in results if got != c["route"] and got != FALLBACK]
    missed = [c["request"] for c, got in results if got == FALLBACK and c["route"] != FALLBACK]
    return {
        "cases": len(cases),
        "accuracy": correct / len(cases),
        "wrong_route_rate": len(wrong) / len(cases),
        "fallback_rate": sum(1 for _, got in results if got == FALLBACK) / len(cases),
        "known_gaps_still_missed": [c["request"] for c in gaps if route_request(c["request"]).name != c["route"]],
        "wrong_routes": wrong,
        "missed_to_review": missed,
    }


def main() -> None:
    cases = json.loads((Path(__file__).parent / "golden.json").read_text())
    report = score(cases)
    print(json.dumps(report, indent=2))
    problems = []
    if report["accuracy"] < MIN_ACCURACY:
        problems.append(f"accuracy {report['accuracy']:.2f} < {MIN_ACCURACY}")
    if report["wrong_route_rate"] > MAX_WRONG_ROUTE_RATE:
        problems.append(f"wrong_route_rate {report['wrong_route_rate']:.2f} > {MAX_WRONG_ROUTE_RATE}")
    if problems:
        raise SystemExit("Routing evaluation failed: " + "; ".join(problems))
    print("Routing evaluation passed.")


if __name__ == "__main__":
    main()
