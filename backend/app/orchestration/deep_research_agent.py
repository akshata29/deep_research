"""
Deep Research Agent - Main orchestrator for multi-agent research system.
"""

import uuid
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
import structlog
from typing import Dict, List, Any, Optional
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatPromptExecutionSettings

from .config import get_orchestration_config, get_project_config
from .memory import MemoryManager, MemoryPlugin
from .memory.utils import create_azure_openai_text_embedding_with_managed_identity
from .search import ModularSearchPlugin, WebSearchProvider, AzureSearchProvider
from .agent_factory import create_agents_with_memory, get_azure_openai_service
from .prompts import MANAGER_PROMPT, FINAL_ANSWER_PROMPT
from .session_manager import OrchestrationSessionManager

logger = structlog.get_logger(__name__)


class DeepResearchAgent:
    """
    Main orchestrator for the Deep Research Agent system using Semantic Kernel.
    
    This class coordinates multiple specialized AI agents to perform comprehensive
    research tasks using Azure OpenAI and Semantic Kernel's MagenticOrchestration.
    """
    
    def __init__(
        self,
        session_id: Optional[str] = None,
        project_id: Optional[str] = None,
        progress_callback: Optional[callable] = None
    ):
        """
        Initialize the research agent system.
        
        Args:
            session_id: Unique session identifier
            project_id: Project identifier for context grouping
            progress_callback: Optional callback for progress updates
        """
        self.session_id = session_id or str(uuid.uuid4())
        self.project_id = project_id or f"project_{self.session_id[:8]}"
        self.is_new_session = session_id is None
        self.progress_callback = progress_callback
        
        # Core components
        self.kernel: Optional[Kernel] = None
        self.memory_manager: Optional[MemoryManager] = None
        self.memory_plugin: Optional[MemoryPlugin] = None
        self.search_plugin: Optional[ModularSearchPlugin] = None
        self.agents: Dict[str, Any] = {}
        self.session_manager = OrchestrationSessionManager()
        
        # Configuration
        self.config = get_orchestration_config()
        self.project_config = get_project_config()
        
        # Result storage  
        self.research_results: List[Dict[str, Any]] = []
        
        logger.info(
            "DeepResearchAgent initialized",
            session_id=self.session_id[:8],
            project_id=self.project_id,
            is_new_session=self.is_new_session
        )
    
    async def initialize(self) -> None:
        """Initialize the agent orchestration system with memory and search."""
        try:
            logger.info("Initializing Deep Research Agent system")
            
            # Initialize memory system
            await self._initialize_memory()
            
            # Initialize search system
            await self._initialize_search()
            
            # Create agents
            await self._create_agents()
            
            # Setup orchestration
            await self._setup_orchestration()
            
            # Initialize runtime
            self._setup_runtime()
            
            logger.info("Deep Research Agent system initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize Deep Research Agent", error=str(e))
            raise
    
    async def _initialize_memory(self) -> None:
        """Initialize the memory management system."""
        try:
            # Create embedding generator using existing Azure infrastructure
            embedding_generator = create_azure_openai_text_embedding_with_managed_identity(
                endpoint=self.config.azure_ai_endpoint,
                api_version=self.config.azure_openai_api_version,
                deployment_name="embedding",  # Try a common embedding model
                service_id="azure_embedding"
            )
            
            logger.debug("Embedding generator created", type=type(embedding_generator).__name__)
            
            # Initialize memory manager
            self.memory_manager = MemoryManager(
                embedding_generator=embedding_generator,
                session_id=self.session_id,
                project_id=self.project_id
            )
            
            await self.memory_manager.initialize()
            
            # Create memory plugin
            self.memory_plugin = MemoryPlugin(self.memory_manager)
            
            logger.info("Memory system initialized")
            
        except Exception as e:
            logger.error("Failed to initialize memory system", error=str(e))
            raise
    
    async def _initialize_search(self) -> None:
        """Initialize the search system."""
        try:
            # Initialize Azure Search provider if configured
            azure_search_provider = None
            if (self.config.azure_search_endpoint and 
                self.config.azure_search_api_key and 
                self.config.azure_search_index_name):
                
                azure_search_provider = AzureSearchProvider(
                    endpoint=self.config.azure_search_endpoint,
                    api_key=self.config.azure_search_api_key,
                    index_name=self.config.azure_search_index_name
                )
                logger.info("Azure Search provider initialized")
            else:
                logger.info("Azure Search not configured, internal search disabled")
            
            # Initialize web search provider if configured
            web_search_provider = None
            if self.config.tavily_api_key:
                web_search_provider = WebSearchProvider(
                    api_key=self.config.tavily_api_key,
                    max_results=self.config.tavily_max_results,
                    max_retries=self.config.tavily_max_retries
                )
                logger.info("Web search provider initialized")
            else:
                logger.info("Tavily API key not configured, web search disabled")
            
            # Create modular search plugin
            self.search_plugin = ModularSearchPlugin(
                azure_search_provider=azure_search_provider,
                web_search_provider=web_search_provider,
                prefer_internal=True
            )
            
            logger.info("Search system initialized")
            
        except Exception as e:
            logger.error("Failed to initialize search system", error=str(e))
            raise
    
    async def _create_agents(self) -> None:
        """Create all research agents."""
        try:
            logger.info("Creating research agents")
            
            self.agents_dict = await create_agents_with_memory(
                memory_plugin=self.memory_plugin,
                search_plugin=self.search_plugin
            )
            
            logger.info(
                "Research agents created",
                agent_count=len(self.agents_dict),
                agents=list(self.agents_dict.keys())
            )
            
        except Exception as e:
            logger.error("Failed to create research agents", error=str(e))
            raise
    
    async def _setup_orchestration(self) -> None:
        """Setup the orchestration manager."""
        try:
            logger.info("Setting up orchestration manager")
            
            # Get manager model configuration
            manager_model_config = self.config.get_model_config("o3")
            
            # Create execution settings with high reasoning effort
            reasoning_settings = AzureChatPromptExecutionSettings(
                reasoning_effort="high"
            )
            
            # Store agents for coordination
            self.agents = self.agents_dict
            
            logger.info("Agent coordination configured")
            
        except Exception as e:
            logger.error("Failed to setup agent coordination", error=str(e))
            raise
    
    def _setup_runtime(self) -> None:
        """Setup the simple runtime."""
        try:
            # Simple runtime - no orchestration needed for now
            logger.info("Runtime initialized")
            
        except Exception as e:
            logger.error("Failed to setup runtime", error=str(e))
            raise
    
    def _debug_agent_response(self, agent_name: str, response: str) -> None:
        """Debug callback for agent responses."""
        logger.debug(
            "Agent response",
            agent=agent_name,
            response_length=len(response),
            response_preview=response[:100] + "..." if len(response) > 100 else response
        )
    
    async def _send_progress_update(self, update_data: Dict[str, Any]) -> None:
        """Send progress update through callback if available."""
        if self.progress_callback:
            try:
                # Get current session state
                session_data = self.session_manager.get_session(self.session_id)
                if session_data:
                    # Include session state in progress update
                    enhanced_update = {
                        **update_data,
                        "session_data": session_data
                    }
                    await self.progress_callback(self.session_id, enhanced_update)
                else:
                    await self.progress_callback(self.session_id, update_data)
            except Exception as e:
                logger.warning("Failed to send progress update", error=str(e))
    
    async def research(self, query: str) -> str:
        """
        Execute research task and return final report.
        
        Args:
            query: Research query/task
            
        Returns:
            Final research report
        """
        if not self.agents:
            raise RuntimeError("Agent system not initialized. Call initialize() first.")
        
        try:
            logger.info(
                "Starting research task",
                query=query[:100] + "..." if len(query) > 100 else query,
                session_id=self.session_id[:8]
            )
            
            # Send initial progress update
            await self._send_progress_update({
                "type": "research_started",
                "message": "Starting multi-agent research orchestration",
                "progress": 0
            })
            
            # Create session record
            self.session_manager.create_session(
                session_id=self.session_id,
                query=query,
                project_id=self.project_id
            )
            
            # Update session status
            self.session_manager.update_session_status(self.session_id, "in_progress")
            
            # Store initial research context (skip if embedding fails)
            try:
                if self.memory_manager:
                    await self.memory_manager.store_research_context(
                        context=f"Research Query: {query}",
                        metadata={
                            "type": "initial_query",
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    )
            except Exception as memory_error:
                logger.warning("Failed to store initial context in memory", error=str(memory_error))
                # Continue without memory storage
            
            # Simple multi-agent coordination (simplified for now)
            logger.info("Starting research with specialized agents")
            
            # Start with lead researcher
            lead_agent = self.agents.get("LeadResearcher")
            research_plan = ""
            if lead_agent:
                start_time = asyncio.get_event_loop().time()
                
                # Send progress update for lead researcher start
                await self._send_progress_update({
                    "type": "agent_started",
                    "agent_name": "LeadResearcher",
                    "message": "Creating research plan...",
                    "progress": 10
                })
                
                try:
                    research_plan = await lead_agent.invoke(
                        f"Create a research plan for: {query}"
                    )
                    execution_time = asyncio.get_event_loop().time() - start_time
                    
                    self.session_manager.add_agent_execution(
                        session_id=self.session_id,
                        agent_name="LeadResearcher",
                        input_data=f"Create a research plan for: {query}",
                        output_data=research_plan,
                        status="completed",
                        execution_time=execution_time,
                        metadata={"role": "planning", "agent_type": "lead_researcher"}
                    )
                    
                    # Send progress update for lead researcher completion
                    await self._send_progress_update({
                        "type": "agent_completed",
                        "agent_name": "LeadResearcher",
                        "message": "Research plan created",
                        "progress": 20,
                        "output_preview": research_plan[:200] + "..." if len(research_plan) > 200 else research_plan
                    })
                    
                    logger.info("Research plan created")
                except Exception as e:
                    execution_time = asyncio.get_event_loop().time() - start_time
                    error_msg = str(e)
                    
                    self.session_manager.add_agent_execution(
                        session_id=self.session_id,
                        agent_name="LeadResearcher",
                        input_data=f"Create a research plan for: {query}",
                        output_data=f"Error: {error_msg}",
                        status="failed",
                        execution_time=execution_time,
                        metadata={"role": "planning", "agent_type": "lead_researcher", "error": error_msg}
                    )
                    
                    logger.error("Lead researcher failed", error=error_msg)
            
            # Use multiple researchers for different aspects
            research_results = []
            researcher_names = ["Researcher1", "Researcher2", "Researcher3"]
            
            for i, agent_name in enumerate(researcher_names):
                agent = self.agents.get(agent_name)
                if agent:
                    start_time = asyncio.get_event_loop().time()
                    
                    # Calculate progress (20% + 40% for researchers = 60% total)
                    progress = 20 + ((i + 1) / len(researcher_names)) * 40
                    
                    # Send progress update for researcher start
                    await self._send_progress_update({
                        "type": "agent_started",
                        "agent_name": agent_name,
                        "message": f"Conducting research phase {i + 1}/3...",
                        "progress": progress - 10
                    })
                    
                    try:
                        result = await agent.invoke(
                            f"Research this topic: {query}"
                        )
                        execution_time = asyncio.get_event_loop().time() - start_time
                        
                        research_results.append(result)
                        
                        self.session_manager.add_agent_execution(
                            session_id=self.session_id,
                            agent_name=agent_name,
                            input_data=f"Research this topic: {query}",
                            output_data=result,
                            status="completed",
                            execution_time=execution_time,
                            metadata={"role": "research", "agent_type": "researcher"}
                        )
                        
                        # Send progress update for researcher completion
                        await self._send_progress_update({
                            "type": "agent_completed",
                            "agent_name": agent_name,
                            "message": f"Research phase {i + 1}/3 completed",
                            "progress": progress,
                            "output_preview": result[:200] + "..." if len(result) > 200 else result
                        })
                        
                        logger.info(f"{agent_name} completed research")
                    except Exception as e:
                        execution_time = asyncio.get_event_loop().time() - start_time
                        error_msg = str(e)
                        
                        self.session_manager.add_agent_execution(
                            session_id=self.session_id,
                            agent_name=agent_name,
                            input_data=f"Research this topic: {query}",
                            output_data=f"Error: {error_msg}",
                            status="failed",
                            execution_time=execution_time,
                            metadata={"role": "research", "agent_type": "researcher", "error": error_msg}
                        )
                        
                        logger.error(f"{agent_name} failed", error=error_msg)
            
            # Synthesize results with summarizer
            synthesis = "No research results to synthesize"
            summarizer = self.agents.get("Summarizer")
            if summarizer and research_results:
                start_time = asyncio.get_event_loop().time()
                try:
                    combined_results = "\n\n".join(research_results)
                    synthesis = await summarizer.invoke(
                        f"Synthesize these research findings: {combined_results}"
                    )
                    execution_time = asyncio.get_event_loop().time() - start_time
                    
                    self.session_manager.add_agent_execution(
                        session_id=self.session_id,
                        agent_name="Summarizer",
                        input_data=f"Synthesize these research findings: {combined_results[:500]}...",
                        output_data=synthesis,
                        status="completed",
                        execution_time=execution_time,
                        metadata={"role": "synthesis", "agent_type": "summarizer"}
                    )
                    
                    logger.info("Research synthesis completed")
                except Exception as e:
                    execution_time = asyncio.get_event_loop().time() - start_time
                    error_msg = str(e)
                    
                    combined_results = "\n\n".join(research_results) if research_results else "No results"
                    self.session_manager.add_agent_execution(
                        session_id=self.session_id,
                        agent_name="Summarizer",
                        input_data=f"Synthesize these research findings: {combined_results[:500]}...",
                        output_data=f"Error: {error_msg}",
                        status="failed",
                        execution_time=execution_time,
                        metadata={"role": "synthesis", "agent_type": "summarizer", "error": error_msg}
                    )
                    
                    logger.error("Summarizer failed", error=error_msg)
            
            # Generate final report
            final_report = synthesis
            report_writer = self.agents.get("ReportWriter")
            if report_writer:
                start_time = asyncio.get_event_loop().time()
                try:
                    final_report = await report_writer.invoke(
                        f"Write a comprehensive research report based on: {synthesis}"
                    )
                    execution_time = asyncio.get_event_loop().time() - start_time
                    
                    self.session_manager.add_agent_execution(
                        session_id=self.session_id,
                        agent_name="ReportWriter",
                        input_data=f"Write a comprehensive research report based on: {synthesis[:500]}...",
                        output_data=final_report,
                        status="completed",
                        execution_time=execution_time,
                        metadata={"role": "writing", "agent_type": "report_writer"}
                    )
                    
                    logger.info("Final report completed")
                except Exception as e:
                    execution_time = asyncio.get_event_loop().time() - start_time
                    error_msg = str(e)
                    
                    self.session_manager.add_agent_execution(
                        session_id=self.session_id,
                        agent_name="ReportWriter",
                        input_data=f"Write a comprehensive research report based on: {synthesis[:500]}...",
                        output_data=f"Error: {error_msg}",
                        status="failed",
                        execution_time=execution_time,
                        metadata={"role": "writing", "agent_type": "report_writer", "error": error_msg}
                    )
                    
                    logger.error("Report writer failed", error=error_msg)
            
            # Store final report in memory
            try:
                if self.memory_manager:
                    await self.memory_manager.store_research_context(
                        context=f"Final Report: {final_report}",
                        metadata={
                            "type": "final_report",
                            "timestamp": datetime.utcnow().isoformat(),
                            "query": query
                        }
                    )
            except Exception as memory_error:
                logger.warning("Failed to store final report in memory", error=str(memory_error))
            
            # Update session with final result
            self.session_manager.update_session_status(
                session_id=self.session_id,
                status="completed",
                final_result=final_report
            )
            
            logger.info(
                "Research task completed",
                session_id=self.session_id[:8],
                report_length=len(final_report)
            )
            
            return final_report
            
        except Exception as e:
            # Update session with error status
            self.session_manager.update_session_status(
                session_id=self.session_id,
                status="failed"
            )
            
            logger.error("Research task failed", error=str(e))
            raise
    
    async def get_session_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current research session.
        
        Returns:
            Session summary information
        """
        try:
            summary = {
                "session_id": self.session_id,
                "project_id": self.project_id,
                "status": "active" if self.agents else "not_initialized",
                "agents_count": len(self.agents_dict) if hasattr(self, 'agents_dict') else 0,
                "memory_summary": None
            }
            
            if self.memory_manager:
                summary["memory_summary"] = await self.memory_manager.get_session_summary()
            
            return summary
            
        except Exception as e:
            logger.error("Failed to get session summary", error=str(e))
            return {
                "session_id": self.session_id,
                "project_id": self.project_id,
                "status": "error",
                "error": str(e)
            }
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        try:
            logger.info("Cleaning up Deep Research Agent resources")
            
            # Memory cleanup (auto-persisted)
            if self.memory_manager:
                logger.info("Memory cleanup completed (auto-persist)")
            
            logger.info("Resource cleanup completed")
            
        except Exception as e:
            logger.warning("Error during cleanup", error=str(e))
