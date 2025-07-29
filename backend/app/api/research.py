"""
Research API endpoints for Deep Research application.

Handles research request orchestration using Azure AI Foundry Agent Service
with Bing grounding integration for comprehensive research capabilities.
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
import json

from app.core.azure_config import AzureServiceManager
from app.models.schemas import (
    ResearchRequest, ResearchResponse, ResearchProgress, ResearchReport,
    ResearchStatus, AvailableModel, ModelType, ResearchSection,
    ResearchPlanRequest, ExecuteResearchRequest, FinalReportRequest, CustomExportRequest
)
from app.services.research_orchestrator import ResearchOrchestrator
from app.services.ai_agent_service import AIAgentService
from app.services.web_search_service import WebSearchService
from app.services.tavily_search_service import TavilySearchService


router = APIRouter()
logger = structlog.get_logger(__name__)


# Active research tasks and WebSocket connections
active_tasks: Dict[str, Dict] = {}
websocket_connections: Dict[str, WebSocket] = {}


system_prompt = f"""
You are an expert researcher. Today is 'todaynow'. Follow these instructions when responding:

- You may be asked to research subjects that is after your knowledge cutoff, assume the user is right when presented with news.
- The user is a highly experienced analyst, no need to simplify it, be as detailed as possible and make sure your response is correct.
- Be highly organized.
- Suggest solutions that I didn't think about.
- Be proactive and anticipate my needs.
- Treat me as an expert in all subject matter.
- Mistakes erode my trust, so be accurate and thorough.
- Provide detailed explanations, I'm comfortable with lots of detail.
- Value good arguments over authorities, the source is irrelevant.
- Consider new technologies and contrarian ideas, not just the conventional wisdom.
- You may use high levels of speculation or prediction, just flag it for me.
"""

async def get_azure_manager(request: Request) -> AzureServiceManager:
    """Dependency to get Azure service manager from app state."""
    if not hasattr(request.app.state, 'azure_manager'):
        raise HTTPException(
            status_code=503,
            detail="Azure services not initialized"
        )
    return request.app.state.azure_manager


@router.get("/models", response_model=List[AvailableModel])
async def get_available_models(
    azure_manager: AzureServiceManager = Depends(get_azure_manager)
):
    """
    Get list of available AI models for research tasks.
    
    Returns:
        List of available models with their capabilities and pricing
    """
    try:
        # Get deployed models from Azure AI project
        deployed_models = await azure_manager.get_deployed_models()
        
        models = []
        
        # Map deployed models to AvailableModel objects
        for category, model_list in deployed_models.items():
            # Handle both old format (single model) and new format (list of models)
            models_to_process = model_list if isinstance(model_list, list) else [model_list]
            
            for model_info in models_to_process:
                model_name = model_info.get("name", "unknown")
                model_display_name = model_info.get("model", model_name)
                
                # Determine model type based on category and name
                # All thinking-related models (GPT-4, O1, DeepSeek) are now categorized as "thinking"
                if category == "thinking":
                    model_type = ModelType.THINKING
                    # Determine specific model characteristics based on actual model name
                    if 'gpt-4' in model_display_name.lower():
                        max_tokens = 128000
                        cost_per_1k = 0.03
                        description = "Advanced GPT-4 model for complex reasoning and analysis"
                    elif 'o1' in model_display_name.lower():
                        max_tokens = 200000
                        cost_per_1k = 0.15
                        description = "Advanced O1 reasoning model with deep thinking capabilities"
                    elif 'deepseek' in model_display_name.lower():
                        max_tokens = 8192
                        cost_per_1k = 0.014
                        description = "Specialized DeepSeek model for advanced reasoning and coding"
                    else:
                        max_tokens = 8192
                        cost_per_1k = 0.02
                        description = "Advanced thinking model for complex analysis"
                elif category == "task" or any(keyword in model_name.lower() for keyword in ['gpt-4o-mini', 'chat4omini', 'o1-mini', 'chato1mini']):
                    model_type = ModelType.TASK
                    max_tokens = 128000 if 'gpt-4o-mini' in model_display_name.lower() else 16384
                    cost_per_1k = 0.00015 if 'gpt-4o-mini' in model_display_name.lower() else 0.003
                    description = "Fast and efficient model for structured tasks"
                elif category == "phi" or any(keyword in model_name.lower() for keyword in ['phi', 'chatphi']):
                    model_type = ModelType.SPECIALIST
                    max_tokens = 8192 if 'phi-3' in model_display_name.lower() else 16384
                    cost_per_1k = 0.001
                    description = "Efficient Phi model for specialized tasks and multimodal capabilities"
                elif category == "embedding" or "embedding" in model_name.lower():
                    model_type = ModelType.EMBEDDING
                    max_tokens = 8191
                    cost_per_1k = 0.0001
                    description = "Text embedding model for similarity and search"
                else:
                    model_type = ModelType.SPECIALIST
                    max_tokens = 8192
                    cost_per_1k = 0.024
                    description = "Specialized model for specific domain tasks"
                
                available_model = AvailableModel(
                    name=model_name,
                    display_name=model_display_name.replace('-', ' ').title(),
                    type=model_type,
                    max_tokens=max_tokens,
                    supports_tools=True,  # Most modern models support tools
                    supports_agents=model_info.get("agent_supported", False),  # Use agent support from model data
                    cost_per_1k_tokens=cost_per_1k,
                    description=description
                )
                
                models.append(available_model)
        
        # Add fallback models if no deployed models found
        if not models:
            models = [
                AvailableModel(
                    name="gpt-4",
                    display_name="GPT-4",
                    type=ModelType.THINKING,
                    max_tokens=8192,
                    supports_tools=True,
                    supports_agents=True,  # GPT-4 supports agents
                    cost_per_1k_tokens=0.03,
                    description="Most capable model for complex reasoning and analysis"
                ),
                AvailableModel(
                    name="gpt-35-turbo",
                    display_name="GPT-3.5 Turbo",
                    type=ModelType.TASK,
                    max_tokens=4096,
                    supports_tools=True,
                    supports_agents=True,  # GPT-3.5 supports agents
                    cost_per_1k_tokens=0.002,
                    description="Fast and efficient model for structured tasks"
                )
            ]
        
        logger.info("Retrieved available models", model_count=len(models), deployed_models=list(deployed_models.keys()))
        return models
        
    except Exception as e:
        logger.error("Failed to get available models", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve available models"
        )


@router.post("/start", response_model=ResearchResponse)
async def start_research(
    request: ResearchRequest,
    azure_manager: AzureServiceManager = Depends(get_azure_manager)
):
    """
    Start a new research task.
    
    Args:
        request: Research request parameters
        
    Returns:
        Research response with task ID and status
    """
    try:
        # Generate unique task ID
        task_id = str(uuid.uuid4())
        
        logger.info(
            "Starting research task",
            task_id=task_id,
            prompt=request.prompt[:100] + "..." if len(request.prompt) > 100 else request.prompt,
            models=request.models_config,
            web_search=request.enable_web_search
        )
        
        # Initialize research orchestrator
        orchestrator = ResearchOrchestrator(
            azure_manager=azure_manager,
            task_id=task_id,
            config=request
        )
        
        # Store task information
        active_tasks[task_id] = {
            "orchestrator": orchestrator,
            "request": request,
            "started_at": datetime.utcnow(),
            "status": ResearchStatus.PENDING,
            "progress": 0
        }
        
        # Start research task asynchronously with progress monitoring
        asyncio.create_task(execute_research_with_progress_updates(orchestrator, task_id))
        
        # Generate WebSocket URL for real-time updates
        websocket_url = f"/api/v1/research/ws/{task_id}"
        
        response = ResearchResponse(
            task_id=task_id,
            status=ResearchStatus.PENDING,
            message="Research task started successfully",
            websocket_url=websocket_url,
            progress=ResearchProgress(
                task_id=task_id,
                status=ResearchStatus.PENDING,
                progress_percentage=0,
                current_step="Initializing research task",
                estimated_completion=datetime.utcnow() + timedelta(minutes=5)
            )
        )
        
        logger.info("Research task initialized", task_id=task_id)
        return response
        
    except Exception as e:
        logger.error("Failed to start research task", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start research task: {str(e)}"
        )


@router.get("/status/{task_id}", response_model=ResearchResponse)
async def get_research_status(
    task_id: str,
    azure_manager: AzureServiceManager = Depends(get_azure_manager)
):
    """
    Get the current status of a research task.
    
    Args:
        task_id: Research task identifier
        
    Returns:
        Current research status and progress
    """
    try:
        if task_id not in active_tasks:
            raise HTTPException(
                status_code=404,
                detail="Research task not found"
            )
        
        task_info = active_tasks[task_id]
        orchestrator = task_info["orchestrator"]
        
        # Get current status from orchestrator
        status = orchestrator.status  # This is a ResearchStatus enum, not async
        progress = await orchestrator.get_progress()
        
        response = ResearchResponse(
            task_id=task_id,
            status=status,
            message=f"Research task is {status.value}",
            progress=progress
        )
        
        # Include report if completed
        if status == ResearchStatus.COMPLETED:
            response.report = orchestrator.get_report()  # This is also sync, not async
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get research status", task_id=task_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve research status"
        )


@router.get("/report/{task_id}", response_model=ResearchReport)
async def get_research_report(
    task_id: str,
    azure_manager: AzureServiceManager = Depends(get_azure_manager)
):
    """
    Get the completed research report.
    
    Args:
        task_id: Research task identifier
        
    Returns:
        Complete research report with all sections
    """
    try:
        if task_id not in active_tasks:
            raise HTTPException(
                status_code=404,
                detail="Research task not found"
            )
        
        task_info = active_tasks[task_id]
        orchestrator = task_info["orchestrator"]
        
        # Check if task is completed
        status = orchestrator.status  # This is a property, not async
        if status != ResearchStatus.COMPLETED:
            raise HTTPException(
                status_code=400,
                detail=f"Research task is not completed (current status: {status.value})"
            )
        
        # Get the complete report
        report = orchestrator.get_report()  # This is sync, not async
        
        logger.info("Retrieved research report", task_id=task_id, sections=len(report.sections))
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get research report", task_id=task_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve research report"
        )


@router.delete("/cancel/{task_id}")
async def cancel_research(
    task_id: str,
    azure_manager: AzureServiceManager = Depends(get_azure_manager)
):
    """
    Cancel an active research task.
    
    Args:
        task_id: Research task identifier
        
    Returns:
        Cancellation confirmation
    """
    try:
        if task_id not in active_tasks:
            raise HTTPException(
                status_code=404,
                detail="Research task not found"
            )
        
        task_info = active_tasks[task_id]
        orchestrator = task_info["orchestrator"]
        
        # Cancel the task
        await orchestrator.cancel()
        
        # Remove from active tasks
        del active_tasks[task_id]
        
        # Close WebSocket connection if exists
        if task_id in websocket_connections:
            await websocket_connections[task_id].close()
            del websocket_connections[task_id]
        
        logger.info("Research task cancelled", task_id=task_id)
        
        return {"message": "Research task cancelled successfully", "task_id": task_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to cancel research task", task_id=task_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to cancel research task"
        )


@router.get("/list")
async def list_research_tasks(
    azure_manager: AzureServiceManager = Depends(get_azure_manager)
):
    """
    List all active and recent research tasks.
    
    Returns:
        List of research tasks with their current status
    """
    try:
        task_list = []
        
        for task_id, task_info in active_tasks.items():
            orchestrator = task_info["orchestrator"]
            status = orchestrator.status  # This is a property, not async
            progress = await orchestrator.get_progress()
            
            task_list.append({
                "task_id": task_id,
                "status": status,
                "started_at": task_info["started_at"].isoformat(),
                "prompt": task_info["request"].prompt[:100] + "..." if len(task_info["request"].prompt) > 100 else task_info["request"].prompt,
                "progress_percentage": progress.progress_percentage if progress else 0,
                "tokens_used": progress.tokens_used if progress else 0,
                "cost_estimate": progress.cost_estimate if progress else 0.0
            })
        
        return {"tasks": task_list, "total_count": len(task_list)}
        
    except Exception as e:
        logger.error("Failed to list research tasks", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to list research tasks"
        )


@router.websocket("/test")
async def test_websocket(websocket: WebSocket):
    """Test WebSocket endpoint for debugging."""
    logger.info("Test WebSocket connection attempt")
    
    try:
        await websocket.accept()
        logger.info("Test WebSocket connection established")
        
        await websocket.send_text(json.dumps({
            "type": "test",
            "message": "WebSocket is working",
            "timestamp": datetime.utcnow().isoformat()
        }))
        
        # Keep connection alive for testing
        while True:
            try:
                message = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                logger.info("Test WebSocket received message", message=message)
                await websocket.send_text(f"Echo: {message}")
            except asyncio.TimeoutError:
                await websocket.send_text(json.dumps({
                    "type": "ping",
                    "timestamp": datetime.utcnow().isoformat()
                }))
            except WebSocketDisconnect:
                logger.info("Test WebSocket client disconnected")
                break
                
    except Exception as e:
        logger.error("Test WebSocket error", error=str(e), exc_info=True)
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass
    finally:
        logger.info("Test WebSocket connection closed")


@router.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    """
    WebSocket endpoint for real-time research progress updates.
    
    Args:
        websocket: WebSocket connection
        task_id: Research task identifier
    """
    logger.info("WebSocket connection attempt", task_id=task_id, active_tasks=list(active_tasks.keys()))
    
    try:
        # Accept WebSocket connection with proper headers
        await websocket.accept()
        websocket_connections[task_id] = websocket
        
        logger.info("WebSocket connection established", task_id=task_id)
    except Exception as e:
        logger.error("Failed to accept WebSocket connection", task_id=task_id, error=str(e), exc_info=True)
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass
        return
    
    try:
        # Send initial connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connection",
            "message": "WebSocket connection established",
            "task_id": task_id,
            "timestamp": datetime.utcnow().isoformat()
        }))
        
        # Immediately send current status if task exists
        if task_id in active_tasks:
            try:
                task_info = active_tasks[task_id]
                orchestrator = task_info["orchestrator"]
                progress = await orchestrator.get_progress()
                
                # Send current status
                status_data = {
                    "type": "progress",
                    "task_id": task_id,
                    "data": {
                        "status": progress.status.value,
                        "progress_percentage": progress.progress_percentage,
                        "current_step": progress.current_step,
                        "tokens_used": progress.tokens_used,
                        "sources_found": progress.sources_found,
                        "estimated_completion": progress.estimated_completion.isoformat() if progress.estimated_completion else None
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                await websocket.send_text(json.dumps(status_data))
                logger.info("Sent current status to WebSocket", task_id=task_id, status=progress.status.value)
                
                # If completed, also send completion message
                if progress.status == ResearchStatus.COMPLETED:
                    completion_data = {
                        "type": "completed",
                        "task_id": task_id,
                        "data": {
                            "status": progress.status.value,
                            "progress_percentage": 100,
                            "current_step": "Research completed",
                            "tokens_used": progress.tokens_used,
                            "sources_found": progress.sources_found
                        },
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await websocket.send_text(json.dumps(completion_data))
                    
            except Exception as e:
                logger.error("Failed to send initial status", task_id=task_id, error=str(e))
        else:
            # Task doesn't exist yet, send waiting status
            try:
                waiting_data = {
                    "type": "waiting",
                    "task_id": task_id,
                    "data": {
                        "status": "waiting",
                        "progress_percentage": 0,
                        "current_step": "Waiting for task to start...",
                        "message": "WebSocket connected, waiting for research task to be created"
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
                await websocket.send_text(json.dumps(waiting_data))
                logger.info("Sent waiting status to WebSocket", task_id=task_id)
            except Exception as e:
                logger.error("Failed to send waiting status", task_id=task_id, error=str(e))
        
        # Keep the connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages from client (optional heartbeat/ping)
                message = await asyncio.wait_for(websocket.receive_text(), timeout=10.0)
                
                # Handle ping/pong for keep-alive
                if message == "ping":
                    await websocket.send_text("pong")
                    
            except asyncio.TimeoutError:
                # Send periodic status updates if task is still active
                if task_id in active_tasks:
                    try:
                        task_info = active_tasks[task_id]
                        orchestrator = task_info["orchestrator"]
                        progress = await orchestrator.get_progress()
                        
                        status_data = {
                            "type": "progress",
                            "task_id": task_id,
                            "data": {
                                "status": progress.status.value,
                                "progress_percentage": progress.progress_percentage,
                                "current_step": progress.current_step,
                                "tokens_used": progress.tokens_used,
                                "sources_found": progress.sources_found,
                                "estimated_completion": progress.estimated_completion.isoformat() if progress.estimated_completion else None
                            },
                            "timestamp": datetime.utcnow().isoformat()
                        }
                        
                        await websocket.send_text(json.dumps(status_data))
                        
                    except Exception as e:
                        logger.error("Failed to send periodic update", task_id=task_id, error=str(e))
                else:
                    # Task still doesn't exist, send waiting status
                    try:
                        waiting_data = {
                            "type": "waiting",
                            "task_id": task_id,
                            "data": {
                                "status": "waiting",
                                "progress_percentage": 0,
                                "current_step": "Waiting for task to start...",
                                "message": "Still waiting for research task to be created"
                            },
                            "timestamp": datetime.utcnow().isoformat()
                        }
                        await websocket.send_text(json.dumps(waiting_data))
                    except Exception as e:
                        logger.error("Failed to send waiting update", task_id=task_id, error=str(e))
                continue
            except WebSocketDisconnect:
                logger.info("WebSocket client disconnected", task_id=task_id)
                break
                
    except WebSocketDisconnect:
        logger.info("WebSocket connection closed", task_id=task_id)
    except Exception as e:
        logger.error("WebSocket error", task_id=task_id, error=str(e))
    finally:
        # Clean up connection
        if task_id in websocket_connections:
            del websocket_connections[task_id]
        logger.info("WebSocket connection cleaned up", task_id=task_id)


async def send_websocket_update(task_id: str, message_data: dict):
    """
    Send a progress update via WebSocket to connected clients.
    
    Args:
        task_id: Research task identifier
        message_data: Dictionary containing message data
    """
    if task_id in websocket_connections:
        try:
            websocket = websocket_connections[task_id]
            await websocket.send_text(json.dumps(message_data))
            logger.debug("WebSocket update sent", task_id=task_id, message_type=message_data.get("type"))
        except Exception as e:
            logger.error("Failed to send WebSocket update", task_id=task_id, error=str(e))
            # Remove broken connection
            if task_id in websocket_connections:
                del websocket_connections[task_id]


async def execute_research_with_progress_updates(orchestrator: ResearchOrchestrator, task_id: str):
    """
    Execute research with periodic WebSocket progress updates.
    
    Args:
        orchestrator: Research orchestrator instance
        task_id: Research task identifier
    """
    try:
        logger.info("Starting research execution with progress monitoring", task_id=task_id)
        
        # Start the research execution
        research_task = asyncio.create_task(orchestrator.execute_research())
        
        # Send initial status update
        try:
            progress = await orchestrator.get_progress()
            message_data = {
                "type": "progress",
                "task_id": task_id,
                "data": {
                    "status": progress.status.value,
                    "progress_percentage": progress.progress_percentage,
                    "current_step": progress.current_step,
                    "tokens_used": progress.tokens_used,
                    "sources_found": progress.sources_found,
                    "estimated_completion": progress.estimated_completion.isoformat() if progress.estimated_completion else None
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            await send_websocket_update(task_id, message_data)
            logger.info("Sent initial progress update", task_id=task_id, status=progress.status.value)
        except Exception as e:
            logger.error("Failed to send initial update", task_id=task_id, error=str(e))
        
        # Monitor progress and send updates
        while not research_task.done():
            try:
                # Get current progress
                progress = await orchestrator.get_progress()
                
                # Send WebSocket update (even if no connections yet)
                message_data = {
                    "type": "progress",
                    "task_id": task_id,
                    "data": {
                        "status": progress.status.value,
                        "progress_percentage": progress.progress_percentage,
                        "current_step": progress.current_step,
                        "tokens_used": progress.tokens_used,
                        "sources_found": progress.sources_found,
                        "estimated_completion": progress.estimated_completion.isoformat() if progress.estimated_completion else None
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                await send_websocket_update(task_id, message_data)
                
                # Update active task status
                if task_id in active_tasks:
                    active_tasks[task_id]["status"] = progress.status
                    active_tasks[task_id]["progress"] = progress.progress_percentage
                
                logger.debug("Progress update sent", task_id=task_id, progress=progress.progress_percentage, step=progress.current_step)
                
                # Wait before next update
                await asyncio.sleep(1.0)  # Update every 1 second for faster UI updates
                
            except Exception as e:
                logger.error("Error sending progress update", task_id=task_id, error=str(e))
                await asyncio.sleep(1.0)
        
        # Wait for research to complete
        await research_task
        
        # Send final completion update
        final_progress = await orchestrator.get_progress()
        completion_data = {
            "type": "completed",
            "task_id": task_id,
            "data": {
                "status": final_progress.status.value,
                "progress_percentage": 100,
                "current_step": "Research completed",
                "tokens_used": final_progress.tokens_used,
                "sources_found": final_progress.sources_found
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await send_websocket_update(task_id, completion_data)
        
        logger.info("Research execution completed with progress updates", task_id=task_id, 
                   tokens_used=final_progress.tokens_used, sources_found=final_progress.sources_found)
        
    except Exception as e:
        logger.error("Research execution failed", task_id=task_id, error=str(e), exc_info=True)
        
        # Send error update
        error_data = {
            "type": "error",
            "task_id": task_id,
            "data": {
                "status": "failed",
                "error": str(e),
                "current_step": "Research failed"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await send_websocket_update(task_id, error_data)
        
        # Update task status
        if task_id in active_tasks:
            active_tasks[task_id]["status"] = ResearchStatus.FAILED


# New phase-specific endpoints

@router.post("/questions", response_model=ResearchResponse)
async def generate_questions(
    request: ResearchRequest,
    azure_manager: AzureServiceManager = Depends(get_azure_manager)
):
    """Generate clarifying questions for the research topic."""
    try:
        task_id = str(uuid.uuid4())
        
        # Create focused prompt for question generation
        now = datetime.now().isoformat()

        questions_prompt = f"""
        Given the following query from the user, ask at least 5 follow-up questions to clarify the research direction:

        <QUERY>
        {request.prompt}
        </QUERY>

        Questions need to be brief and concise. No need to output content that is irrelevant to the question.

        **Respond in the same language as the user's language**
        """

        logger.info("Generating clarifying questions", task_id=task_id, prompt=questions_prompt)

        # Use thinking model for question generation with unique agent name
        ai_service = AIAgentService(azure_manager)
        agent_name = f"thinking-agent-questions-{request.models_config.get('thinking', 'gpt-4').replace('-', '')}"
        response_text = await ai_service.generate_response(
            system_prompt=system_prompt.replace("'todaynow'", now),
            prompt=questions_prompt,
            model_name=request.models_config.get("thinking", "gpt-4"),
            agent_name=agent_name,
            max_tokens=2048
        )

        # Create report with questions
        report = ResearchReport(
            task_id=task_id,
            title=f"Research Questions for: {request.prompt[:50]}...",
            executive_summary="Generated clarifying questions to guide research planning",
            sections=[
                ResearchSection(
                    title="Clarifying Questions",
                    content=response_text,
                    sources=[],
                    confidence_score=0.9,
                    word_count=len(response_text.split())
                )
            ],
            conclusions="Please review and provide feedback on these questions",
            sources=[],
            metadata={"phase": "questions", "topic": request.prompt},
            word_count=len(response_text.split()),
            reading_time_minutes=max(1, len(response_text.split()) // 200)
        )

        return ResearchResponse(
            task_id=task_id,
            status=ResearchStatus.COMPLETED,
            message="Questions generated successfully",
            report=report
        )

    except Exception as e:
        logger.error("Failed to generate questions", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to generate questions: {str(e)}")


@router.post("/plan", response_model=ResearchResponse)
async def create_research_plan(
    request_data: ResearchPlanRequest,
    azure_manager: AzureServiceManager = Depends(get_azure_manager)
):
    """Create a research plan based on topic and feedback."""
    try:
        task_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        # Format questions for better prompt readability
        formatted_questions = '\n'.join([f"{i+1}. {q}" for i, q in enumerate(request_data.questions)])
        
        plan_prompt = f"""
Given the following query from the user:
<QUERY> 
Initial Query: 
{request_data.topic}
Follow-up Questions:
{formatted_questions}
Follow-up Feedback: "{request_data.feedback}"
</QUERY>

Generate a list of sections for the report based on the topic and feedback.
Your plan should be tight and focused with NO overlapping sections or unnecessary filler. Each section needs a sentence summarizing its content.

Integration guidelines:
<GUIDELINES>
- Ensure each section has a distinct purpose with no content overlap.
- Combine related concepts rather than separating them.
- CRITICAL: Every section MUST be directly relevant to the main topic.
- Avoid tangential or loosely related sections that don't directly address the core topic.
</GUIDELINES>

Before submitting, review your structure to ensure it has no redundant sections and follows a logical flow.

**Respond in the same language as the user's language**"
"""

        logger.info("Plan Prompt: ", task_id=task_id, prompt=plan_prompt)

        ai_service = AIAgentService(azure_manager)
        agent_name = f"thinking-agent-plan-{request_data.request.models_config.get('thinking', 'gpt-4').replace('-', '')}"
        response_text = await ai_service.generate_response(
            system_prompt=system_prompt.replace("'todaynow'", now),
            prompt=plan_prompt,
            model_name=request_data.request.models_config.get("thinking", "gpt-4"),
            agent_name=agent_name,
            max_tokens=3072
        )

        report = ResearchReport(
            task_id=task_id,
            title=f"Research Plan: {request_data.topic[:50]}...",
            executive_summary="Comprehensive research plan based on clarifying questions",
            sections=[
                ResearchSection(
                    title="Research Plan",
                    content=response_text,
                    sources=[],
                    confidence_score=0.9,
                    word_count=len(response_text.split())
                )
            ],
            conclusions="Research plan is ready for execution",
            sources=[],
            metadata={"phase": "plan", "topic": request_data.topic, "feedback": request_data.feedback},
            word_count=len(response_text.split()),
            reading_time_minutes=max(1, len(response_text.split()) // 200)
        )

        return ResearchResponse(
            task_id=task_id,
            status=ResearchStatus.COMPLETED,
            message="Research plan created successfully",
            report=report
        )

    except Exception as e:
        logger.error("Failed to create research plan", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create research plan: {str(e)}")


@router.post("/execute", response_model=ResearchResponse)
async def execute_research(
    request_data: ExecuteResearchRequest,
    azure_manager: AzureServiceManager = Depends(get_azure_manager)
):
    """Execute research based on the plan."""
    try:
        task_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        # Step 1: Generate search queries (without Bing grounding)
        research_prompt = f"""
        This is the report plan after user confirmation:
        <PLAN>
        {request_data.plan}
        </PLAN>

        Based on previous report plan, generate a list of Serp queries to further research the topic. Make sure each query is unique and not similar to each other.

        You MUST respond in **JSON** matching this **JSON schema**:

        ```json
        {{
            "type": "array",
            "items": {{
                "type": "object",
                "properties": {{
                    "query": {
                        "type": "string",
                        "description": "The SERP query."
                    },
                    "researchGoal": {
                        "type": "string",
                        "description": "First talk about the goal of the research that this query is meant to accomplish, then go deeper into how to advance the research once the results are found, mention additional research directions. Be as specific as possible, especially for additional research directions. JSON reserved words should be escaped."
                    }
                }},
                "required": [
                    "query",
                    "researchGoal"
                ],
                "additionalProperties": false
            }},
            "description": "List of SERP queries.",
            "$schema": "http://json-schema.org/draft-07/schema#"
        }}
        ```

        Expected output:

        \`\`\`json
        [
        {{
            "query": "This is a sample query.",
            "researchGoal": "This is the reason for the query."
        }}
        ]
        \`\`\`
        """

        logger.info("Research Prompt: ", task_id=task_id, prompt=research_prompt)

        ai_service = AIAgentService(azure_manager)
        agent_name = f"thinking-agent-execute-{request_data.request.models_config.get('thinking', 'gpt-4').replace('-', '')}"
        
        # Step 1: Generate queries without Bing grounding
        logger.info("Step 1: Generating research queries", task_id=task_id)
        queries_response = await ai_service.generate_response(
            system_prompt=system_prompt.replace("'todaynow'", now),
            prompt=research_prompt,
            model_name=request_data.request.models_config.get("thinking", "gpt-4"),
            agent_name=agent_name,
            max_tokens=4096,
            use_bing_grounding=False  # No Bing grounding for query generation
        )

        # Parse the JSON response to extract queries
        try:
            # Extract JSON from markdown code blocks if present
            json_text = queries_response.strip()
            if '```json' in json_text:
                # Extract content between ```json and ```
                start_marker = '```json'
                end_marker = '```'
                start_index = json_text.find(start_marker)
                if start_index != -1:
                    start_index += len(start_marker)
                    end_index = json_text.find(end_marker, start_index)
                    if end_index != -1:
                        json_text = json_text[start_index:end_index].strip()
            
            queries_data = json.loads(json_text)
            if not isinstance(queries_data, list):
                raise ValueError("Response is not a JSON array")
        except (json.JSONDecodeError, ValueError) as e:
            logger.error("Failed to parse queries JSON", task_id=task_id, response=queries_response[:500], error=str(e))
            # Fallback: treat as single query
            queries_data = [{"query": request_data.topic, "researchGoal": "General research"}]

        logger.info("Generated queries", task_id=task_id, query_count=len(queries_data))

        # Step 2: Execute each query with Bing grounding
        aggregated_findings = []
        search_agent_name = f"task-agent-search-{request_data.request.models_config.get('task', 'gpt-4').replace('-', '')}"
        
        for i, query_item in enumerate(queries_data):
            query = query_item.get("query", "")
            research_goal = query_item.get("researchGoal", "")
            
            if not query.strip():
                continue
                
            logger.info(f"Step 2: Executing query {i+1}/{len(queries_data)}", task_id=task_id, query=query)
            
            # Execute individual query with Bing grounding
            query_prompt = f"""
Research Query: {query}
Research Goal: {research_goal}

Please provide comprehensive research findings for this specific query. Include relevant data, statistics, and factual information.
"""
            
            try:
                query_response = await ai_service.generate_response(
                    system_prompt=system_prompt.replace("'todaynow'", now),
                    prompt=query_prompt,
                    model_name=request_data.request.models_config.get("task", "gpt-4"),
                    agent_name=search_agent_name,
                    max_tokens=3072,
                    use_bing_grounding=True  # Enable Bing grounding for individual queries
                )
                
                # Aggregate the findings
                finding_entry = {
                    "query": query,
                    "research_goal": research_goal,
                    "findings": query_response,
                    "query_number": i + 1
                }
                aggregated_findings.append(finding_entry)
                
                logger.info(f"Completed query {i+1}/{len(queries_data)}", task_id=task_id, findings_length=len(query_response))
                
            except Exception as e:
                logger.error(f"Failed to execute query {i+1}", task_id=task_id, query=query, error=str(e))
                # Continue with other queries even if one fails
                finding_entry = {
                    "query": query,
                    "research_goal": research_goal,
                    "findings": f"Error executing query: {str(e)}",
                    "query_number": i + 1
                }
                aggregated_findings.append(finding_entry)

        # Format aggregated findings into a comprehensive report
        findings_text = "# Research Execution Results\n\n"
        findings_text += f"**Total Queries Executed:** {len(aggregated_findings)}\n\n"
        
        for finding in aggregated_findings:
            findings_text += f"## Query {finding['query_number']}: {finding['query']}\n\n"
            findings_text += f"**Research Goal:** {finding['research_goal']}\n\n"
            findings_text += f"**Findings:**\n{finding['findings']}\n\n"
            findings_text += "---\n\n"

        # Create report with aggregated research findings
        report = ResearchReport(
            task_id=task_id,
            title=f"Research Execution: {request_data.topic[:50]}...",
            executive_summary=f"Comprehensive research findings from {len(aggregated_findings)} targeted queries with real-time data",
            sections=[
                ResearchSection(
                    title="Research Findings",
                    content=findings_text,
                    sources=[],
                    confidence_score=0.9,
                    word_count=len(findings_text.split())
                )
            ],
            conclusions="Research execution completed with current information from multiple targeted searches",
            sources=[],
            metadata={
                "phase": "execute", 
                "topic": request_data.topic, 
                "plan": request_data.plan,
                "queries_executed": len(aggregated_findings),
                "aggregated_findings": aggregated_findings  # Store structured data for final report
            },
            word_count=len(findings_text.split()),
            reading_time_minutes=max(1, len(findings_text.split()) // 200)
        )

        return ResearchResponse(
            task_id=task_id,
            status=ResearchStatus.COMPLETED,
            message=f"Research execution completed successfully with {len(aggregated_findings)} queries",
            report=report
        )

    except Exception as e:
        logger.error("Failed to execute research", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to execute research: {str(e)}")


@router.post("/execute-tavily", response_model=ResearchResponse)
async def execute_research_with_tavily(
    request_data: ExecuteResearchRequest,
    azure_manager: AzureServiceManager = Depends(get_azure_manager)
):
    """Execute research based on the plan using Tavily search instead of Bing grounding."""
    try:
        task_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        # Step 1: Generate search queries (same as /execute - without Bing grounding)
        research_prompt = f"""
        This is the report plan after user confirmation:
        <PLAN>
        {request_data.plan}
        </PLAN>

        Based on previous report plan, generate a list of Serp queries to further research the topic. Make sure each query is unique and not similar to each other.

        You MUST respond in **JSON** matching this **JSON schema**:

        ```json
        {{{{
            "type": "array",
            "items": {{{{
                "type": "object",
                "properties": {{{{
                    "query": {{{{
                        "type": "string",
                        "description": "The SERP query."
                    }}}},
                    "researchGoal": {{{{
                        "type": "string",
                        "description": "First talk about the goal of the research that this query is meant to accomplish, then go deeper into how to advance the research once the results are found, mention additional research directions. Be as specific as possible, especially for additional research directions. JSON reserved words should be escaped."
                    }}}}
                }}}},
                "required": [
                    "query",
                    "researchGoal"
                ],
                "additionalProperties": false
            }}}},
            "description": "List of SERP queries.",
            "$schema": "http://json-schema.org/draft-07/schema#"
        }}}}
        ```

        Expected output:

        \\`\\`\\`json
        [
        {{{{
            "query": "This is a sample query.",
            "researchGoal": "This is the reason for the query."
        }}}}
        ]
        \\`\\`\\`
        """

        logger.info("Research Prompt: ", task_id=task_id, prompt=research_prompt)

        ai_service = AIAgentService(azure_manager)
        agent_name = f"thinking-agent-execute-tavily-{request_data.request.models_config.get('thinking', 'gpt-4').replace('-', '')}"
        
        # Step 1: Generate queries without Bing grounding (same as /execute)
        logger.info("Step 1: Generating research queries for Tavily", task_id=task_id)
        queries_response = await ai_service.generate_response(
            system_prompt=system_prompt.replace("'todaynow'", now),
            prompt=research_prompt,
            model_name=request_data.request.models_config.get("thinking", "gpt-4"),
            agent_name=agent_name,
            use_bing_grounding=False  # No Bing grounding for query generation
        )

        # Parse the JSON response to extract queries (same as /execute)
        try:
            # Extract JSON from markdown code blocks if present
            json_text = queries_response.strip()
            if '```json' in json_text:
                # Extract content between ```json and ```
                start_marker = '```json'
                end_marker = '```'
                start_index = json_text.find(start_marker)
                if start_index != -1:
                    start_index += len(start_marker)
                    end_index = json_text.find(end_marker, start_index)
                    if end_index != -1:
                        json_text = json_text[start_index:end_index].strip()
            
            queries_data = json.loads(json_text)
            if not isinstance(queries_data, list):
                raise ValueError("Response is not a JSON array")
        except (json.JSONDecodeError, ValueError) as e:
            logger.error("Failed to parse queries JSON", task_id=task_id, response=queries_response[:500], error=str(e))
            # Fallback: treat as single query
            queries_data = [{"query": request_data.topic, "researchGoal": "General research"}]

        logger.info("Generated queries for Tavily search", task_id=task_id, query_count=len(queries_data))

        # Step 2: Execute each query with Tavily search (NEW IMPLEMENTATION)
        aggregated_findings = []
        tavily_service = TavilySearchService()
        task_agent_name = f"task-agent-tavily-{request_data.request.models_config.get('task', 'gpt-4').replace('-', '')}"
        
        for i, query_item in enumerate(queries_data):
            query = query_item.get("query", "")
            research_goal = query_item.get("researchGoal", "")
            
            if not query.strip():
                continue
                
            logger.info(f"Step 2: Executing Tavily search {i+1}/{len(queries_data)}", task_id=task_id, query=query)
            
            try:
                # Perform Tavily search
                search_results = await tavily_service.search_and_format(
                    query=query,
                    research_goal=research_goal,
                    max_results=5
                )
                                
                context = search_results["context"]
                sources = search_results["sources"]
                images = search_results["images"]
                
                # Safety check: Ensure context doesn't exceed model limits
                MAX_CONTEXT_LENGTH = 230000  # Conservative limit for prompt context
                if len(context) > MAX_CONTEXT_LENGTH:
                    logger.warning(
                        "Context too long, truncating",
                        task_id=task_id,
                        query_number=i+1,
                        original_length=len(context),
                        max_length=MAX_CONTEXT_LENGTH
                    )
                    # Truncate at word boundary
                    truncated = context[:MAX_CONTEXT_LENGTH]
                    last_space = truncated.rfind(' ')
                    if last_space > MAX_CONTEXT_LENGTH * 0.9:
                        context = truncated[:last_space] + "..."
                    else:
                        context = truncated + "..."
                
                # Create search prompt for LLM with Tavily results
                search_prompt = f"""Given the following contexts from a SERP search for the query:
<QUERY>
{query}
</QUERY>

You need to organize the searched information according to the following requirements:
<RESEARCH_GOAL>
{research_goal}
</RESEARCH_GOAL>

The following context from the SERP search:
<CONTEXT>
{context}
</CONTEXT>

You need to think like a human researcher.
Generate a list of learnings from the contexts.
Make sure each learning is unique and not similar to each other.
The learnings should be to the point, as detailed and information dense as possible.
Make sure to include any entities like people, places, companies, products, things, etc in the learnings, as well as any specific entities, metrics, numbers, and dates when available. The learnings will be used to research the topic further.

Citation Rules:

- Please cite the context at the end of sentences when appropriate.
- Please use the format of citation number [number] to reference the context in corresponding parts of your answer.
- If a sentence comes from multiple contexts, please list all relevant citation numbers, e.g., [1][2]. Remember not to group citations at the end but list them in the corresponding parts of your answer.

**Respond in the same language as the user's language**
"""
                
                # Final safety check: Ensure total prompt length is within limits
                total_prompt_length = len(system_prompt) + len(search_prompt)
                MAX_TOTAL_PROMPT_LENGTH = 250000  # Very close to the 256KB limit
                
                if total_prompt_length > MAX_TOTAL_PROMPT_LENGTH:
                    logger.warning(
                        "Total prompt too long, reducing context further",
                        task_id=task_id,
                        query_number=i+1,
                        total_length=total_prompt_length,
                        max_length=MAX_TOTAL_PROMPT_LENGTH
                    )
                    # Calculate how much to reduce the context
                    excess_length = total_prompt_length - MAX_TOTAL_PROMPT_LENGTH
                    new_context_length = len(context) - excess_length - 1000  # Extra buffer
                    
                    if new_context_length > 1000:  # Ensure we still have meaningful context
                        truncated_context = context[:new_context_length]
                        last_space = truncated_context.rfind(' ')
                        if last_space > new_context_length * 0.9:
                            context = truncated_context[:last_space] + "..."
                        else:
                            context = truncated_context + "..."
                        
                        # Rebuild the search prompt with truncated context
                        search_prompt = f"""Given the following contexts from a SERP search for the query:
<QUERY>
{query}
</QUERY>

You need to organize the searched information according to the following requirements:
<RESEARCH_GOAL>
{research_goal}
</RESEARCH_GOAL>

The following context from the SERP search:
<CONTEXT>
{context}
</CONTEXT>

You need to think like a human researcher.
Generate a list of learnings from the contexts.
Make sure each learning is unique and not similar to each other.
The learnings should be to the point, as detailed and information dense as possible.
Make sure to include any entities like people, places, companies, products, things, etc in the learnings, as well as any specific entities, metrics, numbers, and dates when available. The learnings will be used to research the topic further.

Citation Rules:

- Please cite the context at the end of sentences when appropriate.
- Please use the format of citation number [number] to reference the context in corresponding parts of your answer.
- If a sentence comes from multiple contexts, please list all relevant citation numbers, e.g., [1][2]. Remember not to group citations at the end but list them in the corresponding parts of your answer.

**Respond in the same language as the user's language**
"""
                    else:
                        logger.error(
                            "Cannot reduce context sufficiently",
                            task_id=task_id,
                            query_number=i+1,
                            required_reduction=excess_length
                        )
                        raise Exception("Search context too large even after truncation")
                
                # Generate response using task model without grounding
                query_response = await ai_service.generate_response(
                    system_prompt=system_prompt.replace("'todaynow'", now),
                    prompt=search_prompt,
                    model_name=request_data.request.models_config.get("task", "gpt-4"),
                    agent_name=task_agent_name,
                    max_tokens=3072,
                    use_bing_grounding=False  # No Bing grounding - using Tavily results instead
                )
                
                # Aggregate the findings with Tavily metadata
                finding_entry = {
                    "query": query,
                    "research_goal": research_goal,
                    "findings": query_response,
                    "query_number": i + 1,
                    "sources_count": len(sources),
                    "search_method": "tavily"
                }
                aggregated_findings.append(finding_entry)
                
                logger.info(
                    f"Completed Tavily query {i+1}/{len(queries_data)}", 
                    task_id=task_id, 
                    findings_length=len(query_response),
                    sources_found=len(sources)
                )
                
            except Exception as e:
                error_message = str(e)
                
                # Check if it's a content length error
                if "string_above_max_length" in error_message or "string too long" in error_message:
                    logger.error(
                        f"Content length exceeded for Tavily query {i+1}",
                        task_id=task_id,
                        query=query,
                        error=error_message
                    )
                    finding_entry = {
                        "query": query,
                        "research_goal": research_goal,
                        "findings": "Search results were too large for processing. This query returned extensive content that exceeded model limits.",
                        "query_number": i + 1,
                        "sources_count": 0,
                        "search_method": "tavily"
                    }
                else:
                    logger.error(f"Failed to execute Tavily query {i+1}", task_id=task_id, query=query, error=error_message)
                    finding_entry = {
                        "query": query,
                        "research_goal": research_goal,
                        "findings": f"Error executing Tavily search: {error_message}",
                        "query_number": i + 1,
                        "sources_count": 0,
                        "search_method": "tavily"
                    }
                
                aggregated_findings.append(finding_entry)

        # Format aggregated findings into a comprehensive report (same pattern as /execute)
        findings_text = "# Research Execution Results (Tavily Search)\n\n"
        findings_text += f"**Total Queries Executed:** {len(aggregated_findings)}\n"
        findings_text += f"**Search Method:** Tavily API\n\n"
        
        for finding in aggregated_findings:
            findings_text += f"## Query {finding['query_number']}: {finding['query']}\n\n"
            findings_text += f"**Research Goal:** {finding['research_goal']}\n\n"
            findings_text += f"**Sources Found:** {finding['sources_count']}\n\n"
            findings_text += f"**Findings:**\n{finding['findings']}\n\n"
            findings_text += "---\n\n"

        # Create report with aggregated research findings
        report = ResearchReport(
            task_id=task_id,
            title=f"Research Execution (Tavily): {request_data.topic[:50]}...",
            executive_summary=f"Comprehensive research findings from {len(aggregated_findings)} targeted queries using Tavily search API",
            sections=[
                ResearchSection(
                    title="Research Findings (Tavily Search)",
                    content=findings_text,
                    sources=[],
                    confidence_score=0.9,
                    word_count=len(findings_text.split())
                )
            ],
            conclusions="Research execution completed using Tavily search with current information from multiple targeted searches",
            sources=[],
            metadata={
                "phase": "execute_tavily", 
                "topic": request_data.topic, 
                "plan": request_data.plan,
                "queries_executed": len(aggregated_findings),
                "search_method": "tavily",
                "aggregated_findings": aggregated_findings  # Store structured data for final report
            },
            word_count=len(findings_text.split()),
            reading_time_minutes=max(1, len(findings_text.split()) // 200)
        )

        return ResearchResponse(
            task_id=task_id,
            status=ResearchStatus.COMPLETED,
            message=f"Research execution completed successfully with Tavily search - {len(aggregated_findings)} queries processed",
            report=report
        )

    except Exception as e:
        logger.error("Failed to execute research with Tavily", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to execute research with Tavily: {str(e)}")


@router.post("/final-report", response_model=ResearchResponse)
async def generate_final_report(
    request_data: FinalReportRequest,
    azure_manager: AzureServiceManager = Depends(get_azure_manager)
):
    """Generate the final research report."""
    try:
        task_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        # Extract aggregated findings from the research execution if available
        aggregated_data = ""
        if request_data.findings:
            # Use the findings directly (they should contain the aggregated research data)
            aggregated_data = request_data.findings
        else:
            aggregated_data = "No detailed findings provided."
        
        report_prompt = f"""
        This is the report plan after user confirmation:
        <PLAN>
        {request_data.plan}
        </PLAN>

        Here are all the learnings from previous research:
        <LEARNINGS>
        {aggregated_data}
        </LEARNINGS>

        Please write according to the user's writing requirements, if any:
        <REQUIREMENT>
        {request_data.requirement}
        </REQUIREMENT>

        The original research topic user requested is:
        <QUERY>
        {request_data.topic}
        </QUERY>

        Write a final report based on the report plan using the learnings from research.
        Make it as detailed as possible, aim for 5 pages or more, the more the better, include ALL the learnings from research.
        **Respond only the final report content, and no additional text before or after.**
        """

        ai_service = AIAgentService(azure_manager)
        agent_name = f"thinking-agent-finalreport-{request_data.request.models_config.get('thinking', 'gpt-4').replace('-', '') if request_data.request else 'gpt4'}"
        response_text = await ai_service.generate_response(
            system_prompt=system_prompt.replace("'todaynow'", now),
            prompt=report_prompt,
            model_name=request_data.request.models_config.get("thinking", "gpt-4"),
            agent_name=agent_name,
            max_tokens=8192  # Increased for comprehensive report
        )

        report = ResearchReport(
            task_id=task_id,
            title=f"Final Report: {request_data.topic[:50]}...",
            executive_summary="Comprehensive research report with analysis and recommendations based on detailed findings",
            sections=[
                ResearchSection(
                    title="Final Research Report", 
                    content=response_text,
                    sources=[],
                    confidence_score=0.95,
                    word_count=len(response_text.split())
                )
            ],
            conclusions="Research completed successfully with comprehensive analysis",
            sources=[],
            metadata={
                "phase": "final_report", 
                "topic": request_data.topic,
                "plan": request_data.plan,
                "findings_used": len(aggregated_data.split('\n')) if aggregated_data else 0
            },
            word_count=len(response_text.split()),
            reading_time_minutes=max(1, len(response_text.split()) // 200)
        )

        return ResearchResponse(
            task_id=task_id,
            status=ResearchStatus.COMPLETED,
            message="Final report generated successfully with comprehensive findings",
            report=report
        )

    except Exception as e:
        logger.error("Failed to generate final report", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to generate final report: {str(e)}")


@router.post("/customexport", response_model=ResearchResponse)
async def generate_custom_powerpoint(
    request_data: CustomExportRequest,
    azure_manager: AzureServiceManager = Depends(get_azure_manager)
):
    """Generate custom PowerPoint slides from markdown content."""
    try:
        task_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        # Format slide titles for the prompt
        slide_titles_str = '\\n'.join([f"- {title}" for title in request_data.slide_titles])
        
        # Create the specialized prompt for PowerPoint conversion
        powerpoint_prompt = f"""
You are an expert presentation-generation AI tasked with converting detailed Markdown research reports into structured PowerPoint slide content, strictly adhering to the provided PPTX template.

---

**Inputs Provided:**  
- **Markdown Research Report:**  
'''markdown
{request_data.markdown_content}
'''

- **PowerPoint Slide Titles (Template Structure):**  
{slide_titles_str}

---

**Task:**  
Parse the provided Markdown report and map its content accurately to each corresponding slide title provided in the PowerPoint template structure.

- Match each Markdown section heading (e.g., `# Company Snapshot`, `## Key Company Metrics`) exactly with the provided slide titles.
- Clean the Markdown formatting: remove unnecessary details, but preserve important bullet points, numerical metrics, short summaries, and key insights.
- Each slide's content should be concise, structured, and suitable for PowerPoint presentations (brief bullets, short sentences, no lengthy paragraphs).
- Clearly indicate if a certain section has limited information or is missing from the Markdown.

---

**Output (Strict JSON Structure):**  
Produce a JSON object exactly in the following format, which can later be programmatically converted to PPTX slides:

{{
  "slides": [
    {{
      "title": "Company Snapshot",
      "content": [
        "Bullet or short sentence 1",
        "Bullet or short sentence 2",
        "... (up to 5-7 concise bullets per slide)"
      ]
    }},
    {{
      "title": "Key Company Metrics",
      "content": [
        "Metric 1: value (short description)",
        "Metric 2: value (short description)",
        "..."
      ]
    }},
    {{
      "title": "Sales Mix",
      "content": [
        "Segment A: percentage/share",
        "Segment B: percentage/share",
        "..."
      ]
    }},
    {{
      "title": "Revenue by Segment",
      "content": [
        "Segment X: revenue figure",
        "Segment Y: revenue figure",
        "..."
      ]
    }},
    {{
      "title": "Businesses Overview",
      "content": [
        "Business Unit 1: Brief summary",
        "Business Unit 2: Brief summary",
        "..."
      ]
    }},
    {{
      "title": "Stock Graph History",
      "content": [
        "Performance summary (e.g., total return, key highs/lows, major catalysts)",
        "Recent stock trends"
      ]
    }},
    {{
      "title": "Considerations",
      "content": {{
        "Strengths": ["Strength 1", "..."],
        "Weaknesses": ["Weakness 1", "..."],
        "Opportunities": ["Opportunity 1", "..."],
        "Risks": ["Risk 1", "..."]
      }}
    }},
    {{
      "title": "Third-Party Perspectives and Multiples",
      "content": [
        "Analyst consensus view (e.g., Strong Buy)",
        "Valuation metrics (P/E, EV/EBITDA)",
        "Peer benchmarking summary"
      ]
    }},
    {{
      "title": "Credit Perspectives",
      "content": [
        "Credit rating overview",
        "Debt/Liquidity position summary",
        "Key credit risks"
      ]
    }},
    {{
      "title": "Equity Perspectives",
      "content": [
        "Investor sentiment summary",
        "Stock ownership structure",
        "Recent equity performance versus peers"
      ]
    }},
    {{
      "title": "Board of Directors",
      "content": [
        "Key board members and their roles",
        "Board composition summary (expertise areas)"
      ]
    }}
  ]
}}

---

**Rules:**  
- Include **only information from the provided Markdown**; do not invent or extrapolate.
- Maintain the exact slide-title order from the PPTX template.
- If information is unavailable for a particular slide, state clearly: `"Content unavailable in provided Markdown."`
- **CRITICAL: Return ONLY the JSON object, no additional text, explanations, or markdown formatting.**

Begin now.
"""

        ai_service = AIAgentService(azure_manager)
        agent_name = f"thinking-agent-customexport-{request_data.request.models_config.get('thinking', 'gpt-4').replace('-', '') if request_data.request else 'chat4'}"
        
        # Generate the slide-ready JSON
        response_text = await ai_service.generate_response(
            system_prompt=system_prompt.replace("'todaynow'", now),
            prompt=powerpoint_prompt,
            model_name=request_data.request.models_config.get("thinking", "gpt-4") if request_data.request else "chat4",
            agent_name=agent_name,
            max_tokens=8192
        )

        # Parse the JSON response
        try:
            import json
            import re
            
            # Clean the response text - remove markdown code blocks and extra text
            cleaned_response = response_text.strip()
            
            # Try to extract JSON from markdown code blocks first
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', cleaned_response, re.DOTALL)
            if json_match:
                cleaned_response = json_match.group(1)
            else:
                # Look for JSON object pattern without code blocks
                json_match = re.search(r'(\{.*\})', cleaned_response, re.DOTALL)
                if json_match:
                    cleaned_response = json_match.group(1)
            
            # Parse the cleaned JSON
            slides_data = json.loads(cleaned_response)
            
            # Validate structure
            if not isinstance(slides_data, dict) or "slides" not in slides_data:
                raise ValueError("Response is not a valid slides JSON structure")
                
            # Validate slides array
            if not isinstance(slides_data["slides"], list) or len(slides_data["slides"]) == 0:
                raise ValueError("Slides array is empty or invalid")
                
            logger.info("Successfully parsed slides JSON", task_id=task_id, slide_count=len(slides_data["slides"]))
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error("Failed to parse slides JSON", task_id=task_id, response=response_text[:500], error=str(e))
            # Create a fallback response
            slides_data = {
                "slides": [
                    {
                        "title": request_data.slide_titles[0] if request_data.slide_titles else "Generated Content",
                        "content": ["Failed to parse structured content", "Raw content available below", response_text[:500] + "..."]
                    }
                ]
            }

        # Create the PowerPoint file using the existing export service
        from app.services.export_service import ExportService
        export_service = ExportService(azure_manager)
        
        # Generate a temporary PowerPoint file
        pptx_file_path = await export_service.create_custom_powerpoint(
            slides_data=slides_data,
            topic=request_data.topic,
            template_name="sample"  # You can make this configurable
        )

        # Create a report with the JSON structure for download
        json_content = json.dumps(slides_data, indent=2)
        
        report = ResearchReport(
            task_id=task_id,
            title=f"Custom PowerPoint Export: {request_data.topic[:50]}...",
            executive_summary="Generated slide-ready JSON structure for custom PowerPoint template",
            sections=[
                ResearchSection(
                    title="PowerPoint Slides JSON Structure",
                    content=f"```json\n{json_content}\n```",
                    sources=[],
                    confidence_score=0.95,
                    word_count=len(json_content.split())
                )
            ],
            conclusions="PowerPoint slides generated successfully with structured content mapping",
            sources=[],
            metadata={
                "phase": "custom_export",
                "topic": request_data.topic,
                "slide_count": len(slides_data.get("slides", [])),
                "slide_titles": request_data.slide_titles,
                "pptx_file_path": pptx_file_path,
                "slides_data": slides_data  # Store for potential frontend download
            },
            word_count=len(json_content.split()),
            reading_time_minutes=max(1, len(json_content.split()) // 200)
        )

        return ResearchResponse(
            task_id=task_id,
            status=ResearchStatus.COMPLETED,
            message=f"Custom PowerPoint export completed successfully with {len(slides_data.get('slides', []))} slides",
            report=report
        )

    except Exception as e:
        logger.error("Failed to generate custom PowerPoint export", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to generate custom PowerPoint export: {str(e)}")
