"""
Pytest configuration and shared fixtures.
"""
import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, AsyncGenerator, Generator
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock

import pytest
import jwt
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Import our application and services
from registry.main import app
from registry.core.config import Settings
from registry.services.server_service import ServerService
from registry.search.service import FaissService
from registry.health.service import HealthMonitoringService
from registry.core.nginx_service import NginxConfigService

# Import test utilities
from tests.fixtures.factories import (
    ServerInfoFactory,
    create_multiple_servers,
    create_server_with_tools,
)

# Event loop fixture
@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

# Directory fixtures
@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)

@pytest.fixture
def test_settings(temp_dir: Path) -> Settings:
    """Create test settings with temporary directories."""
    test_settings = Settings(
        secret_key="test-secret-key-for-testing-only",
        admin_user="testadmin",
        admin_password="[REDACTED:PASSWORD]",
        container_app_dir=temp_dir / "app",
        container_registry_dir=temp_dir / "app" / "registry",
        container_log_dir=temp_dir / "app" / "logs",
        health_check_interval_seconds=60,  # Longer for tests
        embeddings_model_name="all-MiniLM-L6-v2",
        embeddings_model_dimensions=384,
    )
    
    # Create necessary directories
    test_settings.container_app_dir.mkdir(parents=True, exist_ok=True)
    test_settings.container_registry_dir.mkdir(parents=True, exist_ok=True)
    test_settings.container_log_dir.mkdir(parents=True, exist_ok=True)
    test_settings.servers_dir.mkdir(parents=True, exist_ok=True)
    test_settings.static_dir.mkdir(parents=True, exist_ok=True)
    test_settings.templates_dir.mkdir(parents=True, exist_ok=True)
    
    return test_settings

# New Authentication Fixtures
@pytest.fixture
def mock_keycloak_user_context() -> Dict[str, Any]:
    """Mock user context from Keycloak authentication."""
    return {
        "username": "testuser",
        "is_admin": False,
        "groups": ["mcp-servers-unrestricted"],
        "scopes": [
            "mcp-servers-unrestricted/read",
            "mcp-servers-unrestricted/execute"
        ],
        "accessible_servers": ["currenttime", "mcpgw"],
        "accessible_services": ["all"],
        "ui_permissions": {
            "toggle_service": ["all"],
            "modify_service": ["all"],
            "register_service": ["all"],
            "health_check_service": ["all"]
        }
    }

@pytest.fixture
def mock_admin_user_context() -> Dict[str, Any]:
    """Mock admin user context."""
    return {
        "username": "admin",
        "is_admin": True,
        "groups": ["mcp-servers-unrestricted", "admins"],
        "scopes": ["mcp-servers-unrestricted/read", "mcp-servers-unrestricted/execute"],
        "accessible_servers": ["all"],
        "accessible_services": ["all"],
        "ui_permissions": {
            "toggle_service": ["all"],
            "modify_service": ["all"],
            "register_service": ["all"],
            "health_check_service": ["all"]
        }
    }

@pytest.fixture
def mock_m2m_token() -> str:
    """Mock M2M JWT token for agent authentication."""
    payload = {
        "sub": "agent-test-m2m",
        "scope": "mcp-servers-unrestricted/read mcp-servers-unrestricted/execute",
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow(),
        "client_id": "agent-test-m2m"
    }
    return jwt.encode(payload, "test-secret", algorithm="HS256")

@pytest.fixture
def mock_enhanced_auth(monkeypatch, mock_keycloak_user_context):
    """Mock enhanced_auth dependency."""
    def mock_auth(session=None, authorization=None):
        return mock_keycloak_user_context
    
    monkeypatch.setattr("registry.auth.dependencies.enhanced_auth", mock_auth)
    return mock_auth

# Service Fixtures
@pytest.fixture
def mock_settings(test_settings: Settings, monkeypatch):
    """Mock the global settings for tests."""
    monkeypatch.setattr("registry.core.config.settings", test_settings)
    monkeypatch.setattr("registry.services.server_service.settings", test_settings)
    monkeypatch.setattr("registry.search.service.settings", test_settings)
    monkeypatch.setattr("registry.health.service.settings", test_settings)
    monkeypatch.setattr("registry.core.nginx_service.settings", test_settings)
    return test_settings

@pytest.fixture
def server_service(mock_settings: Settings) -> ServerService:
    """Create a fresh server service for testing."""
    service = ServerService()
    return service

@pytest.fixture
def mock_faiss_service() -> Mock:
    """Create a mock FAISS service."""
    mock_service = Mock(spec=FaissService)
    mock_service.initialize = AsyncMock()
    mock_service.add_or_update_service = AsyncMock()
    mock_service.search_services = AsyncMock(return_value=[])
    mock_service.save_data = AsyncMock()
    return mock_service

@pytest.fixture
def health_service() -> HealthMonitoringService:
    """Create a fresh health monitoring service for testing."""
    service = HealthMonitoringService()
    return service

@pytest.fixture
def nginx_service(mock_settings: Settings) -> NginxConfigService:
    """Create a fresh nginx service for testing."""
    service = NginxConfigService()
    return service

# Test Data Fixtures
@pytest.fixture
def sample_server() -> Dict[str, Any]:
    """Create a sample server for testing."""
    return ServerInfoFactory()

@pytest.fixture
def sample_servers() -> Dict[str, Dict[str, Any]]:
    """Create multiple sample servers for testing."""
    return create_multiple_servers(count=3)

@pytest.fixture
def server_with_tools() -> Dict[str, Any]:
    """Create a server with tools for testing."""
    return create_server_with_tools(num_tools=5)

# Client Fixtures
@pytest.fixture
def test_client() -> TestClient:
    """Create a test client for the FastAPI application."""
    return TestClient(app)

@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async client for testing."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
def authenticated_headers(mock_m2m_token) -> Dict[str, str]:
    """Create headers for authenticated requests."""
    return {
        "Authorization": f"Bearer {mock_m2m_token}"
    }

@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket for testing."""
    mock_ws = Mock()
    mock_ws.client = Mock()
    mock_ws.client.host = "127.0.0.1"
    mock_ws.client.port = 12345
    mock_ws.accept = AsyncMock()
    mock_ws.send_text = AsyncMock()
    mock_ws.receive_text = AsyncMock()
    mock_ws.close = AsyncMock()
    return mock_ws

# Cleanup Fixture
@pytest.fixture(autouse=True)
def cleanup_services():
    """Automatically cleanup services after each test."""
    yield
    # Reset global service states
    from registry.services.server_service import server_service
    from registry.health.service import health_service
    
    server_service.registered_servers.clear()
    server_service.service_state.clear()
    health_service.server_health_status.clear()
    health_service.server_last_check_time.clear()
    health_service.active_connections.clear()

# Test markers
pytest_mark_unit = pytest.mark.unit
pytest_mark_integration = pytest.mark.integration
pytest_mark_e2e = pytest.mark.e2e
pytest_mark_auth = pytest.mark.auth
pytest_mark_servers = pytest.mark.servers
pytest_mark_search = pytest.mark.search
pytest_mark_health = pytest.mark.health
pytest_mark_slow = pytest.mark.slow
