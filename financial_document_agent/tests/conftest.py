"""Pytest configuration and fixtures."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from financial_agent.config.constants import DocumentType, CurrencyConfidence
from financial_agent.config.settings import Settings
from financial_agent.models.document import DocumentInput, DocumentPage
from financial_agent.models.financial_data import (
    AnalysisResult,
    Balance,
    Balances,
    ConvertedAmount,
    FinancialData,
    StatementPeriod,
)
from financial_agent.models.evaluation import AccountConsistency, EvaluationResult


@pytest.fixture
def mock_settings() -> Settings:
    """Create mock settings for testing."""
    with patch.dict(os.environ, {
        "FA_ANTHROPIC_API_KEY": "test-api-key",
        "FA_LLM_MODEL": "claude-sonnet-4-20250514",
        "FA_WORTHINESS_THRESHOLD_EUR": "10000.0",
    }):
        return Settings()


@pytest.fixture
def sample_balance() -> Balance:
    """Create a sample balance."""
    return Balance(amount=15000.00, currency="EUR")


@pytest.fixture
def sample_balances(sample_balance: Balance) -> Balances:
    """Create sample balances."""
    return Balances(
        opening_balance=Balance(amount=10000.00, currency="EUR"),
        closing_balance=sample_balance,
        average_balance=Balance(amount=12500.00, currency="EUR"),
    )


@pytest.fixture
def sample_statement_period() -> StatementPeriod:
    """Create a sample statement period."""
    from datetime import date
    return StatementPeriod(
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31),
    )


@pytest.fixture
def sample_financial_data(
    sample_balances: Balances,
    sample_statement_period: StatementPeriod,
) -> FinancialData:
    """Create sample financial data."""
    return FinancialData(
        document_type=DocumentType.BANK_STATEMENT,
        account_holder="John Doe",
        bank_name="Test Bank",
        account_identifier="DE89370400440532013000",
        statement_period=sample_statement_period,
        currency_detected="EUR",
        base_currency_confidence=CurrencyConfidence.HIGH,
        balances=sample_balances,
    )


@pytest.fixture
def sample_analysis_result(sample_financial_data: FinancialData) -> AnalysisResult:
    """Create a sample analysis result."""
    result = AnalysisResult.from_financial_data(sample_financial_data)
    result.converted_to_eur = ConvertedAmount(
        amount_eur=12500.00,
        conversion_basis="average_balance",
        original_amount=12500.00,
        original_currency="EUR",
        exchange_rate=1.0,
    )
    result.account_consistency = AccountConsistency()
    result.financial_worthiness = EvaluationResult.worthy(
        threshold=10000.00,
        amount=12500.00,
        reason="Average balance of 12500.00 EUR meets or exceeds threshold of 10000.00 EUR",
    )
    result.confidence_score = 0.9
    return result


@pytest.fixture
def fixtures_dir() -> Path:
    """Get the fixtures directory path."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def mock_llm_service(mock_settings: Settings):
    """Create a mock LLM service."""
    mock = MagicMock()

    # Mock text extraction
    mock.extract_text_from_image.return_value = """
    Test Bank
    Account Statement

    Account Holder: John Doe
    Account Number: DE89370400440532013000

    Statement Period: 01/01/2024 - 31/01/2024

    Opening Balance: EUR 10,000.00
    Closing Balance: EUR 15,000.00
    Average Balance: EUR 12,500.00
    """

    # Mock classification
    mock.classify_document.return_value = {
        "document_type": "BANK_STATEMENT",
        "confidence": 0.95,
        "reasoning": "Document contains typical bank statement elements",
        "key_indicators": ["balance", "statement period", "account number"],
    }

    return mock


@pytest.fixture
def mock_exchange_service(mock_settings: Settings):
    """Create a mock exchange service."""
    mock = MagicMock()
    mock.convert.return_value = (12500.00, 1.0)
    mock.get_rate.return_value = 1.0
    return mock
