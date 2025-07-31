"""
Modular search plugin that combines multiple search providers.
"""

from typing import List, Dict, Any, Optional
import structlog
from semantic_kernel.functions import kernel_function
from .web_search_provider import WebSearchProvider
from .azure_search_provider import AzureSearchProvider

logger = structlog.get_logger(__name__)


class ModularSearchPlugin:
    """
    Modular search plugin that combines internal document search and web search.
    """
    
    def __init__(
        self,
        azure_search_provider: Optional[AzureSearchProvider] = None,
        web_search_provider: Optional[WebSearchProvider] = None,
        prefer_internal: bool = True
    ):
        """
        Initialize modular search plugin.
        
        Args:
            azure_search_provider: Azure Search provider for internal documents
            web_search_provider: Web search provider for external search
            prefer_internal: Whether to prefer internal documents over web results
        """
        self.azure_search = azure_search_provider
        self.web_search = web_search_provider
        self.prefer_internal = prefer_internal
        
        logger.info(
            "ModularSearchPlugin initialized",
            azure_search_available=self.azure_search.is_available() if self.azure_search else False,
            web_search_available=self.web_search.is_available() if self.web_search else False
        )
    
    @kernel_function(name="search_documents", description="Search internal documents and web for information")
    async def search_documents(
        self,
        query: str,
        max_results: str = "10",
        include_web: str = "true",
        web_fallback: str = "true"
    ) -> str:
        """
        Search both internal documents and web for information.
        
        Args:
            query: Search query
            max_results: Maximum results as string
            include_web: Include web search as string boolean
            web_fallback: Use web search as fallback as string boolean
            
        Returns:
            Formatted search results
        """
        try:
            # Parse parameters
            try:
                max_results_int = int(max_results)
                max_results_int = max(1, min(50, max_results_int))
            except ValueError:
                max_results_int = 10
            
            include_web_bool = include_web.lower() in ("true", "1", "yes")
            web_fallback_bool = web_fallback.lower() in ("true", "1", "yes")
            
            all_results = []
            
            # Search internal documents first
            internal_results = []
            if self.azure_search and self.azure_search.is_available():
                try:
                    internal_results = await self.azure_search.search(
                        query=query,
                        top=max_results_int // 2 if include_web_bool else max_results_int
                    )
                    all_results.extend(internal_results)
                    logger.debug("Internal search completed", results_count=len(internal_results))
                except Exception as e:
                    logger.warning("Internal search failed", error=str(e))
            
            # Decide whether to search web
            should_search_web = False
            if include_web_bool:
                should_search_web = True
            elif web_fallback_bool and len(internal_results) < 3:
                should_search_web = True
                logger.info("Using web search as fallback due to limited internal results")
            
            # Search web if needed
            if should_search_web and self.web_search and self.web_search.is_available():
                try:
                    web_results = await self.web_search.search(
                        query=query,
                        max_results=max_results_int // 2 if internal_results else max_results_int
                    )
                    all_results.extend(web_results)
                    logger.debug("Web search completed", results_count=len(web_results))
                except Exception as e:
                    logger.warning("Web search failed", error=str(e))
            
            # Sort results by score and preference
            if self.prefer_internal:
                # Boost internal document scores
                for result in all_results:
                    if result.get("source", "").startswith("Internal"):
                        result["score"] = result.get("score", 0.0) * 1.2
            
            # Sort by score
            all_results.sort(key=lambda x: x.get("score", 0.0), reverse=True)
            
            # Limit results
            all_results = all_results[:max_results_int]
            
            if not all_results:
                return f"No results found for query: '{query}'"
            
            # Format results
            formatted_results = [f"Search Results for '{query}' ({len(all_results)} found):"]
            
            for i, result in enumerate(all_results, 1):
                title = result.get("title", "Untitled")
                content = result.get("content", "")
                url = result.get("url", "")
                score = result.get("score", 0.0)
                source = result.get("source", "Unknown")
                
                # Truncate content
                display_content = content[:300] + "..." if len(content) > 300 else content
                
                formatted_results.append(
                    f"\n{i}. [{source}] {title} (Score: {score:.2f})\n"
                    f"   {display_content}\n"
                    f"   URL: {url}" if url else ""
                )
            
            return "\n".join(formatted_results)
            
        except Exception as e:
            logger.error("Search failed", query=query, error=str(e))
            return f"Search error: {str(e)}"
    
    @kernel_function(name="search_internal_only", description="Search only internal documents")
    async def search_internal_only(self, query: str, max_results: str = "10") -> str:
        """
        Search only internal documents.
        
        Args:
            query: Search query
            max_results: Maximum results as string
            
        Returns:
            Formatted search results
        """
        try:
            if not self.azure_search or not self.azure_search.is_available():
                return "Internal document search is not available"
            
            # Parse max_results
            try:
                max_results_int = int(max_results)
                max_results_int = max(1, min(50, max_results_int))
            except ValueError:
                max_results_int = 10
            
            results = await self.azure_search.search(query=query, top=max_results_int)
            
            if not results:
                return f"No internal documents found for query: '{query}'"
            
            # Format results
            formatted_results = [f"Internal Document Results for '{query}' ({len(results)} found):"]
            
            for i, result in enumerate(results, 1):
                title = result.get("title", "Untitled")
                content = result.get("content", "")
                url = result.get("url", "")
                score = result.get("score", 0.0)
                
                # Truncate content
                display_content = content[:300] + "..." if len(content) > 300 else content
                
                formatted_results.append(
                    f"\n{i}. {title} (Score: {score:.2f})\n"
                    f"   {display_content}\n"
                    f"   URL: {url}" if url else ""
                )
            
            return "\n".join(formatted_results)
            
        except Exception as e:
            logger.error("Internal search failed", query=query, error=str(e))
            return f"Internal search error: {str(e)}"
    
    @kernel_function(name="search_web_only", description="Search only the web")
    async def search_web_only(self, query: str, max_results: str = "10") -> str:
        """
        Search only the web.
        
        Args:
            query: Search query
            max_results: Maximum results as string
            
        Returns:
            Formatted search results
        """
        try:
            if not self.web_search or not self.web_search.is_available():
                return "Web search is not available"
            
            # Parse max_results
            try:
                max_results_int = int(max_results)
                max_results_int = max(1, min(50, max_results_int))
            except ValueError:
                max_results_int = 10
            
            results = await self.web_search.search(query=query, max_results=max_results_int)
            
            if not results:
                return f"No web results found for query: '{query}'"
            
            # Format results
            formatted_results = [f"Web Search Results for '{query}' ({len(results)} found):"]
            
            for i, result in enumerate(results, 1):
                title = result.get("title", "Untitled")
                content = result.get("content", "")
                url = result.get("url", "")
                score = result.get("score", 0.0)
                result_type = result.get("type", "web_result")
                
                # Truncate content
                display_content = content[:300] + "..." if len(content) > 300 else content
                
                type_label = "AI Answer" if result_type == "answer" else "Web Result"
                
                formatted_results.append(
                    f"\n{i}. [{type_label}] {title} (Score: {score:.2f})\n"
                    f"   {display_content}\n"
                    f"   URL: {url}" if url else ""
                )
            
            return "\n".join(formatted_results)
            
        except Exception as e:
            logger.error("Web search failed", query=query, error=str(e))
            return f"Web search error: {str(e)}"
    
    @kernel_function(name="get_search_summary", description="Get a quick summary for a topic")
    async def get_search_summary(self, topic: str) -> str:
        """
        Get a quick summary for a topic.
        
        Args:
            topic: Topic to get summary for
            
        Returns:
            Summary text
        """
        try:
            # Try web search first for quick AI-generated answers
            if self.web_search and self.web_search.is_available():
                summary = await self.web_search.get_search_summary(topic)
                if summary:
                    return f"Summary for '{topic}':\n{summary}"
            
            # Fallback to regular search
            search_results = await self.search_documents(
                query=topic,
                max_results="5",
                include_web="true",
                web_fallback="true"
            )
            
            return f"Summary for '{topic}' (from search results):\n{search_results[:500]}..."
            
        except Exception as e:
            logger.error("Failed to get search summary", topic=topic, error=str(e))
            return f"Error getting summary for '{topic}': {str(e)}"
