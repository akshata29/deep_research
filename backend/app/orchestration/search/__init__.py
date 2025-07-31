"""
Search plugins for multi-agent orchestration.
"""

from .modular_search_plugin import ModularSearchPlugin
from .web_search_provider import WebSearchProvider
from .azure_search_provider import AzureSearchProvider

__all__ = [
    "ModularSearchPlugin",
    "WebSearchProvider", 
    "AzureSearchProvider"
]
