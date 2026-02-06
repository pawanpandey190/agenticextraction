"""Pytest fixtures for education credential agent tests."""

import json
from pathlib import Path

import pytest

from education_agent.config.constants import AcademicLevel, DocumentType, GradingSystem
from education_agent.models.credential_data import CredentialData, GradeInfo, Institution
from education_agent.models.grade_conversion import (
    CountryGradingSystem,
    GradeConversionTable,
    GradeRange,
    LetterGradeMapping,
)
from education_agent.services.grade_table_service import GradeTableService


@pytest.fixture
def sample_grade_table() -> GradeConversionTable:
    """Create a sample grade conversion table for testing."""
    return GradeTableService.create_default_table()


@pytest.fixture
def sample_india_credential() -> CredentialData:
    """Create a sample Indian Bachelor's credential."""
    return CredentialData(
        source_file="/path/to/degree.pdf",
        document_type=DocumentType.DEGREE_CERTIFICATE,
        academic_level=AcademicLevel.BACHELOR,
        qualification_name="Bachelor of Technology",
        specialization="Computer Science",
        institution=Institution(
            name="Indian Institute of Technology Delhi",
            country="IN",
            city="New Delhi",
            state="Delhi",
        ),
        student_name="Test Student",
        student_id="2020CS001",
        final_grade=GradeInfo(
            original_value="75%",
            numeric_value=75.0,
            grading_system=GradingSystem.PERCENTAGE,
            max_possible=100.0,
        ),
        year_of_passing="2024",
        confidence_score=0.95,
    )


@pytest.fixture
def sample_us_credential() -> CredentialData:
    """Create a sample US Bachelor's credential."""
    return CredentialData(
        source_file="/path/to/degree.pdf",
        document_type=DocumentType.DEGREE_CERTIFICATE,
        academic_level=AcademicLevel.BACHELOR,
        qualification_name="Bachelor of Science",
        specialization="Computer Science",
        institution=Institution(
            name="Massachusetts Institute of Technology",
            country="US",
            city="Cambridge",
            state="Massachusetts",
        ),
        student_name="Test Student",
        student_id="2020001",
        final_grade=GradeInfo(
            original_value="3.8",
            numeric_value=3.8,
            grading_system=GradingSystem.GPA_4,
            max_possible=4.0,
        ),
        year_of_passing="2024",
        confidence_score=0.95,
    )


@pytest.fixture
def sample_uk_credential() -> CredentialData:
    """Create a sample UK Bachelor's credential."""
    return CredentialData(
        source_file="/path/to/degree.pdf",
        document_type=DocumentType.DEGREE_CERTIFICATE,
        academic_level=AcademicLevel.BACHELOR,
        qualification_name="Bachelor of Engineering",
        specialization="Mechanical Engineering",
        institution=Institution(
            name="University of Cambridge",
            country="GB",
            city="Cambridge",
        ),
        student_name="Test Student",
        final_grade=GradeInfo(
            original_value="2:1",
            numeric_value=None,
            grading_system=GradingSystem.UK_HONORS,
        ),
        year_of_passing="2024",
        confidence_score=0.9,
    )


@pytest.fixture
def sample_semester_mark_sheets() -> list[CredentialData]:
    """Create sample semester mark sheets for Bachelor's validation."""
    mark_sheets = []
    for sem_num in [1, 2, 3, 4, 6, 7, 8]:  # Missing semester 5
        mark_sheets.append(
            CredentialData(
                source_file=f"/path/to/sem{sem_num}.pdf",
                document_type=DocumentType.SEMESTER_MARK_SHEET,
                academic_level=AcademicLevel.BACHELOR,
                qualification_name="Bachelor of Technology",
                semester_number=sem_num,
                institution=Institution(
                    name="Test University",
                    country="IN",
                ),
                final_grade=GradeInfo(
                    original_value=f"{70 + sem_num}%",
                    numeric_value=70.0 + sem_num,
                    grading_system=GradingSystem.PERCENTAGE,
                ),
            )
        )
    return mark_sheets


@pytest.fixture
def grade_table_path(tmp_path: Path) -> Path:
    """Create a temporary grade table file."""
    table_data = {
        "version": "1.0",
        "countries": [
            {
                "country_code": "IN",
                "country_name": "India",
                "system_type": "percentage",
                "numeric_ranges": [
                    {"min_value": 75, "max_value": 100, "french_min": 14, "french_max": 20},
                    {"min_value": 60, "max_value": 74.99, "french_min": 12, "french_max": 13.99},
                    {"min_value": 50, "max_value": 59.99, "french_min": 10, "french_max": 11.99},
                    {"min_value": 0, "max_value": 49.99, "french_min": 0, "french_max": 9.99},
                ],
            }
        ],
        "default_percentage_ranges": [
            {"min_value": 90, "max_value": 100, "french_min": 16, "french_max": 20},
            {"min_value": 0, "max_value": 89.99, "french_min": 0, "french_max": 15.99},
        ],
        "default_gpa_4_ranges": [],
        "default_gpa_10_ranges": [],
    }

    table_file = tmp_path / "grade_table.json"
    table_file.write_text(json.dumps(table_data))
    return table_file
