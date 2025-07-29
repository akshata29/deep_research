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
    ExportRequest, ExportResponse, ExportFormat, ResearchReport, ExportMetadata
)
from app.services.export_service import ExportService
from app.services.export_metadata_manager import ExportMetadataManager


router = APIRouter()
logger = structlog.get_logger(__name__)


# Track export tasks
export_tasks: Dict[str, Dict] = {}

# Initialize export metadata manager
metadata_manager = ExportMetadataManager()


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
        
        # Create export metadata
        export_metadata = ExportMetadata(
            export_id=export_id,
            research_topic=placeholder_report.title,
            task_id=export_request.task_id,
            export_date=datetime.utcnow(),
            format=export_request.format,
            file_name=os.path.basename(file_path),
            file_path=file_path,
            file_size_bytes=file_size,
            status="completed",
            include_sources=export_request.include_sources,
            include_metadata=export_request.include_metadata,
            template_name=export_request.template_name,
            word_count=placeholder_report.word_count,
            sections_count=len(placeholder_report.sections)
        )
        
        # Save metadata
        metadata_manager.save_export_metadata(export_metadata)
        
        # Update export task status
        if export_id in export_tasks:
            export_tasks[export_id].update({
                "status": "completed",
                "file_path": file_path,
                "file_size_bytes": file_size,
                "completed_at": datetime.utcnow(),
                "download_url": f"/api/v1/export/download/{export_id}",
                "metadata": export_metadata
            })
        
        logger.info(
            "Export processing completed",
            export_id=export_id,
            file_size_bytes=file_size,
            format=export_request.format.value
        )
        
    except Exception as e:
        logger.error("Export processing failed", export_id=export_id, error=str(e), exc_info=True)
        
        # Create failed export metadata
        try:
            export_metadata = ExportMetadata(
                export_id=export_id,
                research_topic="Failed Export",
                task_id=export_request.task_id,
                export_date=datetime.utcnow(),
                format=export_request.format,
                file_name="",
                file_path="",
                file_size_bytes=0,
                status="failed",
                include_sources=export_request.include_sources,
                include_metadata=export_request.include_metadata,
                template_name=export_request.template_name
            )
            metadata_manager.save_export_metadata(export_metadata)
        except Exception as metadata_error:
            logger.error("Failed to save error metadata", error=str(metadata_error))
        
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
        
        # Check if export exists in metadata
        export_metadata = metadata_manager.get_export_metadata(export_id)
        if not export_metadata:
            raise HTTPException(
                status_code=404,
                detail="Export not found"
            )
        
        if export_metadata.status != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Export is not ready for download (status: {export_metadata.status})"
            )
        
        file_path = export_metadata.file_path
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(
                status_code=404,
                detail="Export file not found"
            )
        
        # Increment download count
        metadata_manager.increment_download_count(export_id)
        
        # Determine content type based on format
        format_type = export_metadata.format
        if format_type == ExportFormat.MARKDOWN:
            media_type = "text/markdown"
            filename = f"research_report_{export_id}.md"
        elif format_type == ExportFormat.PDF:
            media_type = "application/pdf"
            filename = f"research_report_{export_id}.pdf"
        elif format_type == ExportFormat.DOCX:
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            filename = f"research_report_{export_id}.docx"
        elif format_type == ExportFormat.PPTX:
            media_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
            filename = f"research_report_{export_id}.pptx"
        elif format_type == ExportFormat.HTML:
            media_type = "text/html"
            filename = f"research_report_{export_id}.html"
        elif format_type == ExportFormat.JSON:
            media_type = "application/json"
            filename = f"research_report_{export_id}.json"
        else:
            media_type = "application/octet-stream"
            filename = export_metadata.file_name or f"research_report_{export_id}"
        
        logger.info(
            "Serving export download",
            export_id=export_id,
            filename=filename,
            file_size=export_metadata.file_size_bytes,
            download_count=export_metadata.download_count
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
        # Check if export exists in metadata
        export_metadata = metadata_manager.get_export_metadata(export_id)
        if not export_metadata:
            raise HTTPException(
                status_code=404,
                detail="Export not found"
            )
        
        # Remove file if exists
        file_path = export_metadata.file_path
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            logger.info("Export file deleted", file_path=file_path)
        
        # Remove metadata
        metadata_manager.delete_export_metadata(export_id)
        
        # Remove task from memory if exists
        if export_id in export_tasks:
            del export_tasks[export_id]
        
        logger.info("Export task cleaned up", export_id=export_id)
        
        return {"message": "Export cleaned up successfully", "export_id": export_id}
        
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
    limit: Optional[int] = None,
    offset: int = 0,
    format_filter: Optional[str] = None,
    status_filter: Optional[str] = None,
    azure_manager: AzureServiceManager = Depends(get_azure_manager)
):
    """
    List all exports with metadata and optional filtering.
    
    Args:
        limit: Maximum number of exports to return
        offset: Number of exports to skip for pagination
        format_filter: Filter by export format (markdown, pdf, docx, pptx, html, json)
        status_filter: Filter by export status (processing, completed, failed)
        
    Returns:
        List of exports with metadata and total count
    """
    try:
        # Convert string format filter to ExportFormat enum if provided
        format_enum = None
        if format_filter:
            try:
                format_enum = ExportFormat(format_filter.lower())
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid format filter: {format_filter}"
                )
        
        # Get exports from metadata manager
        exports = metadata_manager.list_exports(
            limit=limit,
            offset=offset,
            format_filter=format_enum,
            status_filter=status_filter
        )
        
        # Convert to response format
        export_list = []
        for export_metadata in exports:
            export_dict = {
                "export_id": export_metadata.export_id,
                "task_id": export_metadata.task_id,
                "research_topic": export_metadata.research_topic,
                "format": export_metadata.format.value,
                "status": export_metadata.status,
                "file_name": export_metadata.file_name,
                "file_size_bytes": export_metadata.file_size_bytes,
                "export_date": export_metadata.export_date.isoformat(),
                "download_count": export_metadata.download_count,
                "last_accessed": export_metadata.last_accessed.isoformat() if export_metadata.last_accessed else None,
                "download_url": f"/api/v1/export/download/{export_metadata.export_id}" if export_metadata.status == "completed" else None,
                "word_count": export_metadata.word_count,
                "sections_count": export_metadata.sections_count,
                "include_sources": export_metadata.include_sources,
                "include_metadata": export_metadata.include_metadata,
                "template_name": export_metadata.template_name
            }
            export_list.append(export_dict)
        
        # Get total count for pagination
        all_exports = metadata_manager.list_exports()
        total_count = len(all_exports)
        
        return {
            "exports": export_list, 
            "total_count": total_count,
            "showing": len(export_list),
            "offset": offset
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to list exports", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to list export tasks"
        )


@router.post("/custom-powerpoint")
async def export_custom_powerpoint(
    request_data: dict,
    azure_manager: AzureServiceManager = Depends(get_azure_manager)
):
    """
    Export custom PowerPoint presentation from slides JSON data.
    
    Args:
        request_data: JSON containing slides_data, topic, and template_name
        
    Returns:
        PowerPoint file download
    """
    try:
        slides_data = request_data.get("slides_data")
        topic = request_data.get("topic", "Research Report")
        template_name = request_data.get("template_name", "business")
        
        if not slides_data:
            raise HTTPException(
                status_code=400,
                detail="slides_data is required"
            )
        
        # Generate export ID
        export_id = str(uuid.uuid4())
        
        logger.info("Creating custom PowerPoint export", topic=topic, template=template_name, export_id=export_id)
        
        # Initialize export service and metadata manager
        export_service = ExportService(azure_manager)
        metadata_manager = ExportMetadataManager()
        
        # Generate the PowerPoint file
        pptx_file_path = await export_service.create_custom_powerpoint(
            slides_data=slides_data,
            topic=topic,
            template_name=template_name
        )
        
        # Verify file exists
        if not os.path.exists(pptx_file_path):
            raise HTTPException(
                status_code=500,
                detail="Failed to generate PowerPoint file"
            )
        
        # Get file size
        file_size = os.path.getsize(pptx_file_path)
        
        # Create export metadata
        export_metadata = ExportMetadata(
            export_id=export_id,
            research_topic=topic,
            task_id="custom_powerpoint",
            export_date=datetime.utcnow(),
            format=ExportFormat.PPTX,
            file_name=os.path.basename(pptx_file_path),
            file_path=pptx_file_path,
            file_size_bytes=file_size,
            status="completed",
            template_name=template_name,
            word_count=len(slides_data.get('slides', [])),
            sections_count=len(slides_data.get('slides', []))
        )
        
        # Save metadata
        metadata_manager.save_export_metadata(export_metadata)
        
        # Generate download filename
        safe_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '-', '_')).rstrip()[:30]
        download_filename = f"{safe_topic}_custom_report.pptx"
        
        logger.info("Custom PowerPoint generated successfully", file_path=pptx_file_path, export_id=export_id)
        
        # Return file as streaming response
        return FileResponse(
            path=pptx_file_path,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            filename=download_filename,
            background=BackgroundTasks()  # Clean up file after download
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to export custom PowerPoint", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export custom PowerPoint: {str(e)}"
        )


@router.get("/storage-stats")
async def get_storage_stats(
    azure_manager: AzureServiceManager = Depends(get_azure_manager)
):
    """
    Get storage statistics for exports.
    
    Returns:
        Storage statistics including total files, size, downloads, and format breakdown
    """
    try:
        stats = metadata_manager.get_storage_stats()
        return {
            "success": True,
            "data": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to get storage stats", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve storage statistics"
        )


@router.post("/cleanup-old")
async def cleanup_old_exports(
    days_old: int = 30,
    azure_manager: AzureServiceManager = Depends(get_azure_manager)
):
    """
    Clean up exports older than specified days.
    
    Args:
        days_old: Number of days (default 30)
        
    Returns:
        List of cleaned up export IDs
    """
    try:
        if days_old < 1:
            raise HTTPException(
                status_code=400,
                detail="days_old must be at least 1"
            )
        
        cleaned_exports = metadata_manager.cleanup_old_exports(days_old)
        
        return {
            "success": True,
            "message": f"Cleaned up {len(cleaned_exports)} old exports",
            "cleaned_export_ids": cleaned_exports,
            "days_old": days_old
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to cleanup old exports", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to cleanup old exports"
        )
