"""Financial data extraction stage."""

import json
from datetime import date, datetime

from ...config.constants import CurrencyConfidence, DocumentType
from ...config.settings import Settings
from ...models.financial_data import Balance, Balances, FinancialData, StatementPeriod
from ...prompts.extraction import get_extraction_prompt
from ...prompts.system import SYSTEM_PROMPT
from ...services.llm_service import LLMService
from ...utils.exceptions import ExtractionError
from ..base import PipelineContext, PipelineStage


class ExtractorStage(PipelineStage):
    """Stage for extracting financial data from documents."""

    def __init__(self, settings: Settings, llm_service: LLMService | None = None) -> None:
        super().__init__(settings)
        self.llm_service = llm_service or LLMService(settings)

    @property
    def name(self) -> str:
        return "extractor"

    def process(self, context: PipelineContext) -> PipelineContext:
        """Extract financial data from the document.

        Args:
            context: Pipeline context

        Returns:
            Updated context with extracted financial data

        Raises:
            ExtractionError: If extraction fails
        """
        if not context.extracted_text:
            raise ExtractionError("No extracted text for data extraction")

        if context.financial_data is None:
            raise ExtractionError("Document not classified")

        document_type = context.financial_data.document_type
        extraction_prompt = get_extraction_prompt(document_type)

        try:
            # Build content for extraction
            content_text = f"Document text:\n\n{context.extracted_text}\n\n{extraction_prompt}"

            # If we have an image, include it
            if context.first_page_base64 and context.first_page_mime_type:
                content_blocks = [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": context.first_page_mime_type,
                            "data": context.first_page_base64,
                        },
                    },
                    {
                        "type": "text",
                        "text": content_text,
                    },
                ]
                result = self._extract(content_blocks)
            else:
                result = self._extract(content_text)

            # Update financial data
            financial_data = self._build_financial_data(result, document_type)
            financial_data.raw_extracted_text = context.extracted_text

            context.financial_data = financial_data

            self.logger.info(
                "Financial data extracted",
                document_type=document_type.value,
                has_balances=financial_data.balances.closing_balance is not None,
                currency=financial_data.currency_detected,
            )

            context.set_stage_result(self.name, {
                "account_holder": financial_data.account_holder,
                "bank_name": financial_data.bank_name,
                "currency_detected": financial_data.currency_detected,
                "has_closing_balance": financial_data.balances.closing_balance is not None,
            })

            return context

        except Exception as e:
            self.logger.error("Extraction failed", error=str(e))
            raise ExtractionError(f"Failed to extract financial data: {e}") from e

    def _extract(self, content: str | list) -> dict:
        """Extract data using LLMService.

        Args:
            content: Text content or content blocks

        Returns:
            Extracted data dictionary
        """
        try:
            # We use analyze_with_structured_output if possible, but here we need a dict
            # The LLMService._extract_json can be used if we call the client directly
            # or we can just use a dummy Pydantic model. 
            # Actually, let's just call the client via a new method in LLMService if needed, 
            # but since I already refactored LLMService, I'll use its internal client to stay consistent.
            
            response = self.llm_service.client.messages.create(
                model=self.llm_service.model,
                max_tokens=self.llm_service.max_tokens,
                temperature=self.llm_service.temperature,
                system=SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": content}
                ],
            )

            response_text = response.content[0].text if response.content else ""
            json_str = self.llm_service._extract_json(response_text)

            return json.loads(json_str)
        except Exception as e:
            self.logger.error("LLM extraction call failed", error=str(e))
            raise ExtractionError(f"LLM extraction call failed: {e}")

    def _build_financial_data(self, result: dict, document_type: DocumentType) -> FinancialData:
        """Build FinancialData from extraction result.

        Args:
            result: Extracted data dictionary
            document_type: Classified document type

        Returns:
            FinancialData model
        """
        # Parse statement period
        period_data = result.get("statement_period", {})
        statement_period = StatementPeriod(
            start_date=self._parse_date(period_data.get("start_date")),
            end_date=self._parse_date(period_data.get("end_date")),
        )

        # Parse balances
        balances_data = result.get("balances", {})
        balances = Balances(
            opening_balance=self._parse_balance(balances_data.get("opening_balance")),
            closing_balance=self._parse_balance(balances_data.get("closing_balance")),
            average_balance=self._parse_balance(balances_data.get("average_balance")),
        )

        # Parse currency confidence
        confidence_str = result.get("currency_confidence", "LOW")
        try:
            currency_confidence = CurrencyConfidence(confidence_str.upper())
        except ValueError:
            currency_confidence = CurrencyConfidence.LOW

        return FinancialData(
            document_type=document_type,
            account_holder=result.get("account_holder"),
            bank_name=result.get("bank_name"),
            account_identifier=result.get("account_identifier"),
            statement_period=statement_period,
            currency_detected=result.get("currency_detected"),
            base_currency_confidence=currency_confidence,
            balances=balances,
        )

    def _parse_date(self, date_str: str | None) -> date | None:
        """Parse a date string.

        Args:
            date_str: Date string in YYYY-MM-DD format

        Returns:
            Parsed date or None
        """
        if not date_str:
            return None

        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            self.logger.warning(f"Could not parse date: {date_str}")
            return None

    def _parse_balance(self, balance_data: dict | None) -> Balance | None:
        """Parse a balance from extraction data.

        Args:
            balance_data: Balance dictionary with amount and currency

        Returns:
            Balance model or None
        """
        if not balance_data:
            return None

        amount = balance_data.get("amount")
        currency = balance_data.get("currency")

        if amount is None or currency is None:
            return None

        try:
            return Balance(amount=float(amount), currency=str(currency).upper())
        except (ValueError, TypeError):
            self.logger.warning(f"Could not parse balance: {balance_data}")
            return None
