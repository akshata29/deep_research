"""
Simple Research Orchestrator using direct OpenAI-style API calls.

This is a fallback implementation that doesn't use Azure AI Foundry Agents,
but instead makes direct calls to the deployed models.
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

import structlog
from openai import AzureOpenAI

from app.models.schemas import (
    ResearchRequest, ResearchStatus, ResearchProgress, ResearchReport,
    ResearchSection, SearchResult
)
from app.core.azure_config import AzureServiceManager
from app.services.web_search_service import WebSearchService


logger = structlog.get_logger(__name__)


class SimpleResearchOrchestrator:
    """
    Simple research orchestrator using direct OpenAI API calls.
    
    This implementation bypasses Azure AI Foundry Agents and uses direct
    calls to deployed models through OpenAI-compatible endpoints.
    """
    
    def __init__(
        self,
        azure_manager: AzureServiceManager,
        task_id: str,
        config: ResearchRequest
    ):
        """Initialize the research orchestrator."""
        self.azure_manager = azure_manager
        self.task_id = task_id
        self.config = config
        
        # Initialize services
        self.search_service = WebSearchService(azure_manager) if config.enable_web_search else None
        
        # Status tracking
        self.status = ResearchStatus.PENDING
        self.progress = 0
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
        
        # OpenAI clients for different models
        self.thinking_client: Optional[AzureOpenAI] = None
        self.task_client: Optional[AzureOpenAI] = None
        self.thinking_model: str = ""
        self.task_model: str = ""
        
        # Cancellation flag
        self._cancelled = False
    
    async def execute_research(self) -> None:
        """Execute the complete research process."""
        try:
            logger.info("Starting simple research execution", task_id=self.task_id)
            
            # Initialize OpenAI clients
            await self._initialize_clients()
            
            # Step 1: Planning (20%)
            await self._planning_phase()
            self._update_progress(20, "Planning completed")
            
            # Step 2: Information gathering (50%)
            if self.config.enable_web_search and not self._cancelled:
                await self._information_gathering()
                self._update_progress(50, "Information gathering completed")
            
            # Step 3: Analysis (80%)
            if not self._cancelled:
                await self._analysis_phase()
                self._update_progress(80, "Analysis completed")
            
            # Step 4: Report generation (100%)
            if not self._cancelled:
                await self._generate_sections()
                self._update_progress(100, "Research completed")
                self.status = ResearchStatus.COMPLETED
                
                logger.info(
                    "Simple research completed successfully",
                    task_id=self.task_id,
                    tokens_used=self.tokens_used,
                    sources_found=self.sources_found
                )
            
        except Exception as e:
            logger.error("Simple research execution failed", task_id=self.task_id, error=str(e))
            self.status = ResearchStatus.FAILED
            self.current_step = f"Error: {str(e)}"
            raise
    
    async def _initialize_clients(self) -> None:
        """Initialize OpenAI clients for deployed models."""
        self.status = ResearchStatus.THINKING
        self.current_step = "Initializing AI models"
        
        try:
            # Get deployed models
            deployed_models = await self.azure_manager.get_deployed_models()
            
            # Get thinking model
            thinking_model_list = deployed_models.get("thinking", [])
            requested_thinking_model = self.config.models_config.get("thinking", "")
            thinking_model_info = None
            
            if requested_thinking_model:
                thinking_model_info = next(
                    (model for model in thinking_model_list if model.get("name") == requested_thinking_model),
                    None
                )
            
            if not thinking_model_info:
                thinking_model_info = thinking_model_list[0] if thinking_model_list else {"name": "gpt-4"}
            
            self.thinking_model = thinking_model_info.get("name", "gpt-4")
            
            # Get task model
            task_model_list = deployed_models.get("task", [])
            requested_task_model = self.config.models_config.get("task", "")
            task_model_info = None
            
            if requested_task_model:
                task_model_info = next(
                    (model for model in task_model_list if model.get("name") == requested_task_model),
                    None
                )
            
            if not task_model_info:
                task_model_info = task_model_list[0] if task_model_list else {"name": "gpt-35-turbo"}
            
            self.task_model = task_model_info.get("name", "gpt-35-turbo")
            
            # Create OpenAI clients using Azure endpoint
            ai_endpoint = self.azure_manager.settings.AZURE_AI_ENDPOINT
            
            if ai_endpoint:
                # Use Azure OpenAI client
                self.thinking_client = AzureOpenAI(
                    azure_endpoint=ai_endpoint,
                    azure_ad_token_provider=self._get_azure_token,
                    api_version="2024-06-01"
                )
                
                self.task_client = self.thinking_client  # Use same client for both
            else:
                raise RuntimeError("Azure AI endpoint not configured")
            
            logger.info(
                "OpenAI clients initialized",
                task_id=self.task_id,
                thinking_model=self.thinking_model,
                task_model=self.task_model,
                endpoint=ai_endpoint
            )
            
        except Exception as e:
            logger.error("Failed to initialize OpenAI clients", task_id=self.task_id, error=str(e))
            raise
    
    def _get_azure_token(self) -> str:
        """Get Azure AD token for authentication."""
        token = self.azure_manager.credential.get_token("https://cognitiveservices.azure.com/.default")
        return token.token
    
    async def _planning_phase(self) -> None:
        """Plan the research approach."""
        self.current_step = "Planning research approach"
        
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
            
            # Get the correct parameters for this model
            model_params = self._get_token_params_for_model(self.thinking_model, 1000, 0.7)
            
            request_params = {
                "model": self.thinking_model,
                "messages": [
                    {"role": "system", "content": "You are a senior research analyst with expertise in comprehensive research planning."},
                    {"role": "user", "content": planning_prompt}
                ],
                **model_params
            }
            
            response = self.thinking_client.chat.completions.create(**request_params)
            
            self.research_plan = response.choices[0].message.content
            self.tokens_used += response.usage.total_tokens
            
            logger.info("Research planning completed", task_id=self.task_id)
            
        except Exception as e:
            logger.error("Planning phase failed", task_id=self.task_id, error=str(e))
            # Don't raise, continue with basic plan
            self.research_plan = f"Basic research plan for: {self.config.prompt}"
    
    async def _information_gathering(self) -> None:
        """Conduct web searches and gather information."""
        if not self.search_service:
            return
        
        self.current_step = "Gathering information"
        
        try:
            # Generate search queries
            search_queries = [
                self.config.prompt,
                f"{self.config.prompt} latest trends 2024",
                f"{self.config.prompt} analysis research",
                f"{self.config.prompt} statistics data",
                f"{self.config.prompt} insights"
            ]
            
            # Conduct searches
            for query in search_queries[:3]:  # Limit to 3 queries for quick test
                if self._cancelled:
                    break
                
                try:
                    results = await self.search_service.search(
                        query=query,
                        limit=5
                    )
                    
                    self.all_sources.extend(results)
                    self.search_queries_made += 1
                    self.sources_found += len(results)
                    
                    # Small delay between searches
                    await asyncio.sleep(0.5)
                    
                except Exception as search_error:
                    logger.warning("Search failed", query=query, error=str(search_error))
                    continue
            
            logger.info(
                "Information gathering completed",
                task_id=self.task_id,
                queries_made=self.search_queries_made,
                sources_found=self.sources_found
            )
            
        except Exception as e:
            logger.error("Failed to conduct searches", task_id=self.task_id, error=str(e))
            # Don't raise, continue without web search results
    
    async def _analysis_phase(self) -> None:
        """Perform analysis using the thinking model."""
        self.status = ResearchStatus.GENERATING
        self.current_step = "Analyzing information"
        
        try:
            # Prepare context with search results
            search_context = ""
            if self.all_sources:
                search_context = "\n\nWEB SEARCH RESULTS:\n"
                for i, source in enumerate(self.all_sources[:5], 1):
                    search_context += f"{i}. {source.title}\n   {source.snippet}\n   Source: {source.url}\n\n"
            
            analysis_prompt = f"""
            Conduct a comprehensive analysis of the following research query:
            
            QUERY: {self.config.prompt}
            
            RESEARCH PLAN:
            {self.research_plan}
            
            {search_context}
            
            Please provide:
            1. Key insights and findings
            2. Multiple perspectives on the topic
            3. Data-driven analysis where possible
            4. Potential implications and conclusions
            5. Areas requiring further investigation
            
            Be analytical, objective, and thorough. Cite sources when relevant.
            Output should be structured and well-organized.
            """
            
            # Build request parameters with proper token parameter for model type
            # Get the correct parameters for this model
            model_params = self._get_token_params_for_model(self.thinking_model, 2000, 0.6)
            
            request_params = {
                "model": self.thinking_model,
                "messages": [
                    {"role": "system", "content": "You are a senior research analyst with expertise in comprehensive analysis."},
                    {"role": "user", "content": analysis_prompt}
                ],
                **model_params
            }
            
            response = self.thinking_client.chat.completions.create(**request_params)
            
            self.analysis_result = response.choices[0].message.content
            self.tokens_used += response.usage.total_tokens
            
            logger.info("Analysis completed", task_id=self.task_id)
            
        except Exception as e:
            logger.error("Analysis phase failed", task_id=self.task_id, error=str(e))
            # Fallback analysis
            self.analysis_result = f"Analysis of: {self.config.prompt}\n\nBased on the research query, this topic requires comprehensive analysis across multiple dimensions."
    
    async def _generate_sections(self) -> None:
        """Generate structured report sections."""
        self.current_step = "Generating report"
        
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
            - Create 3-4 comprehensive sections
            - Each section should be 200-400 words
            - Include executive summary, main findings, implications
            - Maintain high confidence scores (0.7+)
            - Be factual and well-structured
            - Return valid JSON only
            """
            
            # Get the correct parameters for this model
            model_params = self._get_token_params_for_model(self.task_model, 1500, 0.5)
            
            # Build request parameters with proper token parameter for model type
            request_params = {
                "model": self.task_model,
                "messages": [
                    {"role": "system", "content": "You are a report generation specialist. Always respond with valid JSON."},
                    {"role": "user", "content": section_prompt}
                ],
                **model_params
            }
            
            response = self.task_client.chat.completions.create(**request_params)
            
            sections_result = response.choices[0].message.content
            self.tokens_used += response.usage.total_tokens
            
            # Parse and structure sections
            try:
                sections_data = json.loads(sections_result)
                for section_data in sections_data.get("sections", []):
                    section = ResearchSection(
                        title=section_data.get("title", "Untitled Section"),
                        content=section_data.get("content", ""),
                        sources=self.all_sources[:3],  # Limit sources per section
                        confidence_score=section_data.get("confidence_score", 0.8),
                        word_count=section_data.get("word_count", len(section_data.get("content", "").split()))
                    )
                    self.research_sections.append(section)
                    
            except json.JSONDecodeError:
                # Fallback: create sections from the raw response
                content_parts = sections_result.split('\n\n')
                for i, part in enumerate(content_parts[:3]):
                    if part.strip():
                        section = ResearchSection(
                            title=f"Research Finding {i+1}",
                            content=part.strip(),
                            sources=self.all_sources[:2],
                            confidence_score=0.8,
                            word_count=len(part.split())
                        )
                        self.research_sections.append(section)
            
            # Ensure we have at least one section
            if not self.research_sections:
                section = ResearchSection(
                    title="Research Analysis",
                    content=self.analysis_result or f"Analysis of: {self.config.prompt}",
                    sources=self.all_sources[:3],
                    confidence_score=0.7,
                    word_count=len((self.analysis_result or "").split())
                )
                self.research_sections.append(section)
            
            logger.info("Report sections generated", task_id=self.task_id, sections=len(self.research_sections))
            
        except Exception as e:
            logger.error("Failed to generate sections", task_id=self.task_id, error=str(e))
            # Create fallback section
            section = ResearchSection(
                title="Research Summary",
                content=f"Research analysis for: {self.config.prompt}\n\n{self.analysis_result or 'Analysis completed successfully.'}",
                sources=self.all_sources[:3],
                confidence_score=0.7,
                word_count=100
            )
            self.research_sections.append(section)
    
    def _update_progress(self, percentage: int, step: str) -> None:
        """Update progress tracking."""
        self.progress = percentage
        self.current_step = step
        
        # Estimate completion time
        if percentage > 0:
            elapsed = (datetime.utcnow() - self.start_time).total_seconds()
            total_estimated = elapsed * (100 / percentage)
            remaining = total_estimated - elapsed
            self.estimated_completion = datetime.utcnow() + timedelta(seconds=remaining)
    
    async def cancel(self) -> None:
        """Cancel the research process."""
        self._cancelled = True
        self.status = ResearchStatus.CANCELLED
        self.current_step = "Cancelled by user"
        logger.info("Simple research task cancelled", task_id=self.task_id)
    
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
        reading_time = max(1, total_word_count // 200)
        
        return ResearchReport(
            task_id=self.task_id,
            title=f"Research Report: {self.config.prompt[:100]}{'...' if len(self.config.prompt) > 100 else ''}",
            executive_summary=self.research_sections[0].content if self.research_sections else "No summary available",
            sections=self.research_sections,
            conclusions=self.research_sections[-1].content if self.research_sections else "No conclusions available",
            sources=self.all_sources,
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
    
    def _get_token_params_for_model(self, model: str, max_tokens: int, temperature: float) -> Dict[str, Any]:
        """
        Get the correct parameters based on the model.
        
        O1 models:
        - Use 'max_completion_tokens' instead of 'max_tokens'
        - Don't support 'temperature' parameter
        
        Args:
            model: Model name
            max_tokens: Token limit value
            temperature: Temperature value
            
        Returns:
            Dictionary of parameters suitable for the model
        """
        params = {}
        
        # Check if this is an O1 model
        is_o1_model = any(o1_keyword in model.lower() for o1_keyword in ['o1', 'chato1'])
        
        if is_o1_model:
            # O1 models use max_completion_tokens and don't support temperature
            params['max_completion_tokens'] = max_tokens
            # Don't add temperature for O1 models
        else:
            # Regular models use max_tokens and support temperature
            params['max_tokens'] = max_tokens
            params['temperature'] = temperature
            
        return params
