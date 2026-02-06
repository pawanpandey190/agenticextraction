"""Adapters for sub-agents."""

from master_orchestrator.adapters.passport_adapter import PassportAgentAdapter
from master_orchestrator.adapters.financial_adapter import FinancialAgentAdapter
from master_orchestrator.adapters.education_adapter import EducationAgentAdapter

__all__ = [
    "PassportAgentAdapter",
    "FinancialAgentAdapter",
    "EducationAgentAdapter",
]
