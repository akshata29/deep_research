"""
API endpoints for multi-agent research orchestration.
"""

import uuid
import json
from typing import Dict, Any, Optional
from datetime import datetime
import structlog
from fastapi import APIRouter, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from app.orchestration import DeepResearchAgent
from app.models.schemas import ResearchTaskCreate, ResearchTaskResponse

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/orchestration", tags=["orchestration"])

# In-memory storage for active orchestration sessions
# In production, use a proper database or cache
_active_sessions: Dict[str, DeepResearchAgent] = {}

# WebSocket connections for real-time progress updates
_websocket_connections: Dict[str, WebSocket] = {}


class OrchestrationRequest(BaseModel):
    """Request model for orchestration research."""
    query: str = Field(..., description="Research query or task")
    session_id: Optional[str] = Field(None, description="Optional session ID to continue existing session")
    project_id: Optional[str] = Field(None, description="Optional project ID for context grouping")


class OrchestrationResponse(BaseModel):
    """Response model for orchestration research."""
    session_id: str = Field(..., description="Session identifier")
    status: str = Field(..., description="Status of the research task")
    result: Optional[str] = Field(None, description="Research result if completed")
    error: Optional[str] = Field(None, description="Error message if failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class SessionSummaryResponse(BaseModel):
    """Response model for session summary."""
    session_id: str
    project_id: str
    status: str
    agents_count: int
    memory_summary: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@router.post("/research", response_model=OrchestrationResponse)
async def start_orchestration_research(
    request: OrchestrationRequest,
    background_tasks: BackgroundTasks
) -> OrchestrationResponse:
    """
    Start a multi-agent research orchestration task.
    
    This endpoint initiates a comprehensive research task using multiple
    specialized AI agents coordinated through Semantic Kernel's MagenticOrchestration.
    """
    try:
        # Generate or use provided session ID
        session_id = request.session_id or str(uuid.uuid4())
        
        logger.info(
            "Starting orchestration research",
            session_id=session_id[:8],
            query=request.query[:100] + "..." if len(request.query) > 100 else request.query
        )
        
        # Check if session already exists
        if session_id in _active_sessions:
            agent = _active_sessions[session_id]
        else:
            # Create new agent instance with progress callback
            agent = DeepResearchAgent(
                session_id=session_id,
                project_id=request.project_id,
                progress_callback=broadcast_progress_update
            )
            
            # Initialize the agent system
            await agent.initialize()
            
            # Store in active sessions
            _active_sessions[session_id] = agent
        
        # Execute research in background
        background_tasks.add_task(execute_research_task, agent, request.query, session_id)
        
        logger.info(
            "Orchestration research started in background",
            session_id=session_id[:8]
        )
        
        return OrchestrationResponse(
            session_id=session_id,
            status="started",
            result=None,
            metadata={
                "query": request.query,
                "start_time": datetime.utcnow().isoformat(),
                "project_id": agent.project_id
            }
        )
        
    except Exception as e:
        logger.error("Orchestration research failed", error=str(e))
        
        # Remove failed session if it was created
        if 'session_id' in locals() and session_id in _active_sessions:
            del _active_sessions[session_id]
        
        # Raise HTTP exception to properly return error status
        raise HTTPException(
            status_code=500,
            detail=f"Orchestration research failed: {str(e)}"
        )


async def execute_research_task(agent: DeepResearchAgent, query: str, session_id: str):
    """
    Execute the research task in the background.
    
    Args:
        agent: The research agent instance
        query: Research query
        session_id: Session identifier
    """
    try:
        logger.info("Starting background research task", session_id=session_id[:8])
        
        # Execute research
        result = await agent.research(query)
        
        logger.info(
            "Background research task completed",
            session_id=session_id[:8],
            result_length=len(result) if result else 0
        )
        
        # Cleanup active session after completion
        if session_id in _active_sessions:
            del _active_sessions[session_id]
            
    except Exception as e:
        logger.error("Background research task failed", session_id=session_id, error=str(e))
        
        # Update session status to failed
        try:
            agent.session_manager.update_session_status(session_id, "failed", f"Error: {str(e)}")
        except Exception as cleanup_error:
            logger.error("Failed to update session status after error", error=str(cleanup_error))
        
        # Cleanup active session
        if session_id in _active_sessions:
            del _active_sessions[session_id]
        
        # Send error update via WebSocket if connected
        if session_id in _websocket_connections:
            try:
                await broadcast_progress_update(session_id, {
                    "type": "research_failed",
                    "message": f"Research failed: {str(e)}",
                    "error": str(e)
                })
            except Exception as ws_error:
                logger.warning("Failed to send error update via WebSocket", error=str(ws_error))


@router.get("/sessions/{session_id}/details")
async def get_session_details(session_id: str) -> Dict[str, Any]:
    """
    Get detailed session information including agent executions.
    
    Returns comprehensive session data with all agent execution details.
    """
    try:
        # First check if the session is active
        agent = _active_sessions.get(session_id)
        
        if agent and hasattr(agent, 'session_manager'):
            # Get session details from the session manager
            session_details = agent.session_manager.get_session(session_id)
            
            if session_details:
                return {
                    "session_found": True,
                    "source": "active_session",
                    "session_details": session_details
                }
        
        # If not in active sessions, try to load from session manager directly
        from app.orchestration.session_manager import OrchestrationSessionManager
        session_manager = OrchestrationSessionManager()
        
        session_details = session_manager.get_session(session_id)
        
        if session_details:
            return {
                "session_found": True,
                "source": "session_files",
                "session_details": session_details
            }
        else:
            raise HTTPException(status_code=404, detail="Session not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get session details", session_id=session_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/summary", response_model=SessionSummaryResponse)
async def get_session_summary(session_id: str) -> SessionSummaryResponse:
    """
    Get summary information for an orchestration session.
    
    Returns details about the session status, agents, and memory usage.
    """
    try:
        if session_id not in _active_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        agent = _active_sessions[session_id]
        summary = await agent.get_session_summary()
        
        return SessionSummaryResponse(
            session_id=summary["session_id"],
            project_id=summary["project_id"],
            status=summary["status"],
            agents_count=summary["agents_count"],
            memory_summary=summary.get("memory_summary")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get session summary", session_id=session_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}")
async def cleanup_session(session_id: str) -> Dict[str, str]:
    """
    Clean up and remove an orchestration session.
    
    This will clean up resources and remove the session from memory.
    """
    try:
        if session_id not in _active_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        agent = _active_sessions[session_id]
        
        # Clean up agent resources
        await agent.cleanup()
        
        # Remove from active sessions
        del _active_sessions[session_id]
        
        logger.info("Session cleaned up", session_id=session_id[:8])
        
        return {"message": f"Session {session_id} cleaned up successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to cleanup session", session_id=session_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def list_active_sessions() -> Dict[str, Any]:
    """
    List all active orchestration sessions.
    
    Returns basic information about all currently active sessions.
    """
    try:
        sessions = []
        
        for session_id, agent in _active_sessions.items():
            try:
                summary = await agent.get_session_summary()
                sessions.append({
                    "session_id": session_id,
                    "project_id": summary["project_id"],
                    "status": summary["status"],
                    "agents_count": summary["agents_count"]
                })
            except Exception as e:
                logger.warning("Failed to get summary for session", session_id=session_id, error=str(e))
                sessions.append({
                    "session_id": session_id,
                    "status": "error",
                    "error": str(e)
                })
        
        return {
            "active_sessions": sessions,
            "total_count": len(sessions)
        }
        
    except Exception as e:
        logger.error("Failed to list active sessions", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def orchestration_health() -> Dict[str, Any]:
    """
    Health check for the orchestration system.
    
    Returns status of the orchestration components and configuration.
    """
    try:
        from app.orchestration.config import get_orchestration_config
        
        config = get_orchestration_config()
        
        # Check configuration
        config_status = {
            "azure_openai_configured": bool(config.azure_ai_endpoint and config.azure_client_id),
            "azure_search_configured": bool(config.azure_search_endpoint and config.azure_search_api_key),
            "web_search_configured": bool(config.tavily_api_key),
            "embedding_configured": True  # Embedding is part of Azure AI endpoint
        }
        
        return {
            "status": "healthy",
            "active_sessions_count": len(_active_sessions),
            "configuration": config_status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Orchestration health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.websocket("/ws/{session_id}")
async def websocket_progress(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time orchestration progress updates.
    
    Streams agent execution progress, including:
    - Agent start/completion events
    - Progress percentages
    - Agent outputs and status updates
    """
    await websocket.accept()
    
    try:
        # Store WebSocket connection
        _websocket_connections[session_id] = websocket
        
        logger.info("WebSocket connected for orchestration progress", session_id=session_id[:8])
        
        # Send initial connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat()
        }))
        
        # If session exists, send current progress
        if session_id in _active_sessions:
            agent = _active_sessions[session_id]
            
            # Try to get session progress from session manager
            try:
                session_details = agent.session_manager.get_session(session_id)
                if session_details:
                    await websocket.send_text(json.dumps({
                        "type": "session_progress",
                        "session_id": session_id,
                        "status": session_details.get("status", "unknown"),
                        "agent_executions": session_details.get("agent_executions", []),
                        "timestamp": datetime.utcnow().isoformat()
                    }))
            except Exception as e:
                logger.warning("Failed to get session progress", error=str(e))
        
        # Keep connection alive and listen for client messages
        while True:
            try:
                # Wait for client messages (optional heartbeat)
                message = await websocket.receive_text()
                data = json.loads(message)
                
                if data.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }))
                elif data.get("type") == "get_progress":
                    # Send current progress update
                    if session_id in _active_sessions:
                        agent = _active_sessions[session_id]
                        try:
                            session_details = agent.session_manager.get_session(session_id)
                            if session_details:
                                await websocket.send_text(json.dumps({
                                    "type": "progress_update",
                                    "session_id": session_id,
                                    "status": session_details.get("status", "unknown"),
                                    "agent_executions": session_details.get("agent_executions", []),
                                    "final_result": session_details.get("final_result", ""),
                                    "timestamp": datetime.utcnow().isoformat()
                                }))
                        except Exception as e:
                            await websocket.send_text(json.dumps({
                                "type": "error",
                                "message": f"Failed to get progress: {str(e)}",
                                "timestamp": datetime.utcnow().isoformat()
                            }))
                            
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.warning("WebSocket message error", error=str(e))
                break
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error("WebSocket connection error", session_id=session_id, error=str(e))
    finally:
        # Clean up connection
        if session_id in _websocket_connections:
            del _websocket_connections[session_id]
        logger.info("WebSocket disconnected", session_id=session_id[:8])


async def broadcast_progress_update(session_id: str, update_data: Dict[str, Any]):
    """
    Broadcast progress update to connected WebSocket clients.
    
    Args:
        session_id: Session identifier
        update_data: Progress update data
    """
    if session_id in _websocket_connections:
        try:
            websocket = _websocket_connections[session_id]
            
            # Extract session data if available
            session_data = update_data.get("session_data")
            
            # Calculate progress if session data is available
            progress_percentage = 0
            if session_data and "agent_executions" in session_data:
                executions = session_data["agent_executions"]
                total_agents = len(executions)
                completed_agents = sum(1 for exec in executions if exec.get("status") == "completed")
                progress_percentage = (completed_agents / max(total_agents, 1)) * 100 if total_agents > 0 else 0
            
            # Prepare message
            message = {
                "type": "progress_update",
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "update_type": update_data.get("type", "unknown"),
                "message": update_data.get("message", ""),
                "progress_percentage": progress_percentage
            }
            
            # Include session data if available
            if session_data:
                message.update({
                    "status": session_data.get("status", "unknown"),
                    "agent_executions": session_data.get("agent_executions", []),
                    "final_result": session_data.get("final_result", ""),
                    "total_agents": len(session_data.get("agent_executions", [])),
                    "completed_agents": sum(1 for exec in session_data.get("agent_executions", []) if exec.get("status") == "completed"),
                    "failed_agents": sum(1 for exec in session_data.get("agent_executions", []) if exec.get("status") == "failed"),
                    "created_at": session_data.get("created_at", ""),
                    "updated_at": session_data.get("updated_at", ""),
                    "metadata": session_data.get("metadata", {})
                })
            
            await websocket.send_text(json.dumps(message))
            
        except Exception as e:
            logger.warning("Failed to broadcast progress update", 
                          session_id=session_id, error=str(e))
            # Remove broken connection
            if session_id in _websocket_connections:
                del _websocket_connections[session_id]


@router.get("/sessions/{session_id}/progress")
async def get_session_progress(session_id: str) -> Dict[str, Any]:
    """
    Get current progress for an orchestration session.
    
    Returns agent execution status and progress information.
    """
    try:
        # Check if session is active
        if session_id in _active_sessions:
            agent = _active_sessions[session_id]
            session_details = agent.session_manager.get_session(session_id)
        else:
            # Try to load from session manager
            from app.orchestration.session_manager import OrchestrationSessionManager
            session_manager = OrchestrationSessionManager()
            session_details = session_manager.get_session(session_id)
        
        if not session_details:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Calculate progress
        agent_executions = session_details.get("agent_executions", [])
        total_agents = len(agent_executions)
        completed_agents = sum(1 for exec in agent_executions if exec.get("status") == "completed")
        failed_agents = sum(1 for exec in agent_executions if exec.get("status") == "failed")
        
        progress_percentage = (completed_agents / max(total_agents, 1)) * 100 if total_agents > 0 else 0
        
        return {
            "session_id": session_id,
            "status": session_details.get("status", "unknown"),
            "progress_percentage": progress_percentage,
            "total_agents": total_agents,
            "completed_agents": completed_agents,
            "failed_agents": failed_agents,
            "agent_executions": agent_executions,
            "final_result": session_details.get("final_result", ""),
            "created_at": session_details.get("created_at", ""),
            "updated_at": session_details.get("updated_at", ""),
            "metadata": session_details.get("metadata", {}),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get session progress", session_id=session_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get session progress: {str(e)}"
        )
