"""
Unit tests for Deep Research backend API.

Tests core functionality including:
- Health endpoints
- Research API endpoints
- Export functionality
- Azure service integration
"""

import asyncio
import json
import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

import httpx
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import get_settings
from app.models.schemas import ResearchRequest, ResearchStatus, ExportFormat


# Test configuration
@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_azure_manager():
    """Mock Azure service manager."""
    mock_manager = Mock()
    mock_manager.is_initialized = True
    mock_manager.health_check = AsyncMock(return_value={
        "cosmos_db": True,
        "blob_storage": True,
        "key_vault": True,
        "ai_services": True
    })
    mock_manager.get_secret = AsyncMock(return_value="mock-api-key")
    return mock_manager


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_health_check_basic(self, client):
        """Test basic health check endpoint."""
        with patch('app.api.health.get_azure_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.health_check = AsyncMock(return_value={
                "cosmos_db": True,
                "blob_storage": True,
                "key_vault": True,
                "ai_services": True
            })
            mock_get_manager.return_value = mock_manager
            
            response = client.get("/api/v1/health/")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] in ["healthy", "degraded", "unhealthy"]
            assert "timestamp" in data
            assert "version" in data
            assert "azure_services" in data
    
    def test_readiness_check(self, client):
        """Test readiness probe endpoint."""
        with patch('app.api.health.get_azure_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.is_initialized = True
            mock_manager.health_check = AsyncMock(return_value={
                "cosmos_db": True,
                "blob_storage": True,
                "key_vault": True,
                "ai_services": True
            })
            mock_get_manager.return_value = mock_manager
            
            response = client.get("/api/v1/health/ready")
            assert response.status_code == 200
            
            data = response.json()
            assert data["ready"] is True
    
    def test_liveness_check(self, client):
        """Test liveness probe endpoint."""
        response = client.get("/api/v1/health/live")
        assert response.status_code == 200
        
        data = response.json()
        assert data["alive"] is True
        assert "timestamp" in data


class TestResearchEndpoints:
    """Test research API endpoints."""
    
    def test_get_available_models(self, client):
        """Test getting available AI models."""
        with patch('app.api.research.get_azure_manager') as mock_get_manager:
            mock_get_manager.return_value = Mock()
            
            response = client.get("/api/v1/research/models")
            assert response.status_code == 200
            
            data = response.json()
            assert isinstance(data, list)
            assert len(data) > 0
            
            # Check model structure
            model = data[0]
            assert "name" in model
            assert "display_name" in model
            assert "type" in model
            assert "max_tokens" in model
            assert "cost_per_1k_tokens" in model
    
    def test_start_research_valid_request(self, client):
        """Test starting a research task with valid request."""
        research_request = {
            "prompt": "What are the latest trends in artificial intelligence?",
            "models_config": {"thinking": "gpt-4", "task": "gpt-35-turbo"},
            "enable_web_search": True,
            "research_depth": "standard",
            "language": "en"
        }
        
        with patch('app.api.research.get_azure_manager') as mock_get_manager:
            mock_get_manager.return_value = Mock()
            
            with patch('app.services.research_orchestrator.ResearchOrchestrator') as mock_orchestrator:
                mock_instance = Mock()
                mock_orchestrator.return_value = mock_instance
                
                response = client.post("/api/v1/research/start", json=research_request)
                assert response.status_code == 200
                
                data = response.json()
                assert "task_id" in data
                assert data["status"] == "pending"
                assert "message" in data
                assert "websocket_url" in data
    
    def test_start_research_invalid_request(self, client):
        """Test starting research with invalid request."""
        invalid_request = {
            "prompt": "x",  # Too short
            "research_depth": "invalid_depth"
        }
        
        response = client.post("/api/v1/research/start", json=invalid_request)
        assert response.status_code == 422  # Validation error
    
    def test_get_research_status_not_found(self, client):
        """Test getting status for non-existent task."""
        with patch('app.api.research.get_azure_manager') as mock_get_manager:
            mock_get_manager.return_value = Mock()
            
            response = client.get("/api/v1/research/status/non-existent-task")
            assert response.status_code == 404


class TestExportEndpoints:
    """Test export API endpoints."""
    
    def test_create_export_valid_request(self, client):
        """Test creating an export with valid request."""
        export_request = {
            "task_id": "test-task-id",
            "format": "markdown",
            "include_sources": True,
            "include_metadata": True
        }
        
        with patch('app.api.export.get_azure_manager') as mock_get_manager:
            mock_get_manager.return_value = Mock()
            
            with patch('app.services.export_service.ExportService') as mock_export_service:
                mock_service = Mock()
                mock_export_service.return_value = mock_service
                
                response = client.post("/api/v1/export/", json=export_request)
                assert response.status_code == 200
                
                data = response.json()
                assert "export_id" in data
                assert data["status"] == "processing"
                assert data["format"] == "markdown"
    
    def test_get_export_status_not_found(self, client):
        """Test getting status for non-existent export."""
        with patch('app.api.export.get_azure_manager') as mock_get_manager:
            mock_get_manager.return_value = Mock()
            
            response = client.get("/api/v1/export/status/non-existent-export")
            assert response.status_code == 404


class TestModels:
    """Test Pydantic models and validation."""
    
    def test_research_request_validation(self):
        """Test ResearchRequest model validation."""
        # Valid request
        valid_data = {
            "prompt": "Test research prompt with sufficient length",
            "research_depth": "standard",
            "language": "en"
        }
        request = ResearchRequest(**valid_data)
        assert request.prompt == valid_data["prompt"]
        assert request.research_depth == "standard"
        assert request.enable_web_search is True  # Default value
    
    def test_research_request_invalid_depth(self):
        """Test ResearchRequest with invalid depth."""
        with pytest.raises(ValueError):
            ResearchRequest(
                prompt="Test prompt",
                research_depth="invalid_depth"
            )
    
    def test_research_request_invalid_language(self):
        """Test ResearchRequest with invalid language."""
        with pytest.raises(ValueError):
            ResearchRequest(
                prompt="Test prompt",
                language="invalid_lang"
            )


class TestConfiguration:
    """Test application configuration."""
    
    def test_settings_defaults(self):
        """Test default settings values."""
        settings = get_settings()
        assert settings.ENVIRONMENT == "development"
        assert settings.DEBUG is False
        assert settings.LOG_LEVEL == "INFO"
        assert isinstance(settings.ALLOWED_ORIGINS, list)
    
    def test_settings_validation(self):
        """Test settings validation."""
        from app.core.config import validate_production_settings, Settings
        
        # Test with missing production settings
        test_settings = Settings(ENVIRONMENT="production")
        
        # Should raise ValueError for missing required fields
        with pytest.raises(ValueError):
            validate_production_settings(test_settings)


class TestServices:
    """Test service classes."""
    
    @pytest.mark.asyncio
    async def test_research_orchestrator_initialization(self):
        """Test ResearchOrchestrator initialization."""
        from app.services.research_orchestrator import ResearchOrchestrator
        from app.models.schemas import ResearchRequest
        
        mock_azure_manager = Mock()
        mock_config = ResearchRequest(
            prompt="Test research prompt",
            models_config={"thinking": "gpt-4", "task": "gpt-35-turbo"}
        )
        
        orchestrator = ResearchOrchestrator(
            azure_manager=mock_azure_manager,
            task_id="test-task",
            config=mock_config
        )
        
        assert orchestrator.task_id == "test-task"
        assert orchestrator.config == mock_config
        assert orchestrator.status == ResearchStatus.PENDING
    
    def test_export_service_initialization(self):
        """Test ExportService initialization."""
        from app.services.export_service import ExportService
        
        mock_azure_manager = Mock()
        export_service = ExportService(mock_azure_manager)
        
        assert export_service.azure_manager == mock_azure_manager
        assert export_service.export_dir.exists()


# Integration tests
class TestIntegration:
    """Integration tests for full workflows."""
    
    @pytest.mark.asyncio
    async def test_full_research_workflow_mock(self):
        """Test complete research workflow with mocked services."""
        # This would test the full flow from request to completion
        # using mocked Azure services
        pass
    
    @pytest.mark.asyncio
    async def test_export_workflow_mock(self):
        """Test complete export workflow with mocked services."""
        # This would test the full export flow
        # using mocked Azure services
        pass


# Performance tests
class TestPerformance:
    """Performance and load tests."""
    
    def test_concurrent_health_checks(self, client):
        """Test multiple concurrent health check requests."""
        import concurrent.futures
        import threading
        
        def make_request():
            return client.get("/api/v1/health/live")
        
        # Test 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            responses = [future.result() for future in futures]
        
        # All requests should succeed
        assert all(r.status_code == 200 for r in responses)


# Fixtures for test data
@pytest.fixture
def sample_research_report():
    """Sample research report for testing."""
    from app.models.schemas import ResearchReport, ResearchSection
    
    sections = [
        ResearchSection(
            title="Introduction",
            content="This is the introduction section.",
            sources=[],
            confidence_score=0.9,
            word_count=50
        )
    ]
    
    return ResearchReport(
        task_id="test-task",
        title="Test Report",
        executive_summary="Test summary",
        sections=sections,
        conclusions="Test conclusions",
        sources=[],
        word_count=100,
        reading_time_minutes=1
    )


# Run tests with: pytest backend/tests/test_main.py -v
