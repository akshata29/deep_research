"""
Azure Service Manager for Deep Research Application.

This module manages all Azure service connections and configurations following
Azure best practices for authentication, security, and resource management.
"""

import asyncio
import logging
from typing import Dict, Optional, Any
from datetime import datetime, timedelta

import structlog
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from azure.keyvault.secrets import SecretClient
from azure.cosmos import CosmosClient
from azure.storage.blob import BlobServiceClient
from azure.ai.projects import AIProjectClient
from azure.core.exceptions import AzureError

from app.core.config import Settings


logger = structlog.get_logger(__name__)


class AzureServiceManager:
    """
    Centralized manager for all Azure service connections.
    
    Implements Azure best practices:
    - Managed Identity authentication
    - Proper resource lifecycle management
    - Error handling and retry logic
    - Security-first configuration
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize Azure Service Manager.
        
        Args:
            settings: Application settings containing Azure configuration
        """
        self.settings = settings
        self.credential: Optional[DefaultAzureCredential] = None
        
        # Service clients
        self._key_vault_client: Optional[SecretClient] = None
        self._cosmos_client: Optional[CosmosClient] = None
        self._blob_client: Optional[BlobServiceClient] = None
        self._ai_project_client: Optional[AIProjectClient] = None
        
        # Connection status
        self._initialized = False
        self._secrets_cache: Dict[str, str] = {}
        
        # Model deployment cache
        self._models_cache: Optional[Dict[str, Any]] = None
        self._models_cache_timestamp: Optional[datetime] = None
        self._models_cache_ttl_minutes: int = 30  # Cache for 30 minutes by default
    
    async def initialize(self) -> None:
        """
        Initialize all Azure service connections.
        
        This method:
        1. Sets up authentication using Managed Identity
        2. Initializes service clients
        3. Validates connectivity
        4. Caches frequently used secrets
        
        Raises:
            AzureError: If initialization fails
        """
        try:
            logger.info("Initializing Azure services")
            
            # Initialize authentication credential
            await self._setup_authentication()
            
            # Initialize service clients
            await asyncio.gather(
                self._initialize_key_vault(),
                self._initialize_cosmos_db(),
                self._initialize_blob_storage(),
                self._initialize_ai_services(),
                return_exceptions=False
            )
            
            # Cache critical secrets
            await self._cache_secrets()
            
            self._initialized = True
            logger.info("Azure services initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize Azure services", error=str(e))
            raise AzureError(f"Azure service initialization failed: {str(e)}")
    
    async def _setup_authentication(self) -> None:
        """
        Set up Azure authentication using Managed Identity.
        
        Priority order:
        1. Managed Identity (in Azure environments)
        2. Service Principal (CI/CD scenarios)
        3. Interactive browser (development)
        """
        try:
            # Use Managed Identity when running in Azure
            if self.settings.ENVIRONMENT == "production":
                self.credential = ManagedIdentityCredential()
                logger.info("Using Managed Identity authentication")
            else:
                # For development, use DefaultAzureCredential chain
                self.credential = DefaultAzureCredential()
                logger.info("Using DefaultAzureCredential authentication")
            
            # Test authentication by getting a token
            token = self.credential.get_token("https://management.azure.com/.default")
            logger.info("Azure authentication successful")
            
        except Exception as e:
            logger.error("Azure authentication failed", error=str(e))
            raise
    
    async def _initialize_key_vault(self) -> None:
        """Initialize Azure Key Vault client."""
        if not self.settings.KEY_VAULT_URL:
            logger.warning("Key Vault URL not configured, skipping initialization")
            return
        
        try:
            self._key_vault_client = SecretClient(
                vault_url=self.settings.KEY_VAULT_URL,
                credential=self.credential
            )
            
            # Test connectivity
            # Note: This will fail gracefully if no secrets exist
            try:
                list(self._key_vault_client.list_properties_of_secrets())
                logger.info("Key Vault connection verified")
            except Exception:
                logger.warning("Key Vault accessible but no secrets found or no permissions")
                
        except Exception as e:
            logger.error("Failed to initialize Key Vault", error=str(e))
            raise
    
    async def _initialize_cosmos_db(self) -> None:
        """Initialize Azure Cosmos DB client."""
        if not self.settings.COSMOS_DB_ENDPOINT:
            logger.warning("Cosmos DB endpoint not configured, skipping initialization")
            return
        
        try:
            self._cosmos_client = CosmosClient(
                url=self.settings.COSMOS_DB_ENDPOINT,
                credential=self.credential
            )
            
            # Test connectivity and create database/container if needed
            database = self._cosmos_client.create_database_if_not_exists(
                id=self.settings.COSMOS_DB_DATABASE_NAME
            )
            
            container = database.create_container_if_not_exists(
                id=self.settings.COSMOS_DB_CONTAINER_NAME,
                partition_key="/session_id"
            )
            
            logger.info("Cosmos DB connection verified")
            
        except Exception as e:
            logger.error("Failed to initialize Cosmos DB", error=str(e))
            raise
    
    async def _initialize_blob_storage(self) -> None:
        """Initialize Azure Blob Storage client."""
        if not self.settings.STORAGE_ACCOUNT_URL:
            logger.warning("Storage account URL not configured, skipping initialization")
            return
        
        try:
            self._blob_client = BlobServiceClient(
                account_url=self.settings.STORAGE_ACCOUNT_URL,
                credential=self.credential
            )
            
            # Test connectivity and create container if needed
            try:
                self._blob_client.create_container(
                    name=self.settings.STORAGE_CONTAINER_NAME
                )
            except Exception:
                # Container may already exist
                pass
            
            logger.info("Blob Storage connection verified")
            
        except Exception as e:
            logger.error("Failed to initialize Blob Storage", error=str(e))
            raise
    
    async def _initialize_ai_services(self) -> None:
        """Initialize Azure AI Foundry services."""
        if not all([
            self.settings.AZURE_AI_PROJECT_NAME,
            self.settings.AZURE_SUBSCRIPTION_ID
        ]):
            logger.warning("AI Foundry configuration incomplete, skipping initialization")
            logger.debug(
                "Missing AI Foundry configuration",
                project_name=bool(self.settings.AZURE_AI_PROJECT_NAME),
                subscription_id=bool(self.settings.AZURE_SUBSCRIPTION_ID),
                endpoint=bool(self.settings.AZURE_AI_ENDPOINT),
                resource_group=bool(self.settings.AZURE_RESOURCE_GROUP),
                tenant_id=bool(self.settings.AZURE_TENANT_ID)
            )
            return
        
        try:
            logger.info(
                "Initializing AI Project Client",
                endpoint=self.settings.AZURE_AI_ENDPOINT,
                subscription_id=self.settings.AZURE_SUBSCRIPTION_ID,
                resource_group=self.settings.AZURE_RESOURCE_GROUP,
                project_name=self.settings.AZURE_AI_PROJECT_NAME
            )
            
            # Initialize AI Project Client
            # Use project endpoint if available, otherwise fallback to AI endpoint
            project_endpoint = (
                self.settings.AZURE_AI_PROJECT_ENDPOINT or 
                self.settings.AZURE_AI_ENDPOINT
            )
            
            if not project_endpoint:
                logger.warning("No Azure AI project endpoint configured")
                self._ai_project_client = None
                return
            
            logger.info("Initializing AI Project Client", endpoint=project_endpoint)
            
            self._ai_project_client = AIProjectClient(
                endpoint=project_endpoint,
                credential=self.credential,
                subscription_id=self.settings.AZURE_SUBSCRIPTION_ID,
                resource_group_name=self.settings.AZURE_RESOURCE_GROUP,
                project_name=self.settings.AZURE_AI_PROJECT_NAME
            )
            
            logger.info("AI Foundry services initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize AI services", error=str(e), exc_info=True)
            # Don't raise - allow app to continue without AI services
            self._ai_project_client = None
    
    async def _cache_secrets(self) -> None:
        """Cache frequently used secrets from Key Vault."""
        if not self._key_vault_client:
            return
        
        # List of secrets to cache
        secret_names = [
            "bing-search-key",
            "openai-api-key",
            "storage-connection-string"
        ]
        
        for secret_name in secret_names:
            try:
                secret = self._key_vault_client.get_secret(secret_name)
                self._secrets_cache[secret_name] = secret.value
                logger.debug("Cached secret", secret_name=secret_name)
            except Exception:
                logger.warning(f"Could not cache secret: {secret_name}")
    
    async def get_secret(self, secret_name: str) -> Optional[str]:
        """
        Get a secret from Key Vault with caching.
        
        Args:
            secret_name: Name of the secret to retrieve
            
        Returns:
            Secret value or None if not found
        """
        # Check cache first
        if secret_name in self._secrets_cache:
            return self._secrets_cache[secret_name]
        
        # Fetch from Key Vault
        if self._key_vault_client:
            try:
                secret = self._key_vault_client.get_secret(secret_name)
                self._secrets_cache[secret_name] = secret.value
                return secret.value
            except Exception as e:
                logger.error("Failed to retrieve secret", secret_name=secret_name, error=str(e))
        
        return None
    
    def get_ai_project_client(self) -> Optional[AIProjectClient]:
        """
        Get the Azure AI Project client.
        
        Returns:
            AI Project client instance or None if not initialized
        """
        return getattr(self, '_ai_project_client', None)
    
    def get_ai_project_connection_string(self) -> str:
        """
        Get the Azure AI Project connection string.
        
        Returns:
            Connection string for the AI project
        """
        if not all([
            self.settings.AZURE_AI_ENDPOINT,
            self.settings.AZURE_SUBSCRIPTION_ID,
            self.settings.AZURE_RESOURCE_GROUP,
            self.settings.AZURE_AI_PROJECT_NAME
        ]):
            raise ValueError("Missing required AI project configuration")
        
        return (
            f"Endpoint={self.settings.AZURE_AI_ENDPOINT};"
            f"SubscriptionId={self.settings.AZURE_SUBSCRIPTION_ID};"
            f"ResourceGroupName={self.settings.AZURE_RESOURCE_GROUP};"
            f"ProjectName={self.settings.AZURE_AI_PROJECT_NAME}"
        )
    
    @property
    def cosmos_client(self) -> Optional[CosmosClient]:
        """Get Cosmos DB client."""
        return self._cosmos_client
    
    @property
    def blob_client(self) -> Optional[BlobServiceClient]:
        """Get Blob Storage client."""
        return self._blob_client
    
    @property
    def ai_project_client(self) -> Optional[AIProjectClient]:
        """Get AI Project client."""
        return self._ai_project_client
    
    @property
    def is_initialized(self) -> bool:
        """Check if all services are initialized."""
        return self._initialized
    
    async def health_check(self) -> Dict[str, bool]:
        """
        Perform health checks on all Azure services.
        
        Returns:
            Dictionary with service names and their health status
        """
        health_status = {}
        
        # Key Vault health check
        try:
            if self._key_vault_client:
                list(self._key_vault_client.list_properties_of_secrets())
                health_status["key_vault"] = True
            else:
                health_status["key_vault"] = False
        except Exception:
            health_status["key_vault"] = False
        
        # Cosmos DB health check
        try:
            if self._cosmos_client:
                list(self._cosmos_client.list_databases())
                health_status["cosmos_db"] = True
            else:
                health_status["cosmos_db"] = False
        except Exception:
            health_status["cosmos_db"] = False
        
        # Blob Storage health check
        try:
            if self._blob_client:
                list(self._blob_client.list_containers())
                health_status["blob_storage"] = True
            else:
                health_status["blob_storage"] = False
        except Exception:
            health_status["blob_storage"] = False
        
        # AI Services health check
        try:
            if self._ai_project_client:
                # Test AI project connectivity
                health_status["ai_services"] = True
            else:
                health_status["ai_services"] = False
        except Exception:
            health_status["ai_services"] = False
        
        return health_status
    
    async def get_deployed_models(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get all deployed models from the Azure AI project using Azure Management API.
        
        Args:
            force_refresh: If True, bypass cache and fetch fresh data from Azure
        
        Returns:
            Dict containing deployed models organized by capability
        """
        # Check cache first (unless force refresh is requested)
        if not force_refresh and self._is_models_cache_valid():
            logger.debug("Returning cached model deployments")
            return self._models_cache
        
        if not self.credential:
            logger.warning("Azure credential not initialized")
            return self._get_fallback_models()
        
        try:
            # Import required libraries for HTTP requests
            import httpx
            import json
            
            # Get access token for Azure Management API
            token = self.credential.get_token("https://management.azure.com/.default")
            
            # Construct the batch API request
            subscription_id = self.settings.AZURE_SUBSCRIPTION_ID
            resource_group = self.settings.AZURE_RESOURCE_GROUP
            account_name = self.settings.AZURE_AI_PROJECT_NAME  # This should be the Cognitive Services account name
            
            if not all([subscription_id, resource_group, account_name]):
                logger.warning("Missing required Azure configuration for model deployment API")
                return self._get_fallback_models()
            
            # Azure Management API batch endpoint
            batch_url = "https://management.azure.com/batch?api-version=2020-06-01"
            
            # Construct the relative URL for deployments
            relative_url = f"/subscriptions/{subscription_id}/resourcegroups/{resource_group}/providers/Microsoft.CognitiveServices/accounts/{account_name}/deployments?api-version=2023-10-01-preview"
            
            # Batch request payload
            batch_payload = {
                "requests": [{
                    "HttpMethod": "get",
                    "RelativeUrl": relative_url
                }]
            }
            
            headers = {
                "Authorization": f"Bearer {token.token}",
                "Content-Type": "application/json"
            }
            
            logger.info("Fetching model deployments from Azure Management API")
            
            # Make the batch API request using httpx (better Windows compatibility)
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(batch_url, json=batch_payload, headers=headers)
                
                if response.status_code != 200:
                    logger.error(f"Azure Management API request failed with status {response.status_code}: {response.text}")
                    return self._get_fallback_models()
                
                batch_response = response.json()
            
            # Extract deployments from batch response
            if not batch_response.get("responses") or len(batch_response["responses"]) == 0:
                logger.warning("No responses in batch API result")
                return self._get_fallback_models()
            
            first_response = batch_response["responses"][0]
            if first_response.get("httpStatusCode") != 200:
                logger.error(f"Deployment API returned status {first_response.get('httpStatusCode')}")
                return self._get_fallback_models()
            
            deployments = first_response.get("content", {}).get("value", [])
            logger.info(f"Found {len(deployments)} model deployments")
            
            # Process deployments into categorized models - collect all models by category
            models = {
                'thinking': [],
                'task': [],
                'phi': [],
                'embedding': [],
                'other': []
            }
            
            for deployment in deployments:
                deployment_name = deployment.get("name", "unknown")
                model_props = deployment.get("properties", {})
                model_info_raw = model_props.get("model", {})
                
                model_info = {
                    "name": deployment_name,
                    "model": model_info_raw.get("name", deployment_name),
                    "version": model_info_raw.get("version", "latest"),
                    "format": model_info_raw.get("format", "unknown"),
                    "state": model_props.get("provisioningState", "unknown"),
                    "capacity": deployment.get("sku", {}).get("capacity", 0),
                    "deployment_type": deployment.get("sku", {}).get("name", "unknown"),
                    "capabilities": model_props.get("capabilities", {}),
                    "agent_supported": self._is_agent_supported(deployment_name)  # Use deployment name instead of model name
                }
                
                logger.debug(f"Processing deployment: {deployment_name} -> {model_info['model']}")
                
                # Categorize models based on their names and capabilities
                model_name_lower = deployment_name.lower()
                model_actual_name_lower = model_info["model"].lower()
                
                # Combine thinking, reasoning, and deepseek models into "thinking" category
                if any(keyword in model_name_lower for keyword in ['gpt-4', 'chat4', 'o1', 'chato1', 'deepseek', 'chatds']) and 'mini' not in model_name_lower:
                    models['thinking'].append(model_info)
                elif any(keyword in model_name_lower for keyword in ['gpt-4o-mini', 'chat4omini', 'o1-mini', 'chato1mini']):
                    models['task'].append(model_info)
                elif any(keyword in model_name_lower for keyword in ['phi', 'chatphi']):
                    models['phi'].append(model_info)
                elif any(keyword in model_name_lower for keyword in ['embedding', 'ada']):
                    models['embedding'].append(model_info)
                else:
                    models['other'].append(model_info)
            
            # Remove empty categories and flatten structure for backwards compatibility
            final_models = {}
            for category, model_list in models.items():
                if model_list:
                    # Sort models by preference (capacity, then alphabetically)
                    sorted_models = sorted(model_list, key=lambda x: (-x.get('capacity', 0), x.get('name', '')))
                    final_models[category] = sorted_models
            
            # Ensure we have at least thinking and task models by promoting from other categories if needed
            if not final_models.get('thinking') and final_models.get('phi'):
                final_models['thinking'] = final_models['phi'][:1]  # Take best phi model for thinking
            if not final_models.get('task') and final_models.get('phi'):
                final_models['task'] = final_models['phi'][:1]  # Take best phi model for task
            
            if not final_models:
                logger.warning("No suitable models found in deployments, using fallback")
                return self._get_fallback_models()
            
            # Cache the results
            self._models_cache = final_models
            self._models_cache_timestamp = datetime.utcnow()
            
            logger.info("Retrieved and cached deployed models", 
                       model_count=sum(len(models) for models in final_models.values()), 
                       deployments_found=len(deployments),
                       categories=list(final_models.keys()),
                       category_counts={k: len(v) for k, v in final_models.items()},
                       cache_ttl_minutes=self._models_cache_ttl_minutes)
            return final_models
            
        except Exception as e:
            logger.error("Failed to get deployed models from Azure Management API", 
                        error=str(e), 
                        error_type=type(e).__name__)
            
            # If we have cached data but it's expired, return it anyway as fallback
            if self._models_cache:
                logger.warning("Returning expired cached models due to API error")
                return self._models_cache
                
            return self._get_fallback_models()
    
    def _get_fallback_models(self) -> Dict[str, Any]:
        """Get fallback model configuration when Azure models are not available."""
        return {
            'thinking': [{'name': 'gpt-4', 'model': 'gpt-4', 'version': 'latest'}],
            'task': [{'name': 'gpt-35-turbo', 'model': 'gpt-35-turbo', 'version': 'latest'}]
        }
    
    def _is_models_cache_valid(self) -> bool:
        """
        Check if the models cache is still valid.
        
        Returns:
            True if cache exists and is within TTL, False otherwise
        """
        if not self._models_cache or not self._models_cache_timestamp:
            return False
        
        cache_age = datetime.utcnow() - self._models_cache_timestamp
        return cache_age < timedelta(minutes=self._models_cache_ttl_minutes)
    
    def invalidate_models_cache(self) -> None:
        """
        Manually invalidate the models cache.
        
        This can be called when you know the model deployments have changed.
        """
        self._models_cache = None
        self._models_cache_timestamp = None
        logger.info("Model deployment cache invalidated")
    
    def get_models_cache_status(self) -> Dict[str, Any]:
        """
        Get information about the current models cache status.
        
        Returns:
            Dictionary with cache status information
        """
        if not self._models_cache_timestamp:
            return {
                "cached": False,
                "cache_age_minutes": None,
                "cache_ttl_minutes": self._models_cache_ttl_minutes,
                "is_valid": False
            }
        
        cache_age = datetime.utcnow() - self._models_cache_timestamp
        cache_age_minutes = cache_age.total_seconds() / 60
        
        return {
            "cached": True,
            "cache_age_minutes": round(cache_age_minutes, 2),
            "cache_ttl_minutes": self._models_cache_ttl_minutes,
            "is_valid": self._is_models_cache_valid(),
            "cached_at": self._models_cache_timestamp.isoformat(),
            "model_count": len(self._models_cache) if self._models_cache else 0
        }
    
    def set_models_cache_ttl(self, ttl_minutes: int) -> None:
        """
        Set the TTL for the models cache.
        
        Args:
            ttl_minutes: Time-to-live in minutes for the models cache
        """
        self._models_cache_ttl_minutes = max(1, ttl_minutes)  # Minimum 1 minute
        logger.info(f"Models cache TTL set to {self._models_cache_ttl_minutes} minutes")
    
    async def cleanup(self) -> None:
        """Clean up resources and connections."""
        logger.info("Cleaning up Azure service connections")
        
        # Close any open connections
        if self._cosmos_client:
            # Cosmos client doesn't need explicit cleanup
            pass
        
        if self._blob_client:
            # Blob client doesn't need explicit cleanup
            pass
        
        # Clear caches
        self._secrets_cache.clear()
        self._models_cache = None
        self._models_cache_timestamp = None
        
        self._initialized = False
        logger.info("Azure service cleanup completed")
    
    def _is_agent_supported(self, model_name: str) -> bool:
        """Check if a model is supported by Azure AI Agents Service."""
        # Based on Azure AI Foundry Agent Service documentation
        # Only OpenAI models are supported: gpt-4o, gpt-4o-mini, gpt-4, gpt-35-turbo
        
        model_name_lower = model_name.lower()
        
        # Standard OpenAI model names
        standard_supported_models = [
            'gpt-4o',
            'gpt-4o-mini', 
            'gpt-4',
            'gpt-35-turbo',
            'gpt-3.5-turbo'
        ]
        
        # Custom deployment name patterns (common Azure naming conventions)
        custom_patterns = [
            'chat4o',      # GPT-4o variants
            'chat4',       # GPT-4 variants  
            'chato1',      # O1 models (GPT-4o family)
            'gpt4o',       # Alternative GPT-4o naming
            'gpt4',        # Alternative GPT-4 naming
            'gpt35',       # GPT-3.5 variants
            'turbo'        # Turbo variants
        ]
        
        # Check standard names first
        for supported in standard_supported_models:
            if supported in model_name_lower:
                return True
        
        # Check custom deployment patterns
        for pattern in custom_patterns:
            if pattern in model_name_lower:
                return True
        
        return False
