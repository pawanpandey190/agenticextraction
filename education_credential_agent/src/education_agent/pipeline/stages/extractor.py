"""Credential data extraction stage."""

import re
from statistics import mean

from ...config.constants import DocumentType, GradingSystem
from ...config.settings import Settings
from ...models.credential_data import GradeInfo, Institution
from ...prompts.extraction import EXTRACTION_PROMPT
from ...prompts.system import SYSTEM_PROMPT
from ...services.llm_service import LLMService
from ...utils.exceptions import ExtractionError
from ..base import PipelineContext, PipelineStage


class ExtractorStage(PipelineStage):
    """Stage for extracting detailed credential data from documents."""

    def __init__(self, settings: Settings, llm_service: LLMService | None = None) -> None:
        super().__init__(settings)
        self.llm_service = llm_service or LLMService(settings)

    @property
    def name(self) -> str:
        return "extractor"

    def process(self, context: PipelineContext) -> PipelineContext:
        """Extract credential data from all classified documents.

        Args:
            context: Pipeline context

        Returns:
            Updated context with extracted credential data

        Raises:
            ExtractionError: If extraction fails critically
        """
        if not context.credentials:
            raise ExtractionError("No credentials to extract data from")

        for credential in context.credentials:
            file_path = credential.source_file
            extracted_text = context.get_extracted_text(file_path)

            if not extracted_text:
                self.logger.warning(f"No extracted text for {file_path}, skipping extraction")
                continue

            try:
                # Get first page image if available
                first_page_image = context.get_first_page_image(file_path)

                if first_page_image:
                    base64_data, mime_type = first_page_image
                    result = self.llm_service.extract_credentials(
                        text=extracted_text,
                        image_base64=base64_data,
                        mime_type=mime_type,
                        system_prompt=SYSTEM_PROMPT,
                        extraction_prompt=EXTRACTION_PROMPT,
                    )
                else:
                    result = self.llm_service.extract_credentials(
                        text=extracted_text,
                        system_prompt=SYSTEM_PROMPT,
                        extraction_prompt=EXTRACTION_PROMPT,
                    )

                # Update credential with extracted data
                self._update_credential(credential, result)

                self.logger.info(
                    "Credential data extracted",
                    file_path=file_path,
                    institution=credential.institution.name if credential.institution else None,
                    qualification=credential.qualification_name,
                    grade=credential.final_grade.original_value if credential.final_grade else None,
                )

            except Exception as e:
                self.logger.warning(
                    "Extraction failed for document",
                    file_path=file_path,
                    error=str(e),
                )
                context.metadata.add_error(f"Extraction failed for {file_path}: {e}")

        self.logger.info(
            "Extraction completed",
            total_credentials=len(context.credentials),
        )

        context.set_stage_result(self.name, {
            "total_credentials": len(context.credentials),
        })

        return context

    def _update_credential(self, credential, result: dict) -> None:
        """Update credential with extracted data.

        Args:
            credential: Credential to update
            result: Extraction result dictionary
        """
        # Institution
        if inst := result.get("institution"):
            credential.institution = Institution(
                name=inst.get("name") or "Unknown Institution",
                country=inst.get("country"),
                city=inst.get("city"),
                state=inst.get("state"),
            )

        # Student info
        if student := result.get("student"):
            credential.student_name = student.get("name")
            credential.student_id = student.get("id")

        # Qualification
        if qual := result.get("qualification"):
            credential.qualification_name = qual.get("name")
            credential.specialization = qual.get("specialization")

        # Grade info
        if grade := result.get("grade"):
            grading_system = self._parse_grading_system(grade.get("grading_system", "OTHER"))
            original_value = grade.get("original_value", "")
            numeric_value = grade.get("numeric_value")

            # Post-processing: Aggregate grades for consolidated mark sheets if numeric_value is null
            if numeric_value is None and original_value:
                if credential.document_type == DocumentType.CONSOLIDATED_MARK_SHEET:
                    numeric_value = self._aggregate_grades_from_text(original_value)
                    if numeric_value is not None:
                        self.logger.info(
                            "Aggregated grade from semester values",
                            file_path=credential.source_file,
                            original=original_value,
                            aggregated=numeric_value,
                        )
                        original_value = f"{numeric_value}% (calculated average)"

            credential.final_grade = GradeInfo(
                original_value=original_value,
                numeric_value=numeric_value,
                grading_system=grading_system,
                max_possible=grade.get("max_possible"),
            )

        # Semester info (if applicable)
        if semester := result.get("semester"):
            if semester.get("number"):
                credential.semester_number = semester.get("number")

        # Dates
        if dates := result.get("dates"):
            credential.issue_date = dates.get("issue_date")
            credential.completion_date = dates.get("completion_date")
            credential.year_of_passing = dates.get("year_of_passing")

        # Provisional status
        if result.get("is_provisional") is not None:
            credential.is_provisional = result.get("is_provisional", False)

        # Update confidence if provided
        if result.get("confidence") is not None:
            # Average with classification confidence
            current = credential.confidence_score
            new = float(result.get("confidence", 0.5))
            credential.confidence_score = (current + new) / 2

    def _parse_grading_system(self, system_str: str) -> GradingSystem:
        """Parse grading system from string.

        Args:
            system_str: Grading system string

        Returns:
            GradingSystem enum value
        """
        system_str = system_str.upper().strip()

        try:
            return GradingSystem(system_str)
        except ValueError:
            self.logger.warning(f"Unknown grading system: {system_str}, defaulting to OTHER")
            return GradingSystem.OTHER

    def _aggregate_grades_from_text(self, original_value: str) -> float | None:
        """Extract and aggregate numeric grades from text.

        Handles cases like "Multiple semester percentages: 63%, 57%, 62%"

        Args:
            original_value: The original grade value string

        Returns:
            Aggregated grade value, or None if no grades found
        """
        if not original_value:
            return None

        # Pattern to match percentages
        percentage_pattern = r"(\d+(?:\.\d+)?)\s*%"
        percentages = re.findall(percentage_pattern, original_value)

        if percentages:
            numeric_values = [float(p) for p in percentages]
            if numeric_values:
                return round(mean(numeric_values), 2)

        # Pattern to match GPAs (0-10 range)
        gpa_pattern = r"(\d+\.\d+)"
        gpas = re.findall(gpa_pattern, original_value)

        if gpas:
            numeric_values = [float(g) for g in gpas if 0 <= float(g) <= 10]
            if numeric_values:
                return round(mean(numeric_values), 2)

        return None
