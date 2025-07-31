"""
Session management for orchestration system.
Handles storing and retrieving detailed agent execution data.
"""

import os
import json
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
import structlog
from pathlib import Path

logger = structlog.get_logger(__name__)


class OrchestrationSessionManager:
    """
    Manages orchestration sessions with detailed agent execution tracking.
    """
    
    def __init__(self, sessions_dir: str = "sessions"):
        """
        Initialize the session manager.
        
        Args:
            sessions_dir: Directory to store session files
        """
        self.sessions_dir = Path(sessions_dir)
        self.metadata_file = self.sessions_dir / "sessions_orchestration_metadata.json"
        
        # Ensure sessions directory exists
        self.sessions_dir.mkdir(exist_ok=True)
        
        # Initialize metadata file if it doesn't exist
        if not self.metadata_file.exists():
            self._save_metadata({})
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load sessions metadata from file."""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error("Failed to load orchestration session metadata", error=str(e))
            return {}
    
    def _save_metadata(self, metadata: Dict[str, Any]) -> None:
        """Save sessions metadata to file."""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, default=str)
        except Exception as e:
            logger.error("Failed to save orchestration session metadata", error=str(e))
    
    def create_session(
        self, 
        session_id: str,
        query: str,
        project_id: str
    ) -> Dict[str, Any]:
        """
        Create a new orchestration session.
        
        Args:
            session_id: Unique session identifier
            query: Research query
            project_id: Project identifier
            
        Returns:
            Session data
        """
        try:
            session_data = {
                "session_id": session_id,
                "project_id": project_id,
                "query": query,
                "status": "initialized",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "agent_executions": [],
                "final_result": None,
                "metadata": {
                    "total_agents": 0,
                    "completed_agents": 0,
                    "failed_agents": 0,
                    "execution_time_seconds": 0
                }
            }
            
            # Save session data to individual file
            session_file = self.sessions_dir / f"orchestration_{session_id}.json"
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, default=str)
            
            # Update metadata
            metadata = self._load_metadata()
            metadata[session_id] = {
                "session_id": session_id,
                "project_id": project_id,
                "query": query[:100] + "..." if len(query) > 100 else query,
                "status": "initialized",
                "created_at": session_data["created_at"],
                "updated_at": session_data["updated_at"],
                "file_path": str(session_file)
            }
            self._save_metadata(metadata)
            
            logger.info("Orchestration session created", session_id=session_id)
            return session_data
            
        except Exception as e:
            logger.error("Failed to create orchestration session", session_id=session_id, error=str(e))
            raise
    
    def add_agent_execution(
        self,
        session_id: str,
        agent_name: str,
        input_data: str,
        output_data: str,
        metadata: Optional[Dict[str, Any]] = None,
        status: str = "completed",
        execution_time: Optional[float] = None
    ) -> None:
        """
        Add agent execution details to session.
        
        Args:
            session_id: Session identifier
            agent_name: Name of the agent
            input_data: Input provided to the agent
            output_data: Output from the agent
            metadata: Additional metadata
            status: Execution status (completed, failed, etc.)
            execution_time: Time taken for execution in seconds
        """
        try:
            session_data = self.get_session(session_id)
            if not session_data:
                logger.warning("Session not found for agent execution", session_id=session_id)
                return
            
            execution_record = {
                "agent_name": agent_name,
                "status": status,
                "input": input_data,
                "output": output_data,
                "metadata": metadata or {},
                "execution_time_seconds": execution_time,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            session_data["agent_executions"].append(execution_record)
            session_data["updated_at"] = datetime.utcnow().isoformat()
            
            # Update counters
            session_data["metadata"]["total_agents"] = len(session_data["agent_executions"])
            if status == "completed":
                session_data["metadata"]["completed_agents"] += 1
            elif status == "failed":
                session_data["metadata"]["failed_agents"] += 1
            
            if execution_time:
                session_data["metadata"]["execution_time_seconds"] += execution_time
            
            # Save updated session data
            session_file = self.sessions_dir / f"orchestration_{session_id}.json"
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, default=str)
            
            # Update metadata
            metadata = self._load_metadata()
            if session_id in metadata:
                metadata[session_id]["updated_at"] = session_data["updated_at"]
                self._save_metadata(metadata)
            
            logger.debug(
                "Agent execution recorded",
                session_id=session_id,
                agent_name=agent_name,
                status=status
            )
            
        except Exception as e:
            logger.error(
                "Failed to record agent execution",
                session_id=session_id,
                agent_name=agent_name,
                error=str(e)
            )
    
    def update_session_status(
        self,
        session_id: str,
        status: str,
        final_result: Optional[str] = None
    ) -> None:
        """
        Update session status and final result.
        
        Args:
            session_id: Session identifier
            status: New status
            final_result: Final research result if completed
        """
        try:
            session_data = self.get_session(session_id)
            if not session_data:
                logger.warning("Session not found for status update", session_id=session_id)
                return
            
            session_data["status"] = status
            session_data["updated_at"] = datetime.utcnow().isoformat()
            
            if final_result:
                session_data["final_result"] = final_result
            
            # Save updated session data
            session_file = self.sessions_dir / f"orchestration_{session_id}.json"
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, default=str)
            
            # Update metadata
            metadata = self._load_metadata()
            if session_id in metadata:
                metadata[session_id]["status"] = status
                metadata[session_id]["updated_at"] = session_data["updated_at"]
                self._save_metadata(metadata)
            
            logger.info("Session status updated", session_id=session_id, status=status)
            
        except Exception as e:
            logger.error(
                "Failed to update session status",
                session_id=session_id,
                error=str(e)
            )
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session data by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data or None if not found
        """
        try:
            session_file = self.sessions_dir / f"orchestration_{session_id}.json"
            if session_file.exists():
                with open(session_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        except Exception as e:
            logger.error("Failed to get session", session_id=session_id, error=str(e))
            return None
    
    def list_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        List recent sessions.
        
        Args:
            limit: Maximum number of sessions to return
            
        Returns:
            List of session metadata
        """
        try:
            metadata = self._load_metadata()
            sessions = list(metadata.values())
            
            # Sort by created_at descending
            sessions.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            
            return sessions[:limit]
        except Exception as e:
            logger.error("Failed to list sessions", error=str(e))
            return []
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session and its data.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted successfully
        """
        try:
            # Remove session file
            session_file = self.sessions_dir / f"orchestration_{session_id}.json"
            if session_file.exists():
                session_file.unlink()
            
            # Remove from metadata
            metadata = self._load_metadata()
            if session_id in metadata:
                del metadata[session_id]
                self._save_metadata(metadata)
            
            logger.info("Session deleted", session_id=session_id)
            return True
            
        except Exception as e:
            logger.error("Failed to delete session", session_id=session_id, error=str(e))
            return False
    
    def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session summary with execution statistics.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session summary or None if not found
        """
        try:
            session_data = self.get_session(session_id)
            if not session_data:
                return None
            
            return {
                "session_id": session_id,
                "project_id": session_data.get("project_id"),
                "status": session_data.get("status"),
                "query": session_data.get("query"),
                "created_at": session_data.get("created_at"),
                "updated_at": session_data.get("updated_at"),
                "agents_count": len(session_data.get("agent_executions", [])),
                "metadata": session_data.get("metadata", {}),
                "has_result": bool(session_data.get("final_result"))
            }
            
        except Exception as e:
            logger.error("Failed to get session summary", session_id=session_id, error=str(e))
            return None
