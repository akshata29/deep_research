"""
Export metadata management service.

Handles storage, retrieval, and management of export metadata using JSON files.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import structlog
from app.models.schemas import ExportMetadata, ExportFormat

logger = structlog.get_logger(__name__)


class ExportMetadataManager:
    """Manages export metadata storage and retrieval."""
    
    def __init__(self, exports_dir: str = "exports", metadata_file: str = "exports_metadata.json"):
        """Initialize the export metadata manager.
        
        Args:
            exports_dir: Directory to store exports
            metadata_file: JSON file to store metadata
        """
        self.exports_dir = Path(exports_dir)
        self.metadata_file = self.exports_dir / metadata_file
        
        # Create directories if they don't exist
        self.exports_dir.mkdir(exist_ok=True)
        
        # Initialize metadata file if it doesn't exist
        if not self.metadata_file.exists():
            self._save_metadata({})
            
        logger.info(
            "Export metadata manager initialized",
            exports_dir=str(self.exports_dir),
            metadata_file=str(self.metadata_file)
        )
    
    def _load_metadata(self) -> Dict[str, Dict]:
        """Load metadata from JSON file."""
        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning("Failed to load metadata, returning empty dict", error=str(e))
            return {}
    
    def _save_metadata(self, metadata: Dict[str, Dict]) -> None:
        """Save metadata to JSON file."""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, default=str)
        except Exception as e:
            logger.error("Failed to save metadata", error=str(e))
            raise
    
    def save_export_metadata(self, export_metadata: ExportMetadata) -> None:
        """Save export metadata.
        
        Args:
            export_metadata: Export metadata to save
        """
        try:
            metadata_dict = self._load_metadata()
            metadata_dict[export_metadata.export_id] = export_metadata.dict()
            self._save_metadata(metadata_dict)
            
            logger.info(
                "Export metadata saved",
                export_id=export_metadata.export_id,
                topic=export_metadata.research_topic,
                format=export_metadata.format
            )
        except Exception as e:
            logger.error(
                "Failed to save export metadata",
                export_id=export_metadata.export_id,
                error=str(e)
            )
            raise
    
    def get_export_metadata(self, export_id: str) -> Optional[ExportMetadata]:
        """Get metadata for a specific export.
        
        Args:
            export_id: Export identifier
            
        Returns:
            Export metadata if found, None otherwise
        """
        try:
            metadata_dict = self._load_metadata()
            if export_id not in metadata_dict:
                return None
            
            return ExportMetadata(**metadata_dict[export_id])
        except Exception as e:
            logger.error(
                "Failed to get export metadata",
                export_id=export_id,
                error=str(e)
            )
            return None
    
    def list_exports(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
        format_filter: Optional[ExportFormat] = None,
        status_filter: Optional[str] = None
    ) -> List[ExportMetadata]:
        """List all exports with optional filtering.
        
        Args:
            limit: Maximum number of exports to return
            offset: Number of exports to skip
            format_filter: Filter by export format
            status_filter: Filter by export status
            
        Returns:
            List of export metadata
        """
        try:
            metadata_dict = self._load_metadata()
            exports = []
            
            for export_data in metadata_dict.values():
                try:
                    export_metadata = ExportMetadata(**export_data)
                    
                    # Apply filters
                    if format_filter and export_metadata.format != format_filter:
                        continue
                    
                    if status_filter and export_metadata.status != status_filter:
                        continue
                    
                    exports.append(export_metadata)
                except Exception as e:
                    logger.warning(
                        "Failed to parse export metadata",
                        export_data=export_data,
                        error=str(e)
                    )
            
            # Sort by export date (newest first)
            exports.sort(key=lambda x: x.export_date, reverse=True)
            
            # Apply pagination
            if offset > 0:
                exports = exports[offset:]
            
            if limit:
                exports = exports[:limit]
            
            return exports
            
        except Exception as e:
            logger.error("Failed to list exports", error=str(e))
            return []
    
    def update_export_metadata(self, export_id: str, updates: Dict) -> bool:
        """Update specific fields of export metadata.
        
        Args:
            export_id: Export identifier
            updates: Dictionary of fields to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            metadata_dict = self._load_metadata()
            
            if export_id not in metadata_dict:
                logger.warning("Export not found for update", export_id=export_id)
                return False
            
            # Update fields
            metadata_dict[export_id].update(updates)
            self._save_metadata(metadata_dict)
            
            logger.info(
                "Export metadata updated",
                export_id=export_id,
                updates=updates
            )
            return True
            
        except Exception as e:
            logger.error(
                "Failed to update export metadata",
                export_id=export_id,
                error=str(e)
            )
            return False
    
    def delete_export_metadata(self, export_id: str) -> bool:
        """Delete export metadata.
        
        Args:
            export_id: Export identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            metadata_dict = self._load_metadata()
            
            if export_id not in metadata_dict:
                logger.warning("Export not found for deletion", export_id=export_id)
                return False
            
            del metadata_dict[export_id]
            self._save_metadata(metadata_dict)
            
            logger.info("Export metadata deleted", export_id=export_id)
            return True
            
        except Exception as e:
            logger.error(
                "Failed to delete export metadata",
                export_id=export_id,
                error=str(e)
            )
            return False
    
    def increment_download_count(self, export_id: str) -> bool:
        """Increment download count for an export.
        
        Args:
            export_id: Export identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            updates = {
                "download_count": self.get_export_metadata(export_id).download_count + 1 if self.get_export_metadata(export_id) else 1,
                "last_accessed": datetime.utcnow().isoformat()
            }
            return self.update_export_metadata(export_id, updates)
            
        except Exception as e:
            logger.error(
                "Failed to increment download count",
                export_id=export_id,
                error=str(e)
            )
            return False
    
    def cleanup_old_exports(self, days_old: int = 30) -> List[str]:
        """Clean up exports older than specified days.
        
        Args:
            days_old: Number of days after which exports are considered old
            
        Returns:
            List of cleaned up export IDs
        """
        try:
            metadata_dict = self._load_metadata()
            cutoff_date = datetime.utcnow().timestamp() - (days_old * 24 * 60 * 60)
            cleaned_exports = []
            
            for export_id, export_data in list(metadata_dict.items()):
                try:
                    export_metadata = ExportMetadata(**export_data)
                    if export_metadata.export_date.timestamp() < cutoff_date:
                        # Delete file if it exists
                        file_path = Path(export_metadata.file_path)
                        if file_path.exists():
                            file_path.unlink()
                        
                        # Remove metadata
                        del metadata_dict[export_id]
                        cleaned_exports.append(export_id)
                        
                except Exception as e:
                    logger.warning(
                        "Failed to cleanup export",
                        export_id=export_id,
                        error=str(e)
                    )
            
            if cleaned_exports:
                self._save_metadata(metadata_dict)
                logger.info(
                    "Cleaned up old exports",
                    count=len(cleaned_exports),
                    export_ids=cleaned_exports
                )
            
            return cleaned_exports
            
        except Exception as e:
            logger.error("Failed to cleanup old exports", error=str(e))
            return []
    
    def get_storage_stats(self) -> Dict:
        """Get storage statistics for exports.
        
        Returns:
            Dictionary with storage statistics
        """
        try:
            exports = self.list_exports()
            total_files = len(exports)
            total_size = sum(export.file_size_bytes for export in exports)
            total_downloads = sum(export.download_count for export in exports)
            
            # Group by format
            format_stats = {}
            for export in exports:
                format_name = export.format.value
                if format_name not in format_stats:
                    format_stats[format_name] = {"count": 0, "size": 0}
                format_stats[format_name]["count"] += 1
                format_stats[format_name]["size"] += export.file_size_bytes
            
            return {
                "total_files": total_files,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "total_downloads": total_downloads,
                "format_breakdown": format_stats,
                "average_file_size_mb": round((total_size / total_files) / (1024 * 1024), 2) if total_files > 0 else 0
            }
            
        except Exception as e:
            logger.error("Failed to get storage stats", error=str(e))
            return {}
