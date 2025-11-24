import pytest
from unittest.mock import patch, MagicMock
from lever_mcp.server import _list_candidates, _get_candidate, _create_requisition
import os

# Mock environment variable
os.environ["LEVER_API_KEY"] = "test_key"

@pytest.mark.asyncio
async def test_list_candidates():
    mock_response = {"data": [{"id": "123", "name": "John Doe"}]}
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = MagicMock(status_code=200, json=lambda: mock_response)
        
        result = await _list_candidates(limit=5)
        assert "John Doe" in result
        mock_get.assert_called_once()

@pytest.mark.asyncio
async def test_get_candidate():
    mock_response = {"data": {"id": "123", "name": "Jane Doe"}}
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = MagicMock(status_code=200, json=lambda: mock_response)
        
        result = await _get_candidate(candidate_id="123")
        assert "Jane Doe" in result
        mock_get.assert_called_once()

@pytest.mark.asyncio
async def test_create_requisition():
    mock_response = {"data": {"id": "req_123", "name": "Engineer"}}
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=200, json=lambda: mock_response)
        
        result = await _create_requisition(title="Engineer", location="Remote", team="Eng")
        assert "req_123" in result
        mock_post.assert_called_once()

@pytest.mark.asyncio
async def test_error_handling():
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.side_effect = Exception("API Error")
        
        result = await _list_candidates()
        assert "Error listing candidates" in result
