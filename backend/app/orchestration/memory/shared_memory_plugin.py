"""
Shared memory plugin for Semantic Kernel inter-agent communication.
"""

from typing import Any, Dict, List, Optional
import structlog
from semantic_kernel.functions import kernel_function
from .memory_manager import MemoryManager

logger = structlog.get_logger(__name__)


class SharedMemoryPluginSK:
    """
    Shared memory plugin for Semantic Kernel agents to share information.
    """
    
    def __init__(self, memory_manager: MemoryManager):
        """
        Initialize the shared memory plugin.
        
        Args:
            memory_manager: The memory manager instance
        """
        self.memory_manager = memory_manager
        self._shared_data: Dict[str, Any] = {}
    
    @kernel_function(name="share_insight", description="Share an insight or discovery with other agents")
    async def share_insight(self, insight: str, agent_name: str, category: str = "general") -> str:
        """
        Share an insight with other agents.
        
        Args:
            insight: The insight to share
            agent_name: Name of the agent sharing the insight
            category: Category of the insight
            
        Returns:
            Confirmation message
        """
        try:
            # Store in memory for persistence
            metadata = {
                "agent_name": agent_name,
                "category": category,
                "type": "shared_insight"
            }
            
            await self.memory_manager.store_finding(
                finding=insight,
                source=f"Agent: {agent_name}",
                confidence=0.8,
                metadata=metadata
            )
            
            # Also store in local shared data for quick access
            key = f"{agent_name}_{category}_{len(self._shared_data)}"
            self._shared_data[key] = {
                "insight": insight,
                "agent_name": agent_name,
                "category": category,
                "timestamp": self.memory_manager.session_id
            }
            
            logger.debug("Agent shared insight", agent=agent_name, category=category)
            return f"Insight shared successfully by {agent_name} in category '{category}'"
            
        except Exception as e:
            logger.error("Failed to share insight", error=str(e))
            return f"Error sharing insight: {str(e)}"
    
    @kernel_function(name="get_shared_insights", description="Get insights shared by other agents")
    async def get_shared_insights(self, category: Optional[str] = None, agent_name: Optional[str] = None) -> str:
        """
        Get insights shared by other agents.
        
        Args:
            category: Filter by category (optional)
            agent_name: Filter by agent name (optional)
            
        Returns:
            Formatted insights
        """
        try:
            # Search memory for shared insights
            query = "shared insight"
            if category:
                query += f" {category}"
            if agent_name:
                query += f" {agent_name}"
            
            results = await self.memory_manager.search_memory(
                query=query,
                limit=20,
                min_relevance=0.5
            )
            
            # Filter results
            filtered_results = []
            for result in results:
                metadata = result.get("metadata", {})
                if metadata.get("type") != "shared_insight":
                    continue
                
                if category and metadata.get("category") != category:
                    continue
                
                if agent_name and metadata.get("agent_name") != agent_name:
                    continue
                
                filtered_results.append(result)
            
            if not filtered_results:
                filters = []
                if category:
                    filters.append(f"category='{category}'")
                if agent_name:
                    filters.append(f"agent='{agent_name}'")
                filter_text = " with " + ", ".join(filters) if filters else ""
                return f"No shared insights found{filter_text}"
            
            # Format results
            formatted_insights = ["Shared Insights:"]
            for i, result in enumerate(filtered_results, 1):
                metadata = result.get("metadata", {})
                agent = metadata.get("agent_name", "Unknown")
                cat = metadata.get("category", "general")
                
                formatted_insights.append(
                    f"\n{i}. [{agent}] ({cat}) "
                    f"[Relevance: {result['relevance']:.2f}]\n"
                    f"   {result['text']}"
                )
            
            return "\n".join(formatted_insights)
            
        except Exception as e:
            logger.error("Failed to get shared insights", error=str(e))
            return f"Error getting shared insights: {str(e)}"
    
    @kernel_function(name="request_collaboration", description="Request collaboration or input from other agents")
    async def request_collaboration(self, request: str, requesting_agent: str, target_category: str = "general") -> str:
        """
        Request collaboration or input from other agents.
        
        Args:
            request: The collaboration request
            requesting_agent: Name of the requesting agent
            target_category: Category for the request
            
        Returns:
            Confirmation message
        """
        try:
            # Store collaboration request
            metadata = {
                "requesting_agent": requesting_agent,
                "target_category": target_category,
                "type": "collaboration_request"
            }
            
            await self.memory_manager.store_research_context(
                context=f"Collaboration Request: {request}",
                metadata=metadata
            )
            
            logger.debug("Collaboration request submitted", agent=requesting_agent, category=target_category)
            return f"Collaboration request submitted by {requesting_agent} for category '{target_category}'"
            
        except Exception as e:
            logger.error("Failed to submit collaboration request", error=str(e))
            return f"Error submitting collaboration request: {str(e)}"
    
    @kernel_function(name="get_collaboration_requests", description="Get pending collaboration requests")
    async def get_collaboration_requests(self, category: Optional[str] = None) -> str:
        """
        Get pending collaboration requests.
        
        Args:
            category: Filter by category (optional)
            
        Returns:
            Formatted collaboration requests
        """
        try:
            # Search for collaboration requests
            query = "collaboration request"
            if category:
                query += f" {category}"
            
            results = await self.memory_manager.search_memory(
                query=query,
                collection=self.memory_manager.research_context_collection,
                limit=20,
                min_relevance=0.5
            )
            
            # Filter results
            filtered_results = []
            for result in results:
                metadata = result.get("metadata", {})
                if metadata.get("type") != "collaboration_request":
                    continue
                
                if category and metadata.get("target_category") != category:
                    continue
                
                filtered_results.append(result)
            
            if not filtered_results:
                filter_text = f" for category '{category}'" if category else ""
                return f"No pending collaboration requests found{filter_text}"
            
            # Format results
            formatted_requests = ["Collaboration Requests:"]
            for i, result in enumerate(filtered_results, 1):
                metadata = result.get("metadata", {})
                requesting_agent = metadata.get("requesting_agent", "Unknown")
                target_cat = metadata.get("target_category", "general")
                
                formatted_requests.append(
                    f"\n{i}. [{requesting_agent}] → {target_cat}\n"
                    f"   {result['text']}"
                )
            
            return "\n".join(formatted_requests)
            
        except Exception as e:
            logger.error("Failed to get collaboration requests", error=str(e))
            return f"Error getting collaboration requests: {str(e)}"
    
    @kernel_function(name="update_agent_status", description="Update agent status for coordination")
    async def update_agent_status(self, agent_name: str, status: str, current_task: str = "") -> str:
        """
        Update agent status for coordination.
        
        Args:
            agent_name: Name of the agent
            status: Current status (active, idle, completing, error)
            current_task: Description of current task
            
        Returns:
            Confirmation message
        """
        try:
            # Store in shared data for quick access
            self._shared_data[f"status_{agent_name}"] = {
                "agent_name": agent_name,
                "status": status,
                "current_task": current_task,
                "timestamp": self.memory_manager.session_id
            }
            
            # Also store in memory
            status_info = f"Agent {agent_name} status: {status}"
            if current_task:
                status_info += f" - Task: {current_task}"
            
            metadata = {
                "agent_name": agent_name,
                "status": status,
                "current_task": current_task,
                "type": "agent_status"
            }
            
            await self.memory_manager.store_research_context(
                context=status_info,
                metadata=metadata
            )
            
            logger.debug("Agent status updated", agent=agent_name, status=status)
            return f"Status updated for {agent_name}: {status}"
            
        except Exception as e:
            logger.error("Failed to update agent status", error=str(e))
            return f"Error updating agent status: {str(e)}"
    
    @kernel_function(name="get_agent_statuses", description="Get status of all agents")
    async def get_agent_statuses(self) -> str:
        """
        Get status of all agents.
        
        Returns:
            Formatted agent statuses
        """
        try:
            # Get statuses from shared data
            status_data = {k: v for k, v in self._shared_data.items() if k.startswith("status_")}
            
            if not status_data:
                return "No agent status information available"
            
            # Format statuses
            formatted_statuses = ["Agent Statuses:"]
            for key, data in status_data.items():
                agent_name = data.get("agent_name", "Unknown")
                status = data.get("status", "Unknown")
                current_task = data.get("current_task", "")
                
                status_line = f"  - {agent_name}: {status}"
                if current_task:
                    status_line += f" ({current_task})"
                
                formatted_statuses.append(status_line)
            
            return "\n".join(formatted_statuses)
            
        except Exception as e:
            logger.error("Failed to get agent statuses", error=str(e))
            return f"Error getting agent statuses: {str(e)}"
