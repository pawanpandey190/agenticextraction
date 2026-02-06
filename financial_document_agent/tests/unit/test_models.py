"""Unit tests for data models."""

from datetime import date

import pytest

from financial_agent.config.constants import (
    ConsistencyStatus,
    CurrencyConfidence,
    DocumentType,
    WorthinessDecision,
)
from financial_agent.models.document import DocumentPage, ProcessingMetadata
from financial_agent.models.evaluation import AccountConsistency, EvaluationResult
from financial_agent.models.financial_data import (
    AnalysisResult,
    Balance,
    Balances,
    ConvertedAmount,
    FinancialData,
    StatementPeriod,
)


class TestBalance:
    """Tests for Balance model."""

    def test_balance_creation(self):
        """Test creating a balance."""
        balance = Balance(amount=1000.50, currency="EUR")
        assert balance.amount == 1000.50
        assert balance.currency == "EUR"

    def test_balance_str(self):
        """Test balance string representation."""
        balance = Balance(amount=1000.50, currency="EUR")
        assert str(balance) == "1000.50 EUR"

    def test_balance_negative(self):
        """Test negative balance."""
        balance = Balance(amount=-500.00, currency="USD")
        assert balance.amount == -500.00


class TestBalances:
    """Tests for Balances model."""

    def test_balances_empty(self):
        """Test empty balances."""
        balances = Balances()
        assert balances.opening_balance is None
        assert balances.closing_balance is None
        assert balances.average_balance is None

    def test_balances_partial(self):
        """Test partial balances."""
        balances = Balances(
            closing_balance=Balance(amount=1000.00, currency="EUR")
        )
        assert balances.opening_balance is None
        assert balances.closing_balance is not None
        assert balances.closing_balance.amount == 1000.00


class TestStatementPeriod:
    """Tests for StatementPeriod model."""

    def test_period_with_dates(self):
        """Test period with dates."""
        period = StatementPeriod(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )
        assert period.start_date == date(2024, 1, 1)
        assert period.end_date == date(2024, 1, 31)

    def test_period_empty(self):
        """Test empty period."""
        period = StatementPeriod()
        assert period.start_date is None
        assert period.end_date is None


class TestFinancialData:
    """Tests for FinancialData model."""

    def test_get_primary_balance_average(self, sample_financial_data: FinancialData):
        """Test primary balance returns average when available."""
        primary = sample_financial_data.get_primary_balance()
        assert primary is not None
        assert primary.amount == 12500.00

    def test_get_primary_balance_closing(self):
        """Test primary balance returns closing when no average."""
        data = FinancialData(
            document_type=DocumentType.BANK_STATEMENT,
            balances=Balances(closing_balance=Balance(amount=5000.00, currency="EUR")),
        )
        primary = data.get_primary_balance()
        assert primary is not None
        assert primary.amount == 5000.00

    def test_get_primary_balance_none(self):
        """Test primary balance returns None when no balances."""
        data = FinancialData(document_type=DocumentType.UNKNOWN)
        assert data.get_primary_balance() is None

    def test_get_conversion_basis(self, sample_financial_data: FinancialData):
        """Test conversion basis."""
        assert sample_financial_data.get_conversion_basis() == "average_balance"


class TestConvertedAmount:
    """Tests for ConvertedAmount model."""

    def test_converted_amount(self):
        """Test converted amount creation."""
        converted = ConvertedAmount(
            amount_eur=1080.00,
            conversion_basis="closing_balance",
            original_amount=1000.00,
            original_currency="USD",
            exchange_rate=1.08,
        )
        assert converted.amount_eur == 1080.00
        assert converted.original_currency == "USD"


class TestAccountConsistency:
    """Tests for AccountConsistency model."""

    def test_consistency_default(self):
        """Test default consistency."""
        consistency = AccountConsistency()
        assert consistency.status == ConsistencyStatus.PARTIAL
        assert consistency.flags == []

    def test_add_flag(self):
        """Test adding a flag."""
        consistency = AccountConsistency()
        consistency.add_flag("Test flag")
        assert "Test flag" in consistency.flags

    def test_is_consistent(self):
        """Test is_consistent property."""
        consistent = AccountConsistency(status=ConsistencyStatus.CONSISTENT)
        assert consistent.is_consistent is True

        partial = AccountConsistency(status=ConsistencyStatus.PARTIAL)
        assert partial.is_consistent is False


class TestEvaluationResult:
    """Tests for EvaluationResult model."""

    def test_worthy(self):
        """Test worthy result."""
        result = EvaluationResult.worthy(
            threshold=10000.00,
            amount=15000.00,
            reason="Test reason",
        )
        assert result.decision == WorthinessDecision.WORTHY
        assert result.evaluated_amount_eur == 15000.00

    def test_not_worthy(self):
        """Test not worthy result."""
        result = EvaluationResult.not_worthy(
            threshold=10000.00,
            amount=5000.00,
            reason="Test reason",
        )
        assert result.decision == WorthinessDecision.NOT_WORTHY
        assert result.evaluated_amount_eur == 5000.00

    def test_inconclusive(self):
        """Test inconclusive result."""
        result = EvaluationResult.inconclusive(
            threshold=10000.00,
            reason="Test reason",
        )
        assert result.decision == WorthinessDecision.INCONCLUSIVE
        assert result.evaluated_amount_eur is None


class TestAnalysisResult:
    """Tests for AnalysisResult model."""

    def test_from_financial_data(self, sample_financial_data: FinancialData):
        """Test creating AnalysisResult from FinancialData."""
        result = AnalysisResult.from_financial_data(sample_financial_data)
        assert result.document_type == sample_financial_data.document_type
        assert result.account_holder == sample_financial_data.account_holder
        assert result.bank_name == sample_financial_data.bank_name

    def test_json_serialization(self, sample_analysis_result: AnalysisResult):
        """Test JSON serialization."""
        json_str = sample_analysis_result.model_dump_json()
        assert "BANK_STATEMENT" in json_str
        assert "John Doe" in json_str


class TestProcessingMetadata:
    """Tests for ProcessingMetadata model."""

    def test_mark_completed(self):
        """Test marking processing as completed."""
        metadata = ProcessingMetadata()
        assert metadata.processing_completed_at is None

        metadata.mark_completed()
        assert metadata.processing_completed_at is not None

    def test_add_error(self):
        """Test adding errors."""
        metadata = ProcessingMetadata()
        metadata.add_error("Test error")
        assert "Test error" in metadata.errors

    def test_processing_duration(self):
        """Test processing duration calculation."""
        import time

        metadata = ProcessingMetadata()
        time.sleep(0.1)
        metadata.mark_completed()

        duration = metadata.processing_duration_seconds
        assert duration is not None
        assert duration >= 0.1
