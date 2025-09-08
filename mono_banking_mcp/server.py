"""Mono Banking MCP Server using FastMCP."""

import os
import hmac
import hashlib
import json
from typing import Dict, Any

from dotenv import load_dotenv
from fastmcp import FastMCP
from mono_banking_mcp.mono_client import MonoClient
from mono_banking_mcp.database import MonoBankingDB
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.exceptions import HTTPException
from decouple import config as decouple_config

load_dotenv()

mcp = FastMCP("Personal banking MCP powered by Mono API")

mono_client = MonoClient(
    secret_key=os.getenv("MONO_SECRET_KEY", ""),
    base_url=os.getenv("MONO_BASE_URL", "https://api.withmono.com"),
)

# Initialize database for webhook events
db_url = decouple_config("DATABASE_URL", default="sqlite:///./mono_banking.db")
db = MonoBankingDB(db_url=db_url)

# Get webhook secret from environment
WEBHOOK_SECRET = os.getenv("MONO_WEBHOOK_SECRET")


@mcp.tool()
async def list_linked_accounts() -> dict:
    """List Linked Accounts

    Retrieves and displays a list of all external accounts
    linked to the user's profile for review.
    """
    try:
        result = await mono_client.get_customer_accounts()

        if result.get("status") and "data" in result:
            accounts = []
            for account in result["data"]:
                accounts.append(
                    {
                        "id": account.get("_id"),
                        "account_number": account.get("accountNumber"),
                        "account_name": account.get("name"),
                        "bank_name": account.get("institution", {}).get("name"),
                        "bank_code": account.get("institution", {}).get("bankCode"),
                        "account_type": account.get("type"),
                        "currency": account.get("currency"),
                    }
                )

            return {
                "success": True,
                "accounts": accounts,
                "total_accounts": len(accounts),
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
            formatted_balance = balance_data.get("balance", 0) / 100  # kobo to naira

            return {
                "success": True,
                "account_id": balance_data.get("id"),
                "account_number": balance_data.get("account_number"),
                "balance": f"₦{formatted_balance:,.2f}",
                "balance_raw": formatted_balance,
                "currency": balance_data.get("currency", "NGN"),
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
                "verified": True,
            }
        else:
            return {
                "success": False,
                "verified": False,
                "error": result.get("message", "Account verification failed"),
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
    redirect_url: str = "https://mono.co",
) -> dict:
    """Initiate a payment using Mono DirectPay."""
    try:
        # verify recipient account first using client method
        verification_result = await mono_client.resolve_account_name(
            recipient_account_number, recipient_bank_code
        )

        # Check if verification was successful
        if not (verification_result.get("status") and "data" in verification_result):
            return {
                "success": False,
                "error": "Recipient account verification failed",
                "verification_details": verification_result,
            }

        result = await mono_client.initiate_payment(
            amount=amount,
            redirect_url=redirect_url,
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            description=description,
        )

        if result.get("status") and "data" in result:
            payment_data = result["data"]
            return {
                "success": True,
                "message": f"Payment of ₦{amount:,.2f} initiated successfully",
                "recipient_name": verification_result["data"].get("account_name"),
                "recipient_account": recipient_account_number,
                "amount": f"₦{amount:,.2f}",
                "description": description,
                "reference": payment_data.get("reference"),
                "payment_id": payment_data.get("id"),
                "mono_url": payment_data.get("mono_url"),
                "instructions": "Open the mono_url in a browser to complete the payment authorization",
            }
        else:
            return {
                "success": False,
                "error": result.get("message", "Payment initiation failed"),
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
                "updated_at": payment_data.get("updated_at"),
            }
        else:
            return {
                "success": False,
                "error": result.get("message", "Payment verification failed"),
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
                    "slug": bank.get("slug"),
                }
                for bank in banks
            ]

            # Sort banks alphabetically by name
            formatted_banks.sort(key=lambda x: x.get("name", ""))

            return {
                "success": True,
                "banks": formatted_banks,
                "total_banks": len(formatted_banks),
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
                "updated_at": account_data.get("updated_at"),
            }
        else:
            return {"success": False, "error": "Unable to fetch account info"}

    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def get_transaction_history(
    account_id: str, limit: int = 10, page: int = 1
) -> dict:
    """Get transaction history for a linked account."""
    try:
        result = await mono_client.get_account_transactions(account_id, limit, page)

        if result.get("status") and "data" in result:
            transactions = result["data"]
            formatted_transactions = []

            for txn in transactions:
                formatted_transactions.append(
                    {
                        "id": txn.get("_id"),
                        "date": txn.get("date"),
                        "description": txn.get("narration"),
                        "amount": f"₦{(txn.get('amount', 0) / 100):,.2f}",
                        "amount_raw": txn.get("amount", 0) / 100,
                        "type": txn.get("type"),
                        "balance": f"₦{(txn.get('balance', 0) / 100):,.2f}",
                        "reference": txn.get("reference"),
                        "category": txn.get("category"),
                    }
                )

            return {
                "success": True,
                "account_id": account_id,
                "transactions": formatted_transactions,
                "count": len(formatted_transactions),
                "page": page,
                "limit": limit,
            }
        else:
            return {"success": False, "error": "Unable to fetch transactions"}

    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def lookup_bvn(bvn: str, scope: str = "identity") -> dict:
    """Lookup BVN for identity verification or to get linked bank accounts."""
    try:
        result = await mono_client.lookup_bvn(bvn, scope)

        if result.get("status") and "data" in result:
            bvn_data = result["data"]
            return {
                "success": True,
                "bvn": bvn,
                "scope": scope,
                "verification_status": "verified",
                "data": bvn_data,
            }
        else:
            return {
                "success": False,
                "error": result.get("message", "BVN lookup failed"),
                "verification_status": "failed",
            }
    except Exception as e:
        return {"success": False, "error": str(e), "verification_status": "error"}


@mcp.tool()
async def get_account_details(account_id: str) -> dict:
    """Get comprehensive account details including BVN if available."""
    try:
        # get basic account info
        account_result = await mono_client.get_account_info(account_id)

        if not (account_result.get("status") and "data" in account_result):
            return {"success": False, "error": "Unable to fetch account details"}

        account_data = account_result["data"]

        # try to get account number for BVN lookup
        account_number = account_data.get("accountNumber")
        bank_code = account_data.get("institution", {}).get("bankCode")

        details = {
            "success": True,
            "account_id": account_id,
            "account_number": account_number,
            "account_name": account_data.get("name"),
            "bank_name": account_data.get("institution", {}).get("name"),
            "bank_code": bank_code,
            "account_type": account_data.get("type"),
            "currency": account_data.get("currency"),
            "bvn": None,
            "bvn_status": "not_available",
        }

        # attempt BVN lookup if we have account details
        if account_number and bank_code:
            try:
                bvn_result = await mono_client.lookup_account_number(
                    account_number, bank_code
                )
                if bvn_result.get("status") and "data" in bvn_result:
                    details["bvn"] = bvn_result["data"].get("bvn")
                    details["bvn_status"] = "available"
            except Exception as e:
                details["bvn_status"] = f"lookup_failed: {type(e).__name__}"

        return details

    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def initiate_account_linking(
    customer_name: str, customer_email: str, redirect_url: str = "https://mono.co"
) -> dict:
    """Initiate Account Linking

    Initiates account linking process for a customer (returns mono_url for authorization).
    """
    try:
        result = await mono_client.initiate_account_linking(
            customer_name=customer_name,
            customer_email=customer_email,
            redirect_url=redirect_url,
        )

        if result.get("status") and "data" in result:
            link_data = result["data"]
            return {
                "success": True,
                "message": "Account linking initiated successfully",
                "customer_name": customer_name,
                "customer_email": customer_email,
                "mono_url": link_data.get("mono_url"),
                "instructions": "Open the mono_url in a browser to complete account linking",
            }
        else:
            return {
                "success": False,
                "error": result.get("message", "Account linking initiation failed"),
            }

    except Exception as e:
        return {"success": False, "error": str(e)}


# Webhook functionality integrated into FastMCP server
def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """Verify webhook signature using HMAC-SHA256"""
    if not WEBHOOK_SECRET:
        return False

    if not signature:
        return False

    expected_signature = hmac.new(
        WEBHOOK_SECRET.encode(), payload, hashlib.sha256
    ).hexdigest()

    # Ensure both signatures are the same length to prevent timing attacks
    if len(signature) != len(expected_signature):
        return False

    return hmac.compare_digest(signature, expected_signature)


async def handle_account_connected(data: Dict[str, Any]):
    """Handle account connection event"""
    account_id = data.get("id")
    customer_id = data.get("customer")

    # Store account in database
    account_data = {"id": account_id, "customer_id": customer_id, "status": "connected"}

    if db.store_account(account_data):
        print(f"Account connected and stored: {account_id}")
    else:
        print(f"Failed to store account: {account_id}")

    # Store webhook event - ensure account_id is a string
    if account_id and isinstance(account_id, str):
        db.store_webhook_event("account_connected", account_id, data)
    else:
        print(f"Invalid account_id in webhook event: {account_id}")


async def handle_account_updated(data: Dict[str, Any]):
    """Handle account update event"""
    account_info = data.get("account", {})
    account_id = account_info.get("id")
    meta = data.get("meta", {})
    data_status = meta.get("data_status")

    # Update account status in database
    existing_account = db.get_account(account_id)
    if existing_account:
        existing_account.update(
            {
                "status": data_status,
                "bank_name": account_info.get("institution", {}).get("name"),
                "bank_code": account_info.get("institution", {}).get("bankCode"),
            }
        )
        db.store_account(existing_account)

    print(f"Account updated: {account_id}, status: {data_status}")
    db.store_webhook_event("account_updated", account_id, data)


async def handle_account_unlinked(data: Dict[str, Any]):
    """Handle account unlink event"""
    account_info = data.get("account", {})
    account_id = account_info.get("id")

    # Remove account from database
    if db.remove_account(account_id):
        print(f"Account unlinked and removed: {account_id}")
    else:
        print(f"Failed to remove account: {account_id}")

    # Store webhook event - ensure account_id is a string
    if account_id and isinstance(account_id, str):
        db.store_webhook_event("account_unlinked", account_id, data)
    else:
        print(f"Invalid account_id in webhook event: {account_id}")


async def handle_job_update(data: Dict[str, Any]):
    """Handle job status update"""
    account_id = data.get("account")
    job_status = data.get("status")

    print(f"Job update for account {account_id}: {job_status}")
    if account_id and isinstance(account_id, str):
        db.store_webhook_event("job_update", account_id, data)
    else:
        print(f"Invalid account_id in webhook event: {account_id}")

    # Trigger data refresh if job finished
    if job_status == "finished":
        print(f"Job finished for account {account_id} - ready for data sync")


@mcp.custom_route("/mono/webhook", methods=["POST"])
async def handle_webhook(request: Request):
    """Handle incoming Mono webhook events"""
    try:
        # Get raw payload for signature verification
        payload = await request.body()

        # Verify webhook signature
        signature = request.headers.get("mono-webhook-secret", "")
        if not verify_webhook_signature(payload, signature):
            raise HTTPException(
                status_code=401,
                detail="Invalid webhook signature",
            )

        # Parse JSON payload
        try:
            event_data = json.loads(payload.decode())
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON payload")

        event_type = event_data.get("event")
        data = event_data.get("data", {})

        # Handle different webhook events
        if event_type == "mono.events.account_connected":
            await handle_account_connected(data)
        elif event_type == "mono.events.account_updated":
            await handle_account_updated(data)
        elif event_type == "mono.events.account_unlinked":
            await handle_account_unlinked(data)
        elif event_type == "mono.accounts.jobs.update":
            await handle_job_update(data)
        else:
            print(f"Unknown webhook event: {event_type}")

        return JSONResponse({"status": "success"}, status_code=200)

    except HTTPException:
        raise
    except Exception as e:
        print(f"Webhook error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error",
        )


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request):
    """Health check endpoint"""
    return JSONResponse(
        {
            "status": "healthy",
            "service": "mono-banking-mcp",
            "webhook_configured": WEBHOOK_SECRET is not None,
        }
    )


@mcp.tool()
async def get_webhook_events(account_id: str = None, limit: int = 10) -> dict:
    """Get recent webhook events for debugging and monitoring."""
    try:
        events = db.get_webhook_events(account_id=account_id, limit=limit)
        return {
            "success": True,
            "events": events,
            "count": len(events),
            "account_id": account_id,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    mcp.run()


def main():
    """Entry point for CLI"""
    mcp.run()
