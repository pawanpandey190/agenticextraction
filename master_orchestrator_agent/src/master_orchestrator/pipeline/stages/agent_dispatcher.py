"""Agent Dispatcher Stage - Routes documents to appropriate sub-agents."""

from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeoutError
from typing import Callable

import structlog

from master_orchestrator.pipeline.base import MasterPipelineContext, MasterPipelineStage
from master_orchestrator.adapters.passport_adapter import PassportAgentAdapter
from master_orchestrator.adapters.financial_adapter import FinancialAgentAdapter
from master_orchestrator.adapters.education_adapter import EducationAgentAdapter
from master_orchestrator.utils.exceptions import AgentDispatchError

logger = structlog.get_logger(__name__)


class AgentDispatcherStage(MasterPipelineStage):
    """Stage 3: Dispatch documents to appropriate sub-agents."""

    def __init__(
        self,
        passport_adapter: PassportAgentAdapter | None = None,
        financial_adapter: FinancialAgentAdapter | None = None,
        education_adapter: EducationAgentAdapter | None = None,
        progress_callback: Callable | None = None,
    ):
        self._passport_adapter = passport_adapter
        self._financial_adapter = financial_adapter
        self._education_adapter = education_adapter
        self._progress_callback = progress_callback

    @property
    def name(self) -> str:
        return "AgentDispatcher"

    def process(self, context: MasterPipelineContext) -> MasterPipelineContext:
        """Dispatch documents to sub-agents and collect results."""
        if context.document_batch is None:
            raise AgentDispatchError("No document batch available for dispatching")

        logger.info("dispatching_to_agents")

        # Initialize adapters lazily if not provided
        self._ensure_adapters(context)

        # Choose between parallel and sequential processing based on settings
        if context.settings.enable_parallel_dispatch:
            self._process_parallel(context)
        else:
            self._process_sequential(context)

        logger.info(
            "agent_dispatch_complete",
            passport_processed=context.passport_raw_result is not None,
            financial_processed=context.financial_raw_result is not None,
            education_processed=context.education_raw_result is not None,
            parallel=context.settings.enable_parallel_dispatch,
        )

        return context

    def _emit_dispatch_progress(
        self,
        context: MasterPipelineContext,
        message: str,
        sub_agent: str | None = None,
        current_document: str | None = None,
        processed_documents: int = 0,
    ) -> None:
        if self._progress_callback:
            # We call the callback with named arguments
            # MasterOrchestrator._emit_progress expects these
            self._progress_callback(
                message=message,
                sub_agent=sub_agent,
                current_document=current_document,
                processed_documents=processed_documents,
                total_documents=len(context.scanned_documents) if context.scanned_documents else 0
            )

    def _process_sequential(self, context: MasterPipelineContext) -> None:
        """Process agents sequentially (original behavior)."""
        processed_count = 0

        # Process passport documents
        if context.document_batch.passport_documents:
            doc = context.document_batch.passport_documents[0]
            self._emit_dispatch_progress(
                context, 
                f"Processing Passport: {doc.file_name}", 
                "passport", 
                doc.file_name,
                processed_count
            )
            context.passport_raw_result = self._process_passport(context)
            processed_count += 1

        # Process financial documents
        if context.document_batch.financial_documents:
            doc = context.document_batch.financial_documents[0]
            self._emit_dispatch_progress(
                context, 
                f"Processing Financial: {doc.file_name}", 
                "financial", 
                doc.file_name,
                processed_count
            )
            context.financial_raw_result = self._process_financial(context)
            # Financial currently only processes the first doc in sequentially
            processed_count += 1 

        # Process education documents
        if context.document_batch.education_documents:
            docs = context.document_batch.education_documents
            self._emit_dispatch_progress(
                context, 
                f"Processing {len(docs)} Education documents", 
                "education", 
                docs[0].file_name,
                processed_count
            )
            context.education_raw_result = self._process_education(context)
            processed_count += len(docs)

    def _process_parallel(self, context: MasterPipelineContext) -> None:
        """Process agents in parallel for improved performance."""
        assert context.document_batch is not None

        # Build list of tasks to execute
        tasks: list[tuple[str, Callable[[], object | None]]] = []

        if context.document_batch.passport_documents:
            tasks.append(("passport", lambda: self._process_passport(context)))

        if context.document_batch.financial_documents:
            tasks.append(("financial", lambda: self._process_financial(context)))

        if context.document_batch.education_documents:
            tasks.append(("education", lambda: self._process_education(context)))

        if not tasks:
            logger.warning("No documents to process")
            return

        logger.info(
            "starting_parallel_dispatch",
            agent_count=len(tasks),
            timeout_seconds=context.settings.parallel_dispatch_timeout_seconds,
        )

        # Execute tasks in parallel
        results: dict[str, object | None] = {}

        with ThreadPoolExecutor(max_workers=len(tasks)) as executor:
            futures = {
                executor.submit(task_fn): agent_name
                for agent_name, task_fn in tasks
            }

            try:
                for future in as_completed(
                    futures,
                    timeout=context.settings.parallel_dispatch_timeout_seconds,
                ):
                    agent_name = futures[future]
                    try:
                        result = future.result()
                        results[agent_name] = result
                        
                        # Emit progress on agent completion
                        # total_docs = total agents being processed in parallel here
                        # processed_count = number of completed agents
                        processed_agents = len(results)
                        self._emit_dispatch_progress(
                            context,
                            f"Agent {agent_name} completed processing",
                            agent_name,
                            None, # No specific doc name in parallel summary
                            processed_agents
                        )
                        
                        logger.info(
                            "agent_completed",
                            agent=agent_name,
                            success=result is not None,
                        )
                    except Exception as e:
                        logger.error(
                            "agent_failed",
                            agent=agent_name,
                            error=str(e),
                        )
                        context.add_error(f"{agent_name.capitalize()} agent failed: {str(e)}")
                        results[agent_name] = None

            except FuturesTimeoutError:
                logger.error(
                    "parallel_dispatch_timeout",
                    timeout_seconds=context.settings.parallel_dispatch_timeout_seconds,
                )
                context.add_error(
                    f"Agent dispatch timed out after {context.settings.parallel_dispatch_timeout_seconds}s"
                )
                # Cancel remaining futures
                for future in futures:
                    future.cancel()

        # Assign results to context
        context.passport_raw_result = results.get("passport")
        context.financial_raw_result = results.get("financial")
        context.education_raw_result = results.get("education")

    def _ensure_adapters(self, context: MasterPipelineContext) -> None:
        """Initialize adapters if not already provided."""
        if self._passport_adapter is None:
            self._passport_adapter = PassportAgentAdapter(context.settings)

        if self._financial_adapter is None:
            self._financial_adapter = FinancialAgentAdapter(context.settings)

        if self._education_adapter is None:
            self._education_adapter = EducationAgentAdapter(context.settings)

    def _process_passport(self, context: MasterPipelineContext) -> object | None:
        """Process passport documents through passport agent."""
        assert context.document_batch is not None
        assert self._passport_adapter is not None

        docs = context.document_batch.passport_documents
        logger.info("processing_passport_documents", count=len(docs))

        try:
            # Process only the first passport document (one passport expected)
            first_doc = docs[0]
            result = self._passport_adapter.process(first_doc.file_path)

            if len(docs) > 1:
                context.add_warning(
                    f"Multiple passport documents found ({len(docs)}), "
                    f"only processing first: {first_doc.file_name}"
                )

            logger.info(
                "passport_processing_complete",
                file=first_doc.file_name,
                success=result is not None,
            )
            return result

        except Exception as e:
            error_msg = f"Passport agent failed: {str(e)}"
            logger.error("passport_agent_error", error=str(e))
            context.add_error(error_msg)
            return None

    def _process_financial(self, context: MasterPipelineContext) -> object | None:
        """Process financial documents through financial agent."""
        assert context.document_batch is not None
        assert self._financial_adapter is not None

        docs = context.document_batch.financial_documents
        logger.info("processing_financial_documents", count=len(docs))

        try:
            # Process only the first financial document
            first_doc = docs[0]
            result = self._financial_adapter.process(
                first_doc.file_path,
                threshold_eur=context.financial_threshold or context.settings.financial_threshold_eur,
                required_period_months=context.bank_statement_months,
            )

            if len(docs) > 1:
                context.add_warning(
                    f"Multiple financial documents found ({len(docs)}), "
                    f"only processing first: {first_doc.file_name}"
                )

            logger.info(
                "financial_processing_complete",
                file=first_doc.file_name,
                success=result is not None,
            )
            return result

        except Exception as e:
            error_msg = f"Financial agent failed: {str(e)}"
            logger.error("financial_agent_error", error=str(e))
            context.add_error(error_msg)
            return None

    def _process_education(self, context: MasterPipelineContext) -> object | None:
        """Process education documents through education agent."""
        assert context.document_batch is not None
        assert self._education_adapter is not None

        docs = context.document_batch.education_documents
        logger.info("processing_education_documents", count=len(docs))

        try:
            # Process all education documents together
            file_paths = [doc.file_path for doc in docs]
            result = self._education_adapter.process(
                file_paths=file_paths,
                grade_table_path=None,  # Use default
            )

            logger.info(
                "education_processing_complete",
                file_count=len(docs),
                success=result is not None,
            )
            return result

        except Exception as e:
            error_msg = f"Education agent failed: {str(e)}"
            logger.error("education_agent_error", error=str(e))
            context.add_error(error_msg)
            return None
