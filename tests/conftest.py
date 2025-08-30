# Test configuration for Mono Banking MCP Server
import os
import pytest
from unittest.mock import AsyncMock
from mono_banking_mcp.mono_client import MonoClient


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_response():
    """Standard mock response for API calls."""
    def _create_mock(status=True, data=None, message="Success"):
        mock = AsyncMock()
        mock.json.return_value = {
            "status": status,
            "data": data or {},
            "message": message
        }
        mock.raise_for_status.return_value = None
        return mock
    return _create_mock


@pytest.fixture
def sample_account_data():
    """Sample account data for testing."""
    return {
        "_id": "account123",
        "name": "John Doe",
        "accountNumber": "1234567890",
        "type": "SAVINGS",
        "institution": {
            "name": "GTBank",
            "bankCode": "058"
        },
        "balance": 500000,
        "currency": "NGN"
    }


@pytest.fixture
def sample_transaction_data():
    """Sample transaction data for testing."""
    return [
        {
            "_id": "txn1",
            "amount": 10000,
            "type": "debit",
            "narration": "ATM Withdrawal",
            "date": "2024-01-15",
            "balance": 490000
        },
        {
            "_id": "txn2", 
            "amount": 50000,
            "type": "credit",
            "narration": "Salary Payment",
            "date": "2024-01-01",
            "balance": 500000
        }
    ]


@pytest.fixture
def sample_banks_data():
    """Sample Nigerian banks data for testing."""
    return [
        {"name": "Access Bank", "code": "044", "slug": "access-bank"},
        {"name": "GTBank", "code": "058", "slug": "gtbank"},
        {"name": "First Bank", "code": "011", "slug": "first-bank"},
        {"name": "Zenith Bank", "code": "057", "slug": "zenith-bank"}
    ]


@pytest.fixture
def mock_mono_client():
    """Create a mocked MonoClient for testing."""
    return AsyncMock(spec=MonoClient)


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    test_env = {
        "MONO_SECRET_KEY": "test_secret_key",
        "MONO_BASE_URL": "https://api.withmono.com",
        "MONO_ENVIRONMENT": "test"
    }
    
    original_env = {}
    for key, value in test_env.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value
    
    yield
    
    for key, original_value in original_env.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value
