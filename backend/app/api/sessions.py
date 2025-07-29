"""
Session API endpoints for Deep Research application.

Handles research session persistence, management, and restoration
for complete research pipeline state tracking and replay.
"""

import structlog
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from app.core.azure_config import AzureServiceManager
from app.api.research import get_azure_manager
from app.models.schemas import (
    ResearchSession, SessionListResponse, SessionCreateRequest,
    SessionUpdateRequest, SessionRestoreRequest, SessionPhase
)
from app.services.session_manager import SessionManager

router = APIRouter()
logger = structlog.get_logger(__name__)

# Initialize session manager
session_manager = SessionManager()


@router.post("/", response_model=ResearchSession)
async def create_session(
    request: SessionCreateRequest,
    azure_manager: AzureServiceManager = Depends(get_azure_manager)
):
    """
    Create a new research session.
    
    Args:
        request: Session creation request
        
    Returns:
        Created research session
    """
    try:
        session = session_manager.create_session(request)
        logger.info("Session created successfully", session_id=session.session_id)
        return session
        
    except Exception as e:
        logger.error("Failed to create session", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create session: {str(e)}"
        )


@router.get("/list", response_model=SessionListResponse)
async def list_sessions(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of sessions per page"),
    status_filter: Optional[str] = Query(None, description="Filter by session status"),
    tag_filter: Optional[str] = Query(None, description="Filter by tag"),
    search_query: Optional[str] = Query(None, description="Search in title/description"),
    azure_manager: AzureServiceManager = Depends(get_azure_manager)
):
    """
    List research sessions with filtering and pagination.
    
    Args:
        page: Page number (1-based)
        page_size: Number of sessions per page
        status_filter: Filter by session status
        tag_filter: Filter by tag
        search_query: Search query for title/description
        
    Returns:
        Paginated list of research sessions
    """
    try:
        result = session_manager.list_sessions(
            page=page,
            page_size=page_size,
            status_filter=status_filter,
            tag_filter=tag_filter,
            search_query=search_query
        )
        
        logger.info("Sessions listed successfully", 
                   total_count=result.total_count, 
                   page=page)
        return result
        
    except Exception as e:
        logger.error("Failed to list sessions", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list sessions: {str(e)}"
        )


@router.get("/{session_id}", response_model=ResearchSession)
async def get_session(
    session_id: str,
    azure_manager: AzureServiceManager = Depends(get_azure_manager)
):
    """
    Get a specific research session by ID.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Research session details
    """
    try:
        session = session_manager.get_session(session_id)
        
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Session not found: {session_id}"
            )
        
        logger.info("Session retrieved successfully", session_id=session_id)
        return session
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get session", session_id=session_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get session: {str(e)}"
        )


@router.put("/{session_id}", response_model=ResearchSession)
async def update_session(
    session_id: str,
    request: SessionUpdateRequest,
    azure_manager: AzureServiceManager = Depends(get_azure_manager)
):
    """
    Update an existing research session.
    
    Args:
        session_id: Session identifier
        request: Session update request
        
    Returns:
        Updated research session
    """
    try:
        session = session_manager.update_session(session_id, request)
        
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Session not found: {session_id}"
            )
        
        logger.info("Session updated successfully", session_id=session_id)
        return session
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update session", session_id=session_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update session: {str(e)}"
        )


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    azure_manager: AzureServiceManager = Depends(get_azure_manager)
):
    """
    Delete a research session.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Deletion confirmation
    """
    try:
        success = session_manager.delete_session(session_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Session not found: {session_id}"
            )
        
        logger.info("Session deleted successfully", session_id=session_id)
        return {
            "success": True,
            "message": f"Session {session_id} deleted successfully",
            "session_id": session_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete session", session_id=session_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete session: {str(e)}"
        )


@router.post("/{session_id}/save-state")
async def save_session_state(
    session_id: str,
    state_data: dict,
    azure_manager: AzureServiceManager = Depends(get_azure_manager)
):
    """
    Save current research state to a session.
    
    Args:
        session_id: Session identifier
        state_data: Research state data to save
        
    Returns:
        Save confirmation
    """
    try:
        # Extract phase from state data
        phase_str = state_data.get("phase", "topic")
        try:
            phase = SessionPhase(phase_str)
        except ValueError:
            phase = SessionPhase.TOPIC
        
        # Extract task ID if present
        task_id = state_data.get("currentTaskId")
        
        success = session_manager.save_session_state(
            session_id=session_id,
            phase=phase,
            state_data=state_data,
            task_id=task_id
        )
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Session not found: {session_id}"
            )
        
        logger.info("Session state saved successfully", session_id=session_id, phase=phase.value)
        return {
            "success": True,
            "message": f"Session state saved successfully",
            "session_id": session_id,
            "phase": phase.value
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to save session state", session_id=session_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save session state: {str(e)}"
        )


@router.post("/{session_id}/restore")
async def restore_session(
    session_id: str,
    request: SessionRestoreRequest,
    azure_manager: AzureServiceManager = Depends(get_azure_manager)
):
    """
    Restore a session to the current research context.
    
    Args:
        session_id: Session identifier
        request: Restore request with options
        
    Returns:
        Session data for restoration
    """
    try:
        session = session_manager.get_session(session_id)
        
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Session not found: {session_id}"
            )
        
        # Determine which phase to restore to
        restore_phase = request.continue_from_phase or session.current_phase
        
        # Prepare restoration data
        restoration_data = {
            "session_id": session.session_id,
            "phase": restore_phase.value,
            "topic": session.topic or session.description,  # Use description as topic if topic is empty
            "questions": session.questions,
            "feedback": session.feedback,
            "reportPlan": session.report_plan,
            "searchTasks": [task.dict() for task in session.search_tasks],
            "finalReport": session.final_report,
            "currentTaskId": session.task_ids[-1] if session.task_ids else None,
            "researchConfig": session.research_config.dict() if session.research_config else None
        }
        
        logger.info("Session restored successfully", 
                   session_id=session_id, 
                   restore_phase=restore_phase.value)
        
        return {
            "success": True,
            "message": f"Session restored to {restore_phase.value} phase",
            "session_id": session_id,
            "restoration_data": restoration_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to restore session", session_id=session_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to restore session: {str(e)}"
        )


@router.get("/storage/stats")
async def get_storage_stats(
    azure_manager: AzureServiceManager = Depends(get_azure_manager)
):
    """
    Get storage statistics for research sessions.
    
    Returns:
        Storage statistics and information
    """
    try:
        stats = session_manager.get_storage_stats()
        
        logger.info("Storage stats retrieved successfully", 
                   total_sessions=stats.get("total_sessions", 0))
        
        return {
            "success": True,
            "data": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to get storage stats", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get storage stats: {str(e)}"
        )


@router.post("/cleanup")
async def cleanup_old_sessions(
    days_old: int = Query(90, ge=1, description="Archive sessions older than this many days"),
    azure_manager: AzureServiceManager = Depends(get_azure_manager)
):
    """
    Clean up old sessions by archiving them.
    
    Args:
        days_old: Archive sessions older than this many days
        
    Returns:
        Cleanup results
    """
    try:
        result = session_manager.cleanup_old_sessions(days_old)
        
        logger.info("Session cleanup completed", 
                   archived_sessions=result.get("archived_sessions", 0),
                   days_old=days_old)
        
        return result
        
    except Exception as e:
        logger.error("Failed to cleanup sessions", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cleanup sessions: {str(e)}"
        )
