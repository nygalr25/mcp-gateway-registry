"""Integration tests for internal API endpoints."""

import pytest
from typing import Dict, Any
from fastapi.testclient import TestClient
from httpx import AsyncClient

from registry.main import app
from registry.core.config import Settings


@pytest.fixture
def test_server_data() -> Dict[str, Any]:
    """
    Provide test server registration data.
    
    Returns:
        Dict containing server configuration for testing
    """
    return {
        "name": "test-server",
        "description": "Test server for internal API",
        "base_url": "http://test-server:8000",
        "health_check_url": "http://test-server:8000/health",
        "tools": [
            {
                "name": "test-tool",
                "description": "Test tool",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "input": {"type": "string"}
                    }
                }
            }
        ]
    }


@pytest.mark.integration
async def test_internal_register_with_auth(
    async_client: AsyncClient,
    mock_enhanced_auth: Any,
    test_server_data: Dict[str, Any]
) -> None:
    """
    Test server registration with authentication.
    
    Args:
        async_client: Async HTTP client
        mock_enhanced_auth: Mocked authentication
        test_server_data: Test server data
    """
    response = await async_client.post(
        "/internal/register",
        json=test_server_data,
        headers={"Authorization": "Bearer test-token"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == test_server_data["name"]
    assert data["status"] == "registered"


@pytest.mark.integration
async def test_internal_register_without_auth(
    async_client: AsyncClient,
    test_server_data: Dict[str, Any]
) -> None:
    """
    Test server registration without authentication.
    
    Args:
        async_client: Async HTTP client
        test_server_data: Test server data
    """
    response = await async_client.post(
        "/internal/register",
        json=test_server_data
    )
    
    assert response.status_code == 401


@pytest.mark.integration
async def test_internal_remove_with_auth(
    async_client: AsyncClient,
    mock_enhanced_auth: Any,
    test_server_data: Dict[str, Any]
) -> None:
    """
    Test server removal with authentication.
    
    Args:
        async_client: Async HTTP client
        mock_enhanced_auth: Mocked authentication
        test_server_data: Test server data
    """
    # First register the server
    await async_client.post(
        "/internal/register",
        json=test_server_data,
        headers={"Authorization": "Bearer test-token"}
    )
    
    # Then remove it
    response = await async_client.post(
        "/internal/remove",
        json={"name": test_server_data["name"]},
        headers={"Authorization": "Bearer test-token"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "removed"


@pytest.mark.integration
async def test_internal_toggle_with_auth(
    async_client: AsyncClient,
    mock_enhanced_auth: Any,
    test_server_data: Dict[str, Any]
) -> None:
    """
    Test server toggle with authentication.
    
    Args:
        async_client: Async HTTP client
        mock_enhanced_auth: Mocked authentication
        test_server_data: Test server data
    """
    # First register the server
    await async_client.post(
        "/internal/register",
        json=test_server_data,
        headers={"Authorization": "Bearer test-token"}
    )
    
    # Toggle server off
    response = await async_client.post(
        "/internal/toggle",
        json={
            "name": test_server_data["name"],
            "enabled": False
        },
        headers={"Authorization": "Bearer test-token"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "disabled"


@pytest.mark.integration
async def test_internal_healthcheck_with_auth(
    async_client: AsyncClient,
    mock_enhanced_auth: Any,
    test_server_data: Dict[str, Any]
) -> None:
    """
    Test server health check with authentication.
    
    Args:
        async_client: Async HTTP client
        mock_enhanced_auth: Mocked authentication
        test_server_data: Test server data
    """
    # First register the server
    await async_client.post(
        "/internal/register",
        json=test_server_data,
        headers={"Authorization": "Bearer test-token"}
    )
    
    response = await async_client.post(
        "/internal/healthcheck",
        json={"name": test_server_data["name"]},
        headers={"Authorization": "Bearer test-token"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "last_check" in data


@pytest.mark.integration
async def test_internal_add_to_groups(
    async_client: AsyncClient,
    mock_enhanced_auth: Any,
    test_server_data: Dict[str, Any]
) -> None:
    """
    Test adding server to groups.
    
    Args:
        async_client: Async HTTP client
        mock_enhanced_auth: Mocked authentication
        test_server_data: Test server data
    """
    # First register the server
    await async_client.post(
        "/internal/register",
        json=test_server_data,
        headers={"Authorization": "Bearer test-token"}
    )
    
    groups = ["test-group-1", "test-group-2"]
    response = await async_client.post(
        "/internal/add-to-groups",
        json={
            "name": test_server_data["name"],
            "groups": groups
        },
        headers={"Authorization": "Bearer test-token"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["groups"] == groups


@pytest.mark.integration
async def test_internal_remove_from_groups(
    async_client: AsyncClient,
    mock_enhanced_auth: Any,
    test_server_data: Dict[str, Any]
) -> None:
    """
    Test removing server from groups.
    
    Args:
        async_client: Async HTTP client
        mock_enhanced_auth: Mocked authentication
        test_server_data: Test server data
    """
    # First register and add to groups
    await async_client.post(
        "/internal/register",
        json=test_server_data,
        headers={"Authorization": "Bearer test-token"}
    )
    
    groups = ["test-group-1", "test-group-2"]
    await async_client.post(
        "/internal/add-to-groups",
        json={
            "name": test_server_data["name"],
            "groups": groups
        },
        headers={"Authorization": "Bearer test-token"}
    )
    
    # Then remove from groups
    response = await async_client.post(
        "/internal/remove-from-groups",
        json={
            "name": test_server_data["name"],
            "groups": groups
        },
        headers={"Authorization": "Bearer test-token"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["groups"] == []


@pytest.mark.integration
async def test_internal_list_services(
    async_client: AsyncClient,
    mock_enhanced_auth: Any,
    test_server_data: Dict[str, Any]
) -> None:
    """
    Test listing all services.
    
    Args:
        async_client: Async HTTP client
        mock_enhanced_auth: Mocked authentication
        test_server_data: Test server data
    """
    # First register a server
    await async_client.post(
        "/internal/register",
        json=test_server_data,
        headers={"Authorization": "Bearer test-token"}
    )
    
    response = await async_client.get(
        "/internal/list-services",
        headers={"Authorization": "Bearer test-token"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert any(server["name"] == test_server_data["name"] for server in data)
