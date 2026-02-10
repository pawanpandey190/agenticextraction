"""Financial worthiness evaluation stage."""

from ...config.constants import ConsistencyStatus, WorthinessDecision
from ...config.settings import Settings
from ...models.evaluation import AccountConsistency, EvaluationResult
from ..base import PipelineContext, PipelineStage


class EvaluatorStage(PipelineStage):
    """Stage for evaluating financial worthiness."""

    def __init__(self, settings: Settings, threshold_eur: float | None = None, required_period_months: int | None = None) -> None:
        super().__init__(settings)
        self.threshold_eur = threshold_eur or settings.worthiness_threshold_eur
        self.required_period_months = required_period_months

    @property
    def name(self) -> str:
        return "evaluator"

    def process(self, context: PipelineContext) -> PipelineContext:
        """Evaluate financial worthiness.

        Args:
            context: Pipeline context

        Returns:
            Updated context with evaluation result
        """
        if context.analysis_result is None:
            self.logger.warning("No analysis result to evaluate")
            return context

        analysis = context.analysis_result

        # Check account consistency
        consistency = self._check_consistency(context)
        analysis.account_consistency = consistency

        # Evaluate worthiness
        evaluation = self._evaluate_worthiness(context)
        analysis.financial_worthiness = evaluation

        # Calculate confidence score
        confidence = self._calculate_confidence(context)
        analysis.confidence_score = confidence

        self.logger.info(
            "Evaluation completed",
            decision=evaluation.decision.value,
            threshold_eur=self.threshold_eur,
            evaluated_amount_eur=evaluation.evaluated_amount_eur,
            confidence_score=confidence,
        )

        context.set_stage_result(self.name, {
            "decision": evaluation.decision.value,
            "reason": evaluation.reason,
            "threshold_eur": self.threshold_eur,
            "evaluated_amount_eur": evaluation.evaluated_amount_eur,
            "consistency_status": consistency.status.value,
            "confidence_score": confidence,
        })

        return context

    def _check_consistency(self, context: PipelineContext) -> AccountConsistency:
        """Check account consistency.

        Args:
            context: Pipeline context

        Returns:
            AccountConsistency result
        """
        consistency = AccountConsistency()
        flags = []

        if context.financial_data is None:
            consistency.status = ConsistencyStatus.PARTIAL
            flags.append("No financial data available")
            consistency.flags = flags
            return consistency

        financial_data = context.financial_data
        balances = financial_data.balances

        # Check for complete data
        if financial_data.account_holder is None:
            flags.append("Account holder not identified")

        if financial_data.bank_name is None:
            flags.append("Bank name not identified")

        if financial_data.account_identifier is None:
            flags.append("Account identifier not found")

        if financial_data.currency_detected is None:
            flags.append("Currency not detected")

        # Check balance consistency
        if balances.opening_balance and balances.closing_balance:
            # Both balances present - good
            pass
        elif balances.closing_balance:
            # Only closing balance
            flags.append("Opening balance not available")
        elif balances.opening_balance:
            # Only opening balance
            flags.append("Closing balance not available")
        else:
            flags.append("No balance information available")

        # Check currency consistency
        currencies_found = set()
        for balance in [balances.opening_balance, balances.closing_balance, balances.average_balance]:
            if balance:
                currencies_found.add(balance.currency)

        if len(currencies_found) > 1:
            flags.append(f"Multiple currencies detected: {', '.join(currencies_found)}")

        # Determine status
        if not flags:
            consistency.status = ConsistencyStatus.CONSISTENT
        elif len(flags) <= 2:
            consistency.status = ConsistencyStatus.PARTIAL
        else:
            consistency.status = ConsistencyStatus.INCONSISTENT

        consistency.flags = flags
        return consistency

    def _evaluate_worthiness(self, context: PipelineContext) -> EvaluationResult:
        """Evaluate financial worthiness.

        Args:
            context: Pipeline context

        Returns:
            EvaluationResult
        """
        analysis = context.analysis_result

        # Check if we have a converted EUR amount
        if analysis.converted_to_eur is None:
            return EvaluationResult.inconclusive(
                threshold=self.threshold_eur,
                reason="Could not convert amount to EUR for evaluation",
            )

        amount_eur = analysis.converted_to_eur.amount_eur
        conversion_basis = analysis.converted_to_eur.conversion_basis

        # Compare against threshold
        worth_decision = EvaluationResult.worthy
        if amount_eur < self.threshold_eur:
            worth_decision = EvaluationResult.not_worthy

        # Base reason
        reason = f"{conversion_basis.replace('_', ' ').title()} of {amount_eur:.2f} EUR {'meets or exceeds' if amount_eur >= self.threshold_eur else 'is below'} threshold of {self.threshold_eur:.2f} EUR"

        # Period validation
        period_msg = self._check_period_compliance(context)
        if period_msg:
            reason = f"{reason}. {period_msg}"

        if amount_eur >= self.threshold_eur:
            return EvaluationResult.worthy(
                threshold=self.threshold_eur,
                amount=amount_eur,
                reason=reason,
            )
        else:
            return EvaluationResult.not_worthy(
                threshold=self.threshold_eur,
                amount=amount_eur,
                reason=reason,
            )

    def _check_period_compliance(self, context: PipelineContext) -> str | None:
        """Check if statement period meets requirements.

        Returns:
            Validation message or None
        """
        if not self.required_period_months:
            return None

        if not context.financial_data or not context.financial_data.statement_period:
            return "Unable to validate statement duration (missing period data)."

        period = context.financial_data.statement_period
        if not period.start_date or not period.end_date:
            return "Unable to validate statement duration (missing start or end date)."

        # Calculate months
        months = (period.end_date.year - period.start_date.year) * 12 + (period.end_date.month - period.start_date.month)
        
        # Add a partial month if there are significant days remaining
        days = (period.end_date.day - period.start_date.day)
        if days >= 25:
            months += 1
        elif days <= -25:
            months -= 1

        if months < self.required_period_months:
            return f"Statement covers approximately {months} month(s), which is less than the required {self.required_period_months} months."
        else:
            return f"Statement covers approximately {months} month(s), meeting the {self.required_period_months}-month requirement."

    def _calculate_confidence(self, context: PipelineContext) -> float:
        """Calculate overall confidence score.

        Args:
            context: Pipeline context

        Returns:
            Confidence score between 0 and 1
        """
        scores = []

        # Classification confidence
        classification_result = context.get_stage_result("classifier")
        if classification_result:
            scores.append(classification_result.get("confidence", 0.5))

        # Currency confidence
        if context.financial_data:
            from ...config.constants import CurrencyConfidence
            confidence_map = {
                CurrencyConfidence.HIGH: 1.0,
                CurrencyConfidence.MEDIUM: 0.7,
                CurrencyConfidence.LOW: 0.4,
            }
            scores.append(confidence_map.get(context.financial_data.base_currency_confidence, 0.4))

        # Consistency score
        if context.analysis_result and context.analysis_result.account_consistency:
            consistency = context.analysis_result.account_consistency
            consistency_map = {
                ConsistencyStatus.CONSISTENT: 1.0,
                ConsistencyStatus.PARTIAL: 0.7,
                ConsistencyStatus.INCONSISTENT: 0.4,
            }
            scores.append(consistency_map.get(consistency.status, 0.5))

        # Balance availability
        if context.financial_data and context.financial_data.get_primary_balance():
            scores.append(0.9)
        else:
            scores.append(0.3)

        # Calculate weighted average
        if scores:
            return round(sum(scores) / len(scores), 2)

        return 0.5
