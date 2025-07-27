"""
Web Search Service for Deep Research application.

This service integrates with Bing Search API through Azure AI Foundry
to provide real-time web grounding for research tasks.

Features:
- Bing Web Search integration
- Result filtering and ranking
- Content extraction and summarization
- Rate limiting and error handling
"""

import asyncio
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse

import httpx
import structlog
from azure.core.exceptions import AzureError

from app.core.azure_config import AzureServiceManager


logger = structlog.get_logger(__name__)


class WebSearchService:
    """
    Service for conducting web searches using Bing Search API.
    
    Provides comprehensive web search capabilities with:
    - Query optimization
    - Result filtering and ranking
    - Content processing
    - Rate limiting
    """
    
    def __init__(self, azure_manager: AzureServiceManager):
        """
        Initialize Web Search Service.
        
        Args:
            azure_manager: Azure service manager instance
        """
        self.azure_manager = azure_manager
        self.bing_endpoint = "https://api.bing.microsoft.com/v7.0/search"
        
        # Rate limiting
        self.requests_per_minute = 60
        self.request_times: List[datetime] = []
        
        # HTTP client configuration
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
        
        # Search configuration
        self.default_market = "en-US"
        self.safe_search = "Moderate"
        self.response_filter = ["Webpages"]
        
        # Content filtering
        self.excluded_domains = {
            "facebook.com", "twitter.com", "instagram.com", "tiktok.com",
            "reddit.com", "pinterest.com", "youtube.com"
        }
        
        self.preferred_domains = {
            "gov", "edu", "org", "reuters.com", "bloomberg.com",
            "wsj.com", "ft.com", "economist.com", "nature.com", "science.org"
        }
    
    async def search(
        self,
        query: str,
        max_results: int = 10,
        market: Optional[str] = None,
        freshness: Optional[str] = None,
        safe_search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform web search with Bing API.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            market: Market/region for search (e.g., "en-US")
            freshness: Freshness filter ("Day", "Week", "Month")
            safe_search: Safe search setting ("Off", "Moderate", "Strict")
            
        Returns:
            List of search results with metadata
        """
        try:
            # Check rate limiting
            await self._check_rate_limit()
            
            # Get Bing API key from Key Vault
            api_key = await self.azure_manager.get_secret("bing-search-key")
            if not api_key:
                raise AzureError("Bing Search API key not found in Key Vault")
            
            logger.info(
                "Performing web search",
                query=query[:100] + "..." if len(query) > 100 else query,
                max_results=max_results,
                market=market or self.default_market
            )
            
            # Prepare search parameters
            params = {
                "q": self._optimize_query(query),
                "count": min(max_results, 50),  # Bing API limit
                "offset": 0,
                "mkt": market or self.default_market,
                "safeSearch": safe_search or self.safe_search,
                "responseFilter": ",".join(self.response_filter),
                "textDecorations": False,
                "textFormat": "HTML"
            }
            
            # Add freshness filter if specified
            if freshness:
                params["freshness"] = freshness
            
            # Prepare headers
            headers = {
                "Ocp-Apim-Subscription-Key": api_key,
                "User-Agent": "DeepResearch/1.0 (Azure AI Research Assistant)",
                "Accept": "application/json",
                "Accept-Language": "en-US,en;q=0.9"
            }
            
            # Make the search request
            response = await self.http_client.get(
                self.bing_endpoint,
                params=params,
                headers=headers
            )
            
            # Check response status
            if response.status_code != 200:
                logger.error(
                    "Bing Search API error",
                    status_code=response.status_code,
                    response=response.text[:500]
                )
                raise AzureError(f"Bing Search API returned status {response.status_code}")
            
            # Parse response
            search_data = response.json()
            
            # Process search results
            results = await self._process_search_results(search_data, query)
            
            # Update rate limiting tracker
            self.request_times.append(datetime.utcnow())
            
            logger.info(
                "Web search completed",
                query=query[:50] + "..." if len(query) > 50 else query,
                results_count=len(results)
            )
            
            return results
            
        except httpx.TimeoutException:
            logger.error("Search request timed out", query=query)
            raise AzureError("Search request timed out")
        except httpx.RequestError as e:
            logger.error("Search request failed", query=query, error=str(e))
            raise AzureError(f"Search request failed: {str(e)}")
        except Exception as e:
            logger.error("Web search failed", query=query, error=str(e), exc_info=True)
            raise AzureError(f"Web search failed: {str(e)}")
    
    async def search_news(
        self,
        query: str,
        max_results: int = 10,
        category: Optional[str] = None,
        sort_by: str = "Date"
    ) -> List[Dict[str, Any]]:
        """
        Search for news articles using Bing News API.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            category: News category filter
            sort_by: Sort order ("Date", "Relevance")
            
        Returns:
            List of news articles with metadata
        """
        try:
            # Check rate limiting
            await self._check_rate_limit()
            
            # Get API key
            api_key = await self.azure_manager.get_secret("bing-search-key")
            if not api_key:
                raise AzureError("Bing Search API key not found")
            
            # Use Bing News endpoint
            news_endpoint = "https://api.bing.microsoft.com/v7.0/news/search"
            
            # Prepare parameters
            params = {
                "q": query,
                "count": min(max_results, 50),
                "mkt": self.default_market,
                "sortBy": sort_by,
                "textFormat": "HTML"
            }
            
            if category:
                params["category"] = category
            
            # Prepare headers
            headers = {
                "Ocp-Apim-Subscription-Key": api_key,
                "User-Agent": "DeepResearch/1.0 (Azure AI Research Assistant)",
                "Accept": "application/json"
            }
            
            # Make request
            response = await self.http_client.get(
                news_endpoint,
                params=params,
                headers=headers
            )
            
            if response.status_code != 200:
                raise AzureError(f"Bing News API returned status {response.status_code}")
            
            # Process news results
            news_data = response.json()
            results = await self._process_news_results(news_data, query)
            
            # Update rate limiting
            self.request_times.append(datetime.utcnow())
            
            logger.info("News search completed", query=query, results_count=len(results))
            
            return results
            
        except Exception as e:
            logger.error("News search failed", query=query, error=str(e), exc_info=True)
            raise AzureError(f"News search failed: {str(e)}")
    
    async def _process_search_results(
        self,
        search_data: Dict[str, Any],
        original_query: str
    ) -> List[Dict[str, Any]]:
        """
        Process and filter search results from Bing API response.
        
        Args:
            search_data: Raw Bing API response
            original_query: Original search query for relevance scoring
            
        Returns:
            Processed and filtered search results
        """
        results = []
        
        # Extract webpages from response
        webpages = search_data.get("webPages", {}).get("value", [])
        
        for webpage in webpages:
            try:
                # Extract basic information
                title = webpage.get("name", "")
                url = webpage.get("url", "")
                snippet = webpage.get("snippet", "")
                display_url = webpage.get("displayUrl", "")
                
                # Skip if missing essential data
                if not title or not url or not snippet:
                    continue
                
                # Parse domain
                parsed_url = urlparse(url)
                domain = parsed_url.netloc.lower()
                
                # Filter out excluded domains
                if any(excluded in domain for excluded in self.excluded_domains):
                    continue
                
                # Calculate relevance score
                relevance_score = self._calculate_relevance_score(
                    title, snippet, original_query, domain
                )
                
                # Extract published date if available
                published_date = None
                date_published = webpage.get("datePublished")
                if date_published:
                    try:
                        published_date = datetime.fromisoformat(date_published.replace("Z", "+00:00"))
                    except ValueError:
                        pass
                
                # Create result object
                result = {
                    "title": self._clean_text(title),
                    "url": url,
                    "snippet": self._clean_text(snippet),
                    "display_url": display_url,
                    "domain": domain,
                    "relevance_score": relevance_score,
                    "published_date": published_date,
                    "language": webpage.get("language", "en"),
                    "source_type": "web"
                }
                
                results.append(result)
                
            except Exception as e:
                logger.warning("Failed to process search result", error=str(e))
                continue
        
        # Sort by relevance score
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return results
    
    async def _process_news_results(
        self,
        news_data: Dict[str, Any],
        original_query: str
    ) -> List[Dict[str, Any]]:
        """Process news search results."""
        results = []
        
        news_articles = news_data.get("value", [])
        
        for article in news_articles:
            try:
                title = article.get("name", "")
                url = article.get("url", "")
                description = article.get("description", "")
                
                if not title or not url:
                    continue
                
                # Parse domain
                parsed_url = urlparse(url)
                domain = parsed_url.netloc.lower()
                
                # Extract published date
                published_date = None
                date_published = article.get("datePublished")
                if date_published:
                    try:
                        published_date = datetime.fromisoformat(date_published.replace("Z", "+00:00"))
                    except ValueError:
                        pass
                
                # Calculate relevance
                relevance_score = self._calculate_relevance_score(
                    title, description, original_query, domain
                )
                
                result = {
                    "title": self._clean_text(title),
                    "url": url,
                    "snippet": self._clean_text(description),
                    "domain": domain,
                    "relevance_score": relevance_score,
                    "published_date": published_date,
                    "source_type": "news",
                    "provider": article.get("provider", [{}])[0].get("name", "Unknown")
                }
                
                results.append(result)
                
            except Exception as e:
                logger.warning("Failed to process news result", error=str(e))
                continue
        
        # Sort by relevance and recency
        results.sort(key=lambda x: (x["relevance_score"], x.get("published_date") or datetime.min), reverse=True)
        
        return results
    
    def _optimize_query(self, query: str) -> str:
        """
        Optimize search query for better results.
        
        Args:
            query: Original query
            
        Returns:
            Optimized query string
        """
        # Remove excessive whitespace
        query = re.sub(r'\s+', ' ', query.strip())
        
        # Add quotes for exact phrases if needed
        if len(query.split()) > 3 and '"' not in query:
            # Check if it's a question or specific phrase
            question_words = ["what", "how", "why", "when", "where", "who"]
            if any(query.lower().startswith(word) for word in question_words):
                return query
            
            # For compound terms, add quotes around the main concept
            words = query.split()
            if len(words) > 2:
                # Try to identify the main concept (usually first 2-3 words)
                main_concept = " ".join(words[:2])
                rest = " ".join(words[2:])
                return f'"{main_concept}" {rest}'
        
        return query
    
    def _calculate_relevance_score(
        self,
        title: str,
        snippet: str,
        query: str,
        domain: str
    ) -> float:
        """
        Calculate relevance score for a search result.
        
        Args:
            title: Result title
            snippet: Result snippet
            query: Original query
            domain: Source domain
            
        Returns:
            Relevance score between 0.0 and 1.0
        """
        score = 0.0
        query_lower = query.lower()
        title_lower = title.lower()
        snippet_lower = snippet.lower()
        
        # Query term matching in title (high weight)
        query_words = query_lower.split()
        title_words = title_lower.split()
        
        title_matches = sum(1 for word in query_words if word in title_lower)
        title_score = (title_matches / len(query_words)) * 0.4
        score += title_score
        
        # Query term matching in snippet (medium weight)
        snippet_matches = sum(1 for word in query_words if word in snippet_lower)
        snippet_score = (snippet_matches / len(query_words)) * 0.3
        score += snippet_score
        
        # Domain authority bonus
        if any(preferred in domain for preferred in self.preferred_domains):
            score += 0.2
        elif domain.endswith('.gov') or domain.endswith('.edu'):
            score += 0.15
        elif domain.endswith('.org'):
            score += 0.1
        
        # Content quality indicators
        if len(snippet) > 100:  # Substantial content
            score += 0.05
        
        if any(indicator in snippet_lower for indicator in ['study', 'research', 'analysis', 'report']):
            score += 0.05
        
        # Exact phrase matching bonus
        if query_lower in title_lower:
            score += 0.1
        elif query_lower in snippet_lower:
            score += 0.05
        
        return min(score, 1.0)
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text content.
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Decode HTML entities
        html_entities = {
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&#39;': "'",
            '&nbsp;': ' '
        }
        
        for entity, char in html_entities.items():
            text = text.replace(entity, char)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    async def _check_rate_limit(self) -> None:
        """Check and enforce rate limiting."""
        now = datetime.utcnow()
        
        # Remove requests older than 1 minute
        cutoff_time = now - timedelta(minutes=1)
        self.request_times = [
            req_time for req_time in self.request_times
            if req_time > cutoff_time
        ]
        
        # Check if we're at the rate limit
        if len(self.request_times) >= self.requests_per_minute:
            # Calculate wait time
            oldest_request = min(self.request_times)
            wait_time = 60 - (now - oldest_request).total_seconds()
            
            if wait_time > 0:
                logger.info(f"Rate limit reached, waiting {wait_time:.1f} seconds")
                await asyncio.sleep(wait_time)
    
    async def get_search_suggestions(self, query: str) -> List[str]:
        """
        Get search suggestions for a query.
        
        Args:
            query: Partial query
            
        Returns:
            List of suggested queries
        """
        try:
            api_key = await self.azure_manager.get_secret("bing-search-key")
            if not api_key:
                return []
            
            suggestions_endpoint = "https://api.bing.microsoft.com/v7.0/suggestions"
            
            params = {
                "q": query,
                "mkt": self.default_market
            }
            
            headers = {
                "Ocp-Apim-Subscription-Key": api_key,
                "User-Agent": "DeepResearch/1.0",
                "Accept": "application/json"
            }
            
            response = await self.http_client.get(
                suggestions_endpoint,
                params=params,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                suggestion_groups = data.get("suggestionGroups", [])
                
                suggestions = []
                for group in suggestion_groups:
                    for suggestion in group.get("searchSuggestions", []):
                        suggestions.append(suggestion.get("query", ""))
                
                return suggestions[:10]  # Limit to 10 suggestions
            
            return []
            
        except Exception as e:
            logger.error("Failed to get search suggestions", query=query, error=str(e))
            return []
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        await self.http_client.aclose()
        logger.info("Web search service cleaned up")
