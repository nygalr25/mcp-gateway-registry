"""Unit tests for MCP CLI client functionality."""

import pytest
from typing import Dict, Any
from unittest.mock import Mock, patch
from click.testing import CliRunner

from registry.cli.mcp_client import (
    ping,
    list_services,
    call_service,
    authenticate,
    main
)


@pytest.fixture
def cli_runner() -> CliRunner:
    """
    Provide Click CLI test runner.
    
    Returns:
        CliRunner: Click test runner instance
    """
    return CliRunner()


@pytest.fixture
def mock_token() -> str:
    """
    Provide mock M2M authentication token.
    
    Returns:
        str: Mock JWT token
    """
    return "mock.jwt.token"


@pytest.fixture
def mock_service_response() -> Dict[str, Any]:
    """
    Provide mock service response data.
    
    Returns:
        Dict containing sample service response
    """
    return {
        "status": "success",
        "data": {
            "services": [
                {
                    "name": "test-service",
                    "status": "active",
                    "description": "Test service"
                }
            ]
        }
    }


@pytest.mark.unit
def test_ping_command(
    cli_runner: CliRunner,
    mock_token: str
) -> None:
    """
    Test the ping command functionality.
    
    Args:
        cli_runner: Click test runner
        mock_token: Mock authentication token
    """
    with patch('registry.cli.mcp_client.requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"status": "ok"}
        
        result = cli_runner.invoke(
            ping,
            ['--url', 'http://test-server', '--token', mock_token]
        )
        
        assert result.exit_code == 0
        assert "Server is alive" in result.output


@pytest.mark.unit
def test_list_command(
    cli_runner: CliRunner,
    mock_token: str,
    mock_service_response: Dict[str, Any]
) -> None:
    """
    Test the list services command.
    
    Args:
        cli_runner: Click test runner
        mock_token: Mock authentication token
        mock_service_response: Mock service data
    """
    with patch('registry.cli.mcp_client.requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_service_response
        
        result = cli_runner.invoke(
            list_services,
            ['--url', 'http://test-server', '--token', mock_token]
        )
        
        assert result.exit_code == 0
        assert "test-service" in result.output
        assert "active" in result.output


@pytest.mark.unit
def test_call_command(
    cli_runner: CliRunner,
    mock_token: str
) -> None:
    """
    Test the service call command.
    
    Args:
        cli_runner: Click test runner
        mock_token: Mock authentication token
    """
    with patch('registry.cli.mcp_client.requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "result": "calculation complete"
        }
        
        result = cli_runner.invoke(
            call_service,
            [
                '--url', 'http://test-server',
                '--token', mock_token,
                '--service', 'calculator',
                '--tool', 'add',
                '--params', '{"x": 1, "y": 2}'
            ]
        )
        
        assert result.exit_code == 0
        assert "calculation complete" in result.output


@pytest.mark.unit
def test_m2m_authentication(
    cli_runner: CliRunner
) -> None:
    """
    Test M2M authentication process.
    
    Args:
        cli_runner: Click test runner
    """
    with patch('registry.cli.mcp_client.requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "access_token": "new.jwt.token"
        }
        
        result = cli_runner.invoke(
            authenticate,
            [
                '--url', 'http://auth-server',
                '--client-id', 'test-client',
                '--client-secret', 'test-secret'
            ]
        )
        
        assert result.exit_code == 0
        assert "Authentication successful" in result.output
        assert "new.jwt.token" in result.output


@pytest.mark.unit
def test_error_handling(
    cli_runner: CliRunner,
    mock_token: str
) -> None:
    """
    Test CLI error handling.
    
    Args:
        cli_runner: Click test runner
        mock_token: Mock authentication token
    """
    # Test connection error
    with patch('registry.cli.mcp_client.requests.get') as mock_get:
        mock_get.side_effect = ConnectionError("Connection failed")
        
        result = cli_runner.invoke(
            ping,
            ['--url', 'http://test-server', '--token', mock_token]
        )
        
        assert result.exit_code != 0
        assert "Connection failed" in result.output
    
    # Test authentication error
    with patch('registry.cli.mcp_client.requests.get') as mock_get:
        mock_get.return_value.status_code = 401
        
        result = cli_runner.invoke(
            list_services,
            ['--url', 'http://test-server', '--token', 'invalid-token']
        )
        
        assert result.exit_code != 0
        assert "Authentication failed" in result.output


@pytest.mark.unit
def test_json_output_format(
    cli_runner: CliRunner,
    mock_token: str,
    mock_service_response: Dict[str, Any]
) -> None:
    """
    Test JSON output format option.
    
    Args:
        cli_runner: Click test runner
        mock_token: Mock authentication token
        mock_service_response: Mock service data
    """
    with patch('registry.cli.mcp_client.requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_service_response
        
        # Test with JSON output
        result = cli_runner.invoke(
            list_services,
            [
                '--url', 'http://test-server',
                '--token', mock_token,
                '--format', 'json'
            ]
        )
        
        assert result.exit_code == 0
        assert '"name": "test-service"' in result.output
        assert '"status": "active"' in result.output
