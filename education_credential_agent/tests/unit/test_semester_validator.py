"""Unit tests for semester validation functionality."""

import pytest

from education_agent.config.constants import AcademicLevel, DocumentType, GradingSystem
from education_agent.models.credential_data import CredentialData, GradeInfo, Institution
from education_agent.pipeline.stages.semester_validator import validate_bachelor_semesters


class TestSemesterValidation:
    """Tests for Bachelor's semester validation."""

    def test_complete_8_semesters(self, sample_semester_mark_sheets):
        """Test validation with all 8 semesters present."""
        # Add the missing semester 5
        complete_sheets = sample_semester_mark_sheets.copy()
        complete_sheets.append(
            CredentialData(
                source_file="/path/to/sem5.pdf",
                document_type=DocumentType.SEMESTER_MARK_SHEET,
                academic_level=AcademicLevel.BACHELOR,
                qualification_name="Bachelor of Technology",
                semester_number=5,
                institution=Institution(name="Test University", country="IN"),
            )
        )

        # Add the bachelor's degree
        bachelor_degree = CredentialData(
            source_file="/path/to/degree.pdf",
            document_type=DocumentType.DEGREE_CERTIFICATE,
            academic_level=AcademicLevel.BACHELOR,
            qualification_name="Bachelor of Technology",
        )
        complete_sheets.append(bachelor_degree)

        validation = validate_bachelor_semesters(complete_sheets, expected_semesters=8)

        assert validation.is_complete
        assert len(validation.semesters_missing) == 0
        assert len(validation.semesters_found) == 8

    def test_incomplete_semesters(self, sample_semester_mark_sheets):
        """Test validation with missing semester 5."""
        # Add the bachelor's degree
        sample_semester_mark_sheets.append(
            CredentialData(
                source_file="/path/to/degree.pdf",
                document_type=DocumentType.DEGREE_CERTIFICATE,
                academic_level=AcademicLevel.BACHELOR,
                qualification_name="Bachelor of Technology",
            )
        )

        validation = validate_bachelor_semesters(sample_semester_mark_sheets, expected_semesters=8)

        assert not validation.is_complete
        assert 5 in validation.semesters_missing
        assert len(validation.semesters_found) == 7

    def test_6_semester_bachelor(self):
        """Test validation for 3-year Bachelor's (6 semesters)."""
        credentials = [
            CredentialData(
                source_file="/path/to/degree.pdf",
                document_type=DocumentType.DEGREE_CERTIFICATE,
                academic_level=AcademicLevel.BACHELOR,
                qualification_name="Bachelor of Science",
            )
        ]

        # Add semester mark sheets for 1-5 (missing 6)
        for sem in range(1, 6):
            credentials.append(
                CredentialData(
                    source_file=f"/path/to/sem{sem}.pdf",
                    document_type=DocumentType.SEMESTER_MARK_SHEET,
                    academic_level=AcademicLevel.BACHELOR,
                    semester_number=sem,
                )
            )

        validation = validate_bachelor_semesters(credentials, expected_semesters=6)

        assert not validation.is_complete
        assert validation.semesters_missing == [6]
        assert len(validation.semesters_found) == 5

    def test_no_bachelor_degree(self):
        """Test validation when no Bachelor's degree is present."""
        credentials = [
            CredentialData(
                source_file="/path/to/master.pdf",
                document_type=DocumentType.DEGREE_CERTIFICATE,
                academic_level=AcademicLevel.MASTER,
                qualification_name="Master of Technology",
            )
        ]

        validation = validate_bachelor_semesters(credentials)

        assert not validation.is_complete
        assert validation.notes == "No Bachelor's degree found"

    def test_duplicate_semesters(self):
        """Test that duplicate semester numbers are handled."""
        credentials = [
            CredentialData(
                source_file="/path/to/degree.pdf",
                document_type=DocumentType.DEGREE_CERTIFICATE,
                academic_level=AcademicLevel.BACHELOR,
                qualification_name="Bachelor of Technology",
            )
        ]

        # Add duplicate semester 1
        for _ in range(2):
            credentials.append(
                CredentialData(
                    source_file="/path/to/sem1.pdf",
                    document_type=DocumentType.SEMESTER_MARK_SHEET,
                    academic_level=AcademicLevel.BACHELOR,
                    semester_number=1,
                )
            )

        validation = validate_bachelor_semesters(credentials, expected_semesters=8)

        # Should still recognize semester 1 is found, but missing 2-8
        assert 1 in validation.semesters_found
        assert set(validation.semesters_missing) == {2, 3, 4, 5, 6, 7, 8}

    def test_auto_detect_btech_semesters(self):
        """Test automatic detection of expected semesters for B.Tech."""
        credentials = [
            CredentialData(
                source_file="/path/to/degree.pdf",
                document_type=DocumentType.DEGREE_CERTIFICATE,
                academic_level=AcademicLevel.BACHELOR,
                qualification_name="Bachelor of Technology in Computer Science",
            )
        ]

        validation = validate_bachelor_semesters(credentials)

        # B.Tech should expect 8 semesters
        assert validation.expected_semesters == 8

    def test_auto_detect_bsc_semesters(self):
        """Test automatic detection of expected semesters for B.Sc."""
        credentials = [
            CredentialData(
                source_file="/path/to/degree.pdf",
                document_type=DocumentType.DEGREE_CERTIFICATE,
                academic_level=AcademicLevel.BACHELOR,
                qualification_name="Bachelor of Science",
            )
        ]

        validation = validate_bachelor_semesters(credentials)

        # B.Sc should expect 6 semesters
        assert validation.expected_semesters == 6

    def test_semester_record_without_number(self):
        """Test handling of semester mark sheets without semester numbers."""
        credentials = [
            CredentialData(
                source_file="/path/to/degree.pdf",
                document_type=DocumentType.DEGREE_CERTIFICATE,
                academic_level=AcademicLevel.BACHELOR,
                qualification_name="Bachelor of Technology",
            ),
            CredentialData(
                source_file="/path/to/sem.pdf",
                document_type=DocumentType.SEMESTER_MARK_SHEET,
                academic_level=AcademicLevel.BACHELOR,
                semester_number=None,  # No semester number
            ),
        ]

        validation = validate_bachelor_semesters(credentials, expected_semesters=8)

        # Should not count the mark sheet without semester number
        assert len(validation.semesters_found) == 0
        assert validation.semesters_missing == [1, 2, 3, 4, 5, 6, 7, 8]


class TestSemesterValidationEdgeCases:
    """Edge case tests for semester validation."""

    def test_empty_credentials_list(self):
        """Test with empty credentials list."""
        validation = validate_bachelor_semesters([])

        assert not validation.is_complete
        assert validation.notes == "No Bachelor's degree found"

    def test_only_mark_sheets_no_degree(self):
        """Test with only mark sheets but no degree certificate."""
        credentials = [
            CredentialData(
                source_file=f"/path/to/sem{i}.pdf",
                document_type=DocumentType.SEMESTER_MARK_SHEET,
                academic_level=AcademicLevel.BACHELOR,
                semester_number=i,
            )
            for i in range(1, 9)
        ]

        validation = validate_bachelor_semesters(credentials)

        # Even without degree certificate, should validate semesters
        # if academic_level is BACHELOR
        assert validation.expected_semesters == 8

    def test_consolidated_mark_sheet_marks_complete(self):
        """Test that consolidated mark sheet makes validation complete."""
        credentials = [
            CredentialData(
                source_file="/path/to/degree.pdf",
                document_type=DocumentType.DEGREE_CERTIFICATE,
                academic_level=AcademicLevel.BACHELOR,
                qualification_name="Bachelor of Technology",
            ),
            CredentialData(
                source_file="/path/to/consolidated.pdf",
                document_type=DocumentType.CONSOLIDATED_MARK_SHEET,
                academic_level=AcademicLevel.BACHELOR,
            ),
        ]

        validation = validate_bachelor_semesters(credentials, expected_semesters=8)

        # Consolidated mark sheet should mark validation as complete
        assert validation.is_complete
        assert validation.has_consolidated_mark_sheet
        assert validation.notes == "Complete via consolidated mark sheet"
        assert len(validation.semesters_missing) == 0
        # All semesters should be marked as found
        assert validation.semesters_found == [1, 2, 3, 4, 5, 6, 7, 8]

    def test_consolidated_skips_individual_semester_check(self):
        """Test that individual semesters not required when consolidated present."""
        credentials = [
            CredentialData(
                source_file="/path/to/degree.pdf",
                document_type=DocumentType.DEGREE_CERTIFICATE,
                academic_level=AcademicLevel.BACHELOR,
                qualification_name="Bachelor of Technology",
            ),
            CredentialData(
                source_file="/path/to/consolidated.pdf",
                document_type=DocumentType.CONSOLIDATED_MARK_SHEET,
                academic_level=AcademicLevel.BACHELOR,
            ),
            # Only semester 1 mark sheet present, but should still be complete
            CredentialData(
                source_file="/path/to/sem1.pdf",
                document_type=DocumentType.SEMESTER_MARK_SHEET,
                academic_level=AcademicLevel.BACHELOR,
                semester_number=1,
            ),
        ]

        validation = validate_bachelor_semesters(credentials, expected_semesters=8)

        # Should be complete due to consolidated, regardless of individual semesters
        assert validation.is_complete
        assert validation.has_consolidated_mark_sheet

    def test_consolidated_mark_sheet_only_for_bachelor(self):
        """Test that consolidated mark sheet must be at Bachelor level."""
        credentials = [
            CredentialData(
                source_file="/path/to/degree.pdf",
                document_type=DocumentType.DEGREE_CERTIFICATE,
                academic_level=AcademicLevel.BACHELOR,
                qualification_name="Bachelor of Technology",
            ),
            # Consolidated mark sheet at Master level should not affect Bachelor validation
            CredentialData(
                source_file="/path/to/consolidated.pdf",
                document_type=DocumentType.CONSOLIDATED_MARK_SHEET,
                academic_level=AcademicLevel.MASTER,
            ),
        ]

        validation = validate_bachelor_semesters(credentials, expected_semesters=8)

        # Should NOT be complete since consolidated is for Master, not Bachelor
        assert not validation.is_complete
        assert not validation.has_consolidated_mark_sheet

    def test_mixed_academic_levels(self):
        """Test validation ignores non-Bachelor mark sheets."""
        credentials = [
            CredentialData(
                source_file="/path/to/bachelor_degree.pdf",
                document_type=DocumentType.DEGREE_CERTIFICATE,
                academic_level=AcademicLevel.BACHELOR,
                qualification_name="Bachelor of Technology",
            ),
            # Bachelor semester
            CredentialData(
                source_file="/path/to/bachelor_sem1.pdf",
                document_type=DocumentType.SEMESTER_MARK_SHEET,
                academic_level=AcademicLevel.BACHELOR,
                semester_number=1,
            ),
            # Master semester (should be ignored for Bachelor validation)
            CredentialData(
                source_file="/path/to/master_sem1.pdf",
                document_type=DocumentType.SEMESTER_MARK_SHEET,
                academic_level=AcademicLevel.MASTER,
                semester_number=1,
            ),
        ]

        validation = validate_bachelor_semesters(credentials, expected_semesters=8)

        # Should only find the Bachelor semester
        assert validation.semesters_found == [1]


class TestTranscriptWithGrade:
    """Tests for handling transcripts with final grades as complete records."""

    def test_transcript_with_final_grade_marks_complete(self):
        """Test that a transcript with final grade marks validation as complete."""
        credentials = [
            CredentialData(
                source_file="/path/to/degree.pdf",
                document_type=DocumentType.DEGREE_CERTIFICATE,
                academic_level=AcademicLevel.BACHELOR,
                qualification_name="Bachelor of Arts",
            ),
            CredentialData(
                source_file="/path/to/transcript.pdf",
                document_type=DocumentType.TRANSCRIPT,
                academic_level=AcademicLevel.BACHELOR,
                qualification_name="Bachelor of Arts",
                final_grade=GradeInfo(
                    original_value="2.67",
                    numeric_value=2.67,
                    grading_system=GradingSystem.GPA_4,
                    max_possible=4.0,
                ),
            ),
        ]

        validation = validate_bachelor_semesters(credentials, expected_semesters=6)

        # Transcript with final grade should mark validation as complete
        assert validation.is_complete
        assert validation.notes == "Complete via transcript with final grade"
        assert len(validation.semesters_missing) == 0
        # All semesters should be marked as found
        assert validation.semesters_found == [1, 2, 3, 4, 5, 6]

    def test_transcript_without_final_grade_does_not_mark_complete(self):
        """Test that a transcript without final grade does not mark complete."""
        credentials = [
            CredentialData(
                source_file="/path/to/degree.pdf",
                document_type=DocumentType.DEGREE_CERTIFICATE,
                academic_level=AcademicLevel.BACHELOR,
                qualification_name="Bachelor of Arts",
            ),
            CredentialData(
                source_file="/path/to/transcript.pdf",
                document_type=DocumentType.TRANSCRIPT,
                academic_level=AcademicLevel.BACHELOR,
                qualification_name="Bachelor of Arts",
                # No final_grade
            ),
        ]

        validation = validate_bachelor_semesters(credentials, expected_semesters=6)

        # Transcript without final grade should NOT mark validation as complete
        assert not validation.is_complete
        assert validation.semesters_missing == [1, 2, 3, 4, 5, 6]

    def test_transcript_at_wrong_level_does_not_mark_complete(self):
        """Test that a Master's transcript does not mark Bachelor validation complete."""
        credentials = [
            CredentialData(
                source_file="/path/to/degree.pdf",
                document_type=DocumentType.DEGREE_CERTIFICATE,
                academic_level=AcademicLevel.BACHELOR,
                qualification_name="Bachelor of Technology",
            ),
            # Master's transcript should not affect Bachelor validation
            CredentialData(
                source_file="/path/to/master_transcript.pdf",
                document_type=DocumentType.TRANSCRIPT,
                academic_level=AcademicLevel.MASTER,
                qualification_name="Master of Technology",
                final_grade=GradeInfo(
                    original_value="3.5",
                    numeric_value=3.5,
                    grading_system=GradingSystem.GPA_4,
                    max_possible=4.0,
                ),
            ),
        ]

        validation = validate_bachelor_semesters(credentials, expected_semesters=8)

        # Should NOT be complete since transcript is for Master, not Bachelor
        assert not validation.is_complete

    def test_consolidated_takes_precedence_over_transcript(self):
        """Test that consolidated mark sheet takes precedence over transcript."""
        credentials = [
            CredentialData(
                source_file="/path/to/degree.pdf",
                document_type=DocumentType.DEGREE_CERTIFICATE,
                academic_level=AcademicLevel.BACHELOR,
                qualification_name="Bachelor of Technology",
            ),
            CredentialData(
                source_file="/path/to/consolidated.pdf",
                document_type=DocumentType.CONSOLIDATED_MARK_SHEET,
                academic_level=AcademicLevel.BACHELOR,
            ),
            CredentialData(
                source_file="/path/to/transcript.pdf",
                document_type=DocumentType.TRANSCRIPT,
                academic_level=AcademicLevel.BACHELOR,
                final_grade=GradeInfo(
                    original_value="3.8",
                    numeric_value=3.8,
                    grading_system=GradingSystem.GPA_4,
                    max_possible=4.0,
                ),
            ),
        ]

        validation = validate_bachelor_semesters(credentials, expected_semesters=8)

        # Should be complete via consolidated (takes precedence)
        assert validation.is_complete
        assert validation.has_consolidated_mark_sheet
        assert validation.notes == "Complete via consolidated mark sheet"

    def test_international_transcript_marks_complete(self):
        """Test validation with Ethiopian student documents (international case)."""
        credentials = [
            CredentialData(
                source_file="/path/to/bachelor_certificate.pdf",
                document_type=DocumentType.PROVISIONAL_CERTIFICATE,
                academic_level=AcademicLevel.BACHELOR,
                qualification_name="Bachelor of Arts in Sociology",
                institution=Institution(
                    name="Addis Ababa University",
                    country="ET",
                ),
            ),
            CredentialData(
                source_file="/path/to/bachelor_transcript.pdf",
                document_type=DocumentType.TRANSCRIPT,
                academic_level=AcademicLevel.BACHELOR,
                qualification_name="Bachelor of Arts",
                institution=Institution(
                    name="Addis Ababa University",
                    country="ET",
                ),
                final_grade=GradeInfo(
                    original_value="2.67",
                    numeric_value=2.67,
                    grading_system=GradingSystem.GPA_4,
                    max_possible=4.0,
                ),
            ),
        ]

        validation = validate_bachelor_semesters(credentials, expected_semesters=6)

        # Ethiopian transcript with final grade should mark validation as complete
        assert validation.is_complete
        assert validation.notes == "Complete via transcript with final grade"
