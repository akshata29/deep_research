"""
Utility functions for memory ma        return AzureTextEmbedding(
            service_id=service_id,
            endpoint=endpoint,
            api_version=api_version,
            deployment_name=deployment_name,
            ad_token_provider=lambda: credential.get_token("https://cognitiveservices.azure.com/.default").token
        )t and embedding generation.
"""

from typing import Optional
import structlog
from semantic_kernel.connectors.ai.open_ai import AzureTextEmbedding
from azure.identity import DefaultAzureCredential
from app.core.azure_config import AzureServiceManager

logger = structlog.get_logger(__name__)


async def create_azure_openai_text_embedding(
    endpoint: str,
    api_version: str,
    deployment_name: str,
    service_id: str = "azure_embedding"
) -> AzureTextEmbedding:
    """
    Create Azure OpenAI text embedding service using existing Azure infrastructure.
    
    Args:
        endpoint: Azure AI endpoint
        api_version: API version
        deployment_name: Embedding model deployment name
        service_id: Service identifier
        
    Returns:
        AzureTextEmbedding instance
    """
    try:
        # Try to use the shared Azure Service Manager first
        from ..agent_factory import get_azure_service_manager
        azure_service_manager = await get_azure_service_manager()
        
        return AzureTextEmbedding(
            service_id=service_id,
            endpoint=endpoint,
            api_version=api_version,
            deployment_name=deployment_name,
            ad_token_provider=azure_service_manager.credential.get_token
        )
    except Exception as auth_error:
        logger.warning("Azure credential authentication failed for embedding, checking for API key fallback", error=str(auth_error))
        
        # Fallback: Check if there's an API key in the main settings
        from app.core.config import get_settings
        settings = get_settings()
        
        if hasattr(settings, 'AZURE_OPENAI_API_KEY') and settings.AZURE_OPENAI_API_KEY:
            logger.info("Using API key authentication for embedding as fallback")
            return AzureTextEmbedding(
                service_id=service_id,
                api_key=settings.AZURE_OPENAI_API_KEY,
                endpoint=endpoint,
                api_version=api_version,
                deployment_name=deployment_name
            )
        else:
            logger.error("No API key available for embedding fallback authentication")
            raise auth_error
        logger.error("Failed to create Azure text embedding service", error=str(e))
        raise


def create_azure_openai_text_embedding_with_managed_identity(
    endpoint: str,
    api_version: str,
    deployment_name: str,
    service_id: str = "azure_embedding"
) -> AzureTextEmbedding:
    """
    Create Azure OpenAI text embedding service with proper authentication fallback.
    
    Args:
        endpoint: Azure AI endpoint
        api_version: API version
        deployment_name: Embedding model deployment name
        service_id: Service identifier
        
    Returns:
        AzureTextEmbedding instance
    """
    # Strategy 1: Try with API key first (simplest)
    try:
        from app.core.config import get_settings
        settings = get_settings()
        
        if settings.AZURE_OPENAI_API_KEY:
            logger.info("Using Azure OpenAI API key for embedding service")
            return AzureTextEmbedding(
                service_id=service_id,
                api_key=settings.AZURE_OPENAI_API_KEY,
                endpoint=endpoint,
                api_version=api_version,
                deployment_name=deployment_name
            )
    except Exception as api_key_error:
        logger.debug("API key not available or failed", error=str(api_key_error))
    
    # Strategy 2: Use ClientSecretCredential with your existing credentials
    try:
        from azure.identity import ClientSecretCredential
        from app.orchestration.config import get_orchestration_config
        
        config = get_orchestration_config()
        
        credential = ClientSecretCredential(
            tenant_id=config.azure_tenant_id,
            client_id=config.azure_client_id,
            client_secret=config.azure_client_secret
        )
        
        logger.info("Using ClientSecretCredential for embedding service")
        return AzureTextEmbedding(
            service_id=service_id,
            endpoint=endpoint,
            api_version=api_version,
            deployment_name=deployment_name,
            ad_token_provider=lambda: credential.get_token("https://cognitiveservices.azure.com/.default").token
        )
        
    except Exception as credential_error:
        logger.error("ClientSecretCredential authentication failed", error=str(credential_error))
        raise RuntimeError(f"Failed to authenticate embedding service: {credential_error}")
