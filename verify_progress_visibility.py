
import logging
from unittest.mock import MagicMock, patch
from master_orchestrator.pipeline.stages.agent_dispatcher import AgentDispatcherStage
from master_orchestrator.pipeline.base import MasterPipelineContext
from master_orchestrator.config.settings import Settings

# Setup logging
logging.basicConfig(level=logging.INFO)

def test_progress_visibility():
    def progress_callback(**kwargs):
        print(f"PROGRESS UPDATE: {kwargs.get('message')} | Sub-agent: {kwargs.get('sub_agent')}")

    # Mock context and settings
    settings = Settings()
    settings.enable_parallel_dispatch = False # Test sequential for easier trace
    
    context = MasterPipelineContext(input_folder=".", settings=settings)
    context.document_batch = MagicMock()
    context.document_batch.passport_documents = [MagicMock(file_path="p.jpg", file_name="p.jpg")]
    context.document_batch.financial_documents = []
    context.document_batch.education_documents = []
    context.scanned_documents = ["p.jpg"]

    # Mock PassportAdapter
    passport_adapter = MagicMock()
    
    def mock_process(file_path, progress_callback=None):
        if progress_callback:
            progress_callback("OCRProcessor", 1, 3)
            progress_callback("Extractor", 2, 3)
            progress_callback("Scorer", 3, 3)
        return MagicMock()

    passport_adapter.process.side_effect = mock_process

    dispatcher = AgentDispatcherStage(
        passport_adapter=passport_adapter,
        progress_callback=progress_callback
    )

    print("\nTesting progress visibility:")
    dispatcher.process(context)

if __name__ == "__main__":
    test_progress_visibility()
