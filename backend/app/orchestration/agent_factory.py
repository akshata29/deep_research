"""
Agent factory for creating specialized research agents with memory capabilities.
"""

from typing import Dict, Any
import structlog
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

from .memory import MemoryPlugin
from .search import ModularSearchPlugin
from .prompts import (
    LEAD_RESEARCHER_PROMPT,
    RESEARCHER_PROMPT,
    CREDIBILITY_CRITIC_PROMPT,
    REFLECTION_CRITIC_PROMPT,
    SUMMARIZER_PROMPT,
    REPORT_WRITER_PROMPT,
    CITATION_AGENT_PROMPT,
    TRANSLATOR_PROMPT
)
from .config import get_orchestration_config, get_project_config
from app.core.azure_config import AzureServiceManager

logger = structlog.get_logger(__name__)


class ResearchAgent:
    """Simple research agent wrapper around Semantic Kernel."""
    
    def __init__(self, kernel: Kernel, name: str, description: str, instructions: str):
        self.kernel = kernel
        self.name = name
        self.description = description
        self.instructions = instructions
        
    async def invoke(self, query: str, context: str = "") -> str:
        """Invoke the agent with a query."""
        try:
            prompt = f"""
{self.instructions}

Context: {context}
Query: {query}

Response:"""
            
            # Use the kernel's chat completion service
            result = await self.kernel.invoke_prompt(prompt)
            return str(result)
            
        except Exception as e:
            logger.error("Agent invocation failed", agent=self.name, error=str(e))
            raise


# Global service manager instance to avoid recreation
_azure_service_manager = None

async def get_azure_service_manager():
    """Get or create the Azure Service Manager instance."""
    global _azure_service_manager
    if _azure_service_manager is None:
        from app.core.config import get_settings
        settings = get_settings()
        
        # Create a custom service manager that won't hit IMDS
        from azure.identity import ClientSecretCredential
        from app.core.azure_config import AzureServiceManager
        
        # Use ClientSecretCredential directly to avoid IMDS
        try:
            credential = ClientSecretCredential(
                tenant_id=settings.AZURE_TENANT_ID,
                client_id=settings.AZURE_CLIENT_ID,
                client_secret=settings.AZURE_CLIENT_SECRET
            )
            
            # Create service manager with the specific credential
            _azure_service_manager = AzureServiceManager(settings)
            _azure_service_manager.credential = credential
            
            logger.info("Using ClientSecretCredential for Azure authentication")
            
        except Exception as cred_error:
            logger.warning("Failed to create ClientSecretCredential", error=str(cred_error))
            # Fall back to the default initialization
            _azure_service_manager = AzureServiceManager(settings)
            await _azure_service_manager.initialize()
            
    return _azure_service_manager

async def get_azure_openai_service(model_config: Any) -> AzureChatCompletion:
    """
    Create Azure OpenAI service instance using existing Azure infrastructure.
    
    Args:
        model_config: Model configuration
        
    Returns:
        AzureChatCompletion instance
    """
    config = get_orchestration_config()
    
    try:
        # Try to use the shared Azure Service Manager first
        azure_service_manager = await get_azure_service_manager()
        
        return AzureChatCompletion(
            service_id=f"azure_openai_{model_config.deployment_name}",
            endpoint=config.azure_ai_endpoint,
            api_version=config.azure_openai_api_version,
            deployment_name=model_config.deployment_name,
            ad_token_provider=lambda: azure_service_manager.credential.get_token("https://cognitiveservices.azure.com/.default").token
        )
    except Exception as auth_error:
        logger.warning("Azure credential authentication failed, checking for API key fallback", error=str(auth_error))
        
        # Fallback: Check if there's an API key in the main settings
        from app.core.config import get_settings
        settings = get_settings()
        
        if hasattr(settings, 'AZURE_OPENAI_API_KEY') and settings.AZURE_OPENAI_API_KEY:
            logger.info("Using API key authentication as fallback")
            return AzureChatCompletion(
                service_id=f"azure_openai_{model_config.deployment_name}",
                api_key=settings.AZURE_OPENAI_API_KEY,
                endpoint=config.azure_ai_endpoint,
                api_version=config.azure_openai_api_version,
                deployment_name=model_config.deployment_name
            )
        else:
            logger.error("No API key available for fallback authentication")
            raise auth_error


async def create_agent_with_plugins(
    name: str,
    description: str,
    instructions: str,
    model_config: Any,
    memory_plugin: MemoryPlugin,
    search_plugin: ModularSearchPlugin
) -> ResearchAgent:
    """
    Create an agent with memory and search plugins.
    
    Args:
        name: Agent name
        description: Agent description
        instructions: Agent instructions/prompt
        model_config: Model configuration
        memory_plugin: Memory plugin instance
        search_plugin: Search plugin instance
        
    Returns:
        Configured ResearchAgent instance
    """
    try:
        # Create kernel
        kernel = Kernel()
        
        # Add AI service
        chat_service = await get_azure_openai_service(model_config)
        kernel.add_service(chat_service)
        
        # Add plugins
        kernel.add_plugin(memory_plugin, plugin_name="memory")
        kernel.add_plugin(search_plugin, plugin_name="search")
        
        # Create agent
        agent = ResearchAgent(
            kernel=kernel,
            name=name,
            description=description,
            instructions=instructions
        )
        
        logger.debug("Created agent", name=name, model=model_config.deployment_name)
        return agent
        
    except Exception as e:
        logger.error("Failed to create agent", name=name, error=str(e))
        raise


async def create_agents_with_memory(
    memory_plugin: MemoryPlugin,
    search_plugin: ModularSearchPlugin = None
) -> Dict[str, ResearchAgent]:
    """
    Create all research agents with memory capabilities.
    
    Args:
        memory_plugin: Memory plugin instance
        search_plugin: Search plugin instance (optional)
        
    Returns:
        Dictionary of agent name to ResearchAgent instance
    """
    try:
        config = get_orchestration_config()
        project_config = get_project_config()
        
        agents = {}
        
        # Default search plugin if not provided
        if search_plugin is None:
            from .search import ModularSearchPlugin
            search_plugin = ModularSearchPlugin()
        
        # Lead Researcher Agent
        lead_config = config.get_model_config("gpt-4")
        agents["LeadResearcher"] = await create_agent_with_plugins(
            name="LeadResearcher",
            description="Research coordination and strategic planning specialist",
            instructions=LEAD_RESEARCHER_PROMPT,
            model_config=lead_config,
            memory_plugin=memory_plugin,
            search_plugin=search_plugin
        )
        
        # Researcher Agents (specialized)
        researcher_configs = project_config.agents.get("researchers", {})
        researcher_count = researcher_configs.get("count", 3)
        specializations = researcher_configs.get("specializations", [
            "Technical analysis and documentation",
            "Market research and competitive analysis", 
            "Risk assessment and compliance"
        ])
        
        researcher_model = researcher_configs.get("model", "gpt-4-mini")
        researcher_config = config.get_model_config(researcher_model)
        
        for i in range(researcher_count):
            agent_name = f"Researcher{i+1}"
            specialization = specializations[i] if i < len(specializations) else "General research"
            
            agents[agent_name] = await create_agent_with_plugins(
                name=agent_name,
                description=f"Research specialist: {specialization}",
                instructions=RESEARCHER_PROMPT.format(specialization=specialization),
                model_config=researcher_config,
                memory_plugin=memory_plugin,
                search_plugin=search_plugin
            )
        
        # Credibility Critic Agent
        critic_config = config.get_model_config("gpt-4")
        agents["CredibilityCritic"] = await create_agent_with_plugins(
            name="CredibilityCritic",
            description="Source quality assessment and reliability validation specialist",
            instructions=CREDIBILITY_CRITIC_PROMPT,
            model_config=critic_config,
            memory_plugin=memory_plugin,
            search_plugin=search_plugin
        )
        
        # Reflection Critic Agent
        agents["ReflectionCritic"] = await create_agent_with_plugins(
            name="ReflectionCritic",
            description="Quality validation and improvement recommendations specialist",
            instructions=REFLECTION_CRITIC_PROMPT,
            model_config=critic_config,
            memory_plugin=memory_plugin,
            search_plugin=search_plugin
        )
        
        # Summarizer Agent
        summarizer_config = config.get_model_config("gpt-4")
        agents["Summarizer"] = await create_agent_with_plugins(
            name="Summarizer",
            description="Knowledge synthesis and summarization specialist",
            instructions=SUMMARIZER_PROMPT,
            model_config=summarizer_config,
            memory_plugin=memory_plugin,
            search_plugin=search_plugin
        )
        
        # Report Writer Agent
        writer_model = project_config.agents.get("report_writer", {}).get("model", "o3")
        writer_config = config.get_model_config(writer_model)
        agents["ReportWriter"] = await create_agent_with_plugins(
            name="ReportWriter",
            description="Professional report writing with citations specialist",
            instructions=REPORT_WRITER_PROMPT,
            model_config=writer_config,
            memory_plugin=memory_plugin,
            search_plugin=search_plugin
        )
        
        # Citation Agent
        citation_config = config.get_model_config("gpt-4-mini")
        agents["CitationAgent"] = await create_agent_with_plugins(
            name="CitationAgent",
            description="Reference management and citation formatting specialist",
            instructions=CITATION_AGENT_PROMPT,
            model_config=citation_config,
            memory_plugin=memory_plugin,
            search_plugin=search_plugin
        )
        
        # Translator Agent
        translator_config = config.get_model_config("gpt-4-mini")
        agents["Translator"] = await create_agent_with_plugins(
            name="Translator",
            description="Professional terminology translation specialist",
            instructions=TRANSLATOR_PROMPT,
            model_config=translator_config,
            memory_plugin=memory_plugin,
            search_plugin=search_plugin
        )
        
        logger.info(
            "All research agents created successfully",
            agent_count=len(agents),
            agents=list(agents.keys())
        )
        
        return agents
        
    except Exception as e:
        logger.error("Failed to create agents", error=str(e))
        raise
