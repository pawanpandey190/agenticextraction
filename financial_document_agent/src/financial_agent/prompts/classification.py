"""Classification prompts for document type detection."""

CLASSIFICATION_PROMPT = """Analyze this financial document and classify it into one of the following categories:

1. BANK_STATEMENT - A periodic statement showing account transactions, balances, and activity
   - Typically includes opening/closing balances
   - Shows transaction history
   - Has statement period dates
   - Contains account summary

2. BANK_LETTER - Official correspondence from a bank
   - Balance confirmation letters
   - Account verification letters
   - Reference letters
   - Formal notifications

3. CERTIFICATE - Official certificates related to finances
   - Deposit certificates
   - Fixed deposit receipts
   - Investment certificates
   - Guarantee certificates

4. UNKNOWN - Document that doesn't fit the above categories or cannot be classified with confidence

Return your classification as JSON with the following structure:
{
    "document_type": "BANK_STATEMENT" | "BANK_LETTER" | "CERTIFICATE" | "UNKNOWN",
    "confidence": 0.0 to 1.0,
    "reasoning": "Brief explanation of classification decision",
    "key_indicators": ["list", "of", "indicators", "found"]
}

Analyze the document text provided and classify it accurately."""

CLASSIFICATION_WITH_IMAGE_PROMPT = """Analyze this financial document (both the image and extracted text) and classify it.

Consider:
- Visual layout and formatting
- Letterhead and logos
- Document structure
- Textual content

Return your classification as JSON with the following structure:
{
    "document_type": "BANK_STATEMENT" | "BANK_LETTER" | "CERTIFICATE" | "UNKNOWN",
    "confidence": 0.0 to 1.0,
    "reasoning": "Brief explanation of classification decision",
    "key_indicators": ["list", "of", "indicators", "found"]
}"""
