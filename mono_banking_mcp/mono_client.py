import uuid
import httpx
from datetime import datetime
from typing import Any

class MonoClient:
    """
    Mono Open Banking API client following the official Mono API v2 specification.
    Based on Mono's official documentation and API patterns.
    """
    def __init__(self, secret_key: str, base_url: str = "https://api.withmono.com"):
        """
        Initialize Mono client with secret key for API authentication.

        Args:
            secret_key: Mono secret key (from app dashboard)
            base_url: Mono API base URL (same for sandbox/live, key determines environment)
        """
        self.secret_key = secret_key
        self.base_url = base_url
        self.session = httpx.AsyncClient(
            headers={
                "mono-sec-key": secret_key,
                "accept": "application/json",
                "content-type": "application/json",
                "User-Agent": "Mono-Banking-MCP/1.0"
            },
            timeout=30.0
        )

    async def get_customer_accounts(self) -> dict[str, Any]:
        """
        Get all accounts linked to your business/app.

        Returns:
            Dict containing list of linked accounts
        """
        response = await self.session.get(f"{self.base_url}/v2/accounts")
        response.raise_for_status()
        return response.json()

    async def get_account_balance(self, account_id: str) -> dict[str, Any]:
        """
        Get account balance for a specific linked account.

        Args:
            account_id: Mono account ID (obtained after account linking)

        Returns:
            Dict with account balance information
        """
        response = await self.session.get(f"{self.base_url}/v2/accounts/{account_id}/balance")
        response.raise_for_status()
        return response.json()

    async def get_account_info(self, account_id: str) -> dict[str, Any]:
        """
        Get detailed account information.

        Args:
            account_id: Mono account ID

        Returns:
            Dict with account details (name, number, bank, etc.)
        """
        response = await self.session.get(f"{self.base_url}/v2/accounts/{account_id}")
        response.raise_for_status()
        return response.json()

    async def get_account_transactions(self, account_id: str, limit: int = 50, page: int = 1) -> dict[str, Any]:
        """
        Get transaction history for an account.

        Args:
            account_id: Mono account ID
            limit: Number of transactions per page (max 100)
            page: Page number for pagination

        Returns:
            Dict with transaction history
        """
        params = {"limit": min(limit, 100), "page": page}
        response = await self.session.get(f"{self.base_url}/v2/accounts/{account_id}/transactions", params=params)
        response.raise_for_status()
        return response.json()

    async def initiate_account_linking(self, customer_name: str, customer_email: str,
                                     redirect_url: str, reference: str | None = None) -> dict[str, Any]:
        """
        Initiate account linking process to get mono_url for user authorization.

        Args:
            customer_name: Customer's full name
            customer_email: Customer's email address
            redirect_url: URL to redirect after successful linking
            reference: Optional reference for tracking

        Returns:
            Dict containing mono_url for account linking widget
        """
        payload = {
            "customer": {
                "name": customer_name,
                "email": customer_email
            },
            "scope": "auth",
            "redirect_url": redirect_url
        }

        if reference:
            payload["meta"] = {"ref": reference}

        response = await self.session.post(f"{self.base_url}/v2/accounts/initiate", json=payload)
        response.raise_for_status()
        return response.json()

    async def exchange_token(self, code: str) -> dict[str, Any]:
        """
        Exchange authorization code for account ID after successful linking.

        Args:
            code: Authorization code received after account linking

        Returns:
            Dict containing account ID and details
        """
        payload = {"code": code}
        response = await self.session.post(f"{self.base_url}/v2/accounts/auth", json=payload)
        response.raise_for_status()
        return response.json()

    async def initiate_payment(self, amount: float, payment_type: str = "onetime-debit",
                             reference: str | None = None, redirect_url: str = "",
                             customer_name: str = "", customer_email: str = "",
                             customer_phone: str = "", description: str = "",
                             account_id: str | None = None) -> dict[str, Any]:
        """
        Initiate a payment using Mono DirectPay.

        Args:
            amount: Payment amount in Naira
            payment_type: Type of payment ("onetime-debit" for one-time payments)
            reference: Unique reference for the payment
            redirect_url: URL to redirect after payment
            customer_name: Customer's name
            customer_email: Customer's email
            customer_phone: Customer's phone number
            description: Payment description
            account_id: Optional sub-account ID for split payments

        Returns:
            Dict containing mono_url for payment authorization
        """
        if not reference:
            reference = f"MCP-{uuid.uuid4().hex[:8]}-{int(datetime.now().timestamp())}"

        amount_kobo = int(amount * 100)

        payload = {
            "amount": amount_kobo,
            "type": payment_type,
            "reference": reference,
            "redirect_url": redirect_url,
            "customer": {
                "name": customer_name,
                "email": customer_email,
                "phone": customer_phone
            },
            "description": description
        }

        # Add account for split payments if provided
        if account_id:
            payload["method"] = "account"
            payload["account"] = account_id

        response = await self.session.post(f"{self.base_url}/v2/payments/initiate", json=payload)
        response.raise_for_status()
        return response.json()

    async def verify_payment(self, reference: str) -> dict[str, Any]:
        """
        Verify payment status using the payment reference.

        Args:
            reference: Payment reference used during initiation

        Returns:
            Dict containing payment status and details
        """
        response = await self.session.get(f"{self.base_url}/v2/payments/verify/{reference}")
        response.raise_for_status()
        return response.json()

    async def resolve_account_name(self, account_number: str, bank_code: str) -> dict[str, Any]:
        """
        Resolve account name for verification before payments.
        Note: This endpoint might be under /misc/banks/resolve based on guide.

        Args:
            account_number: 10-digit account number
            bank_code: 3-digit bank code

        Returns:
            Dict with account name and verification status
        """
        payload = {
            "account_number": account_number,
            "bank_code": bank_code
        }

        try:
            response = await self.session.post(f"{self.base_url}/misc/banks/resolve", json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError:
            
            response = await self.session.post(f"{self.base_url}/v2/misc/banks/resolve", json=payload)
            response.raise_for_status()
            return response.json()

    async def get_nigerian_banks(self) -> dict[str, Any]:
        """
        Get list of supported Nigerian banks with their codes.

        Returns:
            Dict containing list of banks with names and codes
        """
        try:
            response = await self.session.get(f"{self.base_url}/misc/banks")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError:
            # Fallback to alternative endpoint
            response = await self.session.get(f"{self.base_url}/v2/misc/banks")
            response.raise_for_status()
            return response.json()

    async def lookup_bvn(self, bvn: str, scope: str = "identity") -> dict[str, Any]:
        """
        Lookup BVN information for identity verification.

        Args:
            bvn: Bank Verification Number (11 digits)
            scope: "identity" for basic info, "bank_accounts" for linked accounts

        Returns:
            Dict with BVN verification results
        """
        payload = {"bvn": bvn, "scope": scope}
        response = await self.session.post(f"{self.base_url}/v2/lookup/bvn/initiate", json=payload)
        response.raise_for_status()
        return response.json()

    async def lookup_account_number(self, account_number: str, nip_code: str) -> dict[str, Any]:
        """
        Lookup account number to get masked BVN and verification.

        Args:
            account_number: 10-digit account number
            nip_code: Bank's NIP code (3 digits)

        Returns:
            Dict with account verification and masked BVN
        """
        payload = {"account_number": account_number, "nip_code": nip_code}
        response = await self.session.post(f"{self.base_url}/v3/lookup/account-number", json=payload)
        response.raise_for_status()
        return response.json()

    async def close(self):
        """Close the HTTP session."""
        await self.session.aclose()
