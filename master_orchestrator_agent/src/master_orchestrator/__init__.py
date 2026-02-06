"""Master Document Orchestrator Agent.

Routes documents to specialized sub-agents (passport, financial, education)
and generates unified analysis with cross-validation.
"""

from master_orchestrator.pipeline.orchestrator import MasterOrchestrator
from master_orchestrator.models.unified_result import MasterAnalysisResult

__version__ = "0.1.0"
__all__ = ["MasterOrchestrator", "MasterAnalysisResult"]
