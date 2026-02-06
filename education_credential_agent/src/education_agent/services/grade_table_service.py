"""Grade conversion table loading service."""

import json
from pathlib import Path

import structlog
import yaml

from ..models.grade_conversion import GradeConversionTable
from ..utils.exceptions import ConfigurationError

logger = structlog.get_logger(__name__)


class GradeTableService:
    """Service for loading and managing grade conversion tables."""

    def __init__(self, table_path: str | Path | None = None) -> None:
        """Initialize the grade table service.

        Args:
            table_path: Path to the grade conversion table file (JSON or YAML)
        """
        self.table_path = Path(table_path) if table_path else None
        self._table: GradeConversionTable | None = None

    def load_table(self) -> GradeConversionTable:
        """Load the grade conversion table from file.

        Returns:
            Loaded grade conversion table

        Raises:
            ConfigurationError: If table cannot be loaded
        """
        if self._table is not None:
            return self._table

        if self.table_path is None:
            logger.warning("No grade table path provided, using empty table")
            self._table = GradeConversionTable()
            return self._table

        if not self.table_path.exists():
            raise ConfigurationError(
                f"Grade conversion table not found: {self.table_path}",
                details={"path": str(self.table_path)},
            )

        try:
            content = self.table_path.read_text(encoding="utf-8")

            # Determine file format
            suffix = self.table_path.suffix.lower()
            if suffix in (".yaml", ".yml"):
                data = yaml.safe_load(content)
            elif suffix == ".json":
                data = json.loads(content)
            else:
                # Try JSON first, then YAML
                try:
                    data = json.loads(content)
                except json.JSONDecodeError:
                    data = yaml.safe_load(content)

            self._table = GradeConversionTable.model_validate(data)
            logger.info(
                "Grade conversion table loaded",
                path=str(self.table_path),
                countries=len(self._table.countries),
            )
            return self._table

        except Exception as e:
            raise ConfigurationError(
                f"Failed to load grade conversion table: {e}",
                details={"path": str(self.table_path)},
            ) from e

    def get_table(self) -> GradeConversionTable | None:
        """Get the loaded grade conversion table.

        Returns:
            Grade conversion table or None if not loaded
        """
        return self._table

    def reload_table(self) -> GradeConversionTable:
        """Force reload the grade conversion table.

        Returns:
            Reloaded grade conversion table
        """
        self._table = None
        return self.load_table()

    @staticmethod
    def create_default_table() -> GradeConversionTable:
        """Create a default grade conversion table with common systems.

        Returns:
            Default grade conversion table
        """
        from ..models.grade_conversion import (
            CountryGradingSystem,
            GradeRange,
            LetterGradeMapping,
        )

        # Default percentage ranges (generic)
        default_percentage_ranges = [
            GradeRange(min_value=90, max_value=100, french_min=16, french_max=20),
            GradeRange(min_value=80, max_value=89.99, french_min=14, french_max=15.99),
            GradeRange(min_value=70, max_value=79.99, french_min=12, french_max=13.99),
            GradeRange(min_value=60, max_value=69.99, french_min=10, french_max=11.99),
            GradeRange(min_value=50, max_value=59.99, french_min=8, french_max=9.99),
            GradeRange(min_value=40, max_value=49.99, french_min=6, french_max=7.99),
            GradeRange(min_value=0, max_value=39.99, french_min=0, french_max=5.99),
        ]

        # Default GPA 4.0 ranges
        default_gpa_4_ranges = [
            GradeRange(min_value=3.7, max_value=4.0, french_min=16, french_max=20),
            GradeRange(min_value=3.3, max_value=3.69, french_min=14, french_max=15.99),
            GradeRange(min_value=3.0, max_value=3.29, french_min=12, french_max=13.99),
            GradeRange(min_value=2.7, max_value=2.99, french_min=11, french_max=11.99),
            GradeRange(min_value=2.3, max_value=2.69, french_min=10, french_max=10.99),
            GradeRange(min_value=2.0, max_value=2.29, french_min=9, french_max=9.99),
            GradeRange(min_value=1.0, max_value=1.99, french_min=6, french_max=8.99),
            GradeRange(min_value=0.0, max_value=0.99, french_min=0, french_max=5.99),
        ]

        # Default GPA 10.0 ranges (India)
        default_gpa_10_ranges = [
            GradeRange(min_value=9.0, max_value=10.0, french_min=16, french_max=20),
            GradeRange(min_value=8.0, max_value=8.99, french_min=14, french_max=15.99),
            GradeRange(min_value=7.0, max_value=7.99, french_min=12, french_max=13.99),
            GradeRange(min_value=6.0, max_value=6.99, french_min=10, french_max=11.99),
            GradeRange(min_value=5.0, max_value=5.99, french_min=8, french_max=9.99),
            GradeRange(min_value=4.0, max_value=4.99, french_min=6, french_max=7.99),
            GradeRange(min_value=0.0, max_value=3.99, french_min=0, french_max=5.99),
        ]

        # India percentage system
        india_system = CountryGradingSystem(
            country_code="IN",
            country_name="India",
            system_type="percentage",
            numeric_ranges=[
                GradeRange(min_value=75, max_value=100, french_min=14, french_max=20),
                GradeRange(min_value=60, max_value=74.99, french_min=12, french_max=13.99),
                GradeRange(min_value=50, max_value=59.99, french_min=10, french_max=11.99),
                GradeRange(min_value=40, max_value=49.99, french_min=8, french_max=9.99),
                GradeRange(min_value=35, max_value=39.99, french_min=6, french_max=7.99),
                GradeRange(min_value=0, max_value=34.99, french_min=0, french_max=5.99),
            ],
            notes="Indian universities typically use percentage or CGPA on 10-point scale",
        )

        # US GPA system
        us_system = CountryGradingSystem(
            country_code="US",
            country_name="United States",
            system_type="gpa_4",
            numeric_ranges=[
                GradeRange(min_value=3.7, max_value=4.0, french_min=16, french_max=20),
                GradeRange(min_value=3.3, max_value=3.69, french_min=14, french_max=15.99),
                GradeRange(min_value=3.0, max_value=3.29, french_min=12, french_max=13.99),
                GradeRange(min_value=2.7, max_value=2.99, french_min=11, french_max=11.99),
                GradeRange(min_value=2.3, max_value=2.69, french_min=10, french_max=10.99),
                GradeRange(min_value=2.0, max_value=2.29, french_min=9, french_max=9.99),
                GradeRange(min_value=0.0, max_value=1.99, french_min=0, french_max=8.99),
            ],
            letter_mappings=[
                LetterGradeMapping(letter="A+", french_min=18, french_max=20),
                LetterGradeMapping(letter="A", french_min=16, french_max=17.99),
                LetterGradeMapping(letter="A-", french_min=15, french_max=15.99),
                LetterGradeMapping(letter="B+", french_min=14, french_max=14.99),
                LetterGradeMapping(letter="B", french_min=13, french_max=13.99),
                LetterGradeMapping(letter="B-", french_min=12, french_max=12.99),
                LetterGradeMapping(letter="C+", french_min=11, french_max=11.99),
                LetterGradeMapping(letter="C", french_min=10, french_max=10.99),
                LetterGradeMapping(letter="C-", french_min=9, french_max=9.99),
                LetterGradeMapping(letter="D", french_min=6, french_max=8.99),
                LetterGradeMapping(letter="F", french_min=0, french_max=5.99),
            ],
        )

        # UK honors system
        uk_system = CountryGradingSystem(
            country_code="GB",
            country_name="United Kingdom",
            system_type="letter",
            letter_mappings=[
                LetterGradeMapping(
                    letter="First",
                    french_min=16,
                    french_max=20,
                    description="First Class Honours",
                ),
                LetterGradeMapping(
                    letter="2:1",
                    french_min=14,
                    french_max=15.99,
                    description="Upper Second Class Honours",
                ),
                LetterGradeMapping(
                    letter="2:2",
                    french_min=12,
                    french_max=13.99,
                    description="Lower Second Class Honours",
                ),
                LetterGradeMapping(
                    letter="Third",
                    french_min=10,
                    french_max=11.99,
                    description="Third Class Honours",
                ),
                LetterGradeMapping(
                    letter="Pass",
                    french_min=8,
                    french_max=9.99,
                    description="Ordinary Pass",
                ),
                LetterGradeMapping(
                    letter="Fail",
                    french_min=0,
                    french_max=7.99,
                    description="Fail",
                ),
            ],
            numeric_ranges=[
                GradeRange(min_value=70, max_value=100, french_min=16, french_max=20),
                GradeRange(min_value=60, max_value=69.99, french_min=14, french_max=15.99),
                GradeRange(min_value=50, max_value=59.99, french_min=12, french_max=13.99),
                GradeRange(min_value=40, max_value=49.99, french_min=10, french_max=11.99),
                GradeRange(min_value=0, max_value=39.99, french_min=0, french_max=9.99),
            ],
        )

        # German system (1.0 is best, 5.0 is fail)
        germany_system = CountryGradingSystem(
            country_code="DE",
            country_name="Germany",
            system_type="german_5",
            numeric_ranges=[
                GradeRange(min_value=1.0, max_value=1.5, french_min=16, french_max=20),
                GradeRange(min_value=1.6, max_value=2.5, french_min=14, french_max=15.99),
                GradeRange(min_value=2.6, max_value=3.5, french_min=12, french_max=13.99),
                GradeRange(min_value=3.6, max_value=4.0, french_min=10, french_max=11.99),
                GradeRange(min_value=4.1, max_value=5.0, french_min=0, french_max=9.99),
            ],
            notes="German grades: 1.0-1.5 (sehr gut), 1.6-2.5 (gut), 2.6-3.5 (befriedigend), 3.6-4.0 (ausreichend), 4.1-5.0 (mangelhaft/fail)",
        )

        return GradeConversionTable(
            version="1.0",
            countries=[india_system, us_system, uk_system, germany_system],
            default_percentage_ranges=default_percentage_ranges,
            default_gpa_4_ranges=default_gpa_4_ranges,
            default_gpa_10_ranges=default_gpa_10_ranges,
        )
