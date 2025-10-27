import hashlib
import base64
import json
import time
from typing import Dict, Any, Optional
import httpx

from app.core.config import settings


class HeleketService:
    """Service for managing Heleket payment gateway integration."""

    @staticmethod
    def _generate_signature(data: dict) -> str:
        """
        Generate MD5 signature for Heleket API request.
        Formula: MD5(base64(json_body) + API_KEY)
        """
        json_str = json.dumps(data, ensure_ascii=False)
        base64_data = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")
        signature_str = base64_data + settings.HELEKET_API_KEY
        return hashlib.md5(signature_str.encode("utf-8")).hexdigest()

    @staticmethod
    def _generate_order_id(user_id: int) -> str:
        """Generate unique order ID with format: user_{user_id}_{timestamp}"""
        timestamp = int(time.time())
        return f"user_{user_id}_{timestamp}"

    @staticmethod
    async def create_invoice(user_id: int, amount_usd: float) -> Dict[str, Any]:
        """
        Create a new payment invoice via Heleket API.

        Args:
            user_id: User ID for the invoice
            amount_usd: Amount in USD

        Returns:
            Dict with keys: url, uuid, expired_at, order_id

        Raises:
            httpx.HTTPError: If API request fails
        """
        order_id = HeleketService._generate_order_id(user_id)

        payload = {
            "amount": str(amount_usd),
            "currency": "USD",
            "order_id": order_id,
            "url_callback": f"{settings.APP_URL}/api/payment/webhook",
            "url_success": f"{settings.APP_URL}/dashboard/deposit?status=success",
            "url_return": f"{settings.APP_URL}/dashboard/deposit",
            "lifetime": 3600,  # 1 hour
        }

        signature = HeleketService._generate_signature(payload)

        headers = {
            "merchant": settings.HELEKET_MERCHANT_ID,
            "sign": signature,
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.HELEKET_API_URL}/v1/payment",
                json=payload,
                headers=headers,
                timeout=30.0,
            )
            response.raise_for_status()
            result = response.json()

            if result.get("state") != 0:
                raise Exception(f"Heleket API error: {result.get('message', 'Unknown error')}")

            invoice_data = result.get("result", {})
            return {
                "url": invoice_data.get("url"),
                "uuid": invoice_data.get("uuid"),
                "expired_at": invoice_data.get("expired_at"),
                "order_id": order_id,
            }

    @staticmethod
    def verify_webhook_signature(data: dict, sign: str) -> bool:
        """
        Verify webhook signature from Heleket.

        Args:
            data: Webhook payload (without 'sign' field)
            sign: Signature from webhook

        Returns:
            True if signature is valid, False otherwise
        """
        # Ensure slashes are escaped (PHP json_encode behavior)
        json_str = json.dumps(data, ensure_ascii=False).replace("/", "\\/")
        base64_data = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")
        signature_str = base64_data + settings.HELEKET_API_KEY
        calculated_sign = hashlib.md5(signature_str.encode("utf-8")).hexdigest()

        return calculated_sign == sign

    @staticmethod
    def extract_user_id_from_order(order_id: str) -> Optional[int]:
        """
        Extract user_id from order_id with format: user_{user_id}_{timestamp}

        Args:
            order_id: Order ID string

        Returns:
            User ID as integer, or None if format is invalid
        """
        try:
            parts = order_id.split("_")
            if len(parts) >= 2 and parts[0] == "user":
                return int(parts[1])
        except (ValueError, IndexError):
            pass
        return None
