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
    ResearchPlanRequest, ExecuteResearchRequest, FinalReportRequest
)
from app.services.research_orchestrator import ResearchOrchestrator
from app.services.ai_agent_service import AIAgentService
from app.services.web_search_service import WebSearchService


router = APIRouter()
logger = structlog.get_logger(__name__)


# Active research tasks and WebSocket connections
active_tasks: Dict[str, Dict] = {}
websocket_connections: Dict[str, WebSocket] = {}


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
        questions_prompt = f"""You are a research planning expert. For the research topic "{request.prompt}", generate 3-5 clarifying questions that would help create a comprehensive research plan. 

Focus on:
- Scope and boundaries of the research
- Depth and specific aspects to explore  
- Methodology and approach preferences
- Target audience and use case

Present the questions in a clear, numbered format. Each question should help refine the research direction."""

        # Use thinking model for question generation
        ai_service = AIAgentService(azure_manager)
        response_text = await ai_service.generate_response(
            prompt=questions_prompt,
            model_name=request.models_config.get("thinking", "gpt-4"),
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
        
        plan_prompt = f"""Based on the research topic "{request_data.topic}" and the following feedback: "{request_data.feedback}", create a detailed research plan.

Include:
1. Research objectives and goals
2. Key questions to explore and investigate
3. Methodology and approach strategy
4. Expected outcomes and deliverables
5. Information sources to prioritize

Format as a structured, actionable research plan that will guide the information gathering phase."""

        ai_service = AIAgentService(azure_manager)
        response_text = await ai_service.generate_response(
            prompt=plan_prompt,
            model_name=request_data.request.models_config.get("thinking", "gpt-4"),
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
        
        # Create research execution prompt
        research_prompt = f"""Execute comprehensive research based on this plan: {request_data.plan}
        
Original topic: {request_data.topic}

Conduct thorough research using web search and provide detailed findings with sources. Focus on gathering factual, up-to-date information that addresses the research objectives."""

        # Create orchestrator for actual research execution
        orchestrator = ResearchOrchestrator(
            azure_manager=azure_manager,
            task_id=task_id,
            config=request_data.request
        )
        
        # Update the orchestrator's prompt
        orchestrator.config.prompt = research_prompt
        
        # Execute research synchronously and get the report
        await orchestrator.execute_research()
        research_report = orchestrator.get_report()

        return ResearchResponse(
            task_id=task_id,
            status=ResearchStatus.COMPLETED,
            message="Research execution completed successfully",
            report=research_report
        )

    except Exception as e:
        logger.error("Failed to execute research", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to execute research: {str(e)}")


@router.post("/final-report", response_model=ResearchResponse)
async def generate_final_report(
    request_data: FinalReportRequest,
    azure_manager: AzureServiceManager = Depends(get_azure_manager)
):
    """Generate the final research report."""
    try:
        task_id = str(uuid.uuid4())
        
        report_prompt = f"""Write a comprehensive, beautifully formatted research report in Markdown based on:

**Topic:** {request_data.topic}
**Research Plan:** {request_data.plan}
**Research Findings:** {request_data.findings}
{f"**Additional Requirements:** {request_data.requirement}" if request_data.requirement else ""}

Create a professional research report with proper Markdown formatting including:

# Executive Summary
A concise overview of key findings and recommendations

## Table of Contents
- Introduction
- Methodology  
- Key Findings
- Analysis & Insights
- Conclusions
- Recommendations
- Sources & References

## Introduction
Clear background and context for the research

## Methodology
How the research was conducted

## Key Findings
### Finding 1: [Title]
**Summary:** Brief description
**Details:** Comprehensive analysis
**Impact:** Significance and implications

### Finding 2: [Title]
[Continue pattern...]

## Analysis & Insights
Deep analysis with:
- **Trends:** Key patterns identified
- **Implications:** What this means
- **Opportunities:** Areas for growth/improvement
- **Challenges:** Potential obstacles

## Conclusions
Summary of the most important insights

## Recommendations
### Short-term Actions
1. **Action 1:** Description and rationale
2. **Action 2:** Description and rationale

### Long-term Strategy
1. **Strategy 1:** Description and rationale
2. **Strategy 2:** Description and rationale

## Sources & References
List of all sources consulted

Use proper Markdown formatting with headers (#, ##, ###), bold text (**text**), bullet points (-), numbered lists (1.), and code blocks when appropriate. Make it visually appealing and easy to read."""

        ai_service = AIAgentService(azure_manager)
        response_text = await ai_service.generate_response(
            prompt=report_prompt,
            model_name=request_data.request.models_config.get("thinking", "gpt-4") if request_data.request else "gpt-4",
            max_tokens=6144
        )

        report = ResearchReport(
            task_id=task_id,
            title=f"Final Report: {request_data.topic[:50]}...",
            executive_summary="Comprehensive research report with analysis and recommendations",
            sections=[
                ResearchSection(
                    title="Final Research Report", 
                    content=response_text,
                    sources=[],
                    confidence_score=0.95,
                    word_count=len(response_text.split())
                )
            ],
            conclusions="Research completed successfully",
            sources=[],
            metadata={"phase": "final_report", "topic": request_data.topic},
            word_count=len(response_text.split()),
            reading_time_minutes=max(1, len(response_text.split()) // 200)
        )

        return ResearchResponse(
            task_id=task_id,
            status=ResearchStatus.COMPLETED,
            message="Final report generated successfully",
            report=report
        )

    except Exception as e:
        logger.error("Failed to generate final report", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to generate final report: {str(e)}")
