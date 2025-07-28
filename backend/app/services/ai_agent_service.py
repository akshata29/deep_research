"""
AI Agent Service for Deep Research application.

This service manages Azure AI Foundry Agent Service integration for:
- Creating and managing AI agents
- Running conversations and tasks
- Managing threads and messages
- Tool integration (Bing grounding, function calling)

Implements Azure best practices for AI service integration.
"""

import asyncio
import json
from typing import Dict, List, Optional, Any, Union

import structlog
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import CodeInterpreterTool, BingGroundingTool
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import AzureError

from app.core.azure_config import AzureServiceManager


logger = structlog.get_logger(__name__)


class AIAgentService:
    """
    Service for managing Azure AI Foundry agents and conversations.
    
    Provides a high-level interface for:
    - Agent lifecycle management
    - Conversation threading
    - Tool integration
    - Response processing
    
    Based on Azure AI Foundry Agent Service patterns.
    """
    
    def __init__(self, azure_manager: AzureServiceManager):
        """
        Initialize AI Agent Service.
        
        Args:
            azure_manager: Azure service manager instance
        """
        self.azure_manager = azure_manager
        self.ai_client: Optional[AIProjectClient] = azure_manager.get_ai_project_client()
        
        # Debug logging for client initialization
        if self.ai_client:
            logger.info("AI Project client successfully initialized")
        else:
            logger.error("AI Project client is None - check Azure configuration")
            logger.debug(
                "Azure configuration check",
                endpoint=bool(azure_manager.settings.AZURE_AI_ENDPOINT),
                subscription_id=bool(azure_manager.settings.AZURE_SUBSCRIPTION_ID),
                resource_group=bool(azure_manager.settings.AZURE_RESOURCE_GROUP),
                project_name=bool(azure_manager.settings.AZURE_AI_PROJECT_NAME),
                tenant_id=bool(azure_manager.settings.AZURE_TENANT_ID)
            )
        
        # Agent and thread caches
        self.agents: Dict[str, Any] = {}
        self.threads: Dict[str, Any] = {}
        
        # Construct Bing connection ID from environment variables
        settings = azure_manager.settings
        
        # Initialize tool configurations
        self.available_tools = {
            "code_interpreter": CodeInterpreterTool()
        }
        
        # Store Bing connection ID for later use
        self.bing_connection_id = None
        self.bing_tool = None
        
        # Add Bing grounding tool if all required settings are available
        if all([
            settings.AZURE_SUBSCRIPTION_ID,
            settings.AZURE_RESOURCE_GROUP,
            settings.AZURE_AI_PROJECT_NAME,
            settings.BING_CONNECTION_NAME
        ]):
            # Use the correct Azure AI Foundry connection ID format
            # Based on the error, it should use this format:
            self.bing_connection_id = (
                f"/subscriptions/{settings.AZURE_SUBSCRIPTION_ID}"
                f"/resourceGroups/{settings.AZURE_RESOURCE_GROUP}"  
                f"/providers/Microsoft.CognitiveServices"
                f"/accounts/{settings.AZURE_AI_PROJECT_NAME}"
                f"/projects/{settings.BING_PROJECT_NAME}"
                f"/connections/{settings.BING_CONNECTION_NAME}"
            )
            # Initialize the Bing Grounding tool as per Microsoft documentation
            self.bing_tool = BingGroundingTool(connection_id=self.bing_connection_id)
            logger.info("Bing grounding tool initialized", connection_id=self.bing_connection_id)
        else:
            logger.warning("Bing grounding tool not available - missing required Azure settings")
            logger.debug(
                "Required settings",
                subscription_id=bool(settings.AZURE_SUBSCRIPTION_ID),
                resource_group=bool(settings.AZURE_RESOURCE_GROUP),
                project_name=bool(settings.AZURE_AI_PROJECT_NAME),
                connection_name=bool(settings.BING_CONNECTION_NAME)
            )
    
    def _get_agent_params_for_model(self, model: str, temperature: float, max_tokens: Optional[int]) -> Dict[str, Any]:
        """
        Get the correct parameters for agent creation based on the model.
        
        O1 models don't support the 'temperature' parameter.
        
        Args:
            model: Model name
            temperature: Temperature value
            max_tokens: Maximum tokens value
            
        Returns:
            Dictionary of parameters suitable for the model
        """
        params = {}
        
        # Check if this is an O1 model
        is_o1_model = any(o1_keyword in model.lower() for o1_keyword in ['o1', 'chato1'])
        
        if not is_o1_model:
            # Regular models support temperature
            params['temperature'] = temperature
        # Note: O1 models don't support temperature parameter, so we skip it
        
        if max_tokens is not None:
            if is_o1_model:
                # O1 models might use max_completion_tokens, but for agent creation
                # we'll let the Azure AI service handle this
                params['max_tokens'] = max_tokens
            else:
                params['max_tokens'] = max_tokens
                
        return params

    async def create_agent(
        self,
        name: str,
        model: str,
        instructions: str,
        tools: Optional[List[str]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Any:
        """
        Create a new AI agent with specified configuration, or return existing agent if one with the same name exists.
        
        Args:
            name: Agent name/identifier
            model: Model to use (e.g., "gpt-4", "gpt-35-turbo")
            instructions: System instructions for the agent
            tools: List of tools to enable for the agent
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens per response
            
        Returns:
            Agent instance (existing or newly created)
            
        Raises:
            AzureError: If agent creation fails
        """
        try:
            if not self.ai_client:
                raise AzureError("AI Project client not initialized")
            
            logger.info(
                "Looking for existing agent or creating new one",
                name=name,
                model=model,
                tools=tools or []
            )
            
            # First, check if we already have this agent cached
            if name in self.agents:
                logger.info(f"Found cached agent: {name} with ID: {self.agents[name].id}")
                return self.agents[name]
            
            # List all agents and check if one with the target name exists
            agent_list = self.ai_client.agents.list_agents()
            found_agent = False
            agent_id = None
            
            for agent in agent_list:
                if agent.name == name:
                    agent_id = agent.id
                    found_agent = True
                    break
            
            if found_agent:
                # Get the existing agent
                agent_definition = self.ai_client.agents.get_agent(agent_id)
                logger.info(f"Found existing agent: {name} with ID: {agent_id}")
                
                # Cache the agent
                self.agents[name] = agent_definition
                
                return agent_definition
            else:
                # Create a new agent
                logger.info(f"Creating new agent: {name}")
                
                # Prepare tool configurations
                agent_tools = []
                if tools:
                    for tool_spec in tools:
                        if isinstance(tool_spec, dict):
                            tool_type = tool_spec.get("type")
                            if tool_type == "bing_grounding":
                                # Use the bing grounding tool definitions as per Microsoft documentation
                                if self.bing_tool:
                                    agent_tools.extend(self.bing_tool.definitions)
                                else:
                                    logger.warning("Bing grounding tool not available - no connection configured")
                            elif tool_type == "function":
                                # For function tools, we need to provide the function definition
                                # For now, skip function tools as they need specific function schemas
                                logger.warning("Function tools require specific function definitions - skipping")
                            elif tool_type == "code_interpreter":
                                agent_tools.append({"type": "code_interpreter"})
                            else:
                                logger.warning(f"Unknown tool type: {tool_type}")
                        elif isinstance(tool_spec, str):
                            # Handle string tool names
                            if tool_spec == "bing_grounding":
                                # Use the bing grounding tool definitions as per Microsoft documentation
                                if self.bing_tool:
                                    try:
                                        agent_tools.extend(self.bing_tool.definitions)
                                        logger.info("Added Bing grounding tool to agent", name=name)
                                    except Exception as tool_error:
                                        logger.error("Failed to add Bing grounding tool", error=str(tool_error), name=name)
                                        # Continue without the tool rather than failing
                                else:
                                    logger.warning("Bing grounding tool not available - no connection configured", name=name)
                            elif tool_spec == "function":
                                # For function tools, we need to provide the function definition
                                # For now, skip function tools as they need specific function schemas
                                logger.warning("Function tools require specific function definitions - skipping", name=name)
                            elif tool_spec == "code_interpreter":
                                agent_tools.append({"type": "code_interpreter"})
                            elif tool_spec in self.available_tools:
                                try:
                                    tool = self.available_tools[tool_spec]
                                    agent_tools.extend(tool.definitions)
                                    logger.info("Added tool to agent", tool=tool_spec, name=name)
                                except Exception as tool_error:
                                    logger.error("Failed to add tool", tool=tool_spec, error=str(tool_error), name=name)
                            else:
                                logger.warning(f"Unknown tool requested: {tool_spec}", name=name)
                
                # Get model-specific parameters
                agent_params = self._get_agent_params_for_model(model, temperature, max_tokens)
                
                logger.info(
                    "Creating agent with parameters",
                    name=name,
                    model=model,
                    tools_count=len(agent_tools),
                    agent_params=agent_params
                )
                
                # Create the agent using Azure AI Foundry pattern
                try:
                    agent_definition = self.ai_client.agents.create_agent(
                        model=model,
                        name=name,
                        instructions=instructions,
                        tools=agent_tools,
                        **agent_params
                    )
                    
                    logger.info(f"Created new agent: {name} with ID: {agent_definition.id}")
                    
                    # Cache the agent
                    self.agents[name] = agent_definition
                    
                    return agent_definition
                    
                except Exception as agent_create_error:
                    logger.error(
                        "Failed to create agent with Azure AI service",
                        name=name,
                        model=model,
                        tools_count=len(agent_tools),
                        error=str(agent_create_error),
                        exc_info=True
                    )
                    raise
            
        except Exception as e:
            logger.error(
                "Failed to create or find AI agent",
                name=name,
                model=model,
                error=str(e),
                exc_info=True
            )
            raise AzureError(f"Agent creation/lookup failed: {str(e)}")
    
    async def create_thread(self, metadata: Optional[Dict[str, str]] = None) -> Any:
        """
        Create a new conversation thread.
        
        Args:
            metadata: Optional metadata for the thread
            
        Returns:
            Created thread instance
        """
        try:
            if not self.ai_client:
                raise AzureError("AI Project client not initialized")
            
            logger.info("Creating conversation thread")
            
            # Create the thread using Azure AI Foundry pattern
            thread = self.ai_client.agents.threads.create()
            
            # Cache the thread
            thread_id = thread.id
            self.threads[thread_id] = thread
            
            logger.info("Conversation thread created", thread_id=thread_id)
            
            return thread
            
        except Exception as e:
            logger.error("Failed to create thread", error=str(e), exc_info=True)
            raise AzureError(f"Thread creation failed: {str(e)}")
    
    async def add_message(
        self,
        thread: Any,
        content: str,
        role: str = "user",
        attachments: Optional[List[Dict]] = None
    ) -> Any:
        """
        Add a message to a conversation thread.
        
        Args:
            thread: Thread to add message to
            content: Message content
            role: Message role ("user", "assistant", "system")
            attachments: Optional file attachments
            
        Returns:
            Created message instance
        """
        try:
            if not self.ai_client:
                raise AzureError("AI Project client not initialized")
            
            logger.debug(
                "Adding message to thread",
                thread_id=thread.id,
                role=role,
                content_length=len(content)
            )
            
            # Add the message using Azure AI Foundry pattern
            message = self.ai_client.agents.messages.create(
                thread_id=thread.id,
                role=role,
                content=content
            )
            
            logger.debug("Message added to thread", thread_id=thread.id, message_id=message['id'])
            
            return message
            
        except Exception as e:
            logger.error(
                "Failed to add message",
                thread_id=thread.id,
                error=str(e),
                exc_info=True
            )
            raise AzureError(f"Message creation failed: {str(e)}")
    
    async def run_agent(
        self,
        thread: Any,
        agent: Any,
        additional_instructions: Optional[str] = None,
        tools: Optional[List[Dict]] = None
    ) -> Any:
        """
        Run an agent on a conversation thread.
        
        Args:
            thread: Thread to run on
            agent: Agent to execute
            additional_instructions: Optional additional instructions
            tools: Optional tool overrides
            
        Returns:
            Run instance with execution details
        """
        try:
            if not self.ai_client:
                raise AzureError("AI Project client not initialized")
            
            logger.info(
                "Running agent on thread",
                thread_id=thread.id,
                agent_id=agent.id,
                agent_name=getattr(agent, 'name', 'unknown')
            )
            
            # Create and process run using Azure AI Foundry pattern
            run = self.ai_client.agents.runs.create_and_process(
                thread_id=thread.id,
                agent_id=agent.id
            )
            
            logger.info(
                "Agent run completed",
                thread_id=thread.id,
                agent_id=agent.id,
                run_id=run.id,
                status=run.status
            )
            
            return run
            
        except Exception as e:
            logger.error(
                "Failed to run agent",
                thread_id=thread.id,
                agent_id=agent.id,
                error=str(e),
                exc_info=True
            )
            raise AzureError(f"Agent run failed: {str(e)}")
    
    async def get_run_result(self, run: Any) -> str:
        """
        Get the result content from a completed run.
        
        Args:
            run: Completed run instance
            
        Returns:
            Response content as string
        """
        try:
            if not self.ai_client:
                raise AzureError("AI Project client not initialized")
            
            logger.info("Getting run result", run_id=run.id, status=run.status)
            
            if run.status == "failed":
                error_details = getattr(run, 'last_error', 'Unknown error')
                logger.error("Run failed", run_id=run.id, error=error_details)
                raise AzureError(f"Run failed: {error_details}")
            
            if run.status != "completed":
                logger.warning("Run not completed", run_id=run.id, status=run.status)
                raise ValueError(f"Run is not completed (status: {run.status})")
            
            # Get messages from the thread using Azure AI Foundry pattern
            try:
                messages = self.ai_client.agents.messages.list(thread_id=run.thread_id)
                # Convert to list to work with the messages
                messages_list = list(messages)
                logger.debug("Retrieved messages", run_id=run.id, message_count=len(messages_list))
            except Exception as msg_error:
                logger.error("Failed to retrieve messages", run_id=run.id, error=str(msg_error))
                raise AzureError(f"Failed to retrieve messages: {str(msg_error)}")
            
            # Find the latest assistant message
            assistant_messages = [
                msg for msg in messages_list
                if msg.role == "assistant"
            ]
            
            if not assistant_messages:
                logger.warning("No assistant messages found", run_id=run.id)
                return "No response generated"
            
            # Return the content of the latest message
            latest_message = assistant_messages[0]  # Messages are returned in reverse order
            content = latest_message.content
            
            # Extract text content
            if isinstance(content, list) and content:
                text_parts = []
                for item in content:
                    if hasattr(item, 'text') and hasattr(item.text, 'value'):
                        text_parts.append(item.text.value)
                    elif isinstance(item, dict) and 'text' in item:
                        if isinstance(item['text'], dict) and 'value' in item['text']:
                            text_parts.append(item['text']['value'])
                        else:
                            text_parts.append(str(item['text']))
                    else:
                        text_parts.append(str(item))
                result = '\n'.join(text_parts)
            elif isinstance(content, str):
                result = content
            else:
                result = str(content)
            
            logger.info("Successfully extracted run result", run_id=run.id, result_length=len(result))
            return result
            
        except Exception as e:
            logger.error(
                "Failed to get run result",
                run_id=getattr(run, 'id', 'unknown'),
                error=str(e),
                exc_info=True
            )
            raise AzureError(f"Failed to get run result: {str(e)}")
    
    async def cleanup_agent(self, agent_name: str) -> None:
        """
        Clean up an agent and its resources.
        
        Args:
            agent_name: Name of the agent to clean up
        """
        try:
            if agent_name in self.agents:
                agent = self.agents[agent_name]
                
                # Delete the agent using Azure AI Foundry pattern
                if self.ai_client:
                    self.ai_client.agents.delete_agent(agent.id)
                
                # Remove from cache
                del self.agents[agent_name]
                
                logger.info("Agent cleaned up", agent_name=agent_name)
                
        except Exception as e:
            logger.error(
                "Failed to cleanup agent",
                agent_name=agent_name,
                error=str(e)
            )

    async def get_agent_usage_stats(self) -> Dict[str, Any]:
        """
        Get usage statistics for all agents.
        
        Returns:
            Usage statistics dictionary
        """
        try:
            stats = {
                "total_agents": len(self.agents),
                "total_threads": len(self.threads),
                "agents": {}
            }
            
            for name, agent in self.agents.items():
                stats["agents"][name] = {
                    "agent_id": agent.id,
                    "model": getattr(agent, 'model', 'unknown'),
                    "created_at": getattr(agent, 'created_at', None)
                }
            
            return stats
            
        except Exception as e:
            logger.error("Failed to get usage stats", error=str(e))
            return {"error": str(e)}

    async def generate_response(
        self, 
        system_prompt:str,
        prompt: str, 
        model_name: str, 
        agent_name: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        use_bing_grounding: bool = False
    ) -> str:
        """
        Generate a response for a simple prompt using the AI agent.
        
        This method creates permanent agents that are reused across requests.
        
        Args:
            prompt: The input prompt
            model_name: Model to use for generation
            agent_name: Unique name for the agent (permanent)
            max_tokens: Maximum tokens in response
            temperature: Generation temperature
            use_bing_grounding: Whether to enable Bing grounding tool
            
        Returns:
            Generated response text
        """
        try:
            logger.info("Generating response", model=model_name, agent_name=agent_name, prompt_length=len(prompt), use_bing_grounding=use_bing_grounding)
            
            # Prepare tools for the agent
            tools = []
            if use_bing_grounding:
                if self.bing_tool and self.bing_connection_id:
                    tools.append("bing_grounding")
                    logger.info("Enabling Bing grounding for agent", agent_name=agent_name, connection_id=self.bing_connection_id)
                else:
                    logger.warning("Bing grounding requested but not available - proceeding without it", agent_name=agent_name)
                    use_bing_grounding = False
            
            # Create or reuse agent (create_agent already handles checking if agent exists)
            try:
                agent = await self.create_agent(
                    name=agent_name,
                    instructions=system_prompt,
                    model=model_name,
                    temperature=temperature,
                    tools=tools if tools else None
                )
            except Exception as agent_error:
                logger.error("Failed to create agent, trying without tools", error=str(agent_error), agent_name=agent_name)
                # If agent creation fails with tools, try without tools
                if use_bing_grounding:
                    logger.info("Retrying agent creation without Bing grounding", agent_name=agent_name)
                    agent = await self.create_agent(
                        name=f"{agent_name}-notool",
                        instructions="You are a helpful AI assistant. Provide clear, accurate, and well-structured responses.",
                        model=model_name,
                        temperature=temperature,
                        tools=None
                    )
                else:
                    raise
            
            # Create thread
            thread = await self.create_thread()
            
            # Add message
            await self.add_message(
                thread=thread,
                role="user",
                content=prompt
            )
            
            # Run agent (max_tokens can be passed here if the method supports it)
            run = await self.run_agent(
                thread=thread,
                agent=agent
            )
            
            # Get result
            response = await self.get_run_result(run)
            
            # Don't cleanup agent - keep it permanent for reuse
            logger.info("Response generated successfully", agent_name=agent_name, response_length=len(response))
            return response
            
        except Exception as e:
            logger.error("Failed to generate response", error=str(e), model=model_name, agent_name=agent_name)
            raise
