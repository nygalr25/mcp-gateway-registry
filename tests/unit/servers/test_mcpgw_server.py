"""Unit tests for MCP Gateway Server tools and functionality."""

import pytest
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock

from registry.servers.mcpgw.server import (
    list_services,
    healthcheck_services,
    register_service,
    remove_service,
    toggle_service,
    add_server_to_scopes_groups,
    remove_server_from_scopes_groups,
    find_intelligent_tool
)


@pytest.fixture
def mock_server_data() -> Dict[str, Any]:
    """
    Provide mock server data for testing.
    
    Returns:
        Dict containing test server configuration
    """
    return {
        "name": "test-service",
        "description": "Test service for MCP Gateway",
        "base_url": "http://test-service:8000",
        "health_check_url": "http://test-service:8000/health",
        "tools": [
            {
                "name": "calculate",
                "description": "Performs mathematical calculations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {"type": "string"}
                    }
                }
            }
        ]
    }


@pytest.fixture
def mock_services_list() -> List[Dict[str, Any]]:
    """
    Provide mock list of services.
    
    Returns:
        List of service configurations
    """
    return [
        {
            "name": "service1",
            "description": "First test service",
            "status": "active"
        },
        {
            "name": "service2",
            "description": "Second test service",
            "status": "inactive"
        }
    ]


@pytest.mark.unit
async def test_list_services_tool() -> None:
    """Test the list services tool functionality."""
    # Arrange
    mock_response = [
        {"name": "service1", "status": "active"},
        {"name": "service2", "status": "inactive"}
    ]
    
    # Act
    result = await list_services()
    
    # Assert
    assert isinstance(result, list)
    assert len(result) > 0
    assert all("name" in service for service in result)
    assert all("status" in service for service in result)


@pytest.mark.unit
async def test_healthcheck_services_tool(
    mock_server_data: Dict[str, Any]
) -> None:
    """
    Test the health check services tool.
    
    Args:
        mock_server_data: Mock server configuration
    """
    # Act
    result = await healthcheck_services(
        server_name=mock_server_data["name"]
    )
    
    # Assert
    assert isinstance(result, dict)
    assert "status" in result
    assert "last_check" in result


@pytest.mark.unit
async def test_register_service_tool(
    mock_server_data: Dict[str, Any]
) -> None:
    """
    Test the service registration tool.
    
    Args:
        mock_server_data: Mock server configuration
    """
    # Act
    result = await register_service(
        server_data=mock_server_data
    )
    
    # Assert
    assert isinstance(result, dict)
    assert result["name"] == mock_server_data["name"]
    assert result["status"] == "registered"


@pytest.mark.unit
async def test_remove_service_tool(
    mock_server_data: Dict[str, Any]
) -> None:
    """
    Test the service removal tool.
    
    Args:
        mock_server_data: Mock server configuration
    """
    # First register a service
    await register_service(server_data=mock_server_data)
    
    # Act
    result = await remove_service(
        server_name=mock_server_data["name"]
    )
    
    # Assert
    assert isinstance(result, dict)
    assert result["status"] == "removed"


@pytest.mark.unit
async def test_toggle_service_tool(
    mock_server_data: Dict[str, Any]
) -> None:
    """
    Test the service toggle tool.
    
    Args:
        mock_server_data: Mock server configuration
    """
    # First register a service
    await register_service(server_data=mock_server_data)
    
    # Act - Disable service
    result = await toggle_service(
        server_name=mock_server_data["name"],
        enabled=False
    )
    
    # Assert
    assert isinstance(result, dict)
    assert result["status"] == "disabled"
    
    # Act - Enable service
    result = await toggle_service(
        server_name=mock_server_data["name"],
        enabled=True
    )
    
    # Assert
    assert result["status"] == "enabled"


@pytest.mark.unit
async def test_add_server_to_scopes_groups_tool(
    mock_server_data: Dict[str, Any]
) -> None:
    """
    Test adding server to scopes groups.
    
    Args:
        mock_server_data: Mock server configuration
    """
    # First register a service
    await register_service(server_data=mock_server_data)
    
    # Act
    groups = ["test-group-1", "test-group-2"]
    result = await add_server_to_scopes_groups(
        server_name=mock_server_data["name"],
        groups=groups
    )
    
    # Assert
    assert isinstance(result, dict)
    assert result["groups"] == groups


@pytest.mark.unit
async def test_remove_server_from_scopes_groups_tool(
    mock_server_data: Dict[str, Any]
) -> None:
    """
    Test removing server from scopes groups.
    
    Args:
        mock_server_data: Mock server configuration
    """
    # Setup - Register and add to groups
    await register_service(server_data=mock_server_data)
    groups = ["test-group-1", "test-group-2"]
    await add_server_to_scopes_groups(
        server_name=mock_server_data["name"],
        groups=groups
    )
    
    # Act
    result = await remove_server_from_scopes_groups(
        server_name=mock_server_data["name"],
        groups=groups
    )
    
    # Assert
    assert isinstance(result, dict)
    assert result["groups"] == []


@pytest.mark.unit
async def test_intelligent_tool_finder(
    mock_services_list: List[Dict[str, Any]]
) -> None:
    """
    Test the intelligent tool finder functionality.
    
    Args:
        mock_services_list: List of mock services
    """
    # Arrange
    query = "perform calculation"
    
    # Act
    result = await find_intelligent_tool(
        query=query,
        available_services=mock_services_list
    )
    
    # Assert
    assert isinstance(result, dict)
    assert "tool" in result
    assert "service" in result
    assert "confidence" in result
    assert 0 <= result["confidence"] <= 1
