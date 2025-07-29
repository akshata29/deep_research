"""
Configuration management for Deep Research application.

This module handles all application settings including:
- Azure service configuration
- API settings
- Security settings
- Environment-specific configurations
"""

import os
from functools import lru_cache
from typing import List, Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings with Azure-specific configurations.
    
    Uses pydantic-settings for environment variable handling and validation.
    Follows Azure best practices for configuration management.
    """
    
    # Application settings
    ENVIRONMENT: str = Field(default="development", description="Environment name")
    DEBUG: bool = Field(default=False, description="Debug mode flag")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    
    # API settings
    API_V1_PREFIX: str = Field(default="/api/v1", description="API version prefix")
    ALLOWED_ORIGINS: str = Field(
        default="http://localhost:3000,https://localhost:3000",
        description="CORS allowed origins (comma-separated)"
    )
    ALLOWED_HOSTS: str = Field(
        default="localhost,127.0.0.1,*.azurecontainerapps.io",
        description="Trusted hosts (comma-separated)"
    )
    
    # Azure region and subscription
    AZURE_REGION: str = Field(default="eastus", description="Azure region")
    AZURE_SUBSCRIPTION_ID: Optional[str] = Field(default=None, description="Azure subscription ID")
    AZURE_TENANT_ID: Optional[str] = Field(default=None, description="Azure tenant ID")
    AZURE_RESOURCE_GROUP: Optional[str] = Field(default=None, description="Azure resource group")
    
    # Azure AI Foundry configuration
    AZURE_AI_PROJECT_NAME: Optional[str] = Field(default=None, description="Azure AI Foundry project name")
    AZURE_AI_HUB_NAME: Optional[str] = Field(default=None, description="Azure AI Foundry hub name")
    AZURE_AI_ENDPOINT: Optional[str] = Field(default=None, description="Azure AI Foundry endpoint")
    AZURE_AI_PROJECT_ENDPOINT: Optional[str] = Field(default=None, description="Azure AI Foundry project endpoint")
    
    # Azure OpenAI configuration (for direct API calls)
    AZURE_OPENAI_ENDPOINT: Optional[str] = Field(default=None, description="Azure OpenAI endpoint")
    AZURE_OPENAI_API_KEY: Optional[str] = Field(default=None, description="Azure OpenAI API key")
    AZURE_OPENAI_API_VERSION: str = Field(default="2024-12-01-preview", description="Azure OpenAI API version")
    
    # Model configuration
    DEFAULT_THINKING_MODEL: str = Field(
        default="gpt-4",
        description="Default model for thinking/reasoning tasks"
    )
    DEFAULT_TASK_MODEL: str = Field(
        default="gpt-35-turbo",
        description="Default model for specific tasks"
    )
    AVAILABLE_MODELS: str = Field(
        default="gpt-4,gpt-35-turbo,deepseek-v2,grok-beta,mistral-large",
        description="Available AI models (comma-separated)"
    )
    
    # Bing Search configuration
    BING_SEARCH_ENABLED: bool = Field(default=True, description="Enable Bing search grounding")
    BING_SEARCH_ENDPOINT: Optional[str] = Field(default=None, description="Bing Search API endpoint")
    BING_SEARCH_API_KEY: Optional[str] = Field(default=None, description="Bing Search API key")
    BING_CONNECTION_NAME: Optional[str] = Field(default=None, description="Bing connection name for Azure AI")
    BING_PROJECT_NAME: Optional[str] = Field(default=None, description="Bing ProjectName")

    # Azure Authentication
    AZURE_CLIENT_ID: Optional[str] = Field(default=None, description="Azure client ID")
    AZURE_CLIENT_SECRET: Optional[str] = Field(default=None, description="Azure client secret")
    
    # External API Keys
    TAVILY_API_KEY: Optional[str] = Field(default=None, description="Tavily API key")
    
    # Azure Cosmos DB configuration
    COSMOS_DB_ENDPOINT: Optional[str] = Field(default=None, description="Cosmos DB endpoint")
    COSMOS_DB_DATABASE_NAME: str = Field(default="deep_research", description="Cosmos DB database name")
    COSMOS_DB_CONTAINER_NAME: str = Field(default="sessions", description="Cosmos DB container name")
    
    # Azure Key Vault configuration
    KEY_VAULT_URL: Optional[str] = Field(default=None, description="Azure Key Vault URL")
    
    # Azure Storage configuration
    STORAGE_ACCOUNT_URL: Optional[str] = Field(default=None, description="Storage account URL")
    STORAGE_CONTAINER_NAME: str = Field(default="exports", description="Storage container for exports")
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=100, description="API rate limit per minute")
    
    # Export settings
    MAX_EXPORT_FILE_SIZE_MB: int = Field(default=50, description="Maximum export file size in MB")
    EXPORT_TIMEOUT_SECONDS: int = Field(default=300, description="Export operation timeout")
    
    # WebSocket settings
    WEBSOCKET_ENABLED: bool = Field(default=True, description="Enable WebSocket support")
    
    # Authentication settings (Azure AD B2C)
    AZURE_AD_B2C_TENANT_NAME: Optional[str] = Field(default=None, description="Azure AD B2C tenant name")
    AZURE_AD_B2C_CLIENT_ID: Optional[str] = Field(default=None, description="Azure AD B2C client ID")
    AZURE_AD_B2C_POLICY_NAME: Optional[str] = Field(default=None, description="Azure AD B2C policy name")
    AZURE_AD_B2C_SCOPE: str = Field(
        default="https://graph.microsoft.com/.default",
        description="Azure AD B2C scopes (comma-separated)"
    )

    TAVILY_API_KEY: str = Field(default="", description="Tavily API key")
    TAVILY_API_BASE_URL: str = Field(default="https://api.tavily.com", description="Tavily API URL")

    @validator("ALLOWED_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string."""
        if v is None:
            return "http://localhost:3000,https://localhost:3000"
        if isinstance(v, str):
            return v.strip() if v.strip() else "http://localhost:3000,https://localhost:3000"
        if isinstance(v, list):
            return ",".join(str(item).strip() for item in v if str(item).strip())
        return str(v).strip() if str(v).strip() else "http://localhost:3000"
    
    @validator("ALLOWED_HOSTS", pre=True)
    def parse_allowed_hosts(cls, v):
        """Parse allowed hosts from string."""
        if v is None:
            return "localhost,127.0.0.1,*.azurecontainerapps.io"
        if isinstance(v, str):
            return v.strip() if v.strip() else "localhost,127.0.0.1,*.azurecontainerapps.io"
        if isinstance(v, list):
            return ",".join(str(item).strip() for item in v if str(item).strip())
        return str(v).strip() if str(v).strip() else "localhost"
    
    @validator("AVAILABLE_MODELS", pre=True)
    def parse_available_models(cls, v):
        """Parse available models from string."""
        if v is None:
            return "gpt-4,gpt-35-turbo,deepseek-v2,grok-beta,mistral-large"
        if isinstance(v, str):
            # Return the string as-is, we'll parse it in a property
            return v.strip() if v.strip() else "gpt-4,gpt-35-turbo"
        if isinstance(v, list):
            # Convert list back to comma-separated string
            return ",".join(str(item).strip() for item in v if str(item).strip())
        # Handle other types by converting to string
        return str(v).strip() if str(v).strip() else "gpt-4,gpt-35-turbo"
    
    @property
    def available_models_list(self) -> List[str]:
        """Get available models as a list."""
        if not self.AVAILABLE_MODELS:
            return ["gpt-4", "gpt-35-turbo"]
        return [model.strip() for model in self.AVAILABLE_MODELS.split(",") if model.strip()]
    
    @validator("AZURE_AD_B2C_SCOPE", pre=True)
    def parse_b2c_scopes(cls, v):
        """Parse Azure AD B2C scopes from string."""
        if v is None:
            return "https://graph.microsoft.com/.default"
        if isinstance(v, str):
            return v.strip() if v.strip() else "https://graph.microsoft.com/.default"
        if isinstance(v, list):
            return ",".join(str(item).strip() for item in v if str(item).strip())
        return str(v).strip() if str(v).strip() else "https://graph.microsoft.com/.default"
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Get allowed origins as a list."""
        if not self.ALLOWED_ORIGINS:
            return ["http://localhost:3000", "https://localhost:3000"]
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]
    
    @property
    def allowed_hosts_list(self) -> List[str]:
        """Get allowed hosts as a list."""
        if not self.ALLOWED_HOSTS:
            return ["localhost", "127.0.0.1", "*.azurecontainerapps.io"]
        return [host.strip() for host in self.ALLOWED_HOSTS.split(",") if host.strip()]
    
    @property
    def azure_ad_b2c_scope_list(self) -> List[str]:
        """Get Azure AD B2C scopes as a list."""
        if not self.AZURE_AD_B2C_SCOPE:
            return ["https://graph.microsoft.com/.default"]
        return [scope.strip() for scope in self.AZURE_AD_B2C_SCOPE.split(",") if scope.strip()]
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        # Enable environment variable override
        env_prefix = ""


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings.
    
    Returns:
        Settings: Application configuration instance
        
    This function is cached to avoid re-reading environment variables
    multiple times during the application lifecycle.
    """
    return Settings()


# Development environment defaults
def get_development_settings() -> Settings:
    """Get settings optimized for development environment."""
    return Settings(
        ENVIRONMENT="development",
        DEBUG=True,
        LOG_LEVEL="DEBUG",
        ALLOWED_ORIGINS="http://localhost:3000,http://127.0.0.1:3000",
        ALLOWED_HOSTS="localhost,127.0.0.1"
    )


# Production environment validation
def validate_production_settings(settings: Settings) -> bool:
    """
    Validate that all required settings are present for production.
    
    Args:
        settings: Settings instance to validate
        
    Returns:
        bool: True if all required settings are present
        
    Raises:
        ValueError: If required production settings are missing
    """
    required_fields = [
        "AZURE_SUBSCRIPTION_ID",
        "AZURE_TENANT_ID",
        "AZURE_RESOURCE_GROUP",
        "AZURE_AI_PROJECT_NAME",
        "KEY_VAULT_URL",
        "COSMOS_DB_ENDPOINT",
        "STORAGE_ACCOUNT_URL"
    ]
    
    missing_fields = []
    for field in required_fields:
        if getattr(settings, field) is None:
            missing_fields.append(field)
    
    if missing_fields and settings.ENVIRONMENT == "production":
        raise ValueError(
            f"Missing required production settings: {', '.join(missing_fields)}"
        )
    
    return len(missing_fields) == 0
