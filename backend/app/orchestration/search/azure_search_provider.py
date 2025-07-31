"""
Azure Search provider for internal document search.
"""

from typing import List, Dict, Any, Optional
import structlog
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import AzureError

logger = structlog.get_logger(__name__)


class AzureSearchProvider:
    """
    Azure Search provider for searching internal documents.
    """
    
    def __init__(
        self,
        endpoint: str,
        api_key: Optional[str] = None,
        index_name: str = "documents",
        use_managed_identity: bool = False
    ):
        """
        Initialize Azure Search provider.
        
        Args:
            endpoint: Azure Search endpoint
            api_key: Azure Search API key (if not using managed identity)
            index_name: Search index name
            use_managed_identity: Use managed identity for authentication
        """
        self.endpoint = endpoint
        self.index_name = index_name
        self.use_managed_identity = use_managed_identity
        
        # Initialize search client
        try:
            if use_managed_identity:
                credential = DefaultAzureCredential()
                self.search_client = SearchClient(
                    endpoint=endpoint,
                    index_name=index_name,
                    credential=credential
                )
                logger.info("Azure Search client initialized with managed identity")
            elif api_key:
                credential = AzureKeyCredential(api_key)
                self.search_client = SearchClient(
                    endpoint=endpoint,
                    index_name=index_name,
                    credential=credential
                )
                logger.info("Azure Search client initialized with API key")
            else:
                self.search_client = None
                logger.warning("Azure Search not configured (no credentials provided)")
                
        except Exception as e:
            logger.error("Failed to initialize Azure Search client", error=str(e))
            self.search_client = None
    
    async def search(
        self,
        query: str,
        top: int = 10,
        search_mode: str = "any",
        query_type: str = "semantic",
        semantic_configuration: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search Azure Search index.
        
        Args:
            query: Search query
            top: Number of results to return
            search_mode: Search mode (any, all)
            query_type: Query type (simple, full, semantic)
            semantic_configuration: Semantic configuration name
            
        Returns:
            List of search results
        """
        if not self.search_client:
            logger.warning("Azure Search not available")
            return []
        
        try:
            # Prepare search parameters
            search_params = {
                "search_text": query,
                "top": top,
                "search_mode": search_mode,
                "include_total_count": True
            }
            
            # Add semantic search configuration if available
            if query_type == "semantic" and semantic_configuration:
                search_params["query_type"] = query_type
                search_params["semantic_configuration_name"] = semantic_configuration
            
            # Execute search
            search_results = self.search_client.search(**search_params)
            
            # Process results
            results = []
            for result in search_results:
                # Extract common fields
                processed_result = {
                    "type": "document_result",
                    "title": result.get("title", result.get("name", "Untitled")),
                    "content": result.get("content", result.get("text", "")),
                    "url": result.get("url", result.get("path", "")),
                    "score": result.get("@search.score", 0.0),
                    "source": "Internal Documents",
                    "metadata": {}
                }
                
                # Add semantic information if available
                if hasattr(result, "@search.captions"):
                    captions = getattr(result, "@search.captions", [])
                    if captions:
                        processed_result["captions"] = [
                            {
                                "text": caption.text,
                                "highlights": caption.highlights
                            }
                            for caption in captions
                        ]
                
                # Add additional metadata
                for key, value in result.items():
                    if not key.startswith("@") and key not in ["title", "content", "url", "name", "text", "path"]:
                        processed_result["metadata"][key] = value
                
                results.append(processed_result)
            
            logger.info(
                "Azure Search completed",
                query=query,
                results_count=len(results),
                index=self.index_name
            )
            
            return results
            
        except AzureError as e:
            logger.error("Azure Search API error", query=query, error=str(e))
            return []
        except Exception as e:
            logger.error("Azure Search failed", query=query, error=str(e))
            return []
    
    async def search_multiple_indexes(
        self,
        query: str,
        index_configs: List[Dict[str, Any]],
        top_per_index: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search multiple Azure Search indexes.
        
        Args:
            query: Search query
            index_configs: List of index configurations
            top_per_index: Results per index
            
        Returns:
            Combined search results
        """
        all_results = []
        
        for config in index_configs:
            if not config.get("enabled", True):
                continue
                
            index_name = config.get("index_name")
            if not index_name:
                continue
                
            try:
                # Create client for this index
                if self.use_managed_identity:
                    credential = DefaultAzureCredential()
                else:
                    credential = AzureKeyCredential(config.get("api_key", ""))
                
                search_client = SearchClient(
                    endpoint=self.endpoint,
                    index_name=index_name,
                    credential=credential
                )
                
                # Search this index
                search_results = search_client.search(
                    search_text=query,
                    top=top_per_index,
                    include_total_count=True
                )
                
                # Process results
                for result in search_results:
                    processed_result = {
                        "type": "document_result",
                        "title": result.get("title", result.get("name", "Untitled")),
                        "content": result.get("content", result.get("text", "")),
                        "url": result.get("url", result.get("path", "")),
                        "score": result.get("@search.score", 0.0),
                        "source": f"Internal Documents ({config.get('description', index_name)})",
                        "index_name": index_name,
                        "metadata": {k: v for k, v in result.items() if not k.startswith("@")}
                    }
                    all_results.append(processed_result)
                
                logger.debug(
                    "Searched index",
                    query=query,
                    index=index_name,
                    results_count=len(list(search_results))
                )
                
            except Exception as e:
                logger.warning(
                    "Failed to search index",
                    query=query,
                    index=index_name,
                    error=str(e)
                )
                continue
        
        # Sort by score
        all_results.sort(key=lambda x: x["score"], reverse=True)
        
        logger.info(
            "Multi-index search completed",
            query=query,
            total_results=len(all_results),
            indexes_searched=len([c for c in index_configs if c.get("enabled", True)])
        )
        
        return all_results
    
    def is_available(self) -> bool:
        """Check if Azure Search is available."""
        return self.search_client is not None
