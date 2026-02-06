"""Extraction prompts for financial data."""

from ..config.constants import DocumentType

BASE_EXTRACTION_PROMPT = """Extract financial information from this document. Be precise and thorough.

Return the data as JSON matching this structure:
{
    "account_holder": "Full name of account holder or null if not found",
    "bank_name": "Name of the bank or financial institution or null",
    "account_identifier": "Account number, IBAN, or other identifier or null",
    "statement_period": {
        "start_date": "YYYY-MM-DD or null",
        "end_date": "YYYY-MM-DD or null"
    },
    "currency_detected": "ISO 4217 code (EUR, USD, GBP, etc.) or null",
    "currency_confidence": "HIGH | MEDIUM | LOW",
    "balances": {
        "opening_balance": {"amount": number, "currency": "ISO code"} or null,
        "closing_balance": {"amount": number, "currency": "ISO code"} or null,
        "average_balance": {"amount": number, "currency": "ISO code"} or null
    },
    "additional_notes": "Any relevant observations about the document"
}

Currency detection guidelines:
- HIGH confidence: Explicit ISO code or unambiguous symbol (€ for EUR, £ for GBP)
- MEDIUM confidence: Common symbol with regional context ($ in US document = USD)
- LOW confidence: Ambiguous symbol or no clear indicator

Be exact with amounts - do not round. Use negative numbers for debits/overdrafts."""

BANK_STATEMENT_EXTRACTION_PROMPT = """Extract information from this BANK STATEMENT.

Focus on:
1. Account holder name (individual or company)
2. Bank name and branch if visible
3. Account number/IBAN
4. Statement period (start and end dates)
5. Opening balance
6. Closing balance
7. Average daily balance if shown
8. Currency of the account

Return the data as JSON:
{
    "account_holder": "string or null",
    "bank_name": "string or null",
    "account_identifier": "string or null",
    "statement_period": {
        "start_date": "YYYY-MM-DD or null",
        "end_date": "YYYY-MM-DD or null"
    },
    "currency_detected": "ISO 4217 code or null",
    "currency_confidence": "HIGH | MEDIUM | LOW",
    "balances": {
        "opening_balance": {"amount": number, "currency": "ISO"} or null,
        "closing_balance": {"amount": number, "currency": "ISO"} or null,
        "average_balance": {"amount": number, "currency": "ISO"} or null
    },
    "additional_notes": "string"
}"""

BANK_LETTER_EXTRACTION_PROMPT = """Extract information from this BANK LETTER.

Focus on:
1. Account holder name
2. Bank name
3. Account reference/number
4. Date of the letter
5. Any stated balance or financial position
6. Currency mentioned
7. Purpose of the letter (balance confirmation, reference, etc.)

Return the data as JSON:
{
    "account_holder": "string or null",
    "bank_name": "string or null",
    "account_identifier": "string or null",
    "statement_period": {
        "start_date": null,
        "end_date": "YYYY-MM-DD (letter date) or null"
    },
    "currency_detected": "ISO 4217 code or null",
    "currency_confidence": "HIGH | MEDIUM | LOW",
    "balances": {
        "opening_balance": null,
        "closing_balance": {"amount": number, "currency": "ISO"} or null,
        "average_balance": null
    },
    "additional_notes": "Purpose of letter and any relevant context"
}"""

CERTIFICATE_EXTRACTION_PROMPT = """Extract information from this FINANCIAL CERTIFICATE.

Focus on:
1. Certificate holder name
2. Issuing institution
3. Certificate/account reference number
4. Issue date and maturity date if applicable
5. Principal amount or face value
6. Currency
7. Interest rate if shown
8. Type of certificate

Return the data as JSON:
{
    "account_holder": "string or null",
    "bank_name": "string or null",
    "account_identifier": "string or null",
    "statement_period": {
        "start_date": "YYYY-MM-DD (issue date) or null",
        "end_date": "YYYY-MM-DD (maturity date) or null"
    },
    "currency_detected": "ISO 4217 code or null",
    "currency_confidence": "HIGH | MEDIUM | LOW",
    "balances": {
        "opening_balance": null,
        "closing_balance": {"amount": number (principal/value), "currency": "ISO"} or null,
        "average_balance": null
    },
    "additional_notes": "Certificate type, interest rate, and other relevant details"
}"""

UNKNOWN_EXTRACTION_PROMPT = """Extract any financial information visible in this document.

Look for:
1. Any names that might be account holders
2. Any bank or financial institution names
3. Any account numbers or references
4. Any dates
5. Any monetary amounts with currencies
6. Any other relevant financial information

Return the data as JSON:
{
    "account_holder": "string or null",
    "bank_name": "string or null",
    "account_identifier": "string or null",
    "statement_period": {
        "start_date": "YYYY-MM-DD or null",
        "end_date": "YYYY-MM-DD or null"
    },
    "currency_detected": "ISO 4217 code or null",
    "currency_confidence": "HIGH | MEDIUM | LOW",
    "balances": {
        "opening_balance": {"amount": number, "currency": "ISO"} or null,
        "closing_balance": {"amount": number, "currency": "ISO"} or null,
        "average_balance": {"amount": number, "currency": "ISO"} or null
    },
    "additional_notes": "Description of document and any relevant observations"
}"""


def get_extraction_prompt(document_type: DocumentType) -> str:
    """Get the appropriate extraction prompt for a document type.

    Args:
        document_type: The classified document type

    Returns:
        Extraction prompt string
    """
    prompts = {
        DocumentType.BANK_STATEMENT: BANK_STATEMENT_EXTRACTION_PROMPT,
        DocumentType.BANK_LETTER: BANK_LETTER_EXTRACTION_PROMPT,
        DocumentType.CERTIFICATE: CERTIFICATE_EXTRACTION_PROMPT,
        DocumentType.UNKNOWN: UNKNOWN_EXTRACTION_PROMPT,
    }

    return prompts.get(document_type, BASE_EXTRACTION_PROMPT)
