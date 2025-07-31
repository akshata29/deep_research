"""
Memory manager for managing research context and knowledge.
"""

import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
import structlog
from semantic_kernel.memory import SemanticTextMemory
from semantic_kernel.memory.volatile_memory_store import VolatileMemoryStore
from semantic_kernel.connectors.ai.open_ai import AzureTextEmbedding

logger = structlog.get_logger(__name__)


class MemoryManager:
    """
    Manages semantic memory for research context and knowledge persistence.
    """
    
    def __init__(
        self,
        embedding_generator: Any,
        session_id: str,
        project_id: str
    ):
        """
        Initialize memory manager.
        
        Args:
            embedding_generator: Text embedding service
            session_id: Unique session identifier
            project_id: Project identifier for context grouping
        """
        self.embedding_generator = embedding_generator
        self.session_id = session_id
        self.project_id = project_id
        self.memory: Optional[SemanticTextMemory] = None
        self.collections: Dict[str, str] = {}
        
        # Memory collection names
        self.research_context_collection = f"research_context_{session_id[:8]}"
        self.findings_collection = f"findings_{session_id[:8]}"
        self.sources_collection = f"sources_{session_id[:8]}"
        
    async def initialize(self) -> None:
        """Initialize the semantic memory system."""
        try:
            # Create volatile memory store (in production, use persistent store)
            memory_store = VolatileMemoryStore()
            
            # Initialize semantic memory
            self.memory = SemanticTextMemory(
                storage=memory_store,
                embeddings_generator=self.embedding_generator
            )
            
            # Create collections
            collections_to_create = [
                (self.research_context_collection, "Research context and task information"),
                (self.findings_collection, "Research findings and discoveries"),
                (self.sources_collection, "Source documents and references")
            ]
            
            for collection_name, description in collections_to_create:
                await self._create_collection(collection_name, description)
            
            logger.info(
                "Memory manager initialized",
                session_id=self.session_id,
                project_id=self.project_id,
                collections=list(self.collections.keys())
            )
            
        except Exception as e:
            logger.error("Failed to initialize memory manager", error=str(e))
            raise
    
    async def _create_collection(self, collection_name: str, description: str) -> None:
        """Create a memory collection."""
        try:
            if self.memory:
                # Create collection if it doesn't exist
                self.collections[collection_name] = description
                logger.debug("Memory collection ready", collection=collection_name)
        except Exception as e:
            logger.error("Failed to create memory collection", collection=collection_name, error=str(e))
            raise
    
    async def store_research_context(self, context: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Store research context information.
        
        Args:
            context: Research context text
            metadata: Additional metadata
            
        Returns:
            Memory ID
        """
        try:
            if not self.memory:
                raise RuntimeError("Memory not initialized")
            
            memory_id = str(uuid.uuid4())
            
            # Prepare metadata
            full_metadata = {
                "session_id": self.session_id,
                "project_id": self.project_id,
                "timestamp": datetime.utcnow().isoformat(),
                "type": "research_context",
                **(metadata or {})
            }
            
            # Store in memory
            await self.memory.save_information(
                collection=self.research_context_collection,
                text=context,
                id=memory_id,
                description="Research context",
                additional_metadata=full_metadata
            )
            
            logger.debug("Stored research context", memory_id=memory_id)
            return memory_id
            
        except Exception as e:
            logger.error("Failed to store research context", error=str(e))
            raise
    
    async def store_finding(self, finding: str, source: str, confidence: float, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Store a research finding.
        
        Args:
            finding: The research finding text
            source: Source of the finding
            confidence: Confidence score (0.0 to 1.0)
            metadata: Additional metadata
            
        Returns:
            Memory ID
        """
        try:
            if not self.memory:
                raise RuntimeError("Memory not initialized")
            
            memory_id = str(uuid.uuid4())
            
            # Prepare metadata
            full_metadata = {
                "session_id": self.session_id,
                "project_id": self.project_id,
                "timestamp": datetime.utcnow().isoformat(),
                "type": "finding",
                "source": source,
                "confidence": confidence,
                **(metadata or {})
            }
            
            # Store in memory
            await self.memory.save_information(
                collection=self.findings_collection,
                text=finding,
                id=memory_id,
                description=f"Finding from {source}",
                additional_metadata=full_metadata
            )
            
            logger.debug("Stored finding", memory_id=memory_id, source=source, confidence=confidence)
            return memory_id
            
        except Exception as e:
            logger.error("Failed to store finding", error=str(e))
            raise
    
    async def store_source(self, source_url: str, source_content: str, quality_score: float, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Store source information.
        
        Args:
            source_url: URL or identifier of the source
            source_content: Content or summary of the source
            quality_score: Quality assessment score (0.0 to 1.0)
            metadata: Additional metadata
            
        Returns:
            Memory ID
        """
        try:
            if not self.memory:
                raise RuntimeError("Memory not initialized")
            
            memory_id = str(uuid.uuid4())
            
            # Prepare metadata
            full_metadata = {
                "session_id": self.session_id,
                "project_id": self.project_id,
                "timestamp": datetime.utcnow().isoformat(),
                "type": "source",
                "url": source_url,
                "quality_score": quality_score,
                **(metadata or {})
            }
            
            # Store in memory
            await self.memory.save_information(
                collection=self.sources_collection,
                text=source_content,
                id=memory_id,
                description=f"Source: {source_url}",
                additional_metadata=full_metadata
            )
            
            logger.debug("Stored source", memory_id=memory_id, url=source_url, quality_score=quality_score)
            return memory_id
            
        except Exception as e:
            logger.error("Failed to store source", error=str(e))
            raise
    
    async def search_memory(self, query: str, collection: Optional[str] = None, limit: int = 10, min_relevance: float = 0.7) -> List[Dict[str, Any]]:
        """
        Search memory for relevant information.
        
        Args:
            query: Search query
            collection: Collection to search (if None, searches all)
            limit: Maximum results to return
            min_relevance: Minimum relevance score
            
        Returns:
            List of memory results
        """
        try:
            if not self.memory:
                raise RuntimeError("Memory not initialized")
            
            results = []
            collections_to_search = [collection] if collection else list(self.collections.keys())
            
            for collection_name in collections_to_search:
                try:
                    search_results = await self.memory.search(
                        collection=collection_name,
                        query=query,
                        limit=limit,
                        min_relevance_score=min_relevance
                    )
                    
                    for result in search_results:
                        results.append({
                            "collection": collection_name,
                            "id": result.id,
                            "text": result.text,
                            "relevance": result.relevance,
                            "metadata": result.additional_metadata
                        })
                        
                except Exception as e:
                    logger.warning("Failed to search collection", collection=collection_name, error=str(e))
                    continue
            
            # Sort by relevance
            results.sort(key=lambda x: x["relevance"], reverse=True)
            
            logger.debug("Memory search completed", query=query, results_count=len(results))
            return results[:limit]
            
        except Exception as e:
            logger.error("Failed to search memory", error=str(e))
            raise
    
    async def get_session_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current session's memory.
        
        Returns:
            Session summary statistics
        """
        try:
            if not self.memory:
                raise RuntimeError("Memory not initialized")
            
            summary = {
                "session_id": self.session_id,
                "project_id": self.project_id,
                "collections": {}
            }
            
            for collection_name in self.collections.keys():
                try:
                    # Get all items from collection (this is a simplified approach)
                    search_results = await self.memory.search(
                        collection=collection_name,
                        query="*",  # Search for everything
                        limit=1000,
                        min_relevance_score=0.0
                    )
                    
                    summary["collections"][collection_name] = {
                        "count": len(search_results),
                        "description": self.collections[collection_name]
                    }
                    
                except Exception as e:
                    logger.warning("Failed to get collection summary", collection=collection_name, error=str(e))
                    summary["collections"][collection_name] = {
                        "count": 0,
                        "description": self.collections[collection_name],
                        "error": str(e)
                    }
            
            return summary
            
        except Exception as e:
            logger.error("Failed to get session summary", error=str(e))
            raise
