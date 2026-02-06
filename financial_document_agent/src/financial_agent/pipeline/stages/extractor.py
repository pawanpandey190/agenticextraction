"""Financial data extraction stage."""

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
            content = f"Document text:\n\n{context.extracted_text}\n\n{extraction_prompt}"

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
                        "text": content,
                    },
                ]

                # Use raw API call for mixed content
                result = self._extract_with_image(content_blocks)
            else:
                result = self._extract_from_text(content)

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

    def _extract_from_text(self, content: str) -> dict:
        """Extract data using text-only approach.

        Args:
            content: Text content with extraction prompt

        Returns:
            Extracted data dictionary
        """
        import json

        from openai import OpenAI

        client = OpenAI(api_key=self.settings.openai_api_key.get_secret_value())

        response = client.chat.completions.create(
            model=self.settings.llm_model,
            max_tokens=self.settings.llm_max_tokens,
            temperature=self.settings.llm_temperature,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": content}
            ],
        )

        response_text = response.choices[0].message.content
        json_str = self.llm_service._extract_json(response_text)

        return json.loads(json_str)

    def _extract_with_image(self, content_blocks: list) -> dict:
        """Extract data using image and text.

        Args:
            content_blocks: Content blocks including image

        Returns:
            Extracted data dictionary
        """
        import json

        from openai import OpenAI

        client = OpenAI(api_key=self.settings.openai_api_key.get_secret_value())

        # Convert Anthropic-style content blocks to OpenAI format
        messages_content = []
        for block in content_blocks:
            if block["type"] == "image":
                messages_content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{block['source']['media_type']};base64,{block['source']['data']}"
                    }
                })
            elif block["type"] == "text":
                messages_content.append({
                    "type": "text",
                    "text": block["text"]
                })

        response = client.chat.completions.create(
            model=self.settings.llm_model,
            max_tokens=self.settings.llm_max_tokens,
            temperature=self.settings.llm_temperature,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": messages_content}
            ],
        )

        response_text = response.choices[0].message.content
        json_str = self.llm_service._extract_json(response_text)

        return json.loads(json_str)

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

    def _parse_date(self, date_str: str | None) -> "date | None":
        """Parse a date string.

        Args:
            date_str: Date string in YYYY-MM-DD format

        Returns:
            Parsed date or None
        """
        if not date_str:
            return None

        from datetime import date, datetime

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
