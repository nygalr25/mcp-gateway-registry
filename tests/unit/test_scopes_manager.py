"""Unit tests for scopes manager functionality."""

import pytest
from pathlib import Path
from typing import Dict, Any

from registry.utils.scopes_manager import (
    add_server_to_scopes,
    add_server_to_groups,
    remove_server_from_scopes,
    remove_server_from_groups,
    update_server_scopes,
    trigger_auth_server_reload,
    read_scopes_file,
    write_scopes_file
)


@pytest.fixture
def sample_scopes_data() -> Dict[str, Any]:
    """
    Provide sample scopes data for testing.
    
    Returns:
        Dict containing test scopes configuration
    """
    return {
        "groups": {
            "mcp-servers-unrestricted": {
                "servers": ["existing-server"],
                "scopes": ["read", "execute"]
            }
        },
        "servers": {
            "existing-server": {
                "scopes": ["read", "execute"]
            }
        }
    }


@pytest.fixture
def temp_scopes_file(tmp_path: Path, sample_scopes_data: Dict[str, Any]) -> Path:
    """
    Create a temporary scopes file for testing.
    
    Args:
        tmp_path: Pytest temporary path fixture
        sample_scopes_data: Sample scopes configuration
        
    Returns:
        Path to temporary scopes file
    """
    scopes_file = tmp_path / "scopes.yml"
    write_scopes_file(sample_scopes_data, scopes_file)
    return scopes_file


@pytest.mark.unit
def test_add_server_to_scopes_unrestricted_only(
    temp_scopes_file: Path,
    sample_scopes_data: Dict[str, Any]
) -> None:
    """
    Test adding server to unrestricted scopes group only.
    
    Args:
        temp_scopes_file: Path to test scopes file
        sample_scopes_data: Sample scopes data
    """
    server_name = "new-server"
    
    # Act
    add_server_to_scopes(
        server_name=server_name,
        scopes_file=temp_scopes_file
    )
    
    # Assert
    updated_data = read_scopes_file(temp_scopes_file)
    assert server_name in updated_data["groups"]["mcp-servers-unrestricted"]["servers"]
    assert server_name in updated_data["servers"]
    assert "read" in updated_data["servers"][server_name]["scopes"]
    assert "execute" in updated_data["servers"][server_name]["scopes"]


@pytest.mark.unit
def test_add_server_to_groups_custom(
    temp_scopes_file: Path,
    sample_scopes_data: Dict[str, Any]
) -> None:
    """
    Test adding server to custom groups.
    
    Args:
        temp_scopes_file: Path to test scopes file
        sample_scopes_data: Sample scopes data
    """
    server_name = "custom-server"
    groups = ["group1", "group2"]
    
    # Act
    add_server_to_groups(
        server_name=server_name,
        groups=groups,
        scopes_file=temp_scopes_file
    )
    
    # Assert
    updated_data = read_scopes_file(temp_scopes_file)
    for group in groups:
        assert server_name in updated_data["groups"][group]["servers"]


@pytest.mark.unit
def test_remove_server_from_scopes(
    temp_scopes_file: Path,
    sample_scopes_data: Dict[str, Any]
) -> None:
    """
    Test removing server from scopes configuration.
    
    Args:
        temp_scopes_file: Path to test scopes file
        sample_scopes_data: Sample scopes data
    """
    server_name = "existing-server"
    
    # Act
    remove_server_from_scopes(
        server_name=server_name,
        scopes_file=temp_scopes_file
    )
    
    # Assert
    updated_data = read_scopes_file(temp_scopes_file)
    assert server_name not in updated_data["servers"]
    assert server_name not in updated_data["groups"]["mcp-servers-unrestricted"]["servers"]


@pytest.mark.unit
def test_remove_server_from_groups(
    temp_scopes_file: Path,
    sample_scopes_data: Dict[str, Any]
) -> None:
    """
    Test removing server from specific groups.
    
    Args:
        temp_scopes_file: Path to test scopes file
        sample_scopes_data: Sample scopes data
    """
    server_name = "existing-server"
    groups = ["mcp-servers-unrestricted"]
    
    # Act
    remove_server_from_groups(
        server_name=server_name,
        groups=groups,
        scopes_file=temp_scopes_file
    )
    
    # Assert
    updated_data = read_scopes_file(temp_scopes_file)
    for group in groups:
        assert server_name not in updated_data["groups"][group]["servers"]


@pytest.mark.unit
def test_update_server_scopes(
    temp_scopes_file: Path,
    sample_scopes_data: Dict[str, Any]
) -> None:
    """
    Test updating server scopes.
    
    Args:
        temp_scopes_file: Path to test scopes file
        sample_scopes_data: Sample scopes data
    """
    server_name = "existing-server"
    new_scopes = ["read", "write", "admin"]
    
    # Act
    update_server_scopes(
        server_name=server_name,
        scopes=new_scopes,
        scopes_file=temp_scopes_file
    )
    
    # Assert
    updated_data = read_scopes_file(temp_scopes_file)
    assert set(updated_data["servers"][server_name]["scopes"]) == set(new_scopes)


@pytest.mark.unit
async def test_trigger_auth_server_reload() -> None:
    """Test triggering auth server reload."""
    # Act
    result = await trigger_auth_server_reload()
    
    # Assert
    assert result is True


@pytest.mark.unit
def test_read_scopes_file(
    temp_scopes_file: Path,
    sample_scopes_data: Dict[str, Any]
) -> None:
    """
    Test reading scopes file.
    
    Args:
        temp_scopes_file: Path to test scopes file
        sample_scopes_data: Sample scopes data
    """
    # Act
    data = read_scopes_file(temp_scopes_file)
    
    # Assert
    assert data == sample_scopes_data


@pytest.mark.unit
def test_write_scopes_file(tmp_path: Path) -> None:
    """
    Test writing scopes file.
    
    Args:
        tmp_path: Pytest temporary path fixture
    """
    # Arrange
    test_file = tmp_path / "test_scopes.yml"
    test_data = {
        "groups": {},
        "servers": {}
    }
    
    # Act
    write_scopes_file(test_data, test_file)
    
    # Assert
    assert test_file.exists()
    read_data = read_scopes_file(test_file)
    assert read_data == test_data
