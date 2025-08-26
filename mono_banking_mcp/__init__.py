"""
Mono Banking MCP: A Model Context Protocol server for Nigerian banking operations.

This package provides a complete MCP server implementation for interacting with
the Mono Open Banking API.

Key Features:
- Account linking and management
- Real-time balance inquiries
- Payment initiation (DirectPay)
- Transaction history retrieval
- Account verification
- Nigerian bank directory

Version: 0.1.0
License: MIT
"""

__version__ = "0.1.0"

# Core exports
from .mono_client import MonoClient

# Convenience imports
__all__ = [
    "MonoClient",
    "__version__",
]
