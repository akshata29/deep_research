"""
Export API endpoints for Deep Research application.

Handles export of research reports to various formats including:
- Markdown (raw and formatted)
- PDF generation using WeasyPrint
- PowerPoint presentations using python-pptx with custom templates
"""

import asyncio
import io
import os
import tempfile
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from fastapi.responses import StreamingResponse, FileResponse
import aiofiles

from app.core.azure_config import AzureServiceManager
from app.models.schemas import (
    ExportRequest, ExportResponse, ExportFormat, ResearchReport
)
from app.services.export_service import ExportService


router = APIRouter()
logger = structlog.get_logger(__name__)


# Track export tasks
export_tasks: Dict[str, Dict] = {}


async def get_azure_manager(request: Request) -> AzureServiceManager:
    """Dependency to get Azure service manager from app state."""
    if not hasattr(request.app.state, 'azure_manager'):
        raise HTTPException(
            status_code=503,
            detail="Azure services not initialized"
        )
    return request.app.state.azure_manager


@router.post("/", response_model=ExportResponse)
async def create_export(
    export_request: ExportRequest,
    background_tasks: BackgroundTasks,
    azure_manager: AzureServiceManager = Depends(get_azure_manager)
):
    """
    Create a new export task for a research report.
    
    Args:
        export_request: Export configuration and parameters
        background_tasks: FastAPI background tasks for async processing
        
    Returns:
        Export response with task ID and status
    """
    try:
        # Generate unique export ID
        export_id = str(uuid.uuid4())
        
        logger.info(
            "Creating export task",
            export_id=export_id,
            task_id=export_request.task_id,
            format=export_request.format.value,
            template=export_request.template_name
        )
        
        # TODO: Validate that the research task exists and is completed
        # This would query the research task storage
        
        # Initialize export service
        export_service = ExportService(azure_manager)
        
        # Store export task information
        export_tasks[export_id] = {
            "export_id": export_id,
            "request": export_request,
            "status": "processing",
            "created_at": datetime.utcnow(),
            "service": export_service
        }
        
        # Start export processing in background
        background_tasks.add_task(
            process_export,
            export_id,
            export_request,
            export_service
        )
        
        # Calculate estimated expiration (24 hours from now)
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        response = ExportResponse(
            export_id=export_id,
            status="processing",
            format=export_request.format,
            expires_at=expires_at
        )
        
        logger.info("Export task created", export_id=export_id)
        return response
        
    except Exception as e:
        logger.error("Failed to create export task", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create export task: {str(e)}"
        )


async def process_export(
    export_id: str,
    export_request: ExportRequest,
    export_service: ExportService
):
    """
    Background task to process export generation.
    
    Args:
        export_id: Export task identifier
        export_request: Export configuration
        export_service: Export service instance
    """
    try:
        logger.info("Starting export processing", export_id=export_id)
        
        # TODO: Retrieve the research report from storage
        # For now, create a placeholder report
        placeholder_report = create_placeholder_report(export_request.task_id)
        
        # Process the export based on format
        if export_request.format == ExportFormat.MARKDOWN:
            file_path = await export_service.export_markdown(
                report=placeholder_report,
                export_id=export_id,
                include_metadata=export_request.include_metadata
            )
        elif export_request.format == ExportFormat.PDF:
            file_path = await export_service.export_pdf(
                report=placeholder_report,
                export_id=export_id,
                include_sources=export_request.include_sources,
                include_metadata=export_request.include_metadata
            )
        elif export_request.format == ExportFormat.DOCX:
            file_path = await export_service.export_docx(
                report=placeholder_report,
                export_id=export_id,
                include_sources=export_request.include_sources,
                include_metadata=export_request.include_metadata
            )
        elif export_request.format == ExportFormat.PPTX:
            file_path = await export_service.export_pptx(
                report=placeholder_report,
                export_id=export_id,
                template_name=export_request.template_name,
                custom_branding=export_request.custom_branding
            )
        elif export_request.format == ExportFormat.HTML:
            file_path = await export_service.export_html(
                report=placeholder_report,
                export_id=export_id,
                include_sources=export_request.include_sources,
                include_metadata=export_request.include_metadata
            )
        elif export_request.format == ExportFormat.JSON:
            file_path = await export_service.export_json(
                report=placeholder_report,
                export_id=export_id,
                include_raw_data=True
            )
        else:
            raise ValueError(f"Unsupported export format: {export_request.format}")
        
        # Get file size
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        
        # Update export task status
        if export_id in export_tasks:
            export_tasks[export_id].update({
                "status": "completed",
                "file_path": file_path,
                "file_size_bytes": file_size,
                "completed_at": datetime.utcnow(),
                "download_url": f"/api/v1/export/download/{export_id}"
            })
        
        logger.info(
            "Export processing completed",
            export_id=export_id,
            file_size_bytes=file_size,
            format=export_request.format.value
        )
        
    except Exception as e:
        logger.error("Export processing failed", export_id=export_id, error=str(e), exc_info=True)
        
        # Update export task with error status
        if export_id in export_tasks:
            export_tasks[export_id].update({
                "status": "failed",
                "error": str(e),
                "completed_at": datetime.utcnow()
            })


def create_placeholder_report(task_id: str) -> ResearchReport:
    """
    Create a placeholder research report for testing.
    
    Args:
        task_id: Research task identifier
        
    Returns:
        Placeholder research report
    """
    from app.models.schemas import ResearchSection, SearchResult
    
    # Create sample sections
    sections = [
        ResearchSection(
            title="Executive Summary",
            content="This is a comprehensive research report on the requested topic. The analysis includes multiple perspectives and data sources to provide actionable insights.",
            sources=[],
            confidence_score=0.9,
            word_count=150
        ),
        ResearchSection(
            title="Market Analysis",
            content="## Current Market Conditions\n\nThe market shows strong growth indicators with several key trends emerging:\n\n- **Growth Rate**: 15% YoY increase\n- **Market Size**: $2.3B globally\n- **Key Players**: Company A, Company B, Company C\n\n### Regional Breakdown\n\n| Region | Market Share | Growth Rate |\n|--------|-------------|-------------|\n| North America | 45% | 12% |\n| Europe | 30% | 18% |\n| Asia Pacific | 25% | 22% |",
            sources=[
                SearchResult(
                    title="Market Research Report 2024",
                    url="https://example.com/market-report",
                    snippet="Latest market analysis shows continued growth",
                    relevance_score=0.95,
                    domain="example.com"
                )
            ],
            confidence_score=0.85,
            word_count=200
        ),
        ResearchSection(
            title="Key Findings",
            content="Based on our comprehensive analysis, the following key findings emerge:\n\n1. **Trend 1**: Significant shift towards digital transformation\n2. **Trend 2**: Increased focus on sustainability\n3. **Trend 3**: Growing demand for personalization\n\nThese trends indicate a fundamental change in the industry landscape.",
            sources=[],
            confidence_score=0.88,
            word_count=100
        )
    ]
    
    return ResearchReport(
        task_id=task_id,
        title="Deep Research Report",
        executive_summary="This report provides comprehensive analysis and insights on the requested research topic.",
        sections=sections,
        conclusions="The research indicates strong market opportunities with several key considerations for stakeholders.",
        sources=[],
        metadata={
            "research_type": "comprehensive",
            "models_used": ["gpt-4", "gpt-35-turbo"],
            "web_search_enabled": True,
            "export_generated": True
        },
        word_count=450,
        reading_time_minutes=3
    )


@router.get("/status/{export_id}", response_model=ExportResponse)
async def get_export_status(
    export_id: str,
    azure_manager: AzureServiceManager = Depends(get_azure_manager)
):
    """
    Get the current status of an export task.
    
    Args:
        export_id: Export task identifier
        
    Returns:
        Current export status and download information
    """
    try:
        if export_id not in export_tasks:
            raise HTTPException(
                status_code=404,
                detail="Export task not found"
            )
        
        task_info = export_tasks[export_id]
        
        response = ExportResponse(
            export_id=export_id,
            status=task_info["status"],
            format=task_info["request"].format,
            download_url=task_info.get("download_url"),
            file_size_bytes=task_info.get("file_size_bytes"),
            expires_at=task_info["created_at"] + timedelta(hours=24)
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get export status", export_id=export_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve export status"
        )


@router.get("/download/{export_id}")
async def download_export(
    export_id: str,
    azure_manager: AzureServiceManager = Depends(get_azure_manager)
):
    """
    Download the exported file.
    
    Args:
        export_id: Export task identifier
        
    Returns:
        File download response
    """
    try:
        if export_id not in export_tasks:
            raise HTTPException(
                status_code=404,
                detail="Export task not found"
            )
        
        task_info = export_tasks[export_id]
        
        if task_info["status"] != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Export is not ready for download (status: {task_info['status']})"
            )
        
        file_path = task_info.get("file_path")
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(
                status_code=404,
                detail="Export file not found"
            )
        
        # Determine content type based on format
        format_type = task_info["request"].format
        if format_type == ExportFormat.MARKDOWN:
            media_type = "text/markdown"
            filename = f"research_report_{export_id}.md"
        elif format_type == ExportFormat.PDF:
            media_type = "application/pdf"
            filename = f"research_report_{export_id}.pdf"
        elif format_type == ExportFormat.PPTX:
            media_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
            filename = f"research_report_{export_id}.pptx"
        else:
            media_type = "application/octet-stream"
            filename = f"research_report_{export_id}"
        
        logger.info(
            "Serving export download",
            export_id=export_id,
            filename=filename,
            file_size=task_info.get("file_size_bytes", 0)
        )
        
        return FileResponse(
            path=file_path,
            media_type=media_type,
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to download export", export_id=export_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to download export file"
        )


@router.delete("/cleanup/{export_id}")
async def cleanup_export(
    export_id: str,
    azure_manager: AzureServiceManager = Depends(get_azure_manager)
):
    """
    Clean up export files and task data.
    
    Args:
        export_id: Export task identifier
        
    Returns:
        Cleanup confirmation
    """
    try:
        if export_id not in export_tasks:
            raise HTTPException(
                status_code=404,
                detail="Export task not found"
            )
        
        task_info = export_tasks[export_id]
        
        # Remove file if exists
        file_path = task_info.get("file_path")
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            logger.info("Export file deleted", file_path=file_path)
        
        # Remove task from memory
        del export_tasks[export_id]
        
        logger.info("Export task cleaned up", export_id=export_id)
        
        return {"message": "Export task cleaned up successfully", "export_id": export_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to cleanup export", export_id=export_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to cleanup export task"
        )


@router.get("/list")
async def list_exports(
    azure_manager: AzureServiceManager = Depends(get_azure_manager)
):
    """
    List all export tasks.
    
    Returns:
        List of export tasks with their current status
    """
    try:
        export_list = []
        
        for export_id, task_info in export_tasks.items():
            export_list.append({
                "export_id": export_id,
                "task_id": task_info["request"].task_id,
                "format": task_info["request"].format.value,
                "status": task_info["status"],
                "created_at": task_info["created_at"].isoformat(),
                "file_size_bytes": task_info.get("file_size_bytes"),
                "download_url": task_info.get("download_url"),
                "expires_at": (task_info["created_at"] + timedelta(hours=24)).isoformat()
            })
        
        return {"exports": export_list, "total_count": len(export_list)}
        
    except Exception as e:
        logger.error("Failed to list exports", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to list export tasks"
        )
