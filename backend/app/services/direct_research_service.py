"""
Direct Research Service - For models not supported by Azure AI Agents.

This service provides direct OpenAI-compatible API calls for research tasks
when Azure AI Agents Service is not available or suitable.
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime

import structlog
from openai import AsyncAzureOpenAI
from azure.core.credentials import TokenCredential

from app.core.config import Settings
from app.models.schemas import ResearchProgress, ResearchSection, SearchResult


logger = structlog.get_logger(__name__)


class DirectResearchService:
    """
    Direct research execution service for models not supported by Azure AI Agents.
    
    Uses Azure OpenAI or compatible APIs directly instead of the Agents service.
    """
    
    def __init__(self, settings: Settings, azure_credential: TokenCredential):
        self.settings = settings
        self.azure_credential = azure_credential
        self.tasks: Dict[str, Dict] = {}
        
        # Initialize Azure OpenAI client
        if settings.AZURE_OPENAI_ENDPOINT and settings.AZURE_OPENAI_API_KEY:
            self.client = AsyncAzureOpenAI(
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                api_key=settings.AZURE_OPENAI_API_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION
            )
        elif settings.AZURE_AI_ENDPOINT:
            # Use Azure AI Services endpoint with managed identity
            self.client = AsyncAzureOpenAI(
                azure_endpoint=settings.AZURE_AI_ENDPOINT,
                azure_ad_token_provider=self._get_azure_token,
                api_version=settings.AZURE_OPENAI_API_VERSION
            )
        else:
            raise ValueError("No Azure OpenAI or Azure AI endpoint configured")
        
    def _get_azure_token(self) -> str:
        """Get Azure token for authentication."""
        try:
            token = self.azure_credential.get_token("https://cognitiveservices.azure.com/.default")
            return token.token
        except Exception as e:
            logger.error("Failed to get Azure token", error=str(e))
            raise
    
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
    
    async def generate_response(
        self,
        prompt: str,
        model: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        response_format: Optional[str] = None,
        system_message: Optional[str] = None
    ) -> str:
        """
        Generate a response using direct model API calls.
        
        Args:
            prompt: The user prompt/query
            model: Model name to use
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            response_format: Optional response format ("json" for JSON output)
            system_message: Optional system message
            
        Returns:
            Generated response text
        """
        try:
            # Prepare messages
            messages = []
            
            if system_message:
                messages.append({"role": "system", "content": system_message})
            elif response_format == "json":
                messages.append({
                    "role": "system", 
                    "content": "You are a helpful assistant that responds with valid JSON."
                })
            else:
                messages.append({
                    "role": "system", 
                    "content": "You are a helpful research assistant."
                })
            
            messages.append({"role": "user", "content": prompt})
            
            # Get the correct parameters for this model
            model_params = self._get_token_params_for_model(model, max_tokens, temperature)
            
            # Prepare request parameters
            request_params = {
                "model": model,
                "messages": messages,
                **model_params
            }
            
            # Add response format if specified
            if response_format == "json":
                request_params["response_format"] = {"type": "json_object"}
            
            # Make the API call
            logger.info(
                "Making direct API call",
                model=model,
                model_params=model_params,
                response_format=response_format
            )
            
            response = await self.client.chat.completions.create(**request_params)
            
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                
                logger.info(
                    "Direct API call successful",
                    model=model,
                    response_length=len(content) if content else 0
                )
                
                return content or ""
            else:
                logger.warning("No response choices returned", model=model)
                return ""
                
        except Exception as e:
            logger.error(
                "Direct API call failed",
                model=model,
                error=str(e),
                exc_info=True
            )
            raise
    
    async def _execute_research(
        self,
        task_id: str,
        prompt: str,
        thinking_model: str,
        task_model: str,
        enable_web_search: bool,
        research_depth: str
    ) -> None:
        """Execute the research task."""
        
        try:
            # Phase 1: Strategic thinking
            await self._update_progress(task_id, 15, "Analyzing research requirements")
            strategy = await self._generate_research_strategy(prompt, thinking_model)
            
            # Phase 2: Research planning
            await self._update_progress(task_id, 30, "Creating research plan")
            research_plan = await self._create_research_plan(strategy, thinking_model)
            
            # Phase 3: Information gathering
            await self._update_progress(task_id, 50, "Gathering information")
            gathered_info = await self._gather_information(research_plan, task_model, enable_web_search)
            
            # Phase 4: Analysis and synthesis
            await self._update_progress(task_id, 75, "Analyzing and synthesizing findings")
            analysis = await self._analyze_findings(gathered_info, thinking_model)
            
            # Phase 5: Final report generation
            await self._update_progress(task_id, 90, "Generating final report")
            final_result = await self._generate_final_report(analysis, task_model)
            
            # Mark as completed
            self.tasks[task_id]["status"] = "completed"
            self.tasks[task_id]["result"] = final_result
            await self._update_progress(task_id, 100, "Research completed")
            
            logger.info("Direct research execution completed", task_id=task_id)
            
        except Exception as e:
            logger.error("Direct research execution failed", task_id=task_id, error=str(e))
            self.tasks[task_id]["status"] = "failed"
            self.tasks[task_id]["error"] = str(e)
            await self._update_progress(task_id, 0, f"Research failed: {str(e)}")
    
    async def _generate_research_strategy(self, prompt: str, model: str) -> str:
        """Generate research strategy using thinking model."""
        
        strategy_prompt = f"""
        You are a research strategist. Analyze this research query and create a comprehensive strategy:
        
        Query: {prompt}
        
        Please provide:
        1. Key research questions to explore
        2. Different perspectives to consider
        3. Types of information needed
        4. Potential challenges and considerations
        5. Research methodology approach
        
        Focus on being thorough and systematic in your analysis.
        """
        
        try:
            # Get the correct parameters for this model
            model_params = self._get_token_params_for_model(model, 1500, 0.7)
            
            request_params = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are an expert research strategist."},
                    {"role": "user", "content": strategy_prompt}
                ],
                **model_params
            }
            
            response = await self.client.chat.completions.create(**request_params)
            
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error("Failed to generate research strategy", model=model, error=str(e))
            raise
    
    async def _create_research_plan(self, strategy: str, model: str) -> str:
        """Create detailed research plan based on strategy."""
        
        plan_prompt = f"""
        Based on this research strategy, create a detailed execution plan:
        
        Strategy: {strategy}
        
        Please provide:
        1. Specific search queries to execute
        2. Information sources to prioritize
        3. Key topics to investigate
        4. Analysis framework
        5. Structure for final report
        
        Make the plan actionable and specific.
        """
        
        try:
            # Get the correct parameters for this model
            model_params = self._get_token_params_for_model(model, 1200, 0.5)
            
            request_params = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are a research planning expert."},
                    {"role": "user", "content": plan_prompt}
                ],
                **model_params
            }
            
            response = await self.client.chat.completions.create(**request_params)
            
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error("Failed to create research plan", model=model, error=str(e))
            raise
    
    async def _gather_information(self, plan: str, model: str, enable_web_search: bool) -> str:
        """Gather information based on research plan."""
        
        gather_prompt = f"""
        Execute this research plan and provide comprehensive information:
        
        Plan: {plan}
        
        {"Note: Use your knowledge to provide current, relevant information. Include specific examples, data points, and evidence where possible." if not enable_web_search else "Note: Web search would be integrated here. For now, provide comprehensive information based on your training data."}
        
        Provide detailed findings for each aspect of the research plan.
        Focus on factual information and credible sources.
        """
        
        try:
            # Get the correct parameters for this model
            model_params = self._get_token_params_for_model(model, 2000, 0.6)
            
            request_params = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are a research analyst gathering comprehensive information."},
                    {"role": "user", "content": gather_prompt}
                ],
                **model_params
            }
            
            response = await self.client.chat.completions.create(**request_params)
            
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error("Failed to gather information", model=model, error=str(e))
            raise
    
    async def _analyze_findings(self, findings: str, model: str) -> str:
        """Analyze gathered information using thinking model."""
        
        analysis_prompt = f"""
        Analyze these research findings and provide deep insights:
        
        Findings: {findings}
        
        Please provide:
        1. Key insights and patterns
        2. Connections between different pieces of information
        3. Implications and significance
        4. Areas of uncertainty or conflicting information
        5. Conclusions and recommendations
        
        Focus on critical thinking and synthesis.
        """
        
        try:
            # Get the correct parameters for this model
            model_params = self._get_token_params_for_model(model, 1800, 0.7)
            
            request_params = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are an expert analyst providing deep insights and critical thinking."},
                    {"role": "user", "content": analysis_prompt}
                ],
                **model_params
            }
            
            response = await self.client.chat.completions.create(**request_params)
            
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error("Failed to analyze findings", model=model, error=str(e))
            raise
    
    async def _generate_final_report(self, analysis: str, model: str) -> Dict[str, Any]:
        """Generate final research report."""
        
        report_prompt = f"""
        Create a comprehensive research report based on this analysis:
        
        Analysis: {analysis}
        
        Format the response as a JSON object with this structure:
        {{
            "title": "Research Report Title",
            "executive_summary": "Brief overview of key findings",
            "sections": [
                {{
                    "title": "Section Title",
                    "content": "Section content",
                    "sources": ["Source 1", "Source 2"]
                }}
            ],
            "conclusions": "Main conclusions and recommendations",
            "methodology": "Research methodology used"
        }}
        
        Ensure the report is well-structured, comprehensive, and actionable.
        """
        
        try:
            # Get the correct parameters for this model
            model_params = self._get_token_params_for_model(model, 2500, 0.5)
            
            request_params = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are a research report writer. Respond with valid JSON only."},
                    {"role": "user", "content": report_prompt}
                ],
                **model_params,
                "response_format": {"type": "json_object"}
            }
            
            response = await self.client.chat.completions.create(**request_params)
            
            content = response.choices[0].message.content or "{}"
            return json.loads(content)
            
        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON response", error=str(e))
            # Fallback to structured text response
            return {
                "title": "Research Report",
                "executive_summary": "Research completed successfully",
                "sections": [{
                    "title": "Findings",
                    "content": response.choices[0].message.content or "No content generated",
                    "sources": []
                }],
                "conclusions": "See findings section for detailed information",
                "methodology": "Direct model execution"
            }
        except Exception as e:
            logger.error("Failed to generate final report", model=model, error=str(e))
            raise
    
    async def _update_progress(self, task_id: str, progress: int, step: str) -> None:
        """Update task progress."""
        if task_id in self.tasks:
            self.tasks[task_id]["progress"] = progress
            self.tasks[task_id]["current_step"] = step
            
            logger.debug("Progress updated", task_id=task_id, progress=progress, step=step)
    
    async def get_task_status(self, task_id: str) -> Optional[ResearchProgress]:
        """Get current status of a research task."""
        
        if task_id not in self.tasks:
            return None
        
        task = self.tasks[task_id]
        
        return ResearchProgress(
            task_id=task_id,
            status=task["status"],
            progress_percentage=task["progress"],
            current_step=task["current_step"],
            tokens_used=task["tokens_used"],
            cost_estimate=0.0,  # Calculate based on token usage
            search_queries_made=0,  # Track in implementation
            sources_found=0  # Track in implementation
        )
    
    async def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get result of completed research task."""
        
        if task_id not in self.tasks:
            return None
        
        task = self.tasks[task_id]
        
        if task["status"] != "completed":
            return None
        
        return task.get("result")
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running research task."""
        
        if task_id not in self.tasks:
            return False
        
        self.tasks[task_id]["status"] = "cancelled"
        
        logger.info("Task cancelled", task_id=task_id)
        return True
