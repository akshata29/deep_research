"""
Pydantic models for Deep Research application.

This module defines all request/response models and data structures
used throughout the application with proper validation and documentation.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator


class ResearchStatus(str, Enum):
    """Research task status enumeration."""
    PENDING = "pending"
    THINKING = "thinking"
    SEARCHING = "searching"
    GENERATING = "generating"
    FORMATTING = "formatting"
    COMPLETED = "completed"
    FAILED = "failed"


class ExportFormat(str, Enum):
    """Supported export formats."""
    MARKDOWN = "markdown"
    PDF = "pdf"
    DOCX = "docx"
    PPTX = "pptx"
    HTML = "html"
    JSON = "json"


class ModelType(str, Enum):
    """AI model types for different tasks."""
    THINKING = "thinking"
    TASK = "task"
    SPECIALIST = "specialist"
    EMBEDDING = "embedding"


class AvailableModel(BaseModel):
    """Available AI model configuration."""
    name: str = Field(..., description="Model name")
    display_name: str = Field(..., description="Human-readable model name")
    type: ModelType = Field(..., description="Model type")
    max_tokens: int = Field(..., description="Maximum token limit")
    supports_tools: bool = Field(default=True, description="Whether model supports function calling")
    supports_agents: bool = Field(default=False, description="Whether model supports Azure AI Agents Service")
    cost_per_1k_tokens: float = Field(..., description="Cost per 1000 tokens")
    description: str = Field(..., description="Model description and capabilities")


class ResearchRequest(BaseModel):
    """Research request from frontend."""
    prompt: str = Field(..., min_length=10, max_length=20000, description="Research query or topic")
    models_config: Dict[str, str] = Field(
        default_factory=lambda: {"thinking": "gpt-4", "task": "gpt-35-turbo"},
        description="Model configuration for different tasks"
    )
    enable_web_search: bool = Field(default=True, description="Enable web search grounding")
    max_search_results: int = Field(default=10, ge=1, le=20, description="Maximum web search results")
    research_depth: str = Field(default="standard", description="Research depth: quick, standard, deep")
    output_format: str = Field(default="structured", description="Output format preference")
    language: str = Field(default="en", description="Output language")
    session_id: Optional[str] = Field(default=None, description="Optional session identifier")
    execution_mode: str = Field(default="auto", description="Execution mode: auto, agents, direct")
    
    @validator("research_depth")
    def validate_research_depth(cls, v):
        """Validate research depth parameter."""
        allowed_depths = ["quick", "standard", "deep"]
        if v not in allowed_depths:
            raise ValueError(f"research_depth must be one of: {allowed_depths}")
        return v
    
    @validator("language")
    def validate_language(cls, v):
        """Validate language code."""
        # ISO 639-1 language codes
        allowed_languages = ["en", "es", "fr", "de", "it", "pt", "ru", "zh", "ja", "ko"]
        if v not in allowed_languages:
            raise ValueError(f"language must be one of: {allowed_languages}")
        return v
    
    @validator("execution_mode")
    def validate_execution_mode(cls, v):
        """Validate execution mode parameter."""
        allowed_modes = ["auto", "agents", "direct"]
        if v not in allowed_modes:
            raise ValueError(f"execution_mode must be one of: {allowed_modes}")
        return v


class ResearchProgress(BaseModel):
    """Research progress update."""
    task_id: str = Field(..., description="Unique task identifier")
    status: ResearchStatus = Field(..., description="Current task status")
    progress_percentage: int = Field(ge=0, le=100, description="Progress percentage")
    current_step: str = Field(..., description="Current processing step")
    estimated_completion: Optional[datetime] = Field(default=None, description="Estimated completion time")
    tokens_used: int = Field(default=0, description="Total tokens consumed")
    cost_estimate: float = Field(default=0.0, description="Estimated cost in USD")
    search_queries_made: int = Field(default=0, description="Number of web searches performed")
    sources_found: int = Field(default=0, description="Number of sources discovered")


class SearchResult(BaseModel):
    """Web search result from Bing API."""
    title: str = Field(..., description="Search result title")
    url: str = Field(..., description="Source URL")
    snippet: str = Field(..., description="Content snippet")
    relevance_score: float = Field(ge=0, le=1, description="Relevance score")
    published_date: Optional[datetime] = Field(default=None, description="Publication date")
    domain: str = Field(..., description="Source domain")


class ResearchSection(BaseModel):
    """Individual section of research report."""
    title: str = Field(..., description="Section title")
    content: str = Field(..., description="Section content in Markdown")
    sources: List[SearchResult] = Field(default_factory=list, description="Supporting sources")
    confidence_score: float = Field(ge=0, le=1, description="Confidence in information accuracy")
    word_count: int = Field(ge=0, description="Section word count")


class ResearchReport(BaseModel):
    """Complete research report."""
    task_id: str = Field(..., description="Unique task identifier")
    title: str = Field(..., description="Report title")
    executive_summary: str = Field(..., description="Executive summary")
    sections: List[ResearchSection] = Field(..., description="Report sections")
    conclusions: str = Field(..., description="Key conclusions and insights")
    sources: List[SearchResult] = Field(default_factory=list, description="All sources used")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    word_count: int = Field(ge=0, description="Total word count")
    reading_time_minutes: int = Field(ge=0, description="Estimated reading time")


class ResearchResponse(BaseModel):
    """Research API response."""
    task_id: str = Field(..., description="Unique task identifier")
    status: ResearchStatus = Field(..., description="Current status")
    message: str = Field(..., description="Status message")
    report: Optional[ResearchReport] = Field(default=None, description="Complete report (if finished)")
    progress: Optional[ResearchProgress] = Field(default=None, description="Progress information")
    websocket_url: Optional[str] = Field(default=None, description="WebSocket URL for real-time updates")


class ExportRequest(BaseModel):
    """Export request for research reports."""
    task_id: str = Field(..., description="Research task identifier")
    format: ExportFormat = Field(..., description="Export format")
    template_name: Optional[str] = Field(default=None, description="Template name for PPTX exports")
    include_sources: bool = Field(default=True, description="Include source citations")
    include_metadata: bool = Field(default=True, description="Include report metadata")
    custom_branding: Optional[Dict[str, str]] = Field(default=None, description="Custom branding options")


class ExportResponse(BaseModel):
    """Export API response."""
    export_id: str = Field(default_factory=lambda: str(uuid4()), description="Export identifier")
    status: str = Field(default="processing", description="Export status")
    download_url: Optional[str] = Field(default=None, description="Download URL (when ready)")
    file_size_bytes: Optional[int] = Field(default=None, description="File size in bytes")
    expires_at: Optional[datetime] = Field(default=None, description="Download link expiration")
    format: ExportFormat = Field(..., description="Export format")


class HealthStatus(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Overall health status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Environment name")
    azure_services: Dict[str, bool] = Field(default_factory=dict, description="Azure service health")
    performance_metrics: Dict[str, float] = Field(default_factory=dict, description="Performance metrics")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(default=None, description="Error code")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")
    correlation_id: Optional[str] = Field(default=None, description="Request correlation ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")


class SessionInfo(BaseModel):
    """User session information."""
    session_id: str = Field(..., description="Session identifier")
    user_id: Optional[str] = Field(default=None, description="User identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Session creation time")
    last_activity: datetime = Field(default_factory=datetime.utcnow, description="Last activity timestamp")
    research_count: int = Field(default=0, description="Number of research tasks in session")
    total_tokens_used: int = Field(default=0, description="Total tokens used in session")
    total_cost: float = Field(default=0.0, description="Total cost in session")


class WebSocketMessage(BaseModel):
    """WebSocket message format."""
    type: str = Field(..., description="Message type")
    task_id: Optional[str] = Field(default=None, description="Related task ID")
    data: Dict[str, Any] = Field(default_factory=dict, description="Message data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")


class ModelUsageStats(BaseModel):
    """Model usage statistics."""
    model_name: str = Field(..., description="Model name")
    total_requests: int = Field(default=0, description="Total requests made")
    total_tokens: int = Field(default=0, description="Total tokens processed")
    total_cost: float = Field(default=0.0, description="Total cost")
    average_response_time: float = Field(default=0.0, description="Average response time in seconds")
    error_rate: float = Field(default=0.0, description="Error rate percentage")


# Response models for API documentation
class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool = Field(default=True, description="Operation success status")
    message: str = Field(..., description="Success message")
    data: Optional[Any] = Field(default=None, description="Response data")


# Phase-specific request models
class ResearchPlanRequest(BaseModel):
    """Request for creating research plan."""
    topic: str = Field(..., description="Research topic")
    questions: List[str] = Field(..., description="List of follow-up questions")
    feedback: str = Field(..., description="User feedback on questions")
    request: ResearchRequest = Field(..., description="Base research request configuration")


class ExecuteResearchRequest(BaseModel):
    """Request for executing research."""
    topic: str = Field(..., description="Research topic")
    plan: str = Field(..., description="Research plan to execute")
    request: ResearchRequest = Field(..., description="Base research request configuration")


class FinalReportRequest(BaseModel):
    """Request for generating final report."""
    topic: str = Field(..., description="Research topic")
    plan: str = Field(..., description="Research plan")
    findings: str = Field(..., description="Research findings")
    requirement: str = Field(default="", description="Additional requirements for the report")
    request: Optional[ResearchRequest] = Field(default=None, description="Base research request configuration")
