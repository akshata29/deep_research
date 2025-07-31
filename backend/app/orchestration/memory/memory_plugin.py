"""
Memory plugin for Semantic Kernel agents.
"""

from typing import Any, Dict, List, Optional
import structlog
from semantic_kernel.functions import kernel_function
from semantic_kernel.functions.kernel_arguments import KernelArguments
from .memory_manager import MemoryManager

logger = structlog.get_logger(__name__)


class MemoryPlugin:
    """
    Semantic Kernel plugin for memory operations.
    """
    
    def __init__(self, memory_manager: MemoryManager):
        """
        Initialize the memory plugin.
        
        Args:
            memory_manager: The memory manager instance
        """
        self.memory_manager = memory_manager
    
    @kernel_function(name="store_research_context", description="Store research context information")
    async def store_research_context(self, context: str, metadata: Optional[str] = None) -> str:
        """
        Store research context information.
        
        Args:
            context: Research context text
            metadata: Optional JSON string of metadata
            
        Returns:
            Memory ID as string
        """
        try:
            # Parse metadata if provided
            parsed_metadata = None
            if metadata:
                import json
                try:
                    parsed_metadata = json.loads(metadata)
                except json.JSONDecodeError:
                    logger.warning("Invalid metadata JSON, ignoring", metadata=metadata)
            
            memory_id = await self.memory_manager.store_research_context(context, parsed_metadata)
            return f"Stored research context with ID: {memory_id}"
            
        except Exception as e:
            logger.error("Failed to store research context", error=str(e))
            return f"Error storing research context: {str(e)}"
    
    @kernel_function(name="store_finding", description="Store a research finding")
    async def store_finding(
        self, 
        finding: str, 
        source: str, 
        confidence: str = "0.8",
        metadata: Optional[str] = None
    ) -> str:
        """
        Store a research finding.
        
        Args:
            finding: The research finding text
            source: Source of the finding
            confidence: Confidence score as string (0.0 to 1.0)
            metadata: Optional JSON string of metadata
            
        Returns:
            Status message
        """
        try:
            # Parse confidence
            try:
                confidence_float = float(confidence)
                confidence_float = max(0.0, min(1.0, confidence_float))  # Clamp to [0, 1]
            except ValueError:
                confidence_float = 0.8
                logger.warning("Invalid confidence value, using default", confidence=confidence)
            
            # Parse metadata if provided
            parsed_metadata = None
            if metadata:
                import json
                try:
                    parsed_metadata = json.loads(metadata)
                except json.JSONDecodeError:
                    logger.warning("Invalid metadata JSON, ignoring", metadata=metadata)
            
            memory_id = await self.memory_manager.store_finding(finding, source, confidence_float, parsed_metadata)
            return f"Stored finding with ID: {memory_id} (confidence: {confidence_float})"
            
        except Exception as e:
            logger.error("Failed to store finding", error=str(e))
            return f"Error storing finding: {str(e)}"
    
    @kernel_function(name="store_source", description="Store source information")
    async def store_source(
        self,
        source_url: str,
        source_content: str,
        quality_score: str = "0.8",
        metadata: Optional[str] = None
    ) -> str:
        """
        Store source information.
        
        Args:
            source_url: URL or identifier of the source
            source_content: Content or summary of the source
            quality_score: Quality assessment score as string (0.0 to 1.0)
            metadata: Optional JSON string of metadata
            
        Returns:
            Status message
        """
        try:
            # Parse quality score
            try:
                quality_float = float(quality_score)
                quality_float = max(0.0, min(1.0, quality_float))  # Clamp to [0, 1]
            except ValueError:
                quality_float = 0.8
                logger.warning("Invalid quality score, using default", quality_score=quality_score)
            
            # Parse metadata if provided
            parsed_metadata = None
            if metadata:
                import json
                try:
                    parsed_metadata = json.loads(metadata)
                except json.JSONDecodeError:
                    logger.warning("Invalid metadata JSON, ignoring", metadata=metadata)
            
            memory_id = await self.memory_manager.store_source(source_url, source_content, quality_float, parsed_metadata)
            return f"Stored source with ID: {memory_id} (quality: {quality_float})"
            
        except Exception as e:
            logger.error("Failed to store source", error=str(e))
            return f"Error storing source: {str(e)}"
    
    @kernel_function(name="search_memory", description="Search memory for relevant information")
    async def search_memory(
        self,
        query: str,
        collection: Optional[str] = None,
        limit: str = "10",
        min_relevance: str = "0.7"
    ) -> str:
        """
        Search memory for relevant information.
        
        Args:
            query: Search query
            collection: Collection to search (optional)
            limit: Maximum results as string
            min_relevance: Minimum relevance score as string
            
        Returns:
            Formatted search results
        """
        try:
            # Parse parameters
            try:
                limit_int = int(limit)
                limit_int = max(1, min(100, limit_int))  # Clamp to [1, 100]
            except ValueError:
                limit_int = 10
                logger.warning("Invalid limit value, using default", limit=limit)
            
            try:
                min_relevance_float = float(min_relevance)
                min_relevance_float = max(0.0, min(1.0, min_relevance_float))  # Clamp to [0, 1]
            except ValueError:
                min_relevance_float = 0.7
                logger.warning("Invalid min_relevance value, using default", min_relevance=min_relevance)
            
            results = await self.memory_manager.search_memory(
                query=query,
                collection=collection,
                limit=limit_int,
                min_relevance=min_relevance_float
            )
            
            if not results:
                return f"No relevant information found for query: {query}"
            
            # Format results
            formatted_results = [f"Search Results for '{query}' ({len(results)} found):"]
            
            for i, result in enumerate(results, 1):
                formatted_results.append(
                    f"\n{i}. [Relevance: {result['relevance']:.2f}] "
                    f"Collection: {result['collection']}\n"
                    f"   {result['text'][:200]}{'...' if len(result['text']) > 200 else ''}"
                )
            
            return "\n".join(formatted_results)
            
        except Exception as e:
            logger.error("Failed to search memory", error=str(e))
            return f"Error searching memory: {str(e)}"
    
    @kernel_function(name="get_session_summary", description="Get summary of current research session")
    async def get_session_summary(self) -> str:
        """
        Get a summary of the current session's memory.
        
        Returns:
            Formatted session summary
        """
        try:
            summary = await self.memory_manager.get_session_summary()
            
            formatted_summary = [
                f"Session Summary:",
                f"Session ID: {summary['session_id']}",
                f"Project ID: {summary['project_id']}",
                f"\nMemory Collections:"
            ]
            
            for collection_name, info in summary["collections"].items():
                formatted_summary.append(
                    f"  - {collection_name}: {info['count']} items ({info['description']})"
                )
            
            return "\n".join(formatted_summary)
            
        except Exception as e:
            logger.error("Failed to get session summary", error=str(e))
            return f"Error getting session summary: {str(e)}"
