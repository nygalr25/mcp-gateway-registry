"""Integration tests for server routes."""

import pytest
from typing import Dict, Any
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from tests.fixtures.factories import ServerInfoFactory


@pytest.mark.integration
@pytest.mark.servers
class TestServerRoutes:
    """Integration tests for server management routes."""

    async def test_dashboard_unauthorized(
        self,
        test_client: TestClient
    ) -> None:
        """Test dashboard access without authentication."""
        response = test_client.get("/", follow_redirects=False)
        assert response.status_code == 401

    async def test_dashboard_authorized_with_permissions(
        self,
        test_client: TestClient,
        mock_enhanced_auth: Any
    ) -> None:
        """
        Test dashboard access with proper authentication and permissions.
        
        Args:
            test_client: FastAPI test client
            mock_enhanced_auth: Mocked authentication with permissions
        """
        with patch('registry.services.server_service.server_service') as mock_service:
            mock_service.get_filtered_servers.return_value = {}
            mock_service.is_service_enabled.return_value = False
            
            response = test_client.get("/")
            assert response.status_code == 200
            assert "text/html" in response.headers["content-type"]

    async def test_dashboard_filtered_listings(
        self,
        test_client: TestClient,
        mock_enhanced_auth: Any
    ) -> None:
        """
        Test that dashboard only shows permitted servers.
        
        Args:
            test_client: FastAPI test client
            mock_enhanced_auth: Mocked authentication
        """
        servers = {
            "/permitted": ServerInfoFactory(name="permitted"),
            "/restricted": ServerInfoFactory(name="restricted")
        }
        
        with patch('registry.services.server_service.server_service') as mock_service:
            mock_service.get_filtered_servers.return_value = {
                "/permitted": servers["/permitted"]
            }
            
            response = test_client.get("/")
            assert response.status_code == 200
            content = response.text
            assert "permitted" in content
            assert "restricted" not in content

    async def test_ui_permission_checks(
        self,
        test_client: TestClient,
        mock_enhanced_auth: Any
    ) -> None:
        """
        Test UI permission checks for different actions.
        
        Args:
            test_client: FastAPI test client
            mock_enhanced_auth: Mocked authentication
        """
        server_data = ServerInfoFactory()
        
        # Test with restricted permissions
        restricted_auth = {
            **mock_enhanced_auth,
            "ui_permissions": {
                "toggle_service": [],
                "modify_service": [],
                "register_service": [],
                "health_check_service": []
            }
        }
        
        with patch('registry.auth.dependencies.enhanced_auth', return_value=restricted_auth):
            response = test_client.get("/")
            content = response.text
            assert "Register Server" not in content
            assert "Toggle Service" not in content
            assert "Edit Server" not in content

    async def test_register_server_with_groups(
        self,
        test_client: TestClient,
        mock_enhanced_auth: Any
    ) -> None:
        """
        Test server registration with group assignments.
        
        Args:
            test_client: FastAPI test client
            mock_enhanced_auth: Mocked authentication
        """
        server_data = ServerInfoFactory()
        groups = ["test-group-1", "test-group-2"]
        
        with patch('registry.api.server_routes.server_service') as mock_service, \
             patch('registry.utils.scopes_manager') as mock_scopes:
            
            mock_service.register_server.return_value = True
            mock_scopes.add_server_to_groups.return_value = True
            
            response = test_client.post("/register", json={
                **server_data,
                "groups": groups
            })
            
            assert response.status_code == 201
            data = response.json()
            assert data["groups"] == groups

    async def test_filtered_server_listing(
        self,
        test_client: TestClient,
        mock_enhanced_auth: Any
    ) -> None:
        """
        Test that server listings respect user permissions.
        
        Args:
            test_client: FastAPI test client
            mock_enhanced_auth: Mocked authentication
        """
        servers = {
            "/server1": ServerInfoFactory(name="server1"),
            "/server2": ServerInfoFactory(name="server2")
        }
        
        with patch('registry.api.server_routes.server_service') as mock_service:
            mock_service.get_filtered_servers.return_value = {
                "/server1": servers["/server1"]
            }
            
            response = test_client.get("/api/server_details/all")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert "/server1" in data
            assert "/server2" not in data

    # [Keep other existing tests but update them to use mock_enhanced_auth]
