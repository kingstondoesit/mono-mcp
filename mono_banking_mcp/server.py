#!/usr/bin/env python3
"""
Mono Banking MCP Server using FastMCP.

A simple MCP server for Nigerian banking operations via the Mono Open Banking API.
"""

import os

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from mono_banking_mcp.mono_client import MonoClient

# Load environment variables
load_dotenv()

# Create FastMCP server
mcp = FastMCP("Mono Banking")

# Initialize Mono client
mono_client = MonoClient(
    secret_key=os.getenv("MONO_SECRET_KEY", ""),
    base_url=os.getenv("MONO_BASE_URL", "https://api.withmono.com")
)

@mcp.tool()
async def list_linked_accounts() -> dict:
    """List all bank accounts linked to your Mono app/business."""
    try:
        result = await mono_client.get_customer_accounts()

        if result.get("status") and "data" in result:
            accounts = []
            for account in result["data"]:
                accounts.append({
                    "id": account.get("_id"),
                    "account_number": account.get("accountNumber"),
                    "account_name": account.get("name"),
                    "bank_name": account.get("institution", {}).get("name"),
                    "bank_code": account.get("institution", {}).get("bankCode"),
                    "account_type": account.get("type"),
                    "currency": account.get("currency"),
                })

            return {
                "success": True,
                "accounts": accounts,
                "total_accounts": len(accounts)
            }
        else:
            return {"success": False, "error": "Unable to fetch linked accounts"}

    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def get_account_balance(account_id: str) -> dict:
    """Get current account balance for a linked account."""
    try:
        result = await mono_client.get_account_balance(account_id)

        if result.get("status") and "data" in result:
            balance_data = result["data"]
            formatted_balance = balance_data.get("balance", 0) / 100  # Convert from kobo

            return {
                "success": True,
                "account_id": balance_data.get("id"),
                "account_number": balance_data.get("account_number"),
                "balance": f"₦{formatted_balance:,.2f}",
                "balance_raw": formatted_balance,
                "currency": balance_data.get("currency", "NGN")
            }
        else:
            return {"success": False, "error": "Unable to fetch balance"}

    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def verify_account_name(account_number: str, bank_code: str) -> dict:
    """Verify recipient account name before making payments."""
    try:
        result = await mono_client.resolve_account_name(account_number, bank_code)

        if result.get("status") and "data" in result:
            return {
                "success": True,
                "account_number": account_number,
                "account_name": result["data"].get("account_name"),
                "bank_code": bank_code,
                "bank_name": result["data"].get("bank_name"),
                "verified": True
            }
        else:
            return {
                "success": False,
                "verified": False,
                "error": result.get("message", "Account verification failed")
            }

    except Exception as e:
        return {"success": False, "verified": False, "error": str(e)}

@mcp.tool()
async def initiate_payment(
    amount: float,
    recipient_account_number: str,
    recipient_bank_code: str,
    customer_name: str,
    customer_email: str,
    customer_phone: str,
    description: str,
    redirect_url: str = "https://mono.co"
) -> dict:
    """Initiate a payment using Mono DirectPay (returns mono_url for user authorization)."""
    try:
        # First verify the recipient account
        verification = await verify_account_name(recipient_account_number, recipient_bank_code)

        if not verification.get("verified"):
            return {
                "success": False,
                "error": "Recipient account verification failed",
                "verification_details": verification
            }

        # Proceed with payment initiation
        result = await mono_client.initiate_payment(
            amount=amount,
            redirect_url=redirect_url,
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            description=description
        )

        if result.get("status") and "data" in result:
            payment_data = result["data"]
            return {
                "success": True,
                "message": f"Payment of ₦{amount:,.2f} initiated successfully",
                "recipient_name": verification["account_name"],
                "recipient_account": recipient_account_number,
                "amount": f"₦{amount:,.2f}",
                "description": description,
                "reference": payment_data.get("reference"),
                "payment_id": payment_data.get("id"),
                "mono_url": payment_data.get("mono_url"),
                "instructions": "Open the mono_url in a browser to complete the payment authorization"
            }
        else:
            return {
                "success": False,
                "error": result.get("message", "Payment initiation failed")
            }

    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def verify_payment(reference: str) -> dict:
    """Verify payment status using payment reference."""
    try:
        result = await mono_client.verify_payment(reference)

        if result.get("status") and "data" in result:
            payment_data = result["data"]
            return {
                "success": True,
                "reference": reference,
                "payment_status": payment_data.get("status"),
                "amount": f"₦{(payment_data.get('amount', 0) / 100):,.2f}",
                "description": payment_data.get("description"),
                "customer_name": payment_data.get("customer", {}).get("name"),
                "created_at": payment_data.get("created_at"),
                "updated_at": payment_data.get("updated_at")
            }
        else:
            return {
                "success": False,
                "error": result.get("message", "Payment verification failed")
            }

    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def get_nigerian_banks() -> dict:
    """Get list of all supported Nigerian banks with their codes."""
    try:
        result = await mono_client.get_nigerian_banks()

        if result.get("status") and "data" in result:
            banks = result["data"]
            formatted_banks = [
                {
                    "name": bank.get("name"),
                    "code": bank.get("code"),
                    "slug": bank.get("slug")
                }
                for bank in banks
            ]

            # Sort banks alphabetically by name
            formatted_banks.sort(key=lambda x: x.get("name", ""))

            return {
                "success": True,
                "banks": formatted_banks,
                "total_banks": len(formatted_banks)
            }
        else:
            return {"success": False, "error": "Unable to fetch banks list"}

    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def get_account_info(account_id: str) -> dict:
    """Get detailed information for a linked account."""
    try:
        result = await mono_client.get_account_info(account_id)

        if result.get("status") and "data" in result:
            account_data = result["data"]
            return {
                "success": True,
                "account_id": account_data.get("_id"),
                "account_name": account_data.get("name"),
                "account_number": account_data.get("accountNumber"),
                "bank_name": account_data.get("institution", {}).get("name"),
                "bank_code": account_data.get("institution", {}).get("bankCode"),
                "account_type": account_data.get("type"),
                "currency": account_data.get("currency", "NGN"),
                "bvn": account_data.get("bvn"),
                "created_at": account_data.get("created_at"),
                "updated_at": account_data.get("updated_at")
            }
        else:
            return {"success": False, "error": "Unable to fetch account info"}

    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def get_transaction_history(account_id: str, limit: int = 10, page: int = 1) -> dict:
    """Get transaction history for a linked account."""
    try:
        result = await mono_client.get_account_transactions(account_id, limit, page)

        if result.get("status") and "data" in result:
            transactions = result["data"]
            formatted_transactions = []

            for txn in transactions:
                formatted_transactions.append({
                    "id": txn.get("_id"),
                    "date": txn.get("date"),
                    "description": txn.get("narration"),
                    "amount": f"₦{(txn.get('amount', 0) / 100):,.2f}",
                    "amount_raw": txn.get('amount', 0) / 100,
                    "type": txn.get("type"),
                    "balance": f"₦{(txn.get('balance', 0) / 100):,.2f}",
                    "reference": txn.get("reference"),
                    "category": txn.get("category")
                })

            return {
                "success": True,
                "account_id": account_id,
                "transactions": formatted_transactions,
                "count": len(formatted_transactions),
                "page": page,
                "limit": limit
            }
        else:
            return {"success": False, "error": "Unable to fetch transactions"}

    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def initiate_account_linking(
    customer_name: str,
    customer_email: str,
    redirect_url: str = "https://mono.co"
) -> dict:
    """Initiate account linking process for a customer (returns mono_url for authorization)."""
    try:
        result = await mono_client.initiate_account_linking(
            customer_name=customer_name,
            customer_email=customer_email,
            redirect_url=redirect_url
        )

        if result.get("status") and "data" in result:
            link_data = result["data"]
            return {
                "success": True,
                "message": "Account linking initiated successfully",
                "customer_name": customer_name,
                "customer_email": customer_email,
                "mono_url": link_data.get("mono_url"),
                "instructions": "Open the mono_url in a browser to complete account linking"
            }
        else:
            return {
                "success": False,
                "error": result.get("message", "Account linking initiation failed")
            }

    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    mcp.run()

def main():
    """Entry point for CLI"""
    mcp.run()
