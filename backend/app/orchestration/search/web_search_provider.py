"""
Web search provider using Tavily API.
"""

from typing import List, Dict, Any, Optional
import structlog
import asyncio
from tavily import TavilyClient

logger = structlog.get_logger(__name__)


class WebSearchProvider:
    """
    Web search provider using Tavily API for external research.
    """
    
    def __init__(
        self,
        api_key: str,
        max_results: int = 10,
        max_retries: int = 3
    ):
        """
        Initialize web search provider.
        
        Args:
            api_key: Tavily API key
            max_results: Maximum search results
            max_retries: Maximum retry attempts
        """
        self.api_key = api_key
        self.max_results = max_results
        self.max_retries = max_retries
        self.client = TavilyClient(api_key=api_key) if api_key else None
        
        if not self.client:
            logger.warning("Tavily API key not provided, web search disabled")
    
    async def search(
        self,
        query: str,
        max_results: Optional[int] = None,
        include_answer: bool = True,
        include_raw_content: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Perform web search using Tavily.
        
        Args:
            query: Search query
            max_results: Maximum results (overrides default)
            include_answer: Include AI-generated answer
            include_raw_content: Include raw content
            
        Returns:
            List of search results
        """
        if not self.client:
            logger.warning("Web search not available (no API key)")
            return []
        
        try:
            max_results = max_results or self.max_results
            
            # Execute search with retry logic
            for attempt in range(self.max_retries):
                try:
                    # Run in thread pool since Tavily client is synchronous
                    loop = asyncio.get_event_loop()
                    response = await loop.run_in_executor(
                        None,
                        lambda: self.client.search(
                            query=query,
                            search_depth="advanced",
                            max_results=max_results,
                            include_answer=include_answer,
                            include_raw_content=include_raw_content
                        )
                    )
                    
                    # Process results
                    results = []
                    
                    # Add AI answer if available
                    if include_answer and response.get("answer"):
                        results.append({
                            "type": "answer",
                            "title": "AI-Generated Answer",
                            "content": response["answer"],
                            "url": "tavily://answer",
                            "score": 1.0,
                            "source": "Tavily AI"
                        })
                    
                    # Add search results
                    for item in response.get("results", []):
                        results.append({
                            "type": "web_result",
                            "title": item.get("title", ""),
                            "content": item.get("content", ""),
                            "url": item.get("url", ""),
                            "score": item.get("score", 0.0),
                            "source": "Web Search",
                            "published_date": item.get("published_date"),
                            "raw_content": item.get("raw_content") if include_raw_content else None
                        })
                    
                    logger.info(
                        "Web search completed",
                        query=query,
                        results_count=len(results),
                        attempt=attempt + 1
                    )
                    
                    return results
                    
                except Exception as e:
                    logger.warning(
                        "Web search attempt failed",
                        query=query,
                        attempt=attempt + 1,
                        error=str(e)
                    )
                    
                    if attempt == self.max_retries - 1:
                        raise
                    
                    # Wait before retry
                    await asyncio.sleep(2 ** attempt)
            
            return []
            
        except Exception as e:
            logger.error("Web search failed", query=query, error=str(e))
            return []
    
    async def get_search_summary(self, query: str) -> Optional[str]:
        """
        Get a quick search summary for a query.
        
        Args:
            query: Search query
            
        Returns:
            Summary text or None
        """
        try:
            results = await self.search(
                query=query,
                max_results=5,
                include_answer=True,
                include_raw_content=False
            )
            
            # Look for AI answer first
            for result in results:
                if result.get("type") == "answer":
                    return result.get("content")
            
            # Fallback to first result content
            for result in results:
                if result.get("type") == "web_result" and result.get("content"):
                    return result["content"][:500] + "..." if len(result["content"]) > 500 else result["content"]
            
            return None
            
        except Exception as e:
            logger.error("Failed to get search summary", query=query, error=str(e))
            return None
    
    def is_available(self) -> bool:
        """Check if web search is available."""
        return self.client is not None
