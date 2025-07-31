"""
Multi-agent orchestration module for Deep Research.

This module provides the infrastructure for orchestrating multiple AI agents
using Semantic Kernel to perform comprehensive research tasks.
"""

from .deep_research_agent import DeepResearchAgent
from .agent_factory import create_agents_with_memory
from .memory import MemoryManager, MemoryPlugin, SharedMemoryPluginSK
from .config import OrchestrationConfig
from .search import ModularSearchPlugin

__all__ = [
    "DeepResearchAgent",
    "create_agents_with_memory", 
    "MemoryManager",
    "MemoryPlugin",
    "SharedMemoryPluginSK",
    "OrchestrationConfig",
    "ModularSearchPlugin"
]
