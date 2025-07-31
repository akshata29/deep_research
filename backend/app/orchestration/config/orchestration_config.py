"""
Configuration management for the orchestration system.
"""

import os
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import yaml
import structlog

logger = structlog.get_logger(__name__)


class ModelConfig(BaseModel):
    """Configuration for AI model settings."""
    deployment_name: str
    max_tokens: int = 4000
    temperature: float = 0.7
    top_p: float = 0.9


class AgentConfig(BaseModel):
    """Configuration for individual agents."""
    name: str
    role: str
    model_name: str
    max_iterations: int = 3
    confidence_threshold: float = 0.8


class OrchestrationConfig(BaseSettings):
    """Main configuration for the orchestration system."""
    
    # Azure AI Configuration (matching .env field names)
    azure_ai_endpoint: str = Field(..., description="Azure AI endpoint")
    azure_openai_api_version: str = Field(default="2024-12-01-preview", description="Azure OpenAI API version")
    
    # Azure Authentication (matching .env field names)
    azure_client_id: str = Field(..., description="Azure Client ID")
    azure_client_secret: str = Field(..., description="Azure Client Secret")
    azure_tenant_id: str = Field(..., description="Azure Tenant ID")
    
    # Model Configuration (matching .env field names)
    default_thinking_model: str = Field(default="chat4omini", description="Default thinking model")
    default_task_model: str = Field(default="chat4", description="Default task model")
    available_models: str = Field(default="chat4,chat4omini,chatds,chato1,chato1mini", description="Available models")
    
    # Azure Search Configuration
    azure_search_endpoint: Optional[str] = Field(default=None, description="Azure Search endpoint")
    azure_search_api_key: Optional[str] = Field(default=None, description="Azure Search API key")
    azure_search_index_name: Optional[str] = Field(default=None, description="Azure Search index name")
    
    # Tavily API Configuration
    tavily_api_key: Optional[str] = Field(default=None, description="Tavily API key for web search")
    tavily_max_results: int = Field(default=10, description="Maximum Tavily search results")
    tavily_max_retries: int = Field(default=3, description="Maximum Tavily API retries")
    
    # System Configuration
    company: str = Field(default="Your Company", description="Company name for context")
    debug_mode: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"

    def get_model_config(self, model_name: str) -> ModelConfig:
        """Get model configuration by name."""
        # Map orchestration model names to available models from .env
        model_mapping = {
            "gpt-4": "chat4",
            "gpt-4-mini": "chat4omini", 
            "o3": "chato1",
            "embedding": "embedding"  # Will need to add embedding model to .env
        }
        
        deployment_name = model_mapping.get(model_name, "chat4")
        
        model_configs = {
            "gpt-4": ModelConfig(
                deployment_name=deployment_name,
                max_tokens=4000,
                temperature=0.7
            ),
            "gpt-4-mini": ModelConfig(
                deployment_name=deployment_name,
                max_tokens=2000,
                temperature=0.6
            ),
            "o3": ModelConfig(
                deployment_name=deployment_name,
                max_tokens=8000,
                temperature=0.8
            )
        }
        return model_configs.get(model_name, model_configs["gpt-4"])


class ProjectConfig(BaseModel):
    """Project-specific configuration loaded from YAML."""
    
    system: Dict[str, Any] = Field(default_factory=dict)
    data_sources: Dict[str, Any] = Field(default_factory=dict)
    agents: Dict[str, Any] = Field(default_factory=dict)
    
    @classmethod
    def load_from_file(cls, file_path: str) -> "ProjectConfig":
        """Load project configuration from YAML file."""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f) or {}
                logger.info("Loaded project configuration", file=file_path)
                return cls(**data)
            else:
                logger.warning("Project config file not found, using defaults", file=file_path)
                return cls()
        except Exception as e:
            logger.error("Failed to load project configuration", error=str(e), file=file_path)
            return cls()


# Global configuration instances
_orchestration_config: Optional[OrchestrationConfig] = None
_project_config: Optional[ProjectConfig] = None


def get_orchestration_config() -> OrchestrationConfig:
    """Get the global orchestration configuration instance."""
    global _orchestration_config
    if _orchestration_config is None:
        _orchestration_config = OrchestrationConfig()
    return _orchestration_config


def get_project_config() -> ProjectConfig:
    """Get the global project configuration instance."""
    global _project_config
    if _project_config is None:
        config_path = os.path.join(
            os.path.dirname(__file__), 
            "project_config.yaml"
        )
        _project_config = ProjectConfig.load_from_file(config_path)
    return _project_config
