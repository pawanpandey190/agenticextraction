"""CLI entry point for the financial document agent."""

import argparse
import json
import logging
import sys
from pathlib import Path

import structlog

from .config.settings import Settings, get_settings
from .pipeline.orchestrator import PipelineOrchestrator
from .utils.exceptions import FinancialAgentError


def configure_logging(settings: Settings) -> None:
    """Configure structured logging.

    Args:
        settings: Application settings
    """
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    if settings.log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
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
        prog="financial-agent",
        description="Analyze financial documents and evaluate worthiness",
    )

    parser.add_argument(
        "--file", "-f",
        type=str,
        required=True,
        help="Path to the document file (PDF, PNG, or JPEG)",
    )

    parser.add_argument(
        "--threshold", "-t",
        type=float,
        default=None,
        help="Worthiness threshold in EUR (default: from settings)",
    )

    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Output file path for JSON result (default: stdout)",
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output (console logging)",
    )

    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress all logging output",
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    args = parse_args()

    try:
        # Load settings
        settings = get_settings()

        # Override log format for verbose mode
        if args.verbose:
            settings = Settings(
                **{
                    **settings.model_dump(),
                    "log_format": "console",
                    "log_level": "DEBUG",
                }
            )
        elif args.quiet:
            settings = Settings(
                **{
                    **settings.model_dump(),
                    "log_level": "ERROR",
                }
            )

        # Configure logging
        configure_logging(settings)

        logger = structlog.get_logger(__name__)

        # Validate file exists
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"Error: File not found: {file_path}", file=sys.stderr)
            return 1

        # Create orchestrator
        orchestrator = PipelineOrchestrator(
            settings=settings,
            threshold_eur=args.threshold,
        )

        # Process document
        logger.info("Processing document", file_path=str(file_path))
        result = orchestrator.process(str(file_path))

        # Output result
        result_json = result.model_dump_json(indent=2)

        if args.output:
            output_path = Path(args.output)
            output_path.write_text(result_json)
            logger.info("Result written to file", output_path=str(output_path))
        else:
            print(result_json)

        return 0

    except FinancialAgentError as e:
        print(f"Error: {e.message}", file=sys.stderr)
        if e.details:
            print(f"Details: {json.dumps(e.details, indent=2)}", file=sys.stderr)
        return 1

    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
