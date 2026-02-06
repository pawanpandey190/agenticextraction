"""Currency conversion stage."""

from ...config.constants import DEFAULT_TARGET_CURRENCY
from ...config.settings import Settings
from ...models.financial_data import ConvertedAmount
from ...services.exchange_service import ExchangeService
from ...utils.exceptions import CurrencyConversionError
from ..base import PipelineContext, PipelineStage


class CurrencyConverterStage(PipelineStage):
    """Stage for converting amounts to EUR."""

    def __init__(self, settings: Settings, exchange_service: ExchangeService | None = None) -> None:
        super().__init__(settings)
        self.exchange_service = exchange_service or ExchangeService(settings)

    @property
    def name(self) -> str:
        return "currency_converter"

    def process(self, context: PipelineContext) -> PipelineContext:
        """Convert financial amounts to EUR.

        Args:
            context: Pipeline context

        Returns:
            Updated context with converted amounts

        Raises:
            CurrencyConversionError: If conversion fails
        """
        if context.financial_data is None:
            raise CurrencyConversionError("No financial data to convert")

        financial_data = context.financial_data

        # Get primary balance for conversion
        primary_balance = financial_data.get_primary_balance()

        if primary_balance is None:
            self.logger.warning("No balance available for conversion")
            context.metadata.add_warning("No balance available for currency conversion")

            # Create analysis result without conversion
            from ...models.financial_data import AnalysisResult
            context.analysis_result = AnalysisResult.from_financial_data(financial_data)

            context.set_stage_result(self.name, {
                "converted": False,
                "reason": "No balance available",
            })

            return context

        source_currency = primary_balance.currency
        target_currency = DEFAULT_TARGET_CURRENCY
        conversion_basis = financial_data.get_conversion_basis()

        try:
            # Check if already in EUR
            if source_currency.upper() == target_currency:
                converted_amount = ConvertedAmount(
                    amount_eur=primary_balance.amount,
                    conversion_basis=conversion_basis,
                    original_amount=primary_balance.amount,
                    original_currency=source_currency,
                    exchange_rate=1.0,
                )
            else:
                # Convert to EUR
                amount_eur, rate = self.exchange_service.convert(
                    amount=primary_balance.amount,
                    from_currency=source_currency,
                    to_currency=target_currency,
                )

                converted_amount = ConvertedAmount(
                    amount_eur=round(amount_eur, 2),
                    conversion_basis=conversion_basis,
                    original_amount=primary_balance.amount,
                    original_currency=source_currency,
                    exchange_rate=rate,
                )

            # Create analysis result with conversion
            from ...models.financial_data import AnalysisResult
            analysis_result = AnalysisResult.from_financial_data(financial_data)
            analysis_result.converted_to_eur = converted_amount

            context.analysis_result = analysis_result

            self.logger.info(
                "Currency conversion completed",
                original_amount=primary_balance.amount,
                original_currency=source_currency,
                converted_amount_eur=converted_amount.amount_eur,
                exchange_rate=converted_amount.exchange_rate,
            )

            context.set_stage_result(self.name, {
                "converted": True,
                "original_amount": primary_balance.amount,
                "original_currency": source_currency,
                "converted_amount_eur": converted_amount.amount_eur,
                "exchange_rate": converted_amount.exchange_rate,
                "conversion_basis": conversion_basis,
            })

            return context

        except CurrencyConversionError as e:
            self.logger.error("Currency conversion failed", error=str(e))
            context.metadata.add_error(f"Currency conversion failed: {e}")

            # Create analysis result without conversion
            from ...models.financial_data import AnalysisResult
            context.analysis_result = AnalysisResult.from_financial_data(financial_data)

            context.set_stage_result(self.name, {
                "converted": False,
                "reason": str(e),
            })

            # Don't fail the pipeline, continue without conversion
            return context
