"""
Export Service for Deep Research application.

This service handles exporting research reports to various formats:
- Markdown (raw and formatted)
- PDF generation using ReportLab
- PowerPoint presentations using python-pptx with custom templates

Includes template management and Azure Storage integration for file hosting.
"""

import asyncio
import os
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import json

import structlog
from jinja2 import Environment, FileSystemLoader, Template
import markdown
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.colors import HexColor
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
import aiofiles

from app.core.azure_config import AzureServiceManager
from app.models.schemas import ResearchReport, ResearchSection, ExportFormat


logger = structlog.get_logger(__name__)


class ExportService:
    """
    Service for exporting research reports to various formats.
    
    Supports:
    - Markdown export with custom formatting
    - PDF generation with professional styling
    - PowerPoint presentations with template support
    - Azure Storage integration for file hosting
    """
    
    def __init__(self, azure_manager: AzureServiceManager):
        """
        Initialize Export Service.
        
        Args:
            azure_manager: Azure service manager instance
        """
        self.azure_manager = azure_manager
        
        # Template configuration
        self.templates_dir = Path(__file__).parent.parent / "templates"
        self.templates_dir.mkdir(exist_ok=True)
        
        # Initialize Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=True
        )
        
        # Export directory for temporary files
        self.export_dir = Path(tempfile.gettempdir()) / "deep_research_exports"
        self.export_dir.mkdir(exist_ok=True)
        
        # Template configurations
        self.pptx_templates = {
            "default": "default_template.pptx",
            "business": "business_template.pptx",
            "academic": "academic_template.pptx",
            "executive": "executive_template.pptx"
        }
        
        # Ensure templates exist
        asyncio.create_task(self._ensure_templates_exist())
    
    async def export_markdown(
        self,
        report: ResearchReport,
        export_id: str,
        include_metadata: bool = True
    ) -> str:
        """
        Export research report as Markdown.
        
        Args:
            report: Research report to export
            export_id: Export task identifier
            include_metadata: Whether to include report metadata
            
        Returns:
            Path to the generated Markdown file
        """
        try:
            logger.info("Exporting report as Markdown", export_id=export_id, task_id=report.task_id)
            
            # Generate Markdown content
            markdown_content = await self._generate_markdown_content(report, include_metadata)
            
            # Save to file
            file_path = self.export_dir / f"report_{export_id}.md"
            
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(markdown_content)
            
            logger.info("Markdown export completed", export_id=export_id, file_path=str(file_path))
            
            return str(file_path)
            
        except Exception as e:
            logger.error("Markdown export failed", export_id=export_id, error=str(e), exc_info=True)
            raise
    
    async def export_pdf(
        self,
        report: ResearchReport,
        export_id: str,
        include_sources: bool = True,
        include_metadata: bool = True
    ) -> str:
        """
        Export research report as PDF.
        
        Args:
            report: Research report to export
            export_id: Export task identifier
            include_sources: Whether to include source citations
            include_metadata: Whether to include report metadata
            
        Returns:
            Path to the generated PDF file
        """
        try:
            logger.info("Exporting report as PDF", export_id=export_id, task_id=report.task_id)
            
            # Generate PDF using ReportLab
            file_path = self.export_dir / f"report_{export_id}.pdf"
            
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._generate_pdf_with_reportlab(
                    report, str(file_path), include_sources, include_metadata
                )
            )
            
            logger.info("PDF export completed", export_id=export_id, file_path=str(file_path))
            
            return str(file_path)
            
        except Exception as e:
            logger.error("PDF export failed", export_id=export_id, error=str(e), exc_info=True)
            raise
    
    async def export_pptx(
        self,
        report: ResearchReport,
        export_id: str,
        template_name: Optional[str] = None,
        custom_branding: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Export research report as PowerPoint presentation.
        
        Args:
            report: Research report to export
            export_id: Export task identifier
            template_name: PPTX template to use
            custom_branding: Custom branding options
            
        Returns:
            Path to the generated PPTX file
        """
        try:
            logger.info(
                "Exporting report as PPTX",
                export_id=export_id,
                task_id=report.task_id,
                template=template_name
            )
            
            # Load template
            template_path = await self._get_pptx_template(template_name or "default")
            
            # Create presentation from template
            prs = Presentation(template_path)
            
            # Generate slides based on report content
            await self._populate_pptx_slides(prs, report, custom_branding)
            
            # Save presentation
            file_path = self.export_dir / f"report_{export_id}.pptx"
            
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: prs.save(str(file_path))
            )
            
            logger.info("PPTX export completed", export_id=export_id, file_path=str(file_path))
            
            return str(file_path)
            
        except Exception as e:
            logger.error("PPTX export failed", export_id=export_id, error=str(e), exc_info=True)
            raise
    
    async def _generate_markdown_content(
        self,
        report: ResearchReport,
        include_metadata: bool
    ) -> str:
        """Generate formatted Markdown content for the report."""
        lines = []
        
        # Title
        lines.append(f"# {report.title}")
        lines.append("")
        
        # Metadata
        if include_metadata:
            lines.append("## Report Information")
            lines.append("")
            lines.append(f"- **Generated**: {report.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            lines.append(f"- **Task ID**: `{report.task_id}`")
            lines.append(f"- **Word Count**: {report.word_count:,}")
            lines.append(f"- **Reading Time**: {report.reading_time_minutes} minutes")
            if report.metadata:
                for key, value in report.metadata.items():
                    lines.append(f"- **{key.replace('_', ' ').title()}**: {value}")
            lines.append("")
        
        # Executive Summary
        lines.append("## Executive Summary")
        lines.append("")
        lines.append(report.executive_summary)
        lines.append("")
        
        # Sections
        for section in report.sections:
            lines.append(f"## {section.title}")
            lines.append("")
            lines.append(section.content)
            lines.append("")
            
            # Add sources if available
            if section.sources:
                lines.append("### Sources")
                lines.append("")
                for i, source in enumerate(section.sources, 1):
                    lines.append(f"{i}. [{source.title}]({source.url})")
                    if source.snippet:
                        lines.append(f"   _{source.snippet}_")
                lines.append("")
        
        # Conclusions
        if report.conclusions:
            lines.append("## Conclusions")
            lines.append("")
            lines.append(report.conclusions)
            lines.append("")
        
        # All Sources
        if report.sources and include_metadata:
            lines.append("## References")
            lines.append("")
            for i, source in enumerate(report.sources, 1):
                lines.append(f"{i}. [{source.title}]({source.url})")
                if source.snippet:
                    lines.append(f"   _{source.snippet}_")
                if source.published_date:
                    lines.append(f"   Published: {source.published_date.strftime('%Y-%m-%d')}")
                lines.append("")
        
        return "\n".join(lines)
    
    def _generate_pdf_with_reportlab(
        self,
        report: ResearchReport,
        file_path: str,
        include_sources: bool,
        include_metadata: bool
    ) -> None:
        """Generate PDF using ReportLab."""
        doc = SimpleDocTemplate(file_path, pagesize=A4)
        story = []
        
        # Get styles
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=HexColor('#1a365d'),
            alignment=1  # Center alignment
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            spaceBefore=20,
            textColor=HexColor('#2d3748')
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=12,
            leading=14
        )
        
        # Title
        story.append(Paragraph(report.title, title_style))
        story.append(Spacer(1, 12))
        
        # Metadata
        if include_metadata:
            if report.created_at:
                story.append(Paragraph(f"<b>Generated:</b> {report.created_at.strftime('%Y-%m-%d %H:%M')}", body_style))
            if report.task_id:
                story.append(Paragraph(f"<b>Task ID:</b> {report.task_id}", body_style))
            story.append(Spacer(1, 20))
        
        # Summary
        if report.summary:
            story.append(Paragraph("Executive Summary", heading_style))
            story.append(Paragraph(report.summary, body_style))
            story.append(Spacer(1, 20))
        
        # Sections
        for section in report.sections:
            story.append(Paragraph(section.title, heading_style))
            
            # Clean up content for PDF
            content = section.content.replace('\n\n', '<br/><br/>')
            content = content.replace('\n', ' ')
            
            story.append(Paragraph(content, body_style))
            story.append(Spacer(1, 15))
        
        # Sources
        if include_sources and report.sources:
            story.append(PageBreak())
            story.append(Paragraph("Sources", heading_style))
            
            for i, source in enumerate(report.sources, 1):
                source_text = f"<b>[{i}]</b> {source.title}"
                if source.url:
                    source_text += f"<br/><i>{source.url}</i>"
                if source.author:
                    source_text += f"<br/>Author: {source.author}"
                if source.published_date:
                    source_text += f"<br/>Published: {source.published_date.strftime('%Y-%m-%d')}"
                
                story.append(Paragraph(source_text, body_style))
                story.append(Spacer(1, 10))
        
        # Build PDF
        doc.build(story)
    
    async def _populate_pptx_slides(
        self,
        prs: Presentation,
        report: ResearchReport,
        custom_branding: Optional[Dict[str, str]]
    ) -> None:
        """Populate PowerPoint slides with report content."""
        # Clear existing slides (keep only title slide)
        slide_count = len(prs.slides)
        for i in range(slide_count - 1, 0, -1):
            rId = prs.slides._sldIdLst[i].rId
            prs.part.drop_rel(rId)
            del prs.slides._sldIdLst[i]
        
        # Title slide
        title_slide = prs.slides[0]
        await self._populate_title_slide(title_slide, report, custom_branding)
        
        # Executive Summary slide
        summary_layout = prs.slide_layouts[1]  # Title and Content layout
        summary_slide = prs.slides.add_slide(summary_layout)
        await self._populate_summary_slide(summary_slide, report)
        
        # Section slides
        for section in report.sections:
            section_layout = prs.slide_layouts[1]  # Title and Content layout
            section_slide = prs.slides.add_slide(section_layout)
            await self._populate_section_slide(section_slide, section)
        
        # Key Findings slide (if applicable)
        findings_layout = prs.slide_layouts[1]
        findings_slide = prs.slides.add_slide(findings_layout)
        await self._populate_findings_slide(findings_slide, report)
        
        # Sources slide
        if report.sources:
            sources_layout = prs.slide_layouts[1]
            sources_slide = prs.slides.add_slide(sources_layout)
            await self._populate_sources_slide(sources_slide, report)
    
    async def _populate_title_slide(
        self,
        slide,
        report: ResearchReport,
        custom_branding: Optional[Dict[str, str]]
    ) -> None:
        """Populate the title slide."""
        title = slide.shapes.title
        subtitle = slide.placeholders[1]
        
        title.text = report.title
        
        subtitle_text = f"Deep Research Report\n"
        subtitle_text += f"Generated: {report.created_at.strftime('%B %d, %Y')}\n"
        subtitle_text += f"Reading Time: {report.reading_time_minutes} minutes"
        
        if custom_branding and "company" in custom_branding:
            subtitle_text += f"\n\nPrepared by: {custom_branding['company']}"
        
        subtitle.text = subtitle_text
    
    async def _populate_summary_slide(self, slide, report: ResearchReport) -> None:
        """Populate the executive summary slide."""
        title = slide.shapes.title
        content = slide.placeholders[1]
        
        title.text = "Executive Summary"
        content.text = report.executive_summary
    
    async def _populate_section_slide(self, slide, section: ResearchSection) -> None:
        """Populate a section slide."""
        title = slide.shapes.title
        content = slide.placeholders[1]
        
        title.text = section.title
        
        # Clean markdown formatting for PowerPoint
        clean_content = section.content.replace('**', '').replace('*', '').replace('#', '')
        
        # Truncate if too long
        if len(clean_content) > 500:
            clean_content = clean_content[:497] + "..."
        
        content.text = clean_content
    
    async def _populate_findings_slide(self, slide, report: ResearchReport) -> None:
        """Populate key findings slide."""
        title = slide.shapes.title
        content = slide.placeholders[1]
        
        title.text = "Key Findings"
        
        # Extract key points from sections
        key_points = []
        for section in report.sections:
            if "finding" in section.title.lower() or "key" in section.title.lower():
                # Extract bullet points or first few sentences
                lines = section.content.split('\n')
                for line in lines:
                    if line.strip().startswith(('-', '*', '1.', '2.', '3.')):
                        key_points.append(line.strip())
                    elif len(line.strip()) > 20 and len(key_points) < 5:
                        key_points.append(f"• {line.strip()[:100]}...")
        
        if not key_points:
            key_points = [f"• {report.conclusions[:100]}..."]
        
        content.text = '\n'.join(key_points[:6])  # Limit to 6 points
    
    async def _populate_sources_slide(self, slide, report: ResearchReport) -> None:
        """Populate sources slide."""
        title = slide.shapes.title
        content = slide.placeholders[1]
        
        title.text = "Sources"
        
        source_list = []
        for i, source in enumerate(report.sources[:8], 1):  # Limit to 8 sources
            source_list.append(f"{i}. {source.title}")
            if source.domain:
                source_list.append(f"   {source.domain}")
        
        content.text = '\n'.join(source_list)
    
    async def _get_pptx_template(self, template_name: str) -> str:
        """Get path to PPTX template file."""
        template_file = self.pptx_templates.get(template_name, self.pptx_templates["default"])
        template_path = self.templates_dir / template_file
        
        if not template_path.exists():
            # Create a basic template if it doesn't exist
            await self._create_default_pptx_template(template_path)
        
        return str(template_path)
    
    async def _create_default_pptx_template(self, template_path: Path) -> None:
        """Create a default PPTX template."""
        try:
            # Create a basic presentation template
            prs = Presentation()
            
            # Customize the default slide master
            title_slide_layout = prs.slide_layouts[0]
            slide = prs.slides.add_slide(title_slide_layout)
            
            title = slide.shapes.title
            subtitle = slide.placeholders[1]
            
            title.text = "Deep Research Report"
            subtitle.text = "Professional Research Analysis"
            
            # Save the template
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: prs.save(str(template_path))
            )
            
            logger.info("Created default PPTX template", template_path=str(template_path))
            
        except Exception as e:
            logger.error("Failed to create PPTX template", error=str(e))
    
    async def _ensure_templates_exist(self) -> None:
        """Ensure all required templates exist."""
        try:
            for template_name, template_file in self.pptx_templates.items():
                template_path = self.templates_dir / template_file
                if not template_path.exists():
                    await self._create_default_pptx_template(template_path)
            
            logger.info("All export templates verified")
            
        except Exception as e:
            logger.error("Failed to ensure templates exist", error=str(e))
    
    async def upload_to_azure_storage(self, file_path: str, blob_name: str) -> str:
        """
        Upload exported file to Azure Blob Storage.
        
        Args:
            file_path: Local file path
            blob_name: Blob name in storage
            
        Returns:
            Public URL of the uploaded file
        """
        try:
            blob_client = self.azure_manager.blob_client
            if not blob_client:
                raise ValueError("Azure Blob Storage not configured")
            
            container_name = "exports"
            
            # Upload file
            with open(file_path, 'rb') as data:
                blob_client.get_blob_client(
                    container=container_name,
                    blob=blob_name
                ).upload_blob(data, overwrite=True)
            
            # Generate public URL
            account_url = self.azure_manager.settings.STORAGE_ACCOUNT_URL
            public_url = f"{account_url}/{container_name}/{blob_name}"
            
            logger.info("File uploaded to Azure Storage", blob_name=blob_name, url=public_url)
            
            return public_url
            
        except Exception as e:
            logger.error("Failed to upload to Azure Storage", file_path=file_path, error=str(e))
            raise
    
    def cleanup_export_file(self, file_path: str) -> None:
        """Clean up temporary export file."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.debug("Export file cleaned up", file_path=file_path)
        except Exception as e:
            logger.warning("Failed to cleanup export file", file_path=file_path, error=str(e))
