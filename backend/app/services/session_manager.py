"""
Research Session Manager for Deep Research application.

Handles persistence, retrieval, and management of research sessions
including complete pipeline state and restoration capabilities.
"""

import json
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

import structlog
from app.models.schemas import (
    ResearchSession, SessionPhase, SearchTask, SessionListResponse,
    SessionCreateRequest, SessionUpdateRequest, SessionRestoreRequest,
    ResearchRequest
)

logger = structlog.get_logger(__name__)


class SessionManager:
    """Manages research session persistence and operations."""
    
    def __init__(self, sessions_dir: str = "sessions"):
        """
        Initialize the session manager.
        
        Args:
            sessions_dir: Directory to store session files
        """
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(exist_ok=True)
        self.sessions_file = self.sessions_dir / "sessions_metadata.json"
        self._ensure_sessions_file()
    
    def _ensure_sessions_file(self) -> None:
        """Ensure the sessions metadata file exists."""
        if not self.sessions_file.exists():
            self._save_sessions_data([])
    
    def _load_sessions_data(self) -> List[Dict[str, Any]]:
        """Load sessions data from JSON file."""
        try:
            if self.sessions_file.exists():
                with open(self.sessions_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            logger.error("Failed to load sessions data", error=str(e))
            return []
    
    def _save_sessions_data(self, sessions_data: List[Dict[str, Any]]) -> None:
        """Save sessions data to JSON file."""
        try:
            with open(self.sessions_file, 'w', encoding='utf-8') as f:
                json.dump(sessions_data, f, indent=2, default=str)
        except Exception as e:
            logger.error("Failed to save sessions data", error=str(e))
            raise
    
    def create_session(self, request: SessionCreateRequest) -> ResearchSession:
        """
        Create a new research session.
        
        Args:
            request: Session creation request
            
        Returns:
            Created research session
        """
        try:
            session_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            session = ResearchSession(
                session_id=session_id,
                created_at=now,
                updated_at=now,
                title=request.title,
                description=request.description,
                topic=request.topic,
                tags=request.tags,
                current_phase=SessionPhase.TOPIC if not request.topic else SessionPhase.QUESTIONS
            )
            
            # Save session to storage
            sessions_data = self._load_sessions_data()
            sessions_data.append(session.dict())
            self._save_sessions_data(sessions_data)
            
            logger.info("Research session created", session_id=session_id, title=request.title)
            return session
            
        except Exception as e:
            logger.error("Failed to create session", error=str(e))
            raise
    
    def get_session(self, session_id: str) -> Optional[ResearchSession]:
        """
        Get a specific research session by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Research session if found, None otherwise
        """
        try:
            sessions_data = self._load_sessions_data()
            for session_data in sessions_data:
                if session_data.get("session_id") == session_id:
                    return ResearchSession(**session_data)
            return None
            
        except Exception as e:
            logger.error("Failed to get session", session_id=session_id, error=str(e))
            return None
    
    def update_session(self, session_id: str, updates: SessionUpdateRequest) -> Optional[ResearchSession]:
        """
        Update an existing research session.
        
        Args:
            session_id: Session identifier
            updates: Updates to apply
            
        Returns:
            Updated session if successful, None otherwise
        """
        try:
            sessions_data = self._load_sessions_data()
            
            for i, session_data in enumerate(sessions_data):
                if session_data.get("session_id") == session_id:
                    # Apply updates
                    if updates.title is not None:
                        session_data["title"] = updates.title
                    if updates.description is not None:
                        session_data["description"] = updates.description
                    if updates.tags is not None:
                        session_data["tags"] = updates.tags
                    if updates.notes is not None:
                        session_data["notes"] = updates.notes
                    if updates.status is not None:
                        session_data["status"] = updates.status
                    
                    session_data["updated_at"] = datetime.utcnow().isoformat()
                    
                    # Save updated data
                    self._save_sessions_data(sessions_data)
                    
                    logger.info("Session updated", session_id=session_id)
                    return ResearchSession(**session_data)
            
            return None
            
        except Exception as e:
            logger.error("Failed to update session", session_id=session_id, error=str(e))
            return None
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a research session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            sessions_data = self._load_sessions_data()
            original_count = len(sessions_data)
            
            sessions_data = [s for s in sessions_data if s.get("session_id") != session_id]
            
            if len(sessions_data) < original_count:
                self._save_sessions_data(sessions_data)
                logger.info("Session deleted", session_id=session_id)
                return True
            
            return False
            
        except Exception as e:
            logger.error("Failed to delete session", session_id=session_id, error=str(e))
            return False
    
    def list_sessions(
        self,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[str] = None,
        tag_filter: Optional[str] = None,
        search_query: Optional[str] = None
    ) -> SessionListResponse:
        """
        List research sessions with filtering and pagination.
        
        Args:
            page: Page number (1-based)
            page_size: Number of sessions per page
            status_filter: Filter by session status
            tag_filter: Filter by tag
            search_query: Search in title/description
            
        Returns:
            Paginated list of sessions
        """
        try:
            sessions_data = self._load_sessions_data()
            
            # Apply filters
            filtered_sessions = []
            for session_data in sessions_data:
                # Status filter
                if status_filter and session_data.get("status") != status_filter:
                    continue
                
                # Tag filter
                if tag_filter and tag_filter not in session_data.get("tags", []):
                    continue
                
                # Search query
                if search_query:
                    search_text = f"{session_data.get('title', '')} {session_data.get('description', '')}".lower()
                    if search_query.lower() not in search_text:
                        continue
                
                filtered_sessions.append(session_data)
            
            # Sort by updated_at (most recent first)
            filtered_sessions.sort(
                key=lambda x: x.get("updated_at", ""), 
                reverse=True
            )
            
            # Pagination
            total_count = len(filtered_sessions)
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            paginated_sessions = filtered_sessions[start_idx:end_idx]
            
            # Convert to ResearchSession objects
            sessions = [ResearchSession(**session_data) for session_data in paginated_sessions]
            
            return SessionListResponse(
                sessions=sessions,
                total_count=total_count,
                page=page,
                page_size=page_size
            )
            
        except Exception as e:
            logger.error("Failed to list sessions", error=str(e))
            return SessionListResponse(sessions=[], total_count=0, page=page, page_size=page_size)
    
    def save_session_state(
        self,
        session_id: str,
        phase: SessionPhase,
        state_data: Dict[str, Any],
        task_id: Optional[str] = None
    ) -> bool:
        """
        Save current research state to a session.
        
        Args:
            session_id: Session identifier
            phase: Current research phase
            state_data: Research state data
            task_id: Associated task ID
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            sessions_data = self._load_sessions_data()
            
            for i, session_data in enumerate(sessions_data):
                if session_data.get("session_id") == session_id:
                    # Update session state
                    session_data["current_phase"] = phase.value
                    session_data["updated_at"] = datetime.utcnow().isoformat()
                    
                    # Update specific fields based on phase and state_data
                    if "topic" in state_data:
                        session_data["topic"] = state_data["topic"]
                    if "questions" in state_data:
                        session_data["questions"] = state_data["questions"]
                    if "feedback" in state_data:
                        session_data["feedback"] = state_data["feedback"]
                    if "report_plan" in state_data:
                        session_data["report_plan"] = state_data["report_plan"]
                    if "search_tasks" in state_data:
                        session_data["search_tasks"] = state_data["search_tasks"]
                    if "final_report" in state_data:
                        session_data["final_report"] = state_data["final_report"]
                    if "research_config" in state_data:
                        session_data["research_config"] = state_data["research_config"]
                    
                    # Add task ID if provided
                    if task_id and task_id not in session_data.get("task_ids", []):
                        if "task_ids" not in session_data:
                            session_data["task_ids"] = []
                        session_data["task_ids"].append(task_id)
                    
                    # Calculate completion percentage
                    completion = self._calculate_completion_percentage(session_data)
                    session_data["completion_percentage"] = completion
                    
                    # Save updated data
                    self._save_sessions_data(sessions_data)
                    
                    logger.info("Session state saved", session_id=session_id, phase=phase.value)
                    return True
            
            return False
            
        except Exception as e:
            logger.error("Failed to save session state", session_id=session_id, error=str(e))
            return False
    
    def _calculate_completion_percentage(self, session_data: Dict[str, Any]) -> float:
        """Calculate session completion percentage based on current state."""
        try:
            phase = session_data.get("current_phase", "topic")
            
            phase_weights = {
                "topic": 10.0,
                "questions": 25.0,
                "feedback": 40.0,
                "research": 70.0,
                "report": 90.0,
                "completed": 100.0
            }
            
            base_completion = phase_weights.get(phase, 0.0)
            
            # Add bonus for content completion
            bonus = 0.0
            if session_data.get("topic"):
                bonus += 5.0
            if session_data.get("questions"):
                bonus += 5.0
            if session_data.get("report_plan"):
                bonus += 5.0
            if session_data.get("search_tasks"):
                bonus += 10.0
            if session_data.get("final_report"):
                bonus += 10.0
            
            return min(100.0, base_completion + bonus)
            
        except Exception:
            return 0.0
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics for research sessions.
        
        Returns:
            Dictionary containing storage statistics
        """
        try:
            sessions_data = self._load_sessions_data()
            
            total_sessions = len(sessions_data)
            active_sessions = len([s for s in sessions_data if s.get("status") == "active"])
            completed_sessions = len([s for s in sessions_data if s.get("status") == "completed"])
            archived_sessions = len([s for s in sessions_data if s.get("status") == "archived"])
            
            # Calculate total file size
            total_size = 0
            if self.sessions_file.exists():
                total_size = self.sessions_file.stat().st_size
            
            # Get all unique tags
            all_tags = set()
            for session in sessions_data:
                all_tags.update(session.get("tags", []))
            
            return {
                "total_sessions": total_sessions,
                "active_sessions": active_sessions,
                "completed_sessions": completed_sessions,
                "archived_sessions": archived_sessions,
                "total_size_bytes": total_size,
                "unique_tags": sorted(list(all_tags)),
                "storage_location": str(self.sessions_dir)
            }
            
        except Exception as e:
            logger.error("Failed to get storage stats", error=str(e))
            return {
                "total_sessions": 0,
                "active_sessions": 0,
                "completed_sessions": 0,
                "archived_sessions": 0,
                "total_size_bytes": 0,
                "unique_tags": [],
                "storage_location": str(self.sessions_dir)
            }
    
    def cleanup_old_sessions(self, days_old: int = 90) -> Dict[str, Any]:
        """
        Clean up old sessions based on age.
        
        Args:
            days_old: Archive sessions older than this many days
            
        Returns:
            Cleanup results
        """
        try:
            sessions_data = self._load_sessions_data()
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            archived_count = 0
            for session_data in sessions_data:
                updated_at = datetime.fromisoformat(session_data.get("updated_at", ""))
                if updated_at < cutoff_date and session_data.get("status") == "active":
                    session_data["status"] = "archived"
                    session_data["updated_at"] = datetime.utcnow().isoformat()
                    archived_count += 1
            
            if archived_count > 0:
                self._save_sessions_data(sessions_data)
            
            logger.info("Session cleanup completed", archived_count=archived_count, days_old=days_old)
            return {
                "success": True,
                "archived_sessions": archived_count,
                "days_old": days_old,
                "message": f"Archived {archived_count} sessions older than {days_old} days"
            }
            
        except Exception as e:
            logger.error("Failed to cleanup sessions", error=str(e))
            return {
                "success": False,
                "archived_sessions": 0,
                "days_old": days_old,
                "message": f"Failed to cleanup sessions: {str(e)}"
            }
