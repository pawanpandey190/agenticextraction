"""CLI entry point for passport analysis agent."""

import argparse
import json
import sys
from pathlib import Path

import structlog

from .config.settings import Settings, get_settings
from .pipeline.orchestrator import PassportPipelineOrchestrator


def setup_logging(log_level: str = "INFO", log_format: str = "console") -> None:
    """Configure structured logging.

    Args:
        log_level: Logging level
        log_format: Format (json or console)
    """
    if log_format == "json":
        structlog.configure(
            processors=[
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.BoundLogger,
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )
    else:
        structlog.configure(
            processors=[
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.dev.ConsoleRenderer(),
            ],
            wrapper_class=structlog.BoundLogger,
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        prog="passport-agent",
        description="Analyze passport documents using AI-powered extraction",
    )

    parser.add_argument(
        "input",
        type=str,
        help="Path to passport document (PDF, PNG, JPEG) or directory",
    )

    parser.add_argument(
        "--output",
        "-o",
        choices=["json", "text", "summary"],
        default="text",
        help="Output format (default: text)",
    )

    parser.add_argument(
        "--output-file",
        "-f",
        type=str,
        help="Write output to file instead of stdout",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress all logging output",
    )

    return parser.parse_args()


def format_text_output(result) -> str:
    """Format result as human-readable text.

    Args:
        result: PassportAnalysisResult

    Returns:
        Formatted text string
    """
    lines = []
    lines.append("=" * 60)
    lines.append("PASSPORT ANALYSIS RESULT")
    lines.append("=" * 60)

    # Score and confidence
    lines.append(f"\nAccuracy Score: {result.accuracy_score}/100")
    lines.append(f"Confidence Level: {result.confidence_level}")

    # Visual data
    viz = result.extracted_passport_data
    lines.append("\n--- Visual Inspection Zone Data ---")
    lines.append(f"Name: {viz.first_name or 'N/A'} {viz.last_name or 'N/A'}")
    lines.append(f"Date of Birth: {viz.date_of_birth or 'N/A'}")
    lines.append(f"Passport Number: {viz.passport_number or 'N/A'}")
    lines.append(f"Issuing Country: {viz.issuing_country or 'N/A'}")
    lines.append(f"Expiry Date: {viz.passport_expiry_date or 'N/A'}")
    lines.append(f"Sex: {viz.sex or 'N/A'}")
    lines.append(f"OCR Confidence: {viz.ocr_confidence:.2%}")

    # MRZ data
    if result.extracted_mrz_data:
        mrz = result.extracted_mrz_data
        lines.append("\n--- MRZ Data ---")
        lines.append(f"Name: {mrz.first_name} {mrz.last_name}")
        lines.append(f"Date of Birth: {mrz.date_of_birth}")
        lines.append(f"Passport Number: {mrz.passport_number}")
        lines.append(f"Nationality: {mrz.nationality}")
        lines.append(f"Expiry Date: {mrz.expiry_date}")
        lines.append(f"Sex: {mrz.sex}")

        # Checksum validation
        lines.append("\n--- MRZ Checksums ---")
        for field, valid in result.mrz_checksum_validation.items():
            status = "✓" if valid else "✗"
            lines.append(f"  {field}: {status}")
    else:
        lines.append("\n--- MRZ Data ---")
        lines.append("MRZ not detected or could not be parsed")

    # Field comparison
    if result.field_comparison:
        lines.append("\n--- Field Comparison (Visual vs MRZ) ---")
        for field, match in result.field_comparison.items():
            status = "✓ Match" if match == "match" else "✗ Mismatch"
            lines.append(f"  {field}: {status}")

    # Errors and warnings
    if result.processing_errors:
        lines.append("\n--- Errors ---")
        for error in result.processing_errors:
            lines.append(f"  • {error}")

    if result.processing_warnings:
        lines.append("\n--- Warnings ---")
        for warning in result.processing_warnings:
            lines.append(f"  • {warning}")

    lines.append("\n" + "=" * 60)
    return "\n".join(lines)


def format_summary_output(result) -> str:
    """Format result as brief summary.

    Args:
        result: PassportAnalysisResult

    Returns:
        Summary string
    """
    viz = result.extracted_passport_data
    name = f"{viz.first_name or ''} {viz.last_name or ''}".strip() or "Unknown"

    return (
        f"Passport: {viz.passport_number or 'N/A'} | "
        f"Name: {name} | "
        f"Score: {result.accuracy_score}/100 ({result.confidence_level})"
    )


def process_file(
    orchestrator: PassportPipelineOrchestrator,
    file_path: str,
    output_format: str,
) -> str:
    """Process a single file and return formatted output.

    Args:
        orchestrator: Pipeline orchestrator
        file_path: Path to passport document
        output_format: Output format

    Returns:
        Formatted output string
    """
    result = orchestrator.process(file_path)

    if output_format == "json":
        return result.model_dump_json(indent=2)
    elif output_format == "summary":
        return format_summary_output(result)
    else:
        return format_text_output(result)


def main() -> int:
    """Main entry point.

    Returns:
        Exit code
    """
    args = parse_args()

    # Setup logging
    if args.quiet:
        log_level = "ERROR"
    elif args.verbose:
        log_level = "DEBUG"
    else:
        log_level = "INFO"

    setup_logging(log_level=log_level, log_format="console")
    logger = structlog.get_logger("passport-agent")

    # Load settings
    try:
        settings = get_settings()
    except Exception as e:
        print(f"Error loading settings: {e}", file=sys.stderr)
        print("Make sure PA_ANTHROPIC_API_KEY is set in environment or .env file")
        return 1

    # Create orchestrator
    orchestrator = PassportPipelineOrchestrator(settings)

    # Process input
    input_path = Path(args.input)

    if not input_path.exists():
        print(f"Error: Input path does not exist: {input_path}", file=sys.stderr)
        return 1

    outputs = []

    if input_path.is_dir():
        # Process all supported files in directory
        supported_extensions = {".pdf", ".png", ".jpg", ".jpeg"}
        files = [
            f for f in input_path.iterdir() if f.suffix.lower() in supported_extensions
        ]

        if not files:
            print(f"No supported files found in {input_path}", file=sys.stderr)
            return 1

        logger.info("Processing directory", path=str(input_path), file_count=len(files))

        for file_path in sorted(files):
            try:
                output = process_file(orchestrator, str(file_path), args.output)
                outputs.append(output)
            except Exception as e:
                logger.error("Failed to process file", path=str(file_path), error=str(e))
                outputs.append(f"Error processing {file_path}: {e}")
    else:
        # Process single file
        try:
            output = process_file(orchestrator, str(input_path), args.output)
            outputs.append(output)
        except Exception as e:
            logger.error("Failed to process file", path=str(input_path), error=str(e))
            print(f"Error: {e}", file=sys.stderr)
            return 1

    # Output results
    final_output = "\n\n".join(outputs)

    if args.output_file:
        Path(args.output_file).write_text(final_output)
        logger.info("Output written to file", path=args.output_file)
    else:
        print(final_output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
