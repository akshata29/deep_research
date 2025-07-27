"""
User Settings API endpoints.

Handles user preferences, model configurations, and application settings.
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

import structlog

logger = structlog.get_logger(__name__)

router = APIRouter()


class UserSettings(BaseModel):
    """User settings model."""
    theme: str = Field(default="system", description="UI theme preference")
    notifications: Dict[str, bool] = Field(
        default_factory=lambda: {
            "email": True,
            "push": False,
            "taskCompletion": True,
            "errors": True,
        },
        description="Notification preferences"
    )
    research: Dict[str, Any] = Field(
        default_factory=lambda: {
            "defaultDepth": "standard",
            "maxSources": 20,
            "autoExport": False,
            "preferredFormat": "markdown",
            "defaultThinkingModel": "chato1",
            "defaultTaskModel": "chat4omini",
        },
        description="Research preferences"
    )
    privacy: Dict[str, Any] = Field(
        default_factory=lambda: {
            "dataRetention": 30,
            "shareAnalytics": False,
            "publicReports": False,
        },
        description="Privacy settings"
    )
    ai: Dict[str, Any] = Field(
        default_factory=lambda: {
            "model": "gpt-4",
            "temperature": 0.7,
            "maxTokens": 4000,
        },
        description="AI model preferences"
    )
    # Additional flat settings for form compatibility
    defaultThinkingModel: str = Field(default="chato1", description="Default thinking model")
    defaultTaskModel: str = Field(default="chat4omini", description="Default task model")
    defaultResearchDepth: str = Field(default="standard", description="Default research depth")
    defaultLanguage: str = Field(default="en", description="Default language")
    enableWebSearchByDefault: bool = Field(default=True, description="Enable web search by default")
    enableNotifications: bool = Field(default=True, description="Enable notifications")
    autoExportFormat: str = Field(default="pdf", description="Auto export format")
    maxConcurrentTasks: int = Field(default=3, description="Maximum concurrent tasks")
    defaultInstructions: str = Field(default="", description="Default instructions")
    themePreference: str = Field(default="system", description="Theme preference")
    enableTelemetry: bool = Field(default=True, description="Enable telemetry")


# In-memory storage for demonstration - in production, use a database
_user_settings: Dict[str, UserSettings] = {}


def get_current_user_id() -> str:
    """Get current user ID - mock implementation."""
    # In production, extract from JWT token or session
    return "default_user"


@router.get("/", response_model=UserSettings)
async def get_settings(user_id: str = Depends(get_current_user_id)) -> UserSettings:
    """
    Get user settings.
    
    Returns:
        UserSettings: Current user settings
    """
    try:
        # Return stored settings or default settings
        settings = _user_settings.get(user_id, UserSettings())
        
        logger.info("Retrieved user settings", user_id=user_id)
        return settings
        
    except Exception as e:
        logger.error("Failed to retrieve user settings", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve user settings"
        )


@router.put("/", response_model=UserSettings)
async def update_settings(
    settings: UserSettings,
    user_id: str = Depends(get_current_user_id)
) -> UserSettings:
    """
    Update user settings.
    
    Args:
        settings: Updated user settings
        user_id: Current user ID
        
    Returns:
        UserSettings: Updated settings
    """
    try:
        # Store the settings
        _user_settings[user_id] = settings
        
        logger.info(
            "Updated user settings", 
            user_id=user_id,
            thinking_model=settings.defaultThinkingModel,
            task_model=settings.defaultTaskModel
        )
        
        return settings
        
    except Exception as e:
        logger.error("Failed to update user settings", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to update user settings"
        )


@router.delete("/")
async def reset_settings(user_id: str = Depends(get_current_user_id)) -> Dict[str, str]:
    """
    Reset user settings to defaults.
    
    Args:
        user_id: Current user ID
        
    Returns:
        Success message
    """
    try:
        # Remove stored settings to fall back to defaults
        if user_id in _user_settings:
            del _user_settings[user_id]
        
        logger.info("Reset user settings to defaults", user_id=user_id)
        
        return {"message": "Settings reset to defaults"}
        
    except Exception as e:
        logger.error("Failed to reset user settings", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to reset user settings"
        )
