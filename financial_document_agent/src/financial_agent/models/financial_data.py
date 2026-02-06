"""Financial data extraction models."""

from datetime import date

from pydantic import BaseModel, Field

from ..config.constants import CurrencyConfidence, DocumentType


class StatementPeriod(BaseModel):
    """Statement period with start and end dates."""

    start_date: date | None = Field(default=None, description="Period start date")
    end_date: date | None = Field(default=None, description="Period end date")


class Balance(BaseModel):
    """A monetary balance with amount and currency."""

    amount: float = Field(..., description="Balance amount")
    currency: str = Field(..., min_length=3, max_length=3, description="ISO 4217 currency code")

    def __str__(self) -> str:
        return f"{self.amount:.2f} {self.currency}"


class Balances(BaseModel):
    """Collection of balance information."""

    opening_balance: Balance | None = Field(default=None, description="Opening balance")
    closing_balance: Balance | None = Field(default=None, description="Closing balance")
    average_balance: Balance | None = Field(default=None, description="Average balance")


class ConvertedAmount(BaseModel):
    """Amount converted to EUR."""

    amount_eur: float = Field(..., description="Amount in EUR")
    conversion_basis: str = Field(
        ...,
        description="Basis for conversion (average_balance, closing_balance, stated_balance)",
    )
    original_amount: float | None = Field(default=None, description="Original amount")
    original_currency: str | None = Field(default=None, description="Original currency")
    exchange_rate: float | None = Field(default=None, description="Exchange rate used")


class FinancialData(BaseModel):
    """Extracted financial data from a document."""

    document_type: DocumentType = Field(..., description="Type of document")
    account_holder: str | None = Field(default=None, description="Account holder name")
    bank_name: str | None = Field(default=None, description="Bank name")
    account_identifier: str | None = Field(
        default=None,
        description="Account number or IBAN",
    )
    statement_period: StatementPeriod = Field(
        default_factory=StatementPeriod,
        description="Statement period",
    )
    currency_detected: str | None = Field(
        default=None,
        min_length=3,
        max_length=3,
        description="Primary currency detected (ISO 4217)",
    )
    base_currency_confidence: CurrencyConfidence = Field(
        default=CurrencyConfidence.LOW,
        description="Confidence in currency detection",
    )
    balances: Balances = Field(
        default_factory=Balances,
        description="Balance information",
    )
    raw_extracted_text: str | None = Field(
        default=None,
        description="Raw OCR text (for debugging)",
    )

    def _is_valid_balance(self, balance: Balance | None) -> bool:
        """Check if a balance is valid (not None and not zero)."""
        return balance is not None and abs(balance.amount) > 0.01

    def get_primary_balance(self) -> Balance | None:
        """Get the primary balance for evaluation (average > closing > opening).

        Skips zero balances as they indicate missing data.
        """
        if self._is_valid_balance(self.balances.average_balance):
            return self.balances.average_balance
        if self._is_valid_balance(self.balances.closing_balance):
            return self.balances.closing_balance
        if self._is_valid_balance(self.balances.opening_balance):
            return self.balances.opening_balance
        return None

    def get_conversion_basis(self) -> str:
        """Get the basis used for conversion."""
        if self._is_valid_balance(self.balances.average_balance):
            return "average_balance"
        if self._is_valid_balance(self.balances.closing_balance):
            return "closing_balance"
        if self._is_valid_balance(self.balances.opening_balance):
            return "opening_balance"
        return "stated_balance"


class AnalysisResult(BaseModel):
    """Complete analysis result for a financial document."""

    document_type: DocumentType = Field(..., description="Type of document")
    account_holder: str | None = Field(default=None, description="Account holder name")
    bank_name: str | None = Field(default=None, description="Bank name")
    account_identifier: str | None = Field(default=None, description="Account identifier")
    statement_period: StatementPeriod = Field(
        default_factory=StatementPeriod,
        description="Statement period",
    )
    currency_detected: str | None = Field(default=None, description="Currency detected")
    base_currency_confidence: CurrencyConfidence = Field(
        default=CurrencyConfidence.LOW,
        description="Currency confidence",
    )
    balances: Balances = Field(default_factory=Balances, description="Balances")
    converted_to_eur: ConvertedAmount | None = Field(
        default=None,
        description="Amount converted to EUR",
    )
    account_consistency: "AccountConsistency" = Field(
        default=None,
        description="Account consistency check",
    )
    financial_worthiness: "EvaluationResult" = Field(
        default=None,
        description="Financial worthiness evaluation",
    )
    confidence_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Overall confidence score",
    )

    @classmethod
    def from_financial_data(cls, data: FinancialData) -> "AnalysisResult":
        """Create an AnalysisResult from FinancialData."""
        return cls(
            document_type=data.document_type,
            account_holder=data.account_holder,
            bank_name=data.bank_name,
            account_identifier=data.account_identifier,
            statement_period=data.statement_period,
            currency_detected=data.currency_detected,
            base_currency_confidence=data.base_currency_confidence,
            balances=data.balances,
        )


# Import here to avoid circular imports
from .evaluation import AccountConsistency, EvaluationResult

AnalysisResult.model_rebuild()
