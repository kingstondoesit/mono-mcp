"""
Mono Banking Webhook Server for handling real-time events.
"""

import os
import hmac
import hashlib
import json
from typing import Dict, Any
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
import uvicorn
from dotenv import load_dotenv
from .database import MonoBankingDB

load_dotenv()

app = FastAPI(title="Mono Banking Webhooks", version="1.0.0")
db = MonoBankingDB()

# get webhook secret from environment
WEBHOOK_SECRET = os.getenv("MONO_WEBHOOK_SECRET")


def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """verify webhook signature using HMAC-SHA256"""
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


@app.post("/mono/webhook")
async def handle_webhook(request: Request):
    """handle incoming mono webhook events"""
    try:
        # get raw payload for signature verification
        payload = await request.body()

        # verify webhook signature
        signature = request.headers.get("mono-webhook-secret", "")
        if not verify_webhook_signature(payload, signature):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid webhook signature",
            )

        # parse json payload
        try:
            event_data = json.loads(payload.decode())
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="invalid json payload"
            )

        event_type = event_data.get("event")
        data = event_data.get("data", {})

        # handle different webhook events
        if event_type == "mono.events.account_connected":
            await handle_account_connected(data)
        elif event_type == "mono.events.account_updated":
            await handle_account_updated(data)
        elif event_type == "mono.events.account_unlinked":
            await handle_account_unlinked(data)
        elif event_type == "mono.accounts.jobs.update":
            await handle_job_update(data)
        else:
            print(f"unknown webhook event: {event_type}")

        return JSONResponse({"status": "success"}, status_code=200)

    except HTTPException:
        raise
    except Exception as e:
        print(f"webhook error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="internal server error",
        )


async def handle_account_connected(data: Dict[str, Any]):
    """handle account connection event"""
    account_id = data.get("id")
    customer_id = data.get("customer")

    # store account in database
    account_data = {"id": account_id, "customer_id": customer_id, "status": "connected"}

    if db.store_account(account_data):
        print(f"account connected and stored: {account_id}")
    else:
        print(f"failed to store account: {account_id}")

    # store webhook event - ensure account_id is a string
    if account_id and isinstance(account_id, str):
        db.store_webhook_event("account_connected", account_id, data)
    else:
        print(f"Invalid account_id in webhook event: {account_id}")


async def handle_account_updated(data: Dict[str, Any]):
    """handle account update event"""
    account_info = data.get("account", {})
    account_id = account_info.get("id")
    meta = data.get("meta", {})
    data_status = meta.get("data_status")

    # update account status in database
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

    print(f"account updated: {account_id}, status: {data_status}")
    db.store_webhook_event("account_updated", account_id, data)


async def handle_account_unlinked(data: Dict[str, Any]):
    """handle account unlink event"""
    account_info = data.get("account", {})
    account_id = account_info.get("id")

    # remove account from database
    if db.remove_account(account_id):
        print(f"account unlinked and removed: {account_id}")
    else:
        print(f"failed to remove account: {account_id}")

    # store webhook event - ensure account_id is a string
    if account_id and isinstance(account_id, str):
        db.store_webhook_event("account_unlinked", account_id, data)
    else:
        print(f"Invalid account_id in webhook event: {account_id}")


async def handle_job_update(data: Dict[str, Any]):
    """handle job status update"""
    account_id = data.get("account")
    job_status = data.get("status")

    print(f"job update for account {account_id}: {job_status}")
    if account_id and isinstance(account_id, str):
        db.store_webhook_event("job_update", account_id, data)
    else:
        print(f"Invalid account_id in webhook event: {account_id}")

    # trigger data refresh if job finished
    if job_status == "finished":
        print(f"job finished for account {account_id} - ready for data sync")


@app.get("/health")
async def health_check():
    """health check endpoint"""
    return {"status": "healthy", "service": "mono-banking-webhooks"}


def run_webhook_server(host: str = "0.0.0.0", port: int = 8000):
    """run the webhook server"""
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_webhook_server()
