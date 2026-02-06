"""Integration tests for the pipeline."""

from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from financial_agent.config.constants import DocumentType, CurrencyConfidence
from financial_agent.config.settings import Settings
from financial_agent.models.financial_data import Balance, Balances, FinancialData, StatementPeriod
from financial_agent.pipeline.base import PipelineContext
from financial_agent.pipeline.stages.classifier import ClassifierStage
from financial_agent.pipeline.stages.currency_converter import CurrencyConverterStage
from financial_agent.pipeline.stages.evaluator import EvaluatorStage
from financial_agent.pipeline.stages.extractor import ExtractorStage


class TestClassifierStage:
    """Tests for ClassifierStage."""

    def test_classification(self, mock_settings: Settings, mock_llm_service: MagicMock):
        """Test document classification."""
        stage = ClassifierStage(mock_settings, mock_llm_service)

        context = PipelineContext(
            file_path="/test/document.pdf",
            settings=mock_settings,
        )
        context.extracted_text = "Bank Statement\nAccount: 123456\nBalance: EUR 10,000.00"

        result = stage.process(context)

        assert result.financial_data is not None
        assert result.financial_data.document_type == DocumentType.BANK_STATEMENT


class TestCurrencyConverterStage:
    """Tests for CurrencyConverterStage."""

    def test_eur_no_conversion(self, mock_settings: Settings, mock_exchange_service: MagicMock):
        """Test EUR amount (no conversion needed)."""
        stage = CurrencyConverterStage(mock_settings, mock_exchange_service)

        context = PipelineContext(
            file_path="/test/document.pdf",
            settings=mock_settings,
        )
        context.financial_data = FinancialData(
            document_type=DocumentType.BANK_STATEMENT,
            balances=Balances(
                average_balance=Balance(amount=15000.00, currency="EUR"),
            ),
        )

        result = stage.process(context)

        assert result.analysis_result is not None
        assert result.analysis_result.converted_to_eur is not None
        assert result.analysis_result.converted_to_eur.amount_eur == 15000.00
        assert result.analysis_result.converted_to_eur.exchange_rate == 1.0

    def test_usd_conversion(self, mock_settings: Settings, mock_exchange_service: MagicMock):
        """Test USD to EUR conversion."""
        mock_exchange_service.convert.return_value = (9200.00, 0.92)

        stage = CurrencyConverterStage(mock_settings, mock_exchange_service)

        context = PipelineContext(
            file_path="/test/document.pdf",
            settings=mock_settings,
        )
        context.financial_data = FinancialData(
            document_type=DocumentType.BANK_STATEMENT,
            balances=Balances(
                closing_balance=Balance(amount=10000.00, currency="USD"),
            ),
        )

        result = stage.process(context)

        assert result.analysis_result is not None
        assert result.analysis_result.converted_to_eur is not None
        assert result.analysis_result.converted_to_eur.amount_eur == 9200.00

    def test_no_balance(self, mock_settings: Settings, mock_exchange_service: MagicMock):
        """Test handling of no balance."""
        stage = CurrencyConverterStage(mock_settings, mock_exchange_service)

        context = PipelineContext(
            file_path="/test/document.pdf",
            settings=mock_settings,
        )
        context.financial_data = FinancialData(
            document_type=DocumentType.BANK_LETTER,
        )

        result = stage.process(context)

        assert result.analysis_result is not None
        assert result.analysis_result.converted_to_eur is None


class TestEvaluatorStage:
    """Tests for EvaluatorStage."""

    def test_worthy_evaluation(self, mock_settings: Settings):
        """Test worthy evaluation."""
        stage = EvaluatorStage(mock_settings, threshold_eur=10000.00)

        from financial_agent.models.financial_data import AnalysisResult, ConvertedAmount

        context = PipelineContext(
            file_path="/test/document.pdf",
            settings=mock_settings,
        )
        context.financial_data = FinancialData(
            document_type=DocumentType.BANK_STATEMENT,
            account_holder="John Doe",
            bank_name="Test Bank",
            currency_detected="EUR",
            base_currency_confidence=CurrencyConfidence.HIGH,
            balances=Balances(
                closing_balance=Balance(amount=15000.00, currency="EUR"),
            ),
        )
        context.analysis_result = AnalysisResult.from_financial_data(context.financial_data)
        context.analysis_result.converted_to_eur = ConvertedAmount(
            amount_eur=15000.00,
            conversion_basis="closing_balance",
        )

        result = stage.process(context)

        assert result.analysis_result is not None
        assert result.analysis_result.financial_worthiness is not None
        assert result.analysis_result.financial_worthiness.decision.value == "WORTHY"

    def test_not_worthy_evaluation(self, mock_settings: Settings):
        """Test not worthy evaluation."""
        stage = EvaluatorStage(mock_settings, threshold_eur=10000.00)

        from financial_agent.models.financial_data import AnalysisResult, ConvertedAmount

        context = PipelineContext(
            file_path="/test/document.pdf",
            settings=mock_settings,
        )
        context.financial_data = FinancialData(
            document_type=DocumentType.BANK_STATEMENT,
            balances=Balances(
                closing_balance=Balance(amount=5000.00, currency="EUR"),
            ),
        )
        context.analysis_result = AnalysisResult.from_financial_data(context.financial_data)
        context.analysis_result.converted_to_eur = ConvertedAmount(
            amount_eur=5000.00,
            conversion_basis="closing_balance",
        )

        result = stage.process(context)

        assert result.analysis_result is not None
        assert result.analysis_result.financial_worthiness is not None
        assert result.analysis_result.financial_worthiness.decision.value == "NOT_WORTHY"

    def test_inconclusive_evaluation(self, mock_settings: Settings):
        """Test inconclusive evaluation when no conversion."""
        stage = EvaluatorStage(mock_settings, threshold_eur=10000.00)

        from financial_agent.models.financial_data import AnalysisResult

        context = PipelineContext(
            file_path="/test/document.pdf",
            settings=mock_settings,
        )
        context.financial_data = FinancialData(document_type=DocumentType.UNKNOWN)
        context.analysis_result = AnalysisResult.from_financial_data(context.financial_data)
        # No converted_to_eur set

        result = stage.process(context)

        assert result.analysis_result is not None
        assert result.analysis_result.financial_worthiness is not None
        assert result.analysis_result.financial_worthiness.decision.value == "INCONCLUSIVE"

    def test_consistency_check(self, mock_settings: Settings):
        """Test account consistency checking."""
        stage = EvaluatorStage(mock_settings)

        from financial_agent.models.financial_data import AnalysisResult, ConvertedAmount

        # Complete data - should be consistent
        context = PipelineContext(
            file_path="/test/document.pdf",
            settings=mock_settings,
        )
        context.financial_data = FinancialData(
            document_type=DocumentType.BANK_STATEMENT,
            account_holder="John Doe",
            bank_name="Test Bank",
            account_identifier="DE123456",
            currency_detected="EUR",
            balances=Balances(
                opening_balance=Balance(amount=10000.00, currency="EUR"),
                closing_balance=Balance(amount=15000.00, currency="EUR"),
            ),
        )
        context.analysis_result = AnalysisResult.from_financial_data(context.financial_data)
        context.analysis_result.converted_to_eur = ConvertedAmount(
            amount_eur=15000.00,
            conversion_basis="closing_balance",
        )

        result = stage.process(context)

        assert result.analysis_result.account_consistency is not None
        # Should have few or no flags for complete data
        assert len(result.analysis_result.account_consistency.flags) <= 1
