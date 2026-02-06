"""CLI entry point for Master Orchestrator Agent."""

import argparse
import json
import logging
import signal
import sys
from pathlib import Path

import structlog


def _setup_signal_handlers() -> None:
    """Configure signal handlers for graceful operation.

    SIGPIPE can occur during parallel execution when multiple threads write
    to stdout/stderr and the receiving pipe closes. This is common when
    piping CLI output. We ignore SIGPIPE to prevent exit code 133.
    """
    # Ignore SIGPIPE to prevent broken pipe errors during parallel execution
    # This is safe because we handle write errors in the logging system
    try:
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except (AttributeError, ValueError):
        # SIGPIPE doesn't exist on Windows, and signal handlers may not be
        # settable in some contexts (e.g., non-main threads)
        pass

from master_orchestrator.config.settings import Settings
from master_orchestrator.config.constants import OutputFormat, ClassificationStrategy
from master_orchestrator.pipeline.orchestrator import MasterOrchestrator
from master_orchestrator.utils.exceptions import MasterOrchestratorError


def setup_logging(log_level: str) -> None:
    """Configure structured logging.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stderr,
        level=getattr(logging, log_level.upper()),
    )


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Master Document Orchestrator Agent - Process and analyze documents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  master-orchestrator ./documents
  master-orchestrator ./documents --output ./results --format both
  master-orchestrator ./documents --threshold 20000 --verbose
        """,
    )

    parser.add_argument(
        "input_folder",
        type=Path,
        help="Path to folder containing documents to process",
    )

    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=None,
        help="Output directory for JSON/Excel files (default: current directory)",
    )

    parser.add_argument(
        "--format", "-f",
        type=str,
        choices=["json", "excel", "both"],
        default="both",
        help="Output format (default: both)",
    )

    parser.add_argument(
        "--threshold", "-t",
        type=float,
        default=None,
        help="Financial worthiness threshold in EUR (default: 15000)",
    )

    parser.add_argument(
        "--grade-table", "-g",
        type=Path,
        default=None,
        help="Path to grade conversion table (JSON or YAML)",
    )

    parser.add_argument(
        "--classification-strategy", "-c",
        type=str,
        choices=["hybrid", "llm_only", "filename_only"],
        default=None,
        help="Document classification strategy (default: hybrid)",
    )

    parser.add_argument(
        "--name-match-threshold",
        type=float,
        default=None,
        help="Name matching threshold for cross-validation (default: 0.85)",
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output",
    )

    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress all output except errors",
    )

    parser.add_argument(
        "--json-output",
        action="store_true",
        help="Output result as JSON to stdout (useful for piping)",
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point for CLI."""
    # Set up signal handlers before any parallel operations
    _setup_signal_handlers()

    args = parse_args()

    # Determine log level
    if args.quiet:
        log_level = "ERROR"
    elif args.verbose:
        log_level = "DEBUG"
    else:
        log_level = "INFO"

    setup_logging(log_level)
    logger = structlog.get_logger(__name__)

    try:
        # Load settings from environment
        settings = Settings()

        # Override settings from command line
        if args.threshold is not None:
            settings.financial_threshold_eur = args.threshold

        if args.classification_strategy is not None:
            settings.classification_strategy = ClassificationStrategy(args.classification_strategy)

        if args.name_match_threshold is not None:
            settings.name_match_threshold = args.name_match_threshold

        # Determine output format
        output_format = OutputFormat(args.format)

        # Determine output directory
        output_dir = args.output or Path.cwd()

        logger.info(
            "starting_orchestration",
            input_folder=str(args.input_folder),
            output_dir=str(output_dir),
            output_format=output_format.value,
        )

        # Create orchestrator and process
        orchestrator = MasterOrchestrator(settings=settings)
        result = orchestrator.process(
            input_folder=args.input_folder,
            output_dir=output_dir,
            output_format=output_format,
        )

        # Output result
        if args.json_output:
            # Output raw JSON to stdout for piping
            print(json.dumps(result.to_output_dict(), indent=2))
        else:
            # Print summary to console
            _print_summary(result)

        # Print output file locations
        if not args.quiet:
            print(f"\nOutput files written to: {output_dir}")
            if output_format in (OutputFormat.JSON, OutputFormat.BOTH):
                print(f"  - {output_dir / 'analysis_result.json'}")
            if output_format in (OutputFormat.EXCEL, OutputFormat.BOTH):
                print(f"  - {output_dir / 'analysis_result.xlsx'}")

        _flush_streams()
        return 0

    except MasterOrchestratorError as e:
        logger.error("orchestration_failed", error=e.message, details=e.details)
        if not args.quiet:
            print(f"\nError: {e.message}", file=sys.stderr)
            if e.details:
                print(f"Details: {json.dumps(e.details, indent=2)}", file=sys.stderr)
        _flush_streams()
        return 1

    except Exception as e:
        logger.exception("unexpected_error", error=str(e))
        if not args.quiet:
            print(f"\nUnexpected error: {str(e)}", file=sys.stderr)
        _flush_streams()
        return 2


def _flush_streams() -> None:
    """Safely flush stdout/stderr to prevent SIGPIPE on exit."""
    try:
        sys.stdout.flush()
        sys.stderr.flush()
    except (BrokenPipeError, IOError):
        pass


def _print_summary(result) -> None:
    """Print a human-readable summary of results."""
    print("\n" + "=" * 60)
    print("DOCUMENT ANALYSIS SUMMARY")
    print("=" * 60)

    # Passport summary
    print("\n📘 PASSPORT")
    if result.passport_details:
        pd = result.passport_details
        print(f"   Name: {pd.full_name or 'N/A'}")
        print(f"   DOB: {pd.date_of_birth or 'N/A'}")
        print(f"   Passport: {pd.passport_number or 'N/A'}")
        print(f"   Accuracy: {pd.accuracy_score}%")
    else:
        print("   Not processed")

    # Education summary
    print("\n📗 EDUCATION")
    if result.education_summary:
        ed = result.education_summary
        print(f"   Qualification: {ed.highest_qualification or 'N/A'}")
        print(f"   Institution: {ed.institution or 'N/A'}")
        print(f"   French Grade: {ed.french_equivalent_grade_0_20 or 'N/A'}/20")
        print(f"   Status: {ed.validation_status.value}")
    else:
        print("   Not processed")

    # Financial summary
    print("\n📙 FINANCIAL")
    if result.financial_summary:
        fs = result.financial_summary
        print(f"   Document Type: {fs.document_type or 'N/A'}")
        print(f"   Amount: {fs.amount_original} {fs.base_currency or ''}")
        print(f"   Amount EUR: {fs.amount_eur or 'N/A'}")
        print(f"   Threshold: {fs.financial_threshold_eur} EUR")
        print(f"   Status: {fs.worthiness_status.value}")
    else:
        print("   Not processed")

    # Cross-validation summary
    print("\n🔍 CROSS-VALIDATION")
    if result.cross_validation:
        cv = result.cross_validation
        name_status = "✓" if cv.name_match else ("✗" if cv.name_match is False else "?")
        dob_status = "✓" if cv.dob_match else ("✗" if cv.dob_match is False else "?")
        print(f"   Name Match: {name_status}")
        print(f"   DOB Match: {dob_status}")
        if cv.remarks:
            print(f"   Remarks: {cv.remarks}")
    else:
        print("   Not performed")

    # Metadata
    if result.metadata:
        print("\n📊 PROCESSING INFO")
        print(f"   Documents: {result.metadata.total_documents_scanned}")
        if result.metadata.processing_time_seconds:
            print(f"   Duration: {result.metadata.processing_time_seconds:.2f}s")
        if result.metadata.processing_errors:
            print(f"   Errors: {len(result.metadata.processing_errors)}")
        if result.metadata.processing_warnings:
            print(f"   Warnings: {len(result.metadata.processing_warnings)}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    sys.exit(main())
