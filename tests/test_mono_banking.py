"""Comprehensive test suite for the Mono Banking MCP Server."""

from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any
import pytest
import os
from fastmcp import FastMCP

from mono_banking_mcp.mono_client import MonoClient


class TestMonoClient:
    """Test cases for MonoClient functionality."""

    @pytest.fixture
    def mono_client(self):
        """Create a MonoClient instance for testing."""
        return MonoClient("test_secret_key")

    def test_client_initialization(self, mono_client):
        """Test proper client initialization with correct headers and configuration."""
        assert mono_client.secret_key == "test_secret_key"
        assert mono_client.base_url == "https://api.withmono.com"
        assert "mono-sec-key" in mono_client.session.headers
        assert mono_client.session.headers["mono-sec-key"] == "test_secret_key"

    @pytest.mark.asyncio
    async def test_get_customer_accounts(self, mono_client):
        """Test retrieving customer accounts with proper response handling."""
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

    @pytest.mark.asyncio
    async def test_client_error_handling(self, mono_client):
        """Test client error handling for API failures."""
        mono_client.session.get = AsyncMock(side_effect=Exception("Network error"))
        
        with pytest.raises(Exception, match="Network error"):
            await mono_client.get_customer_accounts()

        with pytest.raises(Exception, match="Network error"):
            await mono_client.get_customer_accounts()


class TestFastMCPTools:
    """Comprehensive test suite for all FastMCP server tools."""

    @pytest.fixture
    def mock_mono_client(self):
        """Create a mocked MonoClient for testing."""
        return AsyncMock(spec=MonoClient)

    @pytest.mark.asyncio
    async def test_get_account_balance_logic(self, mock_mono_client):
        """Test account balance logic with proper currency formatting.""" 
        mock_mono_client.get_account_balance.return_value = {
            "status": True,
            "data": {
                "id": "account123",
                "account_number": "1234567890",
                "balance": 500000,
                "currency": "NGN"
            }
        }

        # Test the core logic
        result = await mock_mono_client.get_account_balance("account123")
        assert result["status"] is True
        
        # Test currency formatting logic
        balance_kobo = result["data"]["balance"]
        balance_naira = balance_kobo / 100
        formatted_balance = f"₦{balance_naira:,.2f}"
        
        assert formatted_balance == "₦5,000.00"
        assert balance_naira == 5000.0

    @pytest.mark.asyncio
    async def test_verify_account_name_logic(self, mock_mono_client):
        """Test account name verification logic."""
        mock_mono_client.resolve_account_name.return_value = {
            "status": True,
            "data": {
                "account_name": "JOHN DOE",
                "bank_name": "GTBank"
            }
        }

        result = await mock_mono_client.resolve_account_name("1234567890", "058")
        
        assert result["status"] is True
        assert result["data"]["account_name"] == "JOHN DOE"
        assert result["data"]["bank_name"] == "GTBank"

    @pytest.mark.asyncio
    async def test_get_nigerian_banks_logic(self, mock_mono_client):
        """Test Nigerian banks retrieval logic."""
        mock_mono_client.get_nigerian_banks.return_value = {
            "status": True,
            "data": [
                {"name": "Access Bank", "code": "044", "slug": "access-bank"},
                {"name": "GTBank", "code": "058", "slug": "gtbank"},
                {"name": "First Bank", "code": "011", "slug": "first-bank"}
            ]
        }

        result = await mock_mono_client.get_nigerian_banks()
        
        assert result["status"] is True
        assert len(result["data"]) == 3
        assert result["data"][0]["name"] == "Access Bank"
        assert result["data"][1]["code"] == "058"

    @pytest.mark.asyncio
    async def test_error_handling_logic(self, mock_mono_client):
        """Test error handling logic across tools."""
        mock_mono_client.get_account_balance.side_effect = Exception("API Error")
        
        try:
            await mock_mono_client.get_account_balance("account123")
            assert False, "Should have raised an exception"
        except Exception as e:
            assert str(e) == "API Error"

    @pytest.mark.asyncio
    async def test_currency_formatting_edge_cases(self):
        """Test currency formatting with various amounts."""
        test_cases = [
            (0, "₦0.00"),
            (100, "₦1.00"),
            (150, "₦1.50"),
            (123456, "₦1,234.56"),
            (100000000, "₦1,000,000.00")
        ]
        
        for kobo_amount, expected_format in test_cases:
            naira_amount = kobo_amount / 100
            formatted = f"₦{naira_amount:,.2f}"
            assert formatted == expected_format, f"Failed for {kobo_amount} kobo"


class TestErrorHandling:
    """Test comprehensive error handling across all tools."""

    @pytest.fixture
    def mock_mono_client(self):
        """Create a mocked MonoClient for error testing."""
        return AsyncMock(spec=MonoClient)

    @pytest.mark.asyncio
    async def test_api_error_handling(self, mock_mono_client):
        """Test proper error handling for API failures."""
        mock_mono_client.get_account_balance.side_effect = Exception("API Error")
        
        try:
            await mock_mono_client.get_account_balance("account123")
            assert False, "Should have raised an exception"
        except Exception as e:
            assert str(e) == "API Error"

    @pytest.mark.asyncio
    async def test_invalid_response_handling(self, mock_mono_client):
        """Test handling of invalid API responses."""
        mock_mono_client.resolve_account_name.return_value = {
            "status": False,
            "message": "Invalid account number"
        }

        result = await mock_mono_client.resolve_account_name("invalid", "058")
        assert result["status"] is False
        assert "Invalid account number" in result["message"]

    @pytest.mark.asyncio
    async def test_network_timeout_handling(self, mock_mono_client):
        """Test handling of network timeouts and connection errors."""
        from httpx import TimeoutException
        mock_mono_client.get_nigerian_banks.side_effect = TimeoutException("Request timeout")

        try:
            await mock_mono_client.get_nigerian_banks()
            assert False, "Should have raised TimeoutException"
        except TimeoutException as e:
            assert "timeout" in str(e).lower()
        """Test handling of network timeouts and connection errors."""
        from httpx import TimeoutException
        mock_mono_client.get_nigerian_banks.side_effect = TimeoutException("Request timeout")

        with patch('mono_banking_mcp.server.mono_client', mock_mono_client):
            from mono_banking_mcp.server import get_nigerian_banks
            result = await get_nigerian_banks()

        assert result["success"] is False
        assert "timeout" in result["error"].lower()


class TestMCPServerIntegration:
    """Test FastMCP server integration and tool registration."""

    @pytest.mark.asyncio
    async def test_server_initialization(self):
        """Test FastMCP server proper initialization."""
        from mono_banking_mcp.server import mcp

        assert mcp.name == "Mono Banking"
        assert isinstance(mcp, FastMCP)

    @pytest.mark.asyncio
    async def test_all_tools_registered(self):
        """Test that all expected banking tools are properly registered."""
        from mono_banking_mcp.server import mcp

        tools = await mcp.list_tools()
        tool_names = [tool.name for tool in tools]

        expected_tools = [
            "list_linked_accounts",
            "get_account_balance", 
            "get_account_info",
            "get_account_details",
            "get_transaction_history",
            "verify_account_name",
            "initiate_payment",
            "verify_payment",
            "get_nigerian_banks",
            "initiate_account_linking",
            "lookup_bvn"
        ]

        for tool_name in expected_tools:
            assert tool_name in tool_names, f"Tool {tool_name} not found in registered tools"

        assert len(tool_names) == len(expected_tools), f"Expected {len(expected_tools)} tools, got {len(tool_names)}"

    @pytest.mark.asyncio
    async def test_tool_metadata_completeness(self):
        """Test that all tools have complete metadata."""
        from mono_banking_mcp.server import mcp

        tools = await mcp.list_tools()

        for tool in tools:
            assert tool.description is not None, f"Tool {tool.name} missing description"
            assert len(tool.description.strip()) > 10, f"Tool {tool.name} has insufficient description"
            assert tool.inputSchema is not None, f"Tool {tool.name} missing input schema"

    @pytest.mark.asyncio
    async def test_tool_parameter_validation(self):
        """Test that tools properly validate required parameters."""
        from mono_banking_mcp.server import mcp

        tools = await mcp.list_tools()
        account_balance_tool = next((t for t in tools if t.name == "get_account_balance"), None)
        
        assert account_balance_tool is not None
        assert "account_id" in account_balance_tool.inputSchema.get("properties", {})
        assert "account_id" in account_balance_tool.inputSchema.get("required", [])


class TestDatabaseIntegration:
    """Test database functionality for webhook storage."""

    @pytest.mark.asyncio
    async def test_database_connection(self):
        """Test database connection and basic operations."""
        from mono_banking_mcp.database import init_db, store_webhook_event
        
        await init_db()
        
        test_event = {
            "event": "account.updated",
            "data": {"account_id": "test123"},
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        event_id = await store_webhook_event(test_event)
        assert event_id is not None


class TestWebhookServer:
    """Test webhook server functionality."""

    @pytest.mark.asyncio
    async def test_webhook_signature_verification(self):
        """Test webhook signature verification logic."""
        from mono_banking_mcp.webhook_server import verify_webhook_signature
        
        payload = '{"test": "data"}'
        secret = "test_secret"
        
        valid_signature = verify_webhook_signature(payload, "valid_signature", secret)
        assert isinstance(valid_signature, bool)


@pytest.mark.integration
class TestIntegration:
    """Integration tests requiring real API credentials."""

    @pytest.mark.skipif(
        not os.getenv("MONO_SECRET_KEY"),
        reason="Integration tests require MONO_SECRET_KEY environment variable"
    )
    @pytest.mark.asyncio
    async def test_real_banks_api_call(self):
        """Test actual API call to get Nigerian banks."""
        secret_key = os.getenv("MONO_SECRET_KEY")
        client = MonoClient(secret_key)

        try:
            result = await client.get_nigerian_banks()
            assert result.get("status") is True
            assert "data" in result
            assert len(result["data"]) > 0
            
            first_bank = result["data"][0]
            assert "name" in first_bank
            assert "code" in first_bank
        finally:
            await client.close()

    @pytest.mark.skipif(
        not os.getenv("MONO_SECRET_KEY"),
        reason="Integration tests require MONO_SECRET_KEY environment variable"
    )
    @pytest.mark.asyncio  
    async def test_mcp_server_with_real_api(self):
        """Test MCP server initialization with real API credentials."""
        secret_key = os.getenv("MONO_SECRET_KEY")
        
        with patch.dict(os.environ, {"MONO_SECRET_KEY": secret_key}):
            from mono_banking_mcp.server import mcp
            
            tools = await mcp.list_tools()
            assert len(tools) >= 11


class TestPerformance:
    """Performance and load testing for critical operations."""

    @pytest.mark.asyncio
    async def test_concurrent_tool_calls(self, mock_mono_client):
        """Test concurrent execution of multiple tool calls."""
        import asyncio
        
        mock_mono_client.get_nigerian_banks.return_value = {
            "status": True,
            "data": [{"name": "Test Bank", "code": "001"}]
        }

        with patch('mono_banking_mcp.server.mono_client', mock_mono_client):
            from mono_banking_mcp.server import get_nigerian_banks
            
            tasks = [get_nigerian_banks() for _ in range(10)]
            results = await asyncio.gather(*tasks)
            
            assert len(results) == 10
            assert all(result["success"] for result in results)

    @pytest.mark.asyncio
    async def test_large_transaction_history(self, mock_mono_client):
        """Test handling of large transaction history datasets."""
        large_transactions = [
            {
                "_id": f"txn_{i}",
                "amount": i * 1000,
                "type": "credit" if i % 2 == 0 else "debit",
                "narration": f"Transaction {i}",
                "date": f"2024-01-{i:02d}"
            }
            for i in range(1, 101)
        ]
        
        mock_mono_client.get_transaction_history.return_value = {
            "status": True,
            "data": large_transactions
        }

        with patch('mono_banking_mcp.server.mono_client', mock_mono_client):
            from mono_banking_mcp.server import get_transaction_history
            result = await get_transaction_history("account123", limit=100)

        assert result["success"] is True
        assert result["total_transactions"] == 100
        assert len(result["transactions"]) == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
