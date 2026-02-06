"""CLI entry point for the education credential agent."""

import argparse
import json
import logging
import sys
from pathlib import Path

import structlog

from .config.settings import Settings, get_settings
from .pipeline.orchestrator import PipelineOrchestrator
from .utils.exceptions import EducationAgentError


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
        prog="education-agent",
        description="Evaluate education credentials from documents",
    )

    parser.add_argument(
        "--folder", "-f",
        type=str,
        default=None,
        help="Path to folder containing document files (PDF, PNG, JPEG, JPG)",
    )

    parser.add_argument(
        "--files",
        type=str,
        nargs="+",
        default=None,
        help="Specific file paths to process",
    )

    parser.add_argument(
        "--grade-table", "-g",
        type=str,
        default=None,
        help="Path to grade conversion table (JSON or YAML)",
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

        # Validate input
        if not args.folder and not args.files:
            print("Error: Either --folder or --files must be provided", file=sys.stderr)
            return 1

        # Validate folder exists
        if args.folder:
            folder_path = Path(args.folder)
            if not folder_path.exists():
                print(f"Error: Folder not found: {folder_path}", file=sys.stderr)
                return 1
            if not folder_path.is_dir():
                print(f"Error: Not a directory: {folder_path}", file=sys.stderr)
                return 1

        # Validate files exist
        if args.files:
            for file_path in args.files:
                if not Path(file_path).exists():
                    print(f"Error: File not found: {file_path}", file=sys.stderr)
                    return 1

        # Validate grade table if provided
        if args.grade_table:
            grade_table_path = Path(args.grade_table)
            if not grade_table_path.exists():
                print(f"Error: Grade table not found: {grade_table_path}", file=sys.stderr)
                return 1

        # Create orchestrator
        orchestrator = PipelineOrchestrator(
            settings=settings,
            grade_table_path=args.grade_table,
        )

        # Process documents
        logger.info(
            "Processing documents",
            folder=args.folder,
            files=args.files,
            grade_table=args.grade_table,
        )

        result = orchestrator.process(
            folder_path=args.folder,
            file_paths=args.files,
        )

        # Output result
        result_json = result.model_dump_json(indent=2)

        if args.output:
            output_path = Path(args.output)
            output_path.write_text(result_json)
            logger.info("Result written to file", output_path=str(output_path))
        else:
            print(result_json)

        return 0

    except EducationAgentError as e:
        print(f"Error: {e.message}", file=sys.stderr)
        if e.details:
            print(f"Details: {json.dumps(e.details, indent=2)}", file=sys.stderr)
        return 1

    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
