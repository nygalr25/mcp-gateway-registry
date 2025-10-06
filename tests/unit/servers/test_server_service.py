"""Integration tests for server routes."""

import pytest
from typing import Dict, Any, List
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from tests.fixtures.factories import ServerInfoFactory


@pytest.mark.integration
@pytest.mark.servers
class TestServerRoutes:
    """Integration tests for server management routes."""

    @pytest.fixture
    def mock_enhanced_auth(self) -> Dict[str, Any]:
        """
        Provide enhanced authentication context for testing.
        
        Returns:
            Dict containing user permissions and authentication context
        """
        return {
            "username": "test_user",
            "is_admin": False,
            "groups": ["mcp-servers-unrestricted"],
            "scopes": [
                "mcp-servers-unrestricted/read",
                "mcp-servers-unrestricted/execute"
            ],
            "accessible_servers": ["calc-service", "translation-service"],
            "accessible_services": ["all"],
            "ui_permissions": {
                "toggle_service": ["calc-service"],
                "modify_service": ["calc-service"],
                "register_service": ["all"],
                "health_check_service": ["all"]
            }
        }

    @pytest.fixture
    def realistic_server_data(self) -> Dict[str, Any]:
        """
        Provide realistic server data for testing.
        
        Returns:
            Dict containing realistic server configuration
        """
        return {
            "server_name": "calculation-service",
            "name": "calculation-service",
            "description": "Advanced mathematical calculation service with multiple operations",
            "path": "/calc",
            "base_url": "http://calc-service:8000",
            "health_check_url": "http://calc-service:8000/health",
            "proxy_pass_url": "http://calc-service:8000",
            "tools": [
                {
                    "name": "add",
                    "description": "Adds two numbers",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "x": {"type": "number", "description": "First number"},
                            "y": {"type": "number", "description": "Second number"}
                        },
                        "required": ["x", "y"]
                    }
                },
                {
                    "name": "multiply",
                    "description": "Multiplies two numbers",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "x": {"type": "number"},
                            "y": {"type": "number"}
                        },
                        "required": ["x", "y"]
                    }
                }
            ],
            "tags": ["mathematics", "calculations", "arithmetic"],
            "num_tools": 2,
            "num_stars": 45,
            "is_python": True,
            "license": "MIT",
            "version": "1.2.0",
            "documentation_url": "http://calc-service:8000/docs"
        }

    @pytest.fixture
    def realistic_servers_list(self) -> List[Dict[str, Any]]:
        """
        Provide list of realistic servers for testing.
        
        Returns:
            List of server configurations with realistic data
        """
        return [
            {
                "server_name": "calculation-service",
                "path": "/calc",
                "description": "Mathematical calculations",
                "tools": ["add", "subtract", "multiply", "divide"]
            },
            {
                "server_name": "translation-service", 
                "path": "/translate",
                "description": "Language translation",
                "tools": ["translate", "detect_language"]
            },
            {
                "server_name": "restricted-service",
                "path": "/restricted",
                "description": "Restricted access service",
                "tools": ["admin_function"]
            }
        ]

    def test_dashboard_unauthorized(
        self,
        test_client: TestClient
    ) -> None:
        """Test dashboard access without authentication."""
        response = test_client.get("/", follow_redirects=False)
        assert response.status_code in [401, 403, 307, 302]

    def test_dashboard_authorized(
        self,
        test_client: TestClient,
        mock_enhanced_auth: Dict[str, Any]
    ) -> None:
        """
        Test dashboard access with enhanced authentication.
        
        Args:
            test_client: FastAPI test client
            mock_enhanced_auth: Mock enhanced authentication context
        """
        with patch('registry.services.server_service.server_service') as mock_service:
            mock_service.get_filtered_servers.return_value = {}
            mock_service.is_service_enabled.return_value = False
            
            response = test_client.get("/")
            assert response.status_code == 200
            assert "text/html" in response.headers["content-type"]

    def test_filtered_server_listings(
        self,
        test_client: TestClient,
        mock_enhanced_auth: Dict[str, Any],
        realistic_servers_list: List[Dict[str, Any]]
    ) -> None:
        """
        Test that server listings are filtered based on user permissions.
        
        Args:
            test_client: FastAPI test client
            mock_enhanced_auth: Mock enhanced authentication context
            realistic_servers_list: List of realistic server configurations
        """
        with patch('registry.services.server_service.server_service') as mock_service:
            # Return only accessible servers
            filtered_servers = {
                "/calc": realistic_servers_list[0],
                "/translate": realistic_servers_list[1]
            }
            mock_service.get_filtered_servers.return_value = filtered_servers
            
            response = test_client.get("/api/server_details/all")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert "/calc" in data
            assert "/translate" in data
            assert "/restricted" not in data

    def test_ui_permission_checks(
        self,
        test_client: TestClient,
        mock_enhanced_auth: Dict[str, Any],
        realistic_server_data: Dict[str, Any]
    ) -> None:
        """
        Test UI permission checks for different server actions.
        
        Args:
            test_client: FastAPI test client
            mock_enhanced_auth: Mock enhanced authentication context
            realistic_server_data: Realistic server test data
        """
        with patch('registry.services.server_service.server_service') as mock_service:
            mock_service.get_server_info.return_value = realistic_server_data
            
            # Test that user can toggle calc-service (has permission)
            mock_service.toggle_service.return_value = True
            response = test_client.post(f"/toggle{realistic_server_data['path']}", data={
                "enabled": "on"
            })
            assert response.status_code == 200
            
            # Test editing permitted service
            response = test_client.get(f"/edit{realistic_server_data['path']}")
            assert response.status_code == 200

    def test_permission_based_access_controls(
        self,
        test_client: TestClient,
        mock_enhanced_auth: Dict[str, Any]
    ) -> None:
        """
        Test access control based on user permissions.
        
        Args:
            test_client: FastAPI test client
            mock_enhanced_auth: Mock enhanced authentication context
        """
        restricted_server = {
            "server_name": "restricted-service",
            "path": "/restricted",
            "description": "Admin only service"
        }
        
        with patch('registry.services.server_service.server_service') as mock_service:
            mock_service.get_server_info.return_value = restricted_server
            mock_service.user_can_access_server_path.return_value = False
            
            # Should deny access to restricted service
            response = test_client.get("/api/server_details/restricted")
            assert response.status_code == 403

    def test_register_server_success(
        self,
        test_client: TestClient,
        mock_enhanced_auth: Dict[str, Any],
        realistic_server_data: Dict[str, Any]
    ) -> None:
        """
        Test successful server registration with realistic data.
        
        Args:
            test_client: FastAPI test client
            mock_enhanced_auth: Mock enhanced authentication context
            realistic_server_data: Realistic server test data
        """
        with patch('registry.api.server_routes.server_service') as mock_service, \
             patch('registry.search.service.faiss_service') as mock_faiss, \
             patch('registry.core.nginx_service.nginx_service') as mock_nginx, \
             patch('registry.health.service.health_service') as mock_health:
            
            mock_service.register_server.return_value = True
            mock_faiss.add_or_update_service = AsyncMock()
            mock_nginx.generate_config.return_value = True
            mock_health.broadcast_health_update = AsyncMock()
            mock_service.get_enabled_services.return_value = []
            mock_service.get_server_info.return_value = None
            
            response = test_client.post("/register", data={
                "name": realistic_server_data["server_name"],
                "description": realistic_server_data["description"],
                "path": realistic_server_data["path"],
                "proxy_pass_url": realistic_server_data["proxy_pass_url"],
                "tags": ",".join(realistic_server_data["tags"]),
                "num_tools": realistic_server_data["num_tools"],
                "num_stars": realistic_server_data["num_stars"],
                "is_python": realistic_server_data["is_python"],
                "license": realistic_server_data["license"],
            })
            
            assert response.status_code == 201
            data = response.json()
            assert data["message"] == "Service registered successfully"
            assert data["service"]["server_name"] == realistic_server_data["server_name"]

    def test_register_server_duplicate_path(
        self,
        test_client: TestClient,
        mock_enhanced_auth: Dict[str, Any],
        realistic_server_data: Dict[str, Any]
    ) -> None:
        """
        Test registering server with duplicate path.
        
        Args:
            test_client: FastAPI test client
            mock_enhanced_auth: Mock enhanced authentication context
            realistic_server_data: Realistic server test data
        """
        with patch('registry.api.server_routes.server_service') as mock_service:
            mock_service.register_server.return_value = False
            
            response = test_client.post("/register", data={
                "name": realistic_server_data["server_name"],
                "description": realistic_server_data["description"],
                "path": realistic_server_data["path"],
                "proxy_pass_url": realistic_server_data["proxy_pass_url"],
            })
            
            assert response.status_code == 400
            data = response.json()
            assert "already exists" in data["error"]

    def test_toggle_service_success(
        self,
        test_client: TestClient,
        mock_enhanced_auth: Dict[str, Any],
        realistic_server_data: Dict[str, Any]
    ) -> None:
        """
        Test successful service toggle with realistic data.
        
        Args:
            test_client: FastAPI test client
            mock_enhanced_auth: Mock enhanced authentication context
            realistic_server_data: Realistic server test data
        """
        with patch('registry.api.server_routes.server_service') as mock_service, \
             patch('registry.search.service.faiss_service') as mock_faiss, \
             patch('registry.core.nginx_service.nginx_service') as mock_nginx, \
             patch('registry.health.service.health_service') as mock_health:
            
            mock_service.get_server_info.return_value = realistic_server_data
            mock_service.toggle_service.return_value = True
            mock_faiss.add_or_update_service = AsyncMock()
            mock_nginx.generate_config.return_value = True
            mock_health.broadcast_health_update = AsyncMock()
            mock_service.get_enabled_services.return_value = []
            
            response = test_client.post(f"/toggle{realistic_server_data['path']}", data={
                "enabled": "on"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["service_path"] == realistic_server_data["path"]
            assert data["new_enabled_state"] is True

    def test_toggle_service_not_found(
        self,
        test_client: TestClient,
        mock_enhanced_auth: Dict[str, Any]
    ) -> None:
        """
        Test toggling non-existent service.
        
        Args:
            test_client: FastAPI test client
            mock_enhanced_auth: Mock enhanced authentication context
        """
        with patch('registry.api.server_routes.server_service') as mock_service:
            mock_service.get_server_info.return_value = None
            
            response = test_client.post("/toggle/nonexistent", data={
                "enabled": "on"
            })
            
            assert response.status_code == 404

    def test_get_server_details_success(
        self,
        test_client: TestClient,
        mock_enhanced_auth: Dict[str, Any],
        realistic_server_data: Dict[str, Any]
    ) -> None:
        """
        Test getting server details with realistic data.
        
        Args:
            test_client: FastAPI test client
            mock_enhanced_auth: Mock enhanced authentication context
            realistic_server_data: Realistic server test data
        """
        with patch('registry.api.server_routes.server_service') as mock_service:
            mock_service.get_server_info.return_value = realistic_server_data
            
            response = test_client.get(f"/api/server_details{realistic_server_data['path']}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["server_name"] == realistic_server_data["server_name"]

    def test_get_server_details_not_found(
        self,
        test_client: TestClient,
        mock_enhanced_auth: Dict[str, Any]
    ) -> None:
        """
        Test getting details for non-existent server.
        
        Args:
            test_client: FastAPI test client
            mock_enhanced_auth: Mock enhanced authentication context
        """
        with patch('registry.api.server_routes.server_service') as mock_service:
            mock_service.get_server_info.return_value = None
            
            response = test_client.get("/api/server_details/nonexistent")
            
            assert response.status_code == 404

    def test_get_all_server_details(
        self,
        test_client: TestClient,
        mock_enhanced_auth: Dict[str, Any],
        realistic_servers_list: List[Dict[str, Any]]
    ) -> None:
        """
        Test getting all server details with filtered results.
        
        Args:
            test_client: FastAPI test client
            mock_enhanced_auth: Mock enhanced authentication context
            realistic_servers_list: List of realistic server configurations
        """
        servers = {
            "/calc": realistic_servers_list[0],
            "/translate": realistic_servers_list[1]
        }
        
        with patch('registry.api.server_routes.server_service') as mock_service:
            mock_service.get_filtered_servers.return_value = servers
            
            response = test_client.get("/api/server_details/all")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert "/calc" in data
            assert "/translate" in data

    # New server service tests
    async def test_get_filtered_servers(
        self,
        test_client: TestClient,
        mock_enhanced_auth: Dict[str, Any],
        realistic_servers_list: List[Dict[str, Any]]
    ) -> None:
        """
        Test filtering servers based on user permissions.
        
        Args:
            test_client: FastAPI test client
            mock_enhanced_auth: Mock enhanced authentication context
            realistic_servers_list: List of realistic server configurations
        """
        with patch('registry.services.server_service.server_service') as mock_service:
            filtered_servers = {
                "/calc": realistic_servers_list[0],
                "/translate": realistic_servers_list[1]
            }
            mock_service.get_filtered_servers.return_value = filtered_servers
            
            response = test_client.get("/api/servers/filtered")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert all(server["server_name"] in ["calculation-service", "translation-service"] for server in data.values())

    async def test_get_all_servers_with_permissions(
        self,
        test_client: TestClient,
        mock_enhanced_auth: Dict[str, Any]
    ) -> None:
        """
        Test retrieving servers with permission information.
        
        Args:
            test_client: FastAPI test client
            mock_enhanced_auth: Mock enhanced authentication context
        """
        with patch('registry.services.server_service.server_service') as mock_service:
            servers_with_permissions = {
                "/calc": {
                    "server_name": "calculation-service",
                    "can_access": True,
                    "can_modify": True,
                    "can_toggle": True
                },
                "/restricted": {
                    "server_name": "restricted-service",
                    "can_access": False,
                    "can_modify": False,
                    "can_toggle": False
                }
            }
            mock_service.get_all_servers_with_permissions.return_value = servers_with_permissions
            
            response = test_client.get("/api/servers/permissions")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data["/calc"]["can_access"] is True
            assert data["/restricted"]["can_access"] is False

    def test_user_can_access_server_path(
        self,
        test_client: TestClient,
        mock_enhanced_auth: Dict[str, Any]
    ) -> None:
        """
        Test server path access permission checking.
        
        Args:
            test_client: FastAPI test client
            mock_enhanced_auth: Mock enhanced authentication context
        """
        with patch('registry.services.server_service.server_service') as mock_service:
            # Mock access control
            mock_service.user_can_access_server_path.side_effect = lambda path, user: path in ["/calc", "/translate"]
            
            # Test accessible server
            response = test_client.get("/api/access-check/calc")
            assert response.status_code == 200
            
            # Test restricted server
            response = test_client.get("/api/access-check/restricted")
            assert response.status_code == 403

    async def test_remove_server(
        self,
        test_client: TestClient,
        mock_enhanced_auth: Dict[str, Any],
        realistic_server_data: Dict[str, Any]
    ) -> None:
        """
        Test server removal functionality.
        
        Args:
            test_client: FastAPI test client
            mock_enhanced_auth: Mock enhanced authentication context
            realistic_server_data: Realistic server test data
        """
        with patch('registry.services.server_service.server_service') as mock_service:
            mock_service.remove_server.return_value = True
            mock_service.get_server_info.return_value = realistic_server_data
            
            response = test_client.delete(f"/api/servers{realistic_server_data['path']}")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "removed"
            assert data["server_name"] == realistic_server_data["server_name"]

    # Keep remaining original tests with updated auth...
    def test_refresh_service_success(
        self,
        test_client: TestClient,
        mock_enhanced_auth: Dict[str, Any],
        realistic_server_data: Dict[str, Any]
    ) -> None:
        """
        Test refreshing service with realistic data.
        
        Args:
            test_client: FastAPI test client
            mock_enhanced_auth: Mock enhanced authentication context
            realistic_server_data: Realistic server test data
        """
        with patch('registry.api.server_routes.server_service') as mock_service, \
             patch('registry.search.service.faiss_service') as mock_faiss:
            
            mock_service.get_server_info.return_value = realistic_server_data
            mock_service.is_service_enabled.return_value = True
            mock_faiss.add_or_update_service = AsyncMock()
            
            response = test_client.post(f"/api/refresh{realistic_server_data['path']}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["service_path"] == realistic_server_data["path"]
            assert data["status"] == "refreshed"

    def test_refresh_service_not_found(
        self,
        test_client: TestClient,
        mock_enhanced_auth: Dict[str, Any]
    ) -> None:
        """
        Test refreshing non-existent service.
        
        Args:
            test_client: FastAPI test client
            mock_enhanced_auth: Mock enhanced authentication context
        """
        with patch('registry.api.server_routes.server_service') as mock_service:
            mock_service.get_server_info.return_value = None
            
            response = test_client.post("/api/refresh/nonexistent")
            
            assert response.status_code == 404

    def test_edit_server_form_success(
        self,
        test_client: TestClient,
        mock_enhanced_auth: Dict[str, Any],
        realistic_server_data: Dict[str, Any]
    ) -> None:
        """
        Test getting edit server form with realistic data.
        
        Args:
            test_client: FastAPI test client
            mock_enhanced_auth: Mock enhanced authentication context
            realistic_server_data: Realistic server test data
        """
        with patch('registry.api.server_routes.server_service') as mock_service:
            mock_service.get_server_info.return_value = realistic_server_data
            
            response = test_client.get(f"/edit{realistic_server_data['path']}")
            
            assert response.status_code == 200
            assert "text/html" in response.headers["content-type"]

    def test_edit_server_form_not_found(
        self,
        test_client: TestClient,
        mock_enhanced_auth: Dict[str, Any]
    ) -> None:
        """
        Test getting edit form for non-existent server.
        
        Args:
            test_client: FastAPI test client
            mock_enhanced_auth: Mock enhanced authentication context
        """
        with patch('registry.api.server_routes.server_service') as mock_service:
            mock_service.get_server_info.return_value = None
            
            response = test_client.get("/edit/nonexistent")
            
            assert response.status_code == 404

    def test_edit_server_submit_success(
        self,
        test_client: TestClient,
        mock_enhanced_auth: Dict[str, Any],
        realistic_server_data: Dict[str, Any]
    ) -> None:
        """
        Test successful server edit submission with realistic data.
        
        Args:
            test_client: FastAPI test client
            mock_enhanced_auth: Mock enhanced authentication context
            realistic_server_data: Realistic server test data
        """
        with patch('registry.api.server_routes.server_service') as mock_service, \
             patch('registry.search.service.faiss_service') as mock_faiss, \
             patch('registry.core.nginx_service.nginx_service') as mock_nginx:
            
            mock_service.get_server_info.return_value = realistic_server_data
            mock_service.update_server.return_value = True
            mock_service.is_service_enabled.return_value = False
            mock_service.get_enabled_services.return_value = []
            mock_faiss.add_or_update_service = AsyncMock()
            mock_nginx.generate_config.return_value = True
            
            response = test_client.post(f"/edit{realistic_server_data['path']}", data={
                "name": "Updated Calculation Service",
                "description": realistic_server_data["description"],
                "proxy_pass_url": realistic_server_data["proxy_pass_url"],
            }, follow_redirects=False)
            
            # Should redirect to main page
            assert response.status_code == 303
            assert response.headers["location"] == "/"

    def test_edit_server_submit_not_found(
        self,
        test_client: TestClient,
        mock_enhanced_auth: Dict[str, Any]
    ) -> None:
        """
        Test editing non-existent server.
        
        Args:
            test_client: FastAPI test client
            mock_enhanced_auth: Mock enhanced authentication context
        """
        with patch('registry.api.server_routes.server_service') as mock_service:
            mock_service.get_server_info.return_value = None
            
            response = test_client.post("/edit/nonexistent", data={
                "name": "Test",
                "proxy_pass_url": "http://localhost:8000",
            })
            
            assert response.status_code == 404
