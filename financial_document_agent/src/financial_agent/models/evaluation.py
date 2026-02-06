"""Evaluation and consistency models."""

from pydantic import BaseModel, Field

from ..config.constants import ConsistencyStatus, WorthinessDecision


class AccountConsistency(BaseModel):
    """Account consistency check results."""

    status: ConsistencyStatus = Field(
        default=ConsistencyStatus.PARTIAL,
        description="Consistency status",
    )
    flags: list[str] = Field(
        default_factory=list,
        description="List of consistency issues or flags",
    )

    def add_flag(self, flag: str) -> None:
        """Add a consistency flag."""
        self.flags.append(flag)

    @property
    def is_consistent(self) -> bool:
        """Check if the account is fully consistent."""
        return self.status == ConsistencyStatus.CONSISTENT


class EvaluationResult(BaseModel):
    """Financial worthiness evaluation result."""

    threshold_eur: float = Field(..., ge=0.0, description="Threshold used in EUR")
    decision: WorthinessDecision = Field(..., description="Worthiness decision")
    reason: str = Field(..., description="Reason for the decision")
    evaluated_amount_eur: float | None = Field(
        default=None,
        description="Amount evaluated in EUR",
    )

    @classmethod
    def worthy(cls, threshold: float, amount: float, reason: str) -> "EvaluationResult":
        """Create a WORTHY result."""
        return cls(
            threshold_eur=threshold,
            decision=WorthinessDecision.WORTHY,
            reason=reason,
            evaluated_amount_eur=amount,
        )

    @classmethod
    def not_worthy(cls, threshold: float, amount: float, reason: str) -> "EvaluationResult":
        """Create a NOT_WORTHY result."""
        return cls(
            threshold_eur=threshold,
            decision=WorthinessDecision.NOT_WORTHY,
            reason=reason,
            evaluated_amount_eur=amount,
        )

    @classmethod
    def inconclusive(cls, threshold: float, reason: str) -> "EvaluationResult":
        """Create an INCONCLUSIVE result."""
        return cls(
            threshold_eur=threshold,
            decision=WorthinessDecision.INCONCLUSIVE,
            reason=reason,
        )
