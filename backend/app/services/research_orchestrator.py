"""
Research Orchestrator for Deep Research application.

This service orchestrates the entire research process by coordinating:
- Multiple AI models for different tasks (thinking, task-specific)
- Web search integration for real-time information
- Report generation and structured output
- Progress tracking and status updates
- Dual execution modes: Azure AI Agents or Direct model execution
"""

import asyncio
import json
import uuid
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

import structlog
from azure.identity import DefaultAzureCredential

from app.core.azure_config import AzureServiceManager
from app.models.schemas import (
    ResearchRequest, ResearchStatus, ResearchProgress, ResearchReport,
    ResearchSection, SearchResult
)
from app.services.direct_research_service import DirectResearchService
from app.services.ai_agent_service import AIAgentService


logger = structlog.get_logger(__name__)


class ResearchOrchestrator:
    """
    Orchestrates the research process using Azure AI Foundry Agent Service.
    
    This class manages the complete research workflow:
    1. Planning and task decomposition
    2. Web search and information gathering
    3. Analysis and synthesis
    4. Report generation and formatting
    """
    
    def __init__(
        self,
        azure_manager: AzureServiceManager,
        task_id: str,
        config: ResearchRequest
    ):
        """
        Initialize the research orchestrator.
        
        Args:
            azure_manager: Azure service manager for AI services
            task_id: Unique identifier for this research task
            config: Research configuration and parameters
        """
        self.azure_manager = azure_manager
        self.task_id = task_id
        self.config = config
        
        # Initialize services
        self.direct_service = DirectResearchService(azure_manager.settings, azure_manager.credential)
        self.ai_agent_service = AIAgentService(azure_manager)
        
        # Determine execution mode
        self.execution_mode = self._determine_execution_mode()
        
        # Status tracking
        self.status = ResearchStatus.PENDING
        self.progress = 0.0
        self.current_step = "Initializing"
        self.start_time = datetime.utcnow()
        self.estimated_completion: Optional[datetime] = None
        
        # Research state
        self.research_plan: str = ""
        self.analysis_result: str = ""
        self.tokens_used = 0
        self.cost_estimate = 0.0
        self.search_queries_made = 0
        self.sources_found = 0
        self.research_sections: List[ResearchSection] = []
        self.all_sources: List[SearchResult] = []
        
        # Azure AI agents
        self.thinking_agent: Optional[Any] = None
        self.task_agent: Optional[Any] = None
        self.thread: Optional[Any] = None
        
        # Cancellation flag
        self._cancelled = False
    
    async def execute_research(self) -> None:
        """
        Execute the complete research process.
        
        This method orchestrates the entire research workflow from start to finish.
        """
        try:
            logger.info(
                "Starting research execution", 
                task_id=self.task_id,
                execution_mode=self.execution_mode
            )
            
            if self.execution_mode == "agents":
                await self._execute_with_agents()
            else:
                await self._execute_direct()
                
        except Exception as e:
            logger.error("Research execution failed", task_id=self.task_id, error=str(e))
            self.status = ResearchStatus.FAILED
            self.current_step = f"Error: {str(e)}"
            raise
    
    async def _execute_with_agents(self) -> None:
        """Execute research using Azure AI Agents."""
        try:
            # Initialize agents
            self._update_progress(5, "Initializing Azure AI Agents...")
            await asyncio.sleep(2)  # Allow frontend to see this step
            await self._initialize_agents()
            
            # Step 1: Planning (10%)
            self._update_progress(8, "Starting research planning phase...")
            await asyncio.sleep(1)  # Allow frontend to see this step
            await self._planning_phase()
            self._update_progress(15, "Research planning completed")
            await asyncio.sleep(1)  # Allow frontend to see this step
            
            # Step 2: Analysis with web grounding (70%)
            if not self._cancelled:
                self._update_progress(20, "Beginning deep analysis with AI agents...")
                await asyncio.sleep(1)  # Allow frontend to see this step
                await self._deep_analysis()
                self._update_progress(75, "Deep analysis completed")
                await asyncio.sleep(1)  # Allow frontend to see this step
            
            # Step 3: Report generation (100%)
            if not self._cancelled:
                self._update_progress(80, "Generating final research report...")
                await asyncio.sleep(1)  # Allow frontend to see this step
                await self._generate_sections()
                self._update_progress(100, "Research completed successfully")
                self.status = ResearchStatus.COMPLETED
                
                logger.info(
                    "Research completed successfully with agents",
                    task_id=self.task_id,
                    tokens_used=self.tokens_used,
                    sources_found=self.sources_found
                )
                
        except Exception as e:
            logger.error("Agents execution failed", task_id=self.task_id, error=str(e))
            raise
    
    async def _execute_direct(self) -> None:
        """Execute research using direct model calls."""
        try:
            # Step 1: Planning (10%)
            await self._direct_planning_phase()
            self._update_progress(10, "Planning completed")
            
            # Step 2: Information gathering (40%)
            if self.config.enable_web_search and not self._cancelled:
                await self._information_gathering()
                self._update_progress(50, "Information gathering completed")
            
            # Step 3: Analysis (70%)
            if not self._cancelled:
                await self._direct_analysis()
                self._update_progress(70, "Analysis completed")
            
            # Step 4: Report generation (100%)
            if not self._cancelled:
                await self._direct_generate_sections()
                self._update_progress(100, "Research completed")
                self.status = ResearchStatus.COMPLETED
                
                logger.info(
                    "Research completed successfully with direct execution",
                    task_id=self.task_id,
                    tokens_used=self.tokens_used,
                    sources_found=self.sources_found
                )
                
        except Exception as e:
            logger.error("Direct execution failed", task_id=self.task_id, error=str(e))
            raise
    
    async def _direct_planning_phase(self) -> None:
        """Plan the research approach using direct model calls."""
        self.current_step = "Planning research approach (direct)"
        
        try:
            planning_prompt = f"""
            You are a research planning expert. Analyze this research query and create a comprehensive research plan:
            
            QUERY: {self.config.prompt}
            
            Consider:
            - Research depth: {self.config.research_depth}
            - Language: {self.config.language}
            - Web search available: {self.config.enable_web_search}
            
            Provide a structured research plan including:
            1. Key research questions to explore
            2. Information sources to prioritize
            3. Search strategies (if web search enabled)
            4. Expected insights and outcomes
            5. Potential challenges and limitations
            
            Format your response as a clear, actionable research plan.
            """
            
            # Get thinking model
            thinking_model = self.config.models_config.get("thinking", "gpt-4")
            
            # Make direct API call
            response = await self.direct_service.generate_response(
                prompt=planning_prompt,
                model=thinking_model,
                max_tokens=2000
            )
            
            self.research_plan = response
            self.tokens_used += 1500  # Estimate token usage
            
            logger.info("Direct research planning completed", task_id=self.task_id)
            
        except Exception as e:
            logger.error("Direct planning phase failed", task_id=self.task_id, error=str(e))
            raise
    
    async def _direct_analysis(self) -> None:
        """Perform deep analysis using thinking agent with Bing grounding if enabled."""
        self.status = ResearchStatus.GENERATING
        
        try:
            # Initialize agents if not already done
            if not self.thinking_agent:
                await self._initialize_agents()
            
            analysis_prompt = f"""
            You are a senior research analyst. Conduct a comprehensive analysis of the following research query:
            
            QUERY: {self.config.prompt}
            
            Research Requirements:
            - Research depth: {self.config.research_depth}
            - Language: {self.config.language}
            - Web search {"enabled" if self.config.enable_web_search else "disabled"}
            
            Please provide:
            1. Key insights and findings
            2. Multiple perspectives on the topic
            3. Data-driven analysis where possible (use web search if available)
            4. Current trends and developments (search for recent information)
            5. Potential implications and conclusions
            6. Areas requiring further investigation
            
            Be analytical, objective, and thorough. If web search is available, use it to find current information and cite sources.
            Output should be structured and well-organized.
            """
            
            # Send analysis request to thinking agent (with Bing grounding if enabled)
            await self.ai_agent_service.add_message(
                thread=self.thread,
                content=analysis_prompt,
                role="user"
            )
            
            run = await self.ai_agent_service.run_agent(
                thread=self.thread,
                agent=self.thinking_agent
            )
            
            analysis_result = await self.ai_agent_service.get_run_result(run)
            
            # Update token usage
            self.tokens_used += getattr(run, 'usage', {}).get('total_tokens', 0)
            
            # Store analysis for section generation
            self.analysis_result = analysis_result
            
            logger.info("Direct analysis completed", task_id=self.task_id, web_search_enabled=self.config.enable_web_search)
            
        except Exception as e:
            logger.error("Direct analysis failed", task_id=self.task_id, error=str(e))
            raise
    
    async def _direct_generate_sections(self) -> None:
        """Generate structured report sections using task agent."""
        self.current_step = "Generating report (direct)"
        
        try:
            # Initialize agents if not already done
            if not self.task_agent:
                await self._initialize_agents()
            
            section_prompt = f"""
            Based on the research analysis, generate a comprehensive report with structured sections.
            
            ORIGINAL QUERY: {self.config.prompt}
            
            ANALYSIS RESULTS:
            {self.analysis_result}
            
            Generate a JSON response with the following structure:
            {{
                "sections": [
                    {{
                        "title": "Section Title",
                        "content": "Detailed section content",
                        "confidence_score": 0.8,
                        "word_count": 250
                    }}
                ]
            }}
            
            Requirements:
            - Create 3-5 comprehensive sections
            - Each section should be 200-500 words
            - Include executive summary, main findings, implications
            - Maintain high confidence scores (0.7+)
            - Be factual and well-structured
            """
            
            # Send section generation request to task agent
            await self.ai_agent_service.add_message(
                thread=self.thread,
                content=section_prompt,
                role="user"
            )
            
            run = await self.ai_agent_service.run_agent(
                thread=self.thread,
                agent=self.task_agent
            )
            
            sections_result = await self.ai_agent_service.get_run_result(run)
            
            # Update token usage
            self.tokens_used += getattr(run, 'usage', {}).get('total_tokens', 0)
            
            # Parse and structure sections
            try:
                sections_data = json.loads(sections_result)
                for section_data in sections_data.get("sections", []):
                    section = ResearchSection(
                        title=section_data.get("title", "Untitled Section"),
                        content=section_data.get("content", ""),
                        sources=[],  # Sources handled by Bing grounding within agents
                        confidence_score=section_data.get("confidence_score", 0.8),
                        word_count=section_data.get("word_count", len(section_data.get("content", "").split()))
                    )
                    self.research_sections.append(section)
                    
            except json.JSONDecodeError:
                # Fallback: create a single section from the raw response
                section = ResearchSection(
                    title="Research Analysis",
                    content=sections_result,
                    sources=[],  # Sources handled by Bing grounding within agents
                    confidence_score=0.8,
                    word_count=len(sections_result.split())
                )
                self.research_sections.append(section)
            
            logger.info("Direct report sections generated", task_id=self.task_id, sections=len(self.research_sections))
            
        except Exception as e:
            logger.error("Failed to generate sections directly", task_id=self.task_id, error=str(e))
            raise
    
    async def _initialize_agents(self) -> None:
        """Initialize Azure AI Foundry agents for different tasks."""
        self.status = ResearchStatus.THINKING
        
        try:
            # Get deployed models dynamically
            deployed_models = await self.azure_manager.get_deployed_models()
            
            # Initialize thinking agent (for reasoning and analysis)
            thinking_model_list = deployed_models.get("thinking", [])
            # Use user's specified thinking model or fall back to first available
            requested_thinking_model = self.config.models_config.get("thinking", "")
            thinking_model_info = None
            
            # Try to find the user's requested model first
            if requested_thinking_model:
                thinking_model_info = next(
                    (model for model in thinking_model_list if model.get("name") == requested_thinking_model),
                    None
                )
            
            # Fall back to first available model if user's choice not found
            if not thinking_model_info:
                thinking_model_info = thinking_model_list[0] if thinking_model_list else {"name": "gpt-4"}
            
            thinking_model = thinking_model_info.get("name", "gpt-4")
            thinking_model_name = f"thinking-agent-{thinking_model}"

            # Use Bing grounding tools if web search is enabled
            tools = [{"type": "bing_grounding"}] if self.config.enable_web_search else []
            self.thinking_agent = await self.ai_agent_service.create_agent(
                model=thinking_model,
                name=thinking_model_name,
                instructions=self._get_thinking_instructions(),
                tools=tools
            )
            
            # Initialize task agent (for structured output)
            task_model_list = deployed_models.get("task", [])
            # Use user's specified task model or fall back to first available
            requested_task_model = self.config.models_config.get("task", "")
            task_model_info = None
            
            # Try to find the user's requested model first
            if requested_task_model:
                task_model_info = next(
                    (model for model in task_model_list if model.get("name") == requested_task_model),
                    None
                )
            
            # Fall back to first available model if user's choice not found
            if not task_model_info:
                task_model_info = task_model_list[0] if task_model_list else {"name": "gpt-35-turbo"}
            task_model = task_model_info.get("name", "gpt-35-turbo")
            task_model_name = f"task-agent-{task_model}"
            
            self.task_agent = await self.ai_agent_service.create_agent(
                model=task_model,
                name=task_model_name,
                instructions=self._get_task_instructions(),
                tools=[]  # No tools for now, just use the model's capabilities
            )
            
            # Create conversation thread
            self.thread = await self.ai_agent_service.create_thread()
            
            logger.info(
                "AI agents initialized successfully", 
                task_id=self.task_id,
                thinking_model=thinking_model,
                task_model=task_model,
                available_models=list(deployed_models.keys())
            )
            
        except Exception as e:
            logger.error("Failed to initialize agents", task_id=self.task_id, error=str(e))
            raise
    
    async def _planning_phase(self) -> None:
        """Plan the research approach using the thinking agent."""
        self._update_progress(10, "Creating research thread...")
        await asyncio.sleep(1)  # Allow frontend to see this step
        
        try:
            planning_prompt = f"""
            You are a research planning expert. Analyze this research query and create a comprehensive research plan:
            
            QUERY: {self.config.prompt}
            
            Consider:
            - Research depth: {self.config.research_depth}
            - Language: {self.config.language}
            - Web search available: {self.config.enable_web_search}
            
            Provide a structured research plan including:
            1. Key research questions to explore
            2. Information sources to prioritize
            3. Search strategies (if web search enabled)
            4. Expected insights and outcomes
            5. Potential challenges and limitations
            
            Format your response as a clear, actionable research plan.
            """
            
            # Create message in thread and run agent
            self._update_progress(12, "Adding research query to thread...")
            await asyncio.sleep(0.5)  # Allow frontend to see this step
            await self.ai_agent_service.add_message(
                thread=self.thread,
                content=planning_prompt,
                role="user"
            )
            
            # Run the agent
            self._update_progress(13, "Running thinking agent for research planning...")
            await asyncio.sleep(0.5)  # Allow frontend to see this step
            run = await self.ai_agent_service.run_agent(
                thread=self.thread,
                agent=self.thinking_agent
            )
            
            # Get response
            self._update_progress(14, "Processing planning results...")
            await asyncio.sleep(0.5)  # Allow frontend to see this step
            plan_response = await self.ai_agent_service.get_run_result(run)
            
            # Update token usage (if available in run)
            self.tokens_used += getattr(run, 'usage', {}).get('total_tokens', 0)
            
            # Store the research plan
            self.research_plan = plan_response
            
            logger.info("Research planning completed", task_id=self.task_id)
            
        except Exception as e:
            logger.error("Planning phase failed", task_id=self.task_id, error=str(e))
            raise
    
    async def _information_gathering(self) -> None:
        """Information gathering is now handled by Bing grounding tools within agents."""
        # Information gathering is now integrated into agent interactions via Bing grounding tools
        # No separate web search API calls needed - agents will use Bing grounding internally
        self._update_progress(20, "Preparing information gathering...")
        await asyncio.sleep(1)  # Allow frontend to see this step
        
        self.current_step = "Information gathering via agent tools"
        
        self._update_progress(25, "Activating agent Bing grounding tools...")
        await asyncio.sleep(1)  # Allow frontend to see this step
        
        logger.info(
            "Information gathering delegated to agent Bing grounding tools",
            task_id=self.task_id,
            web_search_enabled=self.config.enable_web_search
        )
    
    async def _deep_analysis(self) -> None:
        """Perform deep analysis using the thinking agent with Bing grounding if enabled."""
        self.status = ResearchStatus.GENERATING
        
        try:
            self._update_progress(30, "Preparing detailed analysis prompt...")
            await asyncio.sleep(1)  # Allow frontend to see this step
            analysis_prompt = f"""
            You are a senior research analyst. Conduct a comprehensive analysis of the following research query:
            
            QUERY: {self.config.prompt}
            
            Research Requirements:
            - Research depth: {self.config.research_depth}
            - Language: {self.config.language}
            - Web search {"enabled" if self.config.enable_web_search else "disabled"}
            
            Please provide:
            1. Key insights and findings
            2. Multiple perspectives on the topic
            3. Data-driven analysis where possible (use web search if available)
            4. Current trends and developments (search for recent information)
            5. Potential implications and conclusions
            6. Areas requiring further investigation
            
            Be analytical, objective, and thorough. If web search is available, use it to find current information and cite sources.
            Output should be structured and well-organized.
            """
            
            # Send analysis request to thinking agent (with Bing grounding if enabled)
            self._update_progress(35, "Adding analysis request to thread...")
            await asyncio.sleep(0.5)  # Allow frontend to see this step
            await self.ai_agent_service.add_message(
                thread=self.thread,
                content=analysis_prompt,
                role="user"
            )
            
            self._update_progress(40, "Running thinking agent for deep analysis...")
            await asyncio.sleep(0.5)  # Allow frontend to see this step
            run = await self.ai_agent_service.run_agent(
                thread=self.thread,
                agent=self.thinking_agent
            )
            
            self._update_progress(60, "Processing analysis results...")
            await asyncio.sleep(0.5)  # Allow frontend to see this step
            analysis_result = await self.ai_agent_service.get_run_result(run)
            
            # Update token usage
            self.tokens_used += getattr(run, 'usage', {}).get('total_tokens', 0)
            
            # Store analysis for section generation
            self.analysis_result = analysis_result
            
            logger.info("Deep analysis completed", task_id=self.task_id, web_search_enabled=self.config.enable_web_search)
            
        except Exception as e:
            logger.error("Deep analysis failed", task_id=self.task_id, error=str(e))
            raise
    
    async def _generate_sections(self) -> None:
        """Generate structured report sections using the task agent."""
        self.current_step = "Generating report"
        self._update_progress(65, "Preparing report generation...")
        await asyncio.sleep(1)  # Allow frontend to see this step
        
        try:
            section_prompt = f"""
            Based on the research analysis, generate a comprehensive report with structured sections.
            
            ORIGINAL QUERY: {self.config.prompt}
            
            ANALYSIS RESULTS:
            {self.analysis_result}
            
            Generate a JSON response with the following structure:
            {{
                "sections": [
                    {{
                        "title": "Section Title",
                        "content": "Detailed section content",
                        "confidence_score": 0.8,
                        "word_count": 250
                    }}
                ]
            }}
            
            Requirements:
            - Create 3-5 comprehensive sections
            - Each section should be 200-500 words
            - Include executive summary, main findings, implications
            - Maintain high confidence scores (0.7+)
            - Be factual and well-structured
            """
            
            # Send to task agent for structured output
            self._update_progress(70, "Adding report generation request to thread...")
            await asyncio.sleep(0.5)  # Allow frontend to see this step
            await self.ai_agent_service.add_message(
                thread=self.thread,
                content=section_prompt,
                role="user"
            )
            
            self._update_progress(75, "Running task agent for report generation...")
            await asyncio.sleep(0.5)  # Allow frontend to see this step
            run = await self.ai_agent_service.run_agent(
                thread=self.thread,
                agent=self.task_agent
            )
            
            self._update_progress(85, "Processing structured report sections...")
            await asyncio.sleep(0.5)  # Allow frontend to see this step
            sections_result = await self.ai_agent_service.get_run_result(run)
            
            # Parse and structure sections
            self._update_progress(90, "Parsing JSON response into sections...")
            await asyncio.sleep(0.5)  # Allow frontend to see this step
            try:
                # Try to parse the JSON response from the agent
                if sections_result.strip().startswith('{'):
                    sections_data = json.loads(sections_result)
                else:
                    # If it's not JSON, try to extract JSON from the response
                    import re
                    json_match = re.search(r'\{.*\}', sections_result, re.DOTALL)
                    if json_match:
                        sections_data = json.loads(json_match.group())
                    else:
                        raise json.JSONDecodeError("No JSON found", "", 0)
                
                # Process each section from the parsed JSON
                for section_data in sections_data.get("sections", []):
                    section = ResearchSection(
                        title=section_data.get("title", "Untitled Section"),
                        content=section_data.get("content", ""),
                        sources=[],  # Sources handled by Bing grounding within agents
                        confidence_score=section_data.get("confidence_score", 0.8),
                        word_count=section_data.get("word_count", len(section_data.get("content", "").split()))
                    )
                    self.research_sections.append(section)
                    
                logger.info(f"Successfully parsed {len(self.research_sections)} sections from JSON response")
                    
            except (json.JSONDecodeError, AttributeError, KeyError) as e:
                logger.warning(f"Failed to parse JSON response, creating single section: {str(e)}")
                logger.debug(f"Raw response that failed to parse: {sections_result[:500]}...")
                
                # Fallback: create a single section from the raw response
                section = ResearchSection(
                    title="Research Analysis",
                    content=sections_result,
                    sources=[],  # Sources handled by Bing grounding within agents
                    confidence_score=0.8,
                    word_count=len(sections_result.split())
                )
                self.research_sections.append(section)
            
            logger.info("Report sections generated", task_id=self.task_id, sections=len(self.research_sections))
            
        except Exception as e:
            logger.error("Failed to generate sections", task_id=self.task_id, error=str(e))
            raise
    
    async def _generate_search_queries(self) -> List[str]:
        """Generate search queries based on the research plan."""
        # Simple query generation based on the prompt
        # In a more sophisticated version, this could use the thinking agent
        base_query = self.config.prompt
        
        queries = [
            base_query,
            f"{base_query} latest trends",
            f"{base_query} research 2024",
            f"{base_query} analysis",
            f"{base_query} statistics data"
        ]
        
        return queries[:3]  # Return top 3 queries
    
    def _get_thinking_instructions(self) -> str:
        """Get instructions for the thinking agent."""
        return """
        You are a senior research analyst with expertise in comprehensive research and analysis.
        Your role is to:
        1. Plan research approaches systematically
        2. Analyze information from multiple perspectives
        3. Identify key insights and patterns
        4. Provide objective, evidence-based conclusions
        5. Consider potential biases and limitations
        
        Always be thorough, analytical, and evidence-based in your responses.
        """
    
    def _get_task_instructions(self) -> str:
        """Get instructions for the task agent."""
        return """
        You are a report generation specialist focused on creating structured, professional research reports.
        Your role is to:
        1. Transform analysis into well-structured sections
        2. Generate JSON-formatted responses when requested
        3. Ensure consistent formatting and organization
        4. Maintain professional tone and clarity
        5. Include appropriate metadata and confidence scores
        
        Always follow the specified output format exactly and provide high-quality, structured content.
        """
    
    def _update_progress(self, percentage: float, step: str) -> None:
        """Update progress tracking."""
        self.progress = percentage
        self.current_step = step
        
        # Estimate completion time
        if percentage > 0:
            elapsed = (datetime.utcnow() - self.start_time).total_seconds()
            total_estimated = elapsed * (100 / percentage)
            remaining = total_estimated - elapsed
            self.estimated_completion = datetime.utcnow() + timedelta(seconds=remaining)
    
    def cancel(self) -> None:
        """Cancel the research process."""
        self._cancelled = True
        self.status = ResearchStatus.CANCELLED
        self.current_step = "Cancelled by user"
        logger.info("Research task cancelled", task_id=self.task_id)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current research status."""
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "progress": self.progress,
            "current_step": self.current_step,
            "start_time": self.start_time.isoformat(),
            "estimated_completion": self.estimated_completion.isoformat() if self.estimated_completion else None,
            "tokens_used": self.tokens_used,
            "sources_found": self.sources_found,
            "search_queries_made": self.search_queries_made
        }
    
    async def get_progress(self) -> ResearchProgress:
        """Get current research progress."""
        return ResearchProgress(
            task_id=self.task_id,
            status=self.status,
            progress_percentage=self.progress,
            current_step=self.current_step,
            estimated_completion=self.estimated_completion,
            tokens_used=self.tokens_used,
            sources_found=self.sources_found,
            search_queries_made=self.search_queries_made
        )
    
    def get_report(self) -> ResearchReport:
        """Generate the final research report."""
        if self.status != ResearchStatus.COMPLETED:
            raise ValueError("Research is not yet completed")
        
        total_word_count = sum(section.word_count for section in self.research_sections)
        reading_time = max(1, total_word_count // 200)  # Approximate reading time
        
        return ResearchReport(
            task_id=self.task_id,
            title=f"Research Report: {self.config.prompt[:100]}{'...' if len(self.config.prompt) > 100 else ''}",
            executive_summary=self.research_sections[0].content if self.research_sections else "No summary available",
            sections=self.research_sections,
            conclusions=self.research_sections[-1].content if self.research_sections else "No conclusions available",
            sources=[],  # Sources handled by Bing grounding within agents
            word_count=total_word_count,
            reading_time_minutes=reading_time,
            metadata={
                "models_used": self.config.models_config,
                "search_enabled": self.config.enable_web_search,
                "depth": self.config.research_depth,
                "language": self.config.language,
                "tokens_used": self.tokens_used,
                "cost_estimate": self.cost_estimate
            }
        )
    
    def _get_thinking_instructions(self) -> str:
        """
        Get instructions for the thinking agent responsible for research planning, 
        analysis, and strategic reasoning.
        
        Returns:
            str: Detailed instructions for the thinking agent
        """
        return f"""
You are a senior research analyst and strategic thinker specializing in comprehensive research and analysis. Your role is to:

**PRIMARY RESPONSIBILITIES:**
1. Research Planning & Strategy
   - Analyze research queries and develop comprehensive research plans
   - Identify key research questions and angles to explore
   - Plan information gathering strategies and source prioritization
   - Anticipate potential challenges and knowledge gaps

2. Deep Analysis & Synthesis
   - Conduct thorough analysis of information and data
   - Synthesize insights from multiple sources and perspectives
   - Identify patterns, trends, and underlying themes
   - Provide balanced, objective, and nuanced analysis

3. Critical Thinking & Evaluation
   - Evaluate source credibility and information quality
   - Consider multiple perspectives and potential biases
   - Assess the strength of evidence and arguments
   - Identify areas requiring further investigation

**RESEARCH CONTEXT:**
- Research Query: {self.config.prompt}
- Research Depth: {self.config.research_depth}
- Language: {self.config.language}
- Web Search Available: {'Yes' if self.config.enable_web_search else 'No'}

**GUIDELINES:**
- Be thorough, analytical, and objective in your approach
- Use web search capabilities when available to find current, relevant information
- Cite sources when referencing specific information or data
- Consider multiple perspectives and avoid single-source bias
- Structure your responses clearly and logically
- Be honest about uncertainties and limitations in available information
- Focus on providing actionable insights and well-reasoned conclusions

**OUTPUT EXPECTATIONS:**
- Provide comprehensive, well-structured analysis
- Include relevant context and background information
- Highlight key insights and their implications
- Suggest areas for further investigation when appropriate
- Maintain professional, analytical tone throughout
"""
    
    def _get_task_instructions(self) -> str:
        """
        Get instructions for the task agent responsible for structured data processing,
        report generation, and specific task execution.
        
        Returns:
            str: Detailed instructions for the task agent
        """
        return f"""
You are a specialized task execution agent focused on structured data processing and report generation. Your role is to:

**PRIMARY RESPONSIBILITIES:**
1. Structured Data Processing
   - Convert analysis into structured, well-formatted reports
   - Organize information into logical sections and hierarchies
   - Ensure consistent formatting and presentation standards
   - Generate accurate metadata and document properties

2. Report Generation & Formatting
   - Create comprehensive, well-structured research reports
   - Generate executive summaries and key findings sections
   - Organize content into logical sections with clear headings
   - Ensure proper citation and source attribution

3. JSON Output & Data Structuring
   - Generate valid JSON responses when requested
   - Structure data according to specified schemas
   - Maintain data integrity and format consistency
   - Include relevant metadata and confidence scores

**CURRENT TASK CONTEXT:**
- Research Topic: {self.config.prompt}
- Target Language: {self.config.language}
- Expected Depth: {self.config.research_depth}

**OUTPUT REQUIREMENTS:**
- Follow specified JSON schemas exactly when generating structured output
- Ensure all required fields are included with appropriate values
- Maintain high content quality and accuracy standards
- Generate confidence scores based on source quality and information certainty
- Structure content for optimal readability and usefulness

**FORMATTING STANDARDS:**
- Use clear, professional language appropriate for business/academic contexts
- Maintain consistent section structure and hierarchy
- Include proper headings, subheadings, and bullet points where appropriate
- Ensure content is well-organized and flows logically
- Generate accurate word counts and reading time estimates

**QUALITY ASSURANCE:**
- Verify all generated JSON is valid and complete
- Ensure content accuracy and factual correctness
- Maintain objectivity and avoid speculation without evidence
- Include appropriate disclaimers for uncertain information
- Double-check all numerical data and statistics
"""

    def _determine_execution_mode(self) -> str:
        """
        Determine whether to use Azure AI Agents or direct execution.
        
        Returns:
            str: "agents" or "direct"
        """
        # Check user preference first
        if hasattr(self.config, 'execution_mode'):
            if self.config.execution_mode == "direct":
                logger.info("Direct execution mode requested by user", task_id=self.task_id)
                return "direct"
            
            if self.config.execution_mode == "agents":
                logger.info("Agents execution mode requested by user", task_id=self.task_id)
                return "agents"
        
        # Auto mode: check if models support agents
        try:
            thinking_model = self.config.models_config.get("thinking", "gpt-4")
            task_model = self.config.models_config.get("task", "gpt-35-turbo")
            
            # Azure AI Agents supported models (based on Microsoft docs)
            agent_supported_models = {
                "gpt-4o", "gpt-4o-mini", "gpt-4", "gpt-4-32k", 
                "gpt-35-turbo", "gpt-35-turbo-16k"
            }
            
            thinking_supported = thinking_model in agent_supported_models
            task_supported = task_model in agent_supported_models
            
            if thinking_supported and task_supported:
                logger.info(
                    "Using agents execution mode - models support agents",
                    task_id=self.task_id,
                    thinking_model=thinking_model,
                    task_model=task_model
                )
                return "agents"
            else:
                logger.info(
                    "Using direct execution mode - models don't support agents",
                    task_id=self.task_id,
                    thinking_model=thinking_model,
                    task_model=task_model,
                    thinking_supported=thinking_supported,
                    task_supported=task_supported
                )
                return "direct"
                
        except Exception as e:
            logger.warning("Failed to determine model support, defaulting to direct mode", error=str(e))
            return "direct"
