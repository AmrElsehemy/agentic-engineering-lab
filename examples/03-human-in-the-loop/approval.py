"""Explicit approval flow: the model can propose, but cannot approve its own action."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Decision(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class ApprovalRequest:
    action: str
    reason: str
    decision: Decision = Decision.PENDING

    def decide(self, decision: Decision) -> None:
        if self.decision is not Decision.PENDING:
            raise ValueError("approval request is already decided")
        if decision not in (Decision.APPROVED, Decision.REJECTED):
            raise ValueError("decision must be approved or rejected")
        self.decision = decision

    def can_execute(self) -> bool:
        return self.decision is Decision.APPROVED


if __name__ == "__main__":
    request = ApprovalRequest("send a report", "user asked for a weekly summary")
    print({"action": request.action, "decision": request.decision.value, "can_execute": request.can_execute()})
