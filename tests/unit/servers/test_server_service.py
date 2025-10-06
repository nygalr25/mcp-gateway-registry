"""Unit tests for server service functionality."""

import pytest
from typing import Dict, Any, List
from pathlib import Path
from unittest.mock import patch, Mock

from registry.services.server_service import ServerService
from registry.core.config import Settings
from tests.fixtures.factories import ServerInfoFactory


@pytest.mark.unit
class TestServerService:
    """Test suite for ServerService functionality."""

    @pytest.fixture
    def mock_user_context(self) -> Dict[str, Any]:
        """
        Provide mock user context for testing.
        
        Returns:
            Dict containing user permissions and groups
        """
        return {
            "username": "test_user",
            "groups": ["test-group"],
            "accessible_servers": ["server1", "server2"],
            "is_admin": False
        }

    async def test_get_filtered_servers(
        self,
        server_service: ServerService,
        mock_user_context: Dict[str, Any]
    ) -> None:
        """
        Test filtering servers based on user permissions.
        
        Args:
            server_service: Server service instance
            mock_user_context: Mock user context with permissions
        """
        # Arrange
        all_servers = {
            "/server1": ServerInfoFactory(name="server1"),
            "/server2": ServerInfoFactory(name="server2"),
            "/server3": ServerInfoFactory(name="server3")
        }
        server_service.registered_servers = all_servers

        # Act
        filtered_servers = await server_service.get_filtered_servers(
            user_context=mock_user_context
        )

        # Assert
        assert len(filtered_servers) == 2
        assert "/server1" in filtered_servers
        assert "/server2" in filtered_servers
        assert "/server3" not in filtered_servers

    async def test_get_all_servers_with_permissions(
        self,
        server_service: ServerService,
        mock_user_context: Dict[str, Any]
    ) -> None:
        """
        Test retrieving servers with permission information.
        
        Args:
            server_service: Server service instance
            mock_user_context: Mock user context with permissions
        """
        # Arrange
        servers = {
            "/server1": ServerInfoFactory(name="server1"),
            "/server2": ServerInfoFactory(name="server2")
        }
        server_service.registered_servers = servers

        # Act
        result = await server_service.get_all_servers_with_permissions(
            user_context=mock_user_context
        )

        # Assert
        assert len(result) == 2
        assert all("can_access" in server for server in result.values())
        assert result["/server1"]["can_access"] is True
        assert result["/server2"]["can_access"] is True

    def test_user_can_access_server_path(
        self,
        server_service: ServerService,
        mock_user_context: Dict[str, Any]
    ) -> None:
        """
        Test server path access permission checking.
        
        Args:
            server_service: Server service instance
            mock_user_context: Mock user context with permissions
        """
        # Test admin access
        admin_context = {**mock_user_context, "is_admin": True}
        assert server_service.user_can_access_server_path(
            server_path="/any-server",
            user_context=admin_context
        ) is True

        # Test regular user access
        assert server_service.user_can_access_server_path(
            server_path="/server1",
            user_context=mock_user_context
        ) is True
        
        assert server_service.user_can_access_server_path(
            server_path="/restricted",
            user_context=mock_user_context
        ) is False

    async def test_remove_server(
        self,
        server_service: ServerService,
        mock_user_context: Dict[str, Any]
    ) -> None:
        """
        Test server removal functionality.
        
        Args:
            server_service: Server service instance
            mock_user_context: Mock user context with permissions
        """
        # Arrange
        server_path = "/server1"
        server_data = ServerInfoFactory(name="server1")
        server_service.registered_servers = {server_path: server_data}

        # Act
        with patch('pathlib.Path.unlink') as mock_unlink:
            result = await server_service.remove_server(
                server_path=server_path,
                user_context=mock_user_context
            )

        # Assert
        assert result is True
        assert server_path not in server_service.registered_servers
        mock_unlink.assert_called_once()
