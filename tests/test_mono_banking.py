"""
Test suite for the Mono Banking MCP Server.

Run with: pytest tests/
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mono_banking_mcp.mono_client import MonoClient


class TestMonoClient:
    """Test cases for MonoClient."""

    @pytest.fixture
    def mono_client(self):
        """Create a MonoClient instance for testing."""
        return MonoClient("test_secret_key")

    def test_client_initialization(self, mono_client):
        """Test client initialization."""
        assert mono_client.secret_key == "test_secret_key"
        assert mono_client.base_url == "https://api.withmono.com"
        assert "mono-sec-key" in mono_client.session.headers

    @pytest.mark.asyncio
    async def test_get_customer_accounts(self, mono_client):
        """Test getting customer accounts."""
        # Mock the HTTP response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": True,
            "data": [
                {
                    "_id": "account123",
                    "accountNumber": "1234567890",
                    "name": "John Doe",
                    "institution": {"name": "Test Bank", "bankCode": "001"}
                }
            ]
        }
        mock_response.raise_for_status.return_value = None

        mono_client.session.get = AsyncMock(return_value=mock_response)

        result = await mono_client.get_customer_accounts()

        assert result["status"] is True
        assert len(result["data"]) == 1
        assert result["data"][0]["_id"] == "account123"

class TestFastMCPTools:
    """Test cases for FastMCP server tools."""

    @pytest.fixture
    def mock_mono_client(self):
        """Create a mocked MonoClient."""
        return AsyncMock(spec=MonoClient)

    @pytest.mark.asyncio
    async def test_get_account_balance_tool(self, mock_mono_client):
        """Test the get_account_balance FastMCP tool."""
        # Mock the client response
        mock_mono_client.get_account_balance.return_value = {
            "status": True,
            "data": {
                "id": "account123",
                "account_number": "1234567890",
                "balance": 500000,  # in kobo
                "currency": "NGN"
            }
        }

        # Import and patch the mono_client in the server module
        with patch('mono_banking_mcp.server.mono_client', mock_mono_client):
            from mono_banking_mcp.server import get_account_balance
            result = await get_account_balance("account123")

        assert result["success"] is True
        assert result["balance"] == "₦5,000.00"
        assert result["balance_raw"] == 5000.0
        assert result["currency"] == "NGN"

    @pytest.mark.asyncio
    async def test_verify_account_name_tool(self, mock_mono_client):
        """Test the verify_account_name FastMCP tool."""
        mock_mono_client.resolve_account_name.return_value = {
            "status": True,
            "data": {
                "account_name": "JOHN DOE",
                "bank_name": "Test Bank"
            }
        }

        with patch('mono_banking_mcp.server.mono_client', mock_mono_client):
            from mono_banking_mcp.server import verify_account_name
            result = await verify_account_name("1234567890", "001")

        assert result["success"] is True
        assert result["verified"] is True
        assert result["account_name"] == "JOHN DOE"
        assert result["bank_code"] == "001"

    @pytest.mark.asyncio
    async def test_get_nigerian_banks_tool(self, mock_mono_client):
        """Test the get_nigerian_banks FastMCP tool."""
        mock_mono_client.get_nigerian_banks.return_value = {
            "status": True,
            "data": [
                {"name": "Access Bank", "code": "044", "slug": "access-bank"},
                {"name": "GTBank", "code": "058", "slug": "gtbank"}
            ]
        }

        with patch('mono_banking_mcp.server.mono_client', mock_mono_client):
            from mono_banking_mcp.server import get_nigerian_banks
            result = await get_nigerian_banks()

        assert result["success"] is True
        assert result["total_banks"] == 2
        assert len(result["banks"]) == 2
        assert result["banks"][0]["name"] == "Access Bank"

    @pytest.mark.asyncio
    async def test_error_handling(self, mock_mono_client):
        """Test error handling in FastMCP tools."""
        # Mock client to raise an exception
        mock_mono_client.get_account_balance.side_effect = Exception("API Error")

        with patch('mono_banking_mcp.server.mono_client', mock_mono_client):
            from mono_banking_mcp.server import get_account_balance
            result = await get_account_balance("account123")

        assert result["success"] is False
        assert "API Error" in result["error"]

class TestMCPServerIntegration:
    """Test FastMCP server integration."""

    @pytest.mark.asyncio
    async def test_server_initialization(self):
        """Test that the FastMCP server initializes correctly."""
        from mono_banking_mcp.server import mcp

        # Check that the server is properly initialized
        assert mcp.name == "Mono Banking"

        # Check that tools are registered using the list_tools method
        tools = await mcp.list_tools()
        tool_names = [tool.name for tool in tools]

        expected_tools = [
            "list_linked_accounts",
            "get_account_balance",
            "get_account_info",
            "get_transaction_history",
            "verify_account_name",
            "initiate_payment",
            "verify_payment",
            "get_nigerian_banks",
            "initiate_account_linking"
        ]

        for tool_name in expected_tools:
            assert tool_name in tool_names, f"Tool {tool_name} not found in registered tools"

    @pytest.mark.asyncio
    async def test_tool_metadata(self):
        """Test that tools have proper metadata."""
        from mono_banking_mcp.server import mcp

        tools = await mcp.list_tools()

        # Check that each tool has a description
        for tool in tools:
            assert tool.description is not None, f"Tool {tool.name} missing description"
            assert len(tool.description.strip()) > 0, f"Tool {tool.name} has empty description"

# Integration tests (require actual API credentials)
@pytest.mark.integration
class TestIntegration:
    """Integration tests that require real API credentials."""

    @pytest.mark.skip(reason="Requires real API credentials")
    @pytest.mark.asyncio
    async def test_real_api_call(self):
        """Test actual API call (only run with real credentials)."""
        import os
        secret_key = os.getenv("MONO_SECRET_KEY")
        if not secret_key:
            pytest.skip("MONO_SECRET_KEY not found")

        client = MonoClient(secret_key)

        try:
            # Test getting banks list directly from client
            result = await client.get_nigerian_banks()
            assert result.get("status") is True
            assert "data" in result
            assert len(result["data"]) > 0
        finally:
            await client.close()

if __name__ == "__main__":
    pytest.main([__file__])
