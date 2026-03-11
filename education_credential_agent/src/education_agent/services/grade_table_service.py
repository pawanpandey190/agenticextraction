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
            GradeRange(min_value=80, max_value=90, french_min=14, french_max=16),
            GradeRange(min_value=70, max_value=80, french_min=12, french_max=14),
            GradeRange(min_value=60, max_value=70, french_min=10, french_max=12),
            GradeRange(min_value=50, max_value=60, french_min=8, french_max=10),
            GradeRange(min_value=40, max_value=50, french_min=6, french_max=8),
            GradeRange(min_value=0, max_value=40, french_min=0, french_max=6),
        ]

        # Default GPA 4.0 ranges
        default_gpa_4_ranges = [
            GradeRange(min_value=3.7, max_value=4.0, french_min=16, french_max=20),
            GradeRange(min_value=3.3, max_value=3.7, french_min=14, french_max=16),
            GradeRange(min_value=3.0, max_value=3.3, french_min=12, french_max=14),
            GradeRange(min_value=2.7, max_value=3.0, french_min=11, french_max=12),
            GradeRange(min_value=2.3, max_value=2.7, french_min=10, french_max=11),
            GradeRange(min_value=2.0, max_value=2.3, french_min=9, french_max=10),
            GradeRange(min_value=1.0, max_value=2.0, french_min=6, french_max=9),
            GradeRange(min_value=0.0, max_value=1.0, french_min=0, french_max=6),
        ]

        # Default GPA 10.0 ranges (India)
        default_gpa_10_ranges = [
            GradeRange(min_value=9.0, max_value=10.0, french_min=16, french_max=20),
            GradeRange(min_value=8.0, max_value=9.0, french_min=14, french_max=16),
            GradeRange(min_value=7.0, max_value=8.0, french_min=12, french_max=14),
            GradeRange(min_value=6.0, max_value=7.0, french_min=10, french_max=12),
            GradeRange(min_value=5.0, max_value=6.0, french_min=8, french_max=10),
            GradeRange(min_value=4.0, max_value=5.0, french_min=6, french_max=8),
            GradeRange(min_value=0.0, max_value=4.0, french_min=0, french_max=6),
        ]

        # India percentage system
        india_system = CountryGradingSystem(
            country_code="IN",
            country_name="India",
            system_type="percentage",
            numeric_ranges=[
                GradeRange(min_value=75, max_value=100, french_min=14, french_max=20),
                GradeRange(min_value=60, max_value=75, french_min=12, french_max=14),
                GradeRange(min_value=50, max_value=60, french_min=10, french_max=12),
                GradeRange(min_value=35, max_value=50, french_min=8, french_max=10),
                GradeRange(min_value=0, max_value=35, french_min=0, french_max=8),
            ],
            foundation_minimum_pct=35.0,
            foundation_minimum_gpa10=4.0,
            notes="India: Official pass 33-35%, Foundation Min 35% → 8/20 French equiv.",
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
                GradeRange(min_value=2.0, max_value=2.29, french_min=8,  french_max=9.99),
                GradeRange(min_value=0.0, max_value=1.99, french_min=0,  french_max=7.99),
            ],
            letter_mappings=[
                LetterGradeMapping(letter="A+", french_min=18, french_max=20),
                LetterGradeMapping(letter="A",  french_min=16, french_max=17.99),
                LetterGradeMapping(letter="A-", french_min=15, french_max=15.99),
                LetterGradeMapping(letter="B+", french_min=14, french_max=14.99),
                LetterGradeMapping(letter="B",  french_min=13, french_max=13.99),
                LetterGradeMapping(letter="B-", french_min=12, french_max=12.99),
                LetterGradeMapping(letter="C+", french_min=11, french_max=11.99),
                LetterGradeMapping(letter="C",  french_min=10, french_max=10.99),
                LetterGradeMapping(letter="C-", french_min=9,  french_max=9.99),
                LetterGradeMapping(letter="D",  french_min=8,  french_max=8.99, description="Pass — Foundation Min"),
                LetterGradeMapping(letter="F",  french_min=0,  french_max=7.99),
            ],
            foundation_minimum_pct=50.0,  # US: GPA 2.0/4.0 = 50% → 8/20
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
                GradeRange(min_value=40, max_value=49.99, french_min=8,  french_max=11),
                GradeRange(min_value=0,  max_value=39.99, french_min=0,  french_max=8),
            ],
            foundation_minimum_letter="Pass",  # UK: Pass grade (40%+) → 8/20
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
            foundation_minimum_pct=25.0,  # Germany: 4.0/5.0 inverted = ((5-4)/4)*100 = 25% → 8/20
            notes="German grades: 1.0-1.5 (sehr gut), 1.6-2.5 (gut), 2.6-3.5 (befriedigend), 3.6-4.0 (ausreichend), 4.1-5.0 (mangelhaft/fail)",
        )

        # ── SOUTH ASIA ─────────────────────────────────────────────────────────

        # Nepal — percentage 0-100, Foundation Min 35% → 8/20
        nepal_system = CountryGradingSystem(
            country_code="NP",
            country_name="Nepal",
            system_type="percentage",
            numeric_ranges=[
                GradeRange(min_value=80, max_value=100, french_min=14, french_max=20),
                GradeRange(min_value=65, max_value=80, french_min=12, french_max=14),
                GradeRange(min_value=50, max_value=65, french_min=10, french_max=12),
                GradeRange(min_value=35, max_value=50, french_min=8, french_max=10),
                GradeRange(min_value=0, max_value=35, french_min=0, french_max=8),
            ],
            foundation_minimum_pct=35.0,
            notes="Nepal: Official pass 32%, Foundation Min 35% → 8/20 French equiv.",
        )

        # Pakistan — percentage 0-100, Foundation Min 35% → 8/20
        pakistan_system = CountryGradingSystem(
            country_code="PK",
            country_name="Pakistan",
            system_type="percentage",
            numeric_ranges=[
                GradeRange(min_value=80, max_value=100, french_min=14, french_max=20),
                GradeRange(min_value=65, max_value=80, french_min=12, french_max=14),
                GradeRange(min_value=50, max_value=65, french_min=10, french_max=12),
                GradeRange(min_value=35, max_value=50, french_min=8, french_max=10),
                GradeRange(min_value=0, max_value=35, french_min=0, french_max=8),
            ],
            foundation_minimum_pct=35.0,
            notes="Pakistan: Official pass 33%, Foundation Min 35% → 8/20 French equiv.",
        )

        # Bangladesh — GPA 0-5.0, Foundation Min 2.0 → 8/20
        # Formula: (GPA / 5.0) * 20
        bangladesh_system = CountryGradingSystem(
            country_code="BD",
            country_name="Bangladesh",
            system_type="gpa_10",  # Handled as custom 5.0 scale via numeric_ranges
            numeric_ranges=[
                GradeRange(min_value=4.5, max_value=5.0, french_min=16, french_max=20),
                GradeRange(min_value=3.5, max_value=4.5, french_min=12, french_max=16),
                GradeRange(min_value=2.5, max_value=3.5, french_min=10, french_max=12),
                GradeRange(min_value=2.0, max_value=2.5, french_min=8, french_max=10),
                GradeRange(min_value=0.0, max_value=2.0, french_min=0, french_max=8),
            ],
            foundation_minimum_pct=40.0,
            foundation_minimum_gpa10=2.0, # Bangladesh: 2.0 GPA on 5.0 scale → 8/20
            notes="Bangladesh: Official pass 1.0, Foundation Min 2.0 → 8/20 French equiv.",
        )

        # Sri Lanka — percentage 0-100, Foundation Min 40% → 8/20
        srilanka_system = CountryGradingSystem(
            country_code="LK",
            country_name="Sri Lanka",
            system_type="percentage",
            numeric_ranges=[
                GradeRange(min_value=80, max_value=100, french_min=14, french_max=20),
                GradeRange(min_value=65, max_value=80, french_min=12, french_max=14),
                GradeRange(min_value=50, max_value=65, french_min=10, french_max=12),
                GradeRange(min_value=40, max_value=50, french_min=8, french_max=10),
                GradeRange(min_value=0, max_value=40, french_min=0, french_max=8),
            ],
            foundation_minimum_pct=40.0,
            notes="Sri Lanka: Official pass 35%, Foundation Min 40% → 8/20 French equiv.",
        )

        # ── GCC & MENA REGION ───────────────────────────────────────────────────
        # All GCC countries: Official pass 50%, Foundation Min 50% → 8/20

        def _gcc_percentage_ranges():
            """Standard GCC percentage ranges: Foundation Min 50% → 8/20."""
            return [
                GradeRange(min_value=85, max_value=100, french_min=14, french_max=20),
                GradeRange(min_value=75, max_value=85, french_min=12, french_max=14),
                GradeRange(min_value=65, max_value=75, french_min=10, french_max=12),
                GradeRange(min_value=50, max_value=65, french_min=8, french_max=10),
                GradeRange(min_value=0, max_value=50, french_min=0, french_max=8),
            ]

        uae_system = CountryGradingSystem(
            country_code="AE",
            country_name="United Arab Emirates",
            system_type="percentage",
            numeric_ranges=_gcc_percentage_ranges(),
            foundation_minimum_pct=50.0,
            notes="UAE: Official pass 50%, Foundation Min 50% → 8/20 French equiv.",
        )

        saudi_system = CountryGradingSystem(
            country_code="SA",
            country_name="Saudi Arabia",
            system_type="percentage",
            numeric_ranges=_gcc_percentage_ranges(),
            foundation_minimum_pct=50.0,
            notes="Saudi Arabia: Official pass 50%, Foundation Min 50% → 8/20 French equiv.",
        )

        # Qatar has slightly higher Foundation Min: 45%
        qatar_system = CountryGradingSystem(
            country_code="QA",
            country_name="Qatar",
            system_type="percentage",
            numeric_ranges=[
                GradeRange(min_value=85, max_value=100, french_min=14, french_max=20),
                GradeRange(min_value=75, max_value=85, french_min=12, french_max=14),
                GradeRange(min_value=65, max_value=75, french_min=10, french_max=12),
                GradeRange(min_value=45, max_value=65, french_min=8, french_max=10),
                GradeRange(min_value=0, max_value=45, french_min=0, french_max=8),
            ],
            foundation_minimum_pct=45.0,
            notes="Qatar: Official pass 40%, Foundation Min 45% → 8/20 French equiv.",
        )

        kuwait_system = CountryGradingSystem(
            country_code="KW",
            country_name="Kuwait",
            system_type="percentage",
            numeric_ranges=_gcc_percentage_ranges(),
            foundation_minimum_pct=50.0,
            notes="Kuwait: Official pass 50%, Foundation Min 50% → 8/20 French equiv.",
        )

        bahrain_system = CountryGradingSystem(
            country_code="BH",
            country_name="Bahrain",
            system_type="percentage",
            numeric_ranges=_gcc_percentage_ranges(),
            foundation_minimum_pct=50.0,
            notes="Bahrain: Official pass 50%, Foundation Min 50% → 8/20 French equiv.",
        )

        oman_system = CountryGradingSystem(
            country_code="OM",
            country_name="Oman",
            system_type="percentage",
            numeric_ranges=_gcc_percentage_ranges(),
            foundation_minimum_pct=50.0,
            notes="Oman: Official pass 50%, Foundation Min 50% → 8/20 French equiv.",
        )

        egypt_system = CountryGradingSystem(
            country_code="EG",
            country_name="Egypt",
            system_type="percentage",
            numeric_ranges=_gcc_percentage_ranges(),
            foundation_minimum_pct=50.0,
            notes="Egypt: Official pass 50%, Foundation Min 50% → 8/20 French equiv.",
        )

        # ── SUB-SAHARAN AFRICA ──────────────────────────────────────────────────

        # Kenya — KCSE letter grade A to E, Foundation Min D (35%) → 8/20
        kenya_system = CountryGradingSystem(
            country_code="KE",
            country_name="Kenya",
            system_type="letter",
            letter_mappings=[
                LetterGradeMapping(letter="A",  french_min=18, french_max=20, description="Excellent"),
                LetterGradeMapping(letter="A-", french_min=16, french_max=18, description="Very Good"),
                LetterGradeMapping(letter="B+", french_min=15, french_max=16, description="Good Plus"),
                LetterGradeMapping(letter="B",  french_min=14, french_max=15, description="Good"),
                LetterGradeMapping(letter="B-", french_min=13, french_max=14, description="Good Minus"),
                LetterGradeMapping(letter="C+", french_min=12, french_max=13, description="Average Plus"),
                LetterGradeMapping(letter="C",  french_min=11, french_max=12, description="Average"),
                LetterGradeMapping(letter="C-", french_min=10, french_max=11, description="Average Minus"),
                LetterGradeMapping(letter="D+", french_min=9,  french_max=10, description="Below Average (D+)"),
                LetterGradeMapping(letter="D",  french_min=8,  french_max=9,  description="Below Average — Foundation Min"),
                LetterGradeMapping(letter="D-", french_min=4,  french_max=8,  description="Poor"),
                LetterGradeMapping(letter="E",  french_min=0,  french_max=4,  description="Fail"),
            ],
            foundation_minimum_letter="D",  # Kenya: D grade (35%) → 8/20
            notes="Kenya KCSE: A-E scale. Official pass D- (30%), Foundation Min D (35%) → 8/20.",
        )

        # Nigeria — WAEC A1-F9, Foundation Min D7 (45%) → 8/20
        nigeria_system = CountryGradingSystem(
            country_code="NG",
            country_name="Nigeria",
            system_type="letter",
            letter_mappings=[
                LetterGradeMapping(letter="A1", french_min=18, french_max=20, description="Distinction"),
                LetterGradeMapping(letter="B2", french_min=16, french_max=18, description="Very Good"),
                LetterGradeMapping(letter="B3", french_min=14, french_max=16, description="Good"),
                LetterGradeMapping(letter="C4", french_min=12, french_max=14, description="Credit"),
                LetterGradeMapping(letter="C5", french_min=11, french_max=12, description="Credit"),
                LetterGradeMapping(letter="C6", french_min=10, french_max=11, description="Credit"),
                LetterGradeMapping(letter="D7", french_min=8,  french_max=10, description="Pass — Foundation Min"),
                LetterGradeMapping(letter="E8", french_min=5,  french_max=8,  description="Pass (below foundation)"),
                LetterGradeMapping(letter="F9", french_min=0,  french_max=5,  description="Fail"),
            ],
            foundation_minimum_letter="D7",
            notes="Nigeria WAEC: Official pass E8, Foundation Min D7 (45%) → 8/20.",
        )

        # Ghana — WASSCE (same WAEC scale as Nigeria)
        ghana_system = CountryGradingSystem(
            country_code="GH",
            country_name="Ghana",
            system_type="letter",
            letter_mappings=[
                LetterGradeMapping(letter="A1", french_min=18, french_max=20, description="Distinction"),
                LetterGradeMapping(letter="B2", french_min=16, french_max=18, description="Very Good"),
                LetterGradeMapping(letter="B3", french_min=14, french_max=16, description="Good"),
                LetterGradeMapping(letter="C4", french_min=12, french_max=14, description="Credit"),
                LetterGradeMapping(letter="C5", french_min=11, french_max=12, description="Credit"),
                LetterGradeMapping(letter="C6", french_min=10, french_max=11, description="Credit"),
                LetterGradeMapping(letter="D7", french_min=8,  french_max=10, description="Pass — Foundation Min"),
                LetterGradeMapping(letter="E8", french_min=5,  french_max=8,  description="Pass (below foundation)"),
                LetterGradeMapping(letter="F9", french_min=0,  french_max=5,  description="Fail"),
            ],
            foundation_minimum_letter="D7",
            notes="Ghana WASSCE: Official pass E8, Foundation Min D7 (45%) → 8/20.",
        )

        # South Africa — NSC Level 1-7, Foundation Min Level 3 (40%) → 8/20
        south_africa_system = CountryGradingSystem(
            country_code="ZA",
            country_name="South Africa",
            system_type="percentage",
            numeric_ranges=[
                GradeRange(min_value=80, max_value=100, french_min=16, french_max=20),
                GradeRange(min_value=70, max_value=80,  french_min=14, french_max=16),
                GradeRange(min_value=60, max_value=70,  french_min=12, french_max=14),
                GradeRange(min_value=50, max_value=60,  french_min=10, french_max=12),
                GradeRange(min_value=40, max_value=50,  french_min=8,  french_max=10),
                GradeRange(min_value=30, max_value=40,  french_min=4,  french_max=8),
                GradeRange(min_value=0,  max_value=30,  french_min=0,  french_max=4),
            ],
            letter_mappings=[
                LetterGradeMapping(letter="Level 7", french_min=16, french_max=20, description="Outstanding (80-100%)"),
                LetterGradeMapping(letter="Level 6", french_min=14, french_max=16, description="Meritorious (70-79%)"),
                LetterGradeMapping(letter="Level 5", french_min=12, french_max=14, description="Substantial (60-69%)"),
                LetterGradeMapping(letter="Level 4", french_min=10, french_max=12, description="Adequate (50-59%)"),
                LetterGradeMapping(letter="Level 3", french_min=8,  french_max=10, description="Moderate (40-49%) — Foundation Min"),
                LetterGradeMapping(letter="Level 2", french_min=4,  french_max=8,  description="Elementary (30-39%)"),
                LetterGradeMapping(letter="Level 1", french_min=0,  french_max=4,  description="Not Achieved (<30%)"),
            ],
            foundation_minimum_pct=40.0,  # Level 3 = 40%-49% → 8/20
            notes="South Africa NSC: Level 1-7. Level 3 (40%) = Foundation Min → 8/20.",
        )

        # ── FRANCOPHONE AFRICA (already on French 0-20 scale) ─────────────────
        # No conversion needed — grade transfers directly.

        morocco_system = CountryGradingSystem(
            country_code="MA",
            country_name="Morocco",
            system_type="percentage",  # FRENCH_20 handled in grade_converter; ranges as fallback
            numeric_ranges=[
                GradeRange(min_value=16, max_value=20, french_min=16, french_max=20),
                GradeRange(min_value=14, max_value=16, french_min=14, french_max=16),
                GradeRange(min_value=12, max_value=14, french_min=12, french_max=14),
                GradeRange(min_value=10, max_value=12, french_min=10, french_max=12),
                GradeRange(min_value=8,  max_value=10, french_min=8,  french_max=10),
                GradeRange(min_value=0,  max_value=8,  french_min=0,  french_max=8),
            ],
            foundation_minimum_pct=40.0,  # 8/20 ÷ 20 * 100 = 40%
            notes="Morocco uses French 0-20 scale directly. Official pass 10/20. Foundation Min 8/20.",
        )

        def _french_20_system(code, name):
            """Create a Francophone country system (direct 0-20 mapping)."""
            return CountryGradingSystem(
                country_code=code,
                country_name=name,
                system_type="percentage",
                numeric_ranges=[
                    GradeRange(min_value=16, max_value=20, french_min=16, french_max=20),
                    GradeRange(min_value=14, max_value=16, french_min=14, french_max=16),
                    GradeRange(min_value=12, max_value=14, french_min=12, french_max=14),
                    GradeRange(min_value=10, max_value=12, french_min=10, french_max=12),
                    GradeRange(min_value=8,  max_value=10, french_min=8,  french_max=10),
                    GradeRange(min_value=0,  max_value=8,  french_min=0,  french_max=8),
                ],
                foundation_minimum_pct=40.0,  # 8/20 ÷ 20 * 100 = 40%
                notes=f"{name} uses French 0-20 scale directly. Official pass 10/20. Foundation Min 8/20.",
            )

        algeria_system   = _french_20_system("DZ", "Algeria")
        tunisia_system   = _french_20_system("TN", "Tunisia")
        senegal_system   = _french_20_system("SN", "Senegal")
        ivory_system     = _french_20_system("CI", "Côte d'Ivoire")
        cameroon_system  = _french_20_system("CM", "Cameroon")

        # ── ASIA-PACIFIC ────────────────────────────────────────────────────────

        # China — 0-100%, Foundation Min 60% → 8/20
        china_system = CountryGradingSystem(
            country_code="CN",
            country_name="China",
            system_type="percentage",
            numeric_ranges=[
                GradeRange(min_value=90, max_value=100, french_min=16, french_max=20),
                GradeRange(min_value=80, max_value=90,  french_min=13, french_max=16),
                GradeRange(min_value=70, max_value=80,  french_min=10, french_max=13),
                GradeRange(min_value=60, max_value=70,  french_min=8,  french_max=10),
                GradeRange(min_value=0,  max_value=60,  french_min=0,  french_max=8),
            ],
            foundation_minimum_pct=60.0,  # China official threshold → 8/20
            notes="China: Official pass 60%, Foundation Min 60% → 8/20. Higher local pass standard.",
        )

        # Vietnam — 0-10 scale, Foundation Min 4.0 → 8/20
        # Formula (4/10)*20 = 8 ✅ — formula works correctly here
        vietnam_system = CountryGradingSystem(
            country_code="VN",
            country_name="Vietnam",
            system_type="gpa_10",
            numeric_ranges=[
                GradeRange(min_value=9.0, max_value=10.0, french_min=18, french_max=20),
                GradeRange(min_value=8.0, max_value=9.0,  french_min=16, french_max=18),
                GradeRange(min_value=7.0, max_value=8.0,  french_min=14, french_max=16),
                GradeRange(min_value=6.0, max_value=7.0,  french_min=12, french_max=14),
                GradeRange(min_value=5.0, max_value=6.0,  french_min=10, french_max=12),
                GradeRange(min_value=4.0, max_value=5.0,  french_min=8,  french_max=10),
                GradeRange(min_value=0.0, max_value=4.0,  french_min=0,  french_max=8),
            ],
            foundation_minimum_pct=40.0,
            foundation_minimum_gpa10=4.0, # Vietnam: 4.0 on 10 scale → 8/20
            notes="Vietnam: Official pass 5.0, Foundation Min 4.0 → 8/20 French equiv.",
        )

        # Philippines — 1.0-5.0 (inverted: 1.0=best). Foundation Min 3.0 (≈75%) → 8/20
        # Grade 3.0 represents 75% in Philippine system. Range-based for accuracy.
        philippines_system = CountryGradingSystem(
            country_code="PH",
            country_name="Philippines",
            system_type="german_5",
            numeric_ranges=[
                GradeRange(min_value=1.0, max_value=1.5, french_min=18, french_max=20),
                GradeRange(min_value=1.5, max_value=2.0, french_min=15, french_max=18),
                GradeRange(min_value=2.0, max_value=2.5, french_min=12, french_max=15),
                GradeRange(min_value=2.5, max_value=3.0, french_min=8, french_max=12),
                GradeRange(min_value=3.0, max_value=3.0, french_min=8,  french_max=8),
                GradeRange(min_value=3.0, max_value=5.0, french_min=0,  french_max=8),
            ],
            foundation_minimum_pct=75.0, # 3.0 on 1.0-5.0 scale is 75%
            notes="Philippines: Foundation Min 3.0 (75%) → 8/20.",
        )

        # Indonesia — GPA 0-4.0, Foundation Min 2.0 → 8/20
        # Formula: (2.0/4.0)*20 = 10 (formula gives 10, document says 8). Use ranges.
        indonesia_system = CountryGradingSystem(
            country_code="ID",
            country_name="Indonesia",
            system_type="gpa_4",
            numeric_ranges=[
                GradeRange(min_value=3.5, max_value=4.0, french_min=16, french_max=20),
                GradeRange(min_value=3.0, max_value=3.5, french_min=13, french_max=16),
                GradeRange(min_value=2.5, max_value=3.0, french_min=10, french_max=13),
                GradeRange(min_value=2.0, max_value=2.5, french_min=8,  french_max=10),
                GradeRange(min_value=0.0, max_value=2.0, french_min=0,  french_max=8),
            ],
            foundation_minimum_pct=50.0,  # 2.0/4.0 = 50% → 8/20
            notes="Indonesia: GPA 0-4.0. Official pass 2.0, Foundation Min 2.0 → 8/20.",
        )

        # Malaysia SPM — A+ to G, Foundation Min E (40%) → 8/20
        malaysia_system = CountryGradingSystem(
            country_code="MY",
            country_name="Malaysia",
            system_type="letter",
            letter_mappings=[
                LetterGradeMapping(letter="A+", french_min=18, french_max=20, description="Excellent (90-100%)"),
                LetterGradeMapping(letter="A",  french_min=16, french_max=18, description="Excellent (80-89%)"),
                LetterGradeMapping(letter="A-", french_min=14, french_max=16, description="Very Good (70-79%)"),
                LetterGradeMapping(letter="B+", french_min=13, french_max=14, description="Good (65-69%)"),
                LetterGradeMapping(letter="B",  french_min=12, french_max=13, description="Good (60-64%)"),
                LetterGradeMapping(letter="C+", french_min=11, french_max=12, description="Satisfactory (55-59%)"),
                LetterGradeMapping(letter="C",  french_min=10, french_max=11, description="Satisfactory (50-54%)"),
                LetterGradeMapping(letter="D",  french_min=9,  french_max=10, description="Pass (45-49%)"),
                LetterGradeMapping(letter="E",  french_min=8,  french_max=9,  description="Pass — Foundation Min (40-44%)"),
                LetterGradeMapping(letter="G",  french_min=0,  french_max=8,  description="Fail (<40%)"),
            ],
            foundation_minimum_letter="E",  # Malaysia SPM: grade E (40%) → 8/20
            notes="Malaysia SPM: A+ to G. Foundation Min E (40%) → 8/20.",
        )

        # ── EASTERN EUROPE & LATIN AMERICA ─────────────────────────────────────

        # Russia — 1-5 scale (5=best, 3=pass). Foundation Min 3 → 8/20
        russia_system = CountryGradingSystem(
            country_code="RU",
            country_name="Russia",
            system_type="german_5",
            numeric_ranges=[
                GradeRange(min_value=5.0, max_value=5.0, french_min=18, french_max=20),
                GradeRange(min_value=4.0, max_value=5.0, french_min=13, french_max=18),
                GradeRange(min_value=3.0, max_value=4.0, french_min=8,  french_max=13),
                GradeRange(min_value=0.0, max_value=3.0, french_min=0,  french_max=8),
            ],
            foundation_minimum_pct=50.0,
            notes="Russia: Official pass 3, Foundation Min 3 → 8/20 French equiv.",
        )

        # Brazil — 0-10 scale, Foundation Min 4.0 → 8/20
        # Formula: (4/10)*20 = 8 ✅ — formula works correctly
        brazil_system = CountryGradingSystem(
            country_code="BR",
            country_name="Brazil",
            system_type="gpa_10",
            numeric_ranges=[
                GradeRange(min_value=9.0, max_value=10.0, french_min=18, french_max=20),
                GradeRange(min_value=8.0, max_value=9.0,  french_min=16, french_max=18),
                GradeRange(min_value=7.0, max_value=8.0,  french_min=14, french_max=16),
                GradeRange(min_value=6.0, max_value=7.0,  french_min=12, french_max=14),
                GradeRange(min_value=5.0, max_value=6.0,  french_min=10, french_max=12),
                GradeRange(min_value=4.0, max_value=5.0,  french_min=8,  french_max=10),
                GradeRange(min_value=0.0, max_value=4.0,  french_min=0,  french_max=8),
            ],
            foundation_minimum_pct=40.0,
            foundation_minimum_gpa10=4.0, # Brazil: 4.0 on 10 scale → 8/20
            notes="Brazil: Official pass 5.0, Foundation Min 4.0 → 8/20 French equiv.",
        )

        # Mexico — 0-10 scale, Foundation Min 5.0 → 8/20
        mexico_system = CountryGradingSystem(
            country_code="MX",
            country_name="Mexico",
            system_type="gpa_10",
            numeric_ranges=[
                GradeRange(min_value=9.0, max_value=10.0, french_min=18, french_max=20),
                GradeRange(min_value=8.0, max_value=9.0,  french_min=14, french_max=18),
                GradeRange(min_value=7.0, max_value=8.0,  french_min=11, french_max=14),
                GradeRange(min_value=6.0, max_value=7.0,  french_min=9,  french_max=11),
                GradeRange(min_value=5.0, max_value=6.0,  french_min=8,  french_max=9),
                GradeRange(min_value=0.0, max_value=5.0,  french_min=0,  french_max=8),
            ],
            foundation_minimum_pct=50.0,
            foundation_minimum_gpa10=5.0, # Mexico: 5.0 on 10 scale → 8/20
            notes="Mexico: Official pass 6.0, Foundation Min 5.0 → 8/20 French equiv.",
        )

        # Turkey — 0-100%, Foundation Min 45% → 8/20
        turkey_system = CountryGradingSystem(
            country_code="TR",
            country_name="Turkey",
            system_type="percentage",
            numeric_ranges=[
                GradeRange(min_value=85, max_value=100, french_min=16, french_max=20),
                GradeRange(min_value=70, max_value=85,  french_min=13, french_max=16),
                GradeRange(min_value=60, max_value=70,  french_min=10, french_max=13),
                GradeRange(min_value=45, max_value=60,  french_min=8,  french_max=10),
                GradeRange(min_value=0,  max_value=45,  french_min=0,  french_max=8),
            ],
            foundation_minimum_pct=45.0,
            notes="Turkey: 0-100%. Official pass 45%, Foundation Min 45% → 8/20.",
        )

        # ── INTERNATIONAL CURRICULA ──────────────────────────────────────────

        # IB Diploma — 24 points → 8/20
        ib_system = CountryGradingSystem(
            country_code="IB",
            country_name="International Baccalaureate",
            system_type="percentage", # Handled via range
            numeric_ranges=[
                GradeRange(min_value=40, max_value=45, french_min=16, french_max=20),
                GradeRange(min_value=35, max_value=40, french_min=14, french_max=16),
                GradeRange(min_value=30, max_value=35, french_min=12, french_max=14),
                GradeRange(min_value=24, max_value=30, french_min=8,  french_max=12),
                GradeRange(min_value=0,  max_value=24, french_min=0,  french_max=8),
            ],
            foundation_minimum_pct=53.3, # 24/45 ≈ 53.3%
            notes="IB Diploma: Foundation Min 24 points → 8/20.",
        )

        # Cambridge A-Levels — EEE → 8/20
        alevel_system = CountryGradingSystem(
            country_code="AL",
            country_name="Cambridge A-Levels",
            system_type="letter",
            letter_mappings=[
                LetterGradeMapping(letter="A*", french_min=18, french_max=20),
                LetterGradeMapping(letter="A",  french_min=16, french_max=18),
                LetterGradeMapping(letter="B",  french_min=14, french_max=16),
                LetterGradeMapping(letter="C",  french_min=12, french_max=14),
                LetterGradeMapping(letter="D",  french_min=10, french_max=12),
                LetterGradeMapping(letter="E",  french_min=8,  french_max=10),
                LetterGradeMapping(letter="U",  french_min=0,  french_max=8),
            ],
            foundation_minimum_letter="E",
            notes="A-Levels: Foundation Min Grade E (pass) → 8/20.",
        )

        return GradeConversionTable(
            version="2.1",
            countries=[
                # South Asia
                india_system, nepal_system, pakistan_system, bangladesh_system, srilanka_system,
                # GCC & MENA
                uae_system, saudi_system, qatar_system, kuwait_system,
                bahrain_system, oman_system, egypt_system,
                # Sub-Saharan Africa
                kenya_system, nigeria_system, ghana_system, south_africa_system,
                # Francophone Africa (French 0-20 direct)
                morocco_system, algeria_system, tunisia_system, senegal_system,
                ivory_system, cameroon_system,
                # Asia-Pacific
                china_system, vietnam_system, philippines_system, indonesia_system, malaysia_system,
                # Eastern Europe & Latin America
                russia_system, brazil_system, mexico_system, turkey_system,
                # International
                ib_system, alevel_system,
                # Existing: US, UK, Germany
                us_system, uk_system, germany_system,
            ],
            default_percentage_ranges=default_percentage_ranges,
            default_gpa_4_ranges=default_gpa_4_ranges,
            default_gpa_10_ranges=default_gpa_10_ranges,
        )
