import json
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.models.user import get_async_session, User, Transaction
from app.users import current_active_user
from app.services.heleket_service import HeleketService
from app.services.credit_service import CreditService
from app.services.discount_service import DiscountService

router = APIRouter()


class InvoiceRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Amount in USD (minimum $1)")


class InvoiceResponse(BaseModel):
    invoice_url: str
    uuid: str
    expires_at: int
    order_id: str


@router.post("/invoice", response_model=InvoiceResponse)
async def create_invoice(
    request: InvoiceRequest,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Create a new Heleket payment invoice for the current user.

    Minimum amount: $1.00 USD
    """
    if request.amount < 1.0:
        raise HTTPException(status_code=400, detail="Minimum amount is $1.00 USD")

    try:
        invoice_data = await HeleketService.create_invoice(user.id, request.amount)
        return InvoiceResponse(**invoice_data)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create invoice: {str(e)}"
        )


@router.post("/webhook")
async def heleket_webhook(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Webhook endpoint for Heleket payment notifications.

    This endpoint is called by Heleket when a payment status changes.
    No authentication required, but signature is verified.
    """
    try:
        # Parse webhook payload
        body = await request.json()

        # Extract signature
        sign = body.get("sign")
        if not sign:
            raise HTTPException(status_code=401, detail="Missing signature")

        # Remove sign from data for verification
        webhook_data = {k: v for k, v in body.items() if k != "sign"}

        # Verify signature
        if not HeleketService.verify_webhook_signature(webhook_data, sign):
            raise HTTPException(status_code=401, detail="Invalid signature")

        # Process payment if status is 'paid'
        status = webhook_data.get("status")
        if status == "paid":
            # Extract user_id from order_id
            order_id = webhook_data.get("order_id")
            user_id = HeleketService.extract_user_id_from_order(order_id)

            if not user_id:
                # Log error but return success to avoid retries
                print(f"Invalid order_id format: {order_id}")
                return {"state": 0}

            # Get merchant_amount (amount credited to merchant after fees)
            merchant_amount = float(webhook_data.get("merchant_amount", 0))
            payment_amount_usd = webhook_data.get("payment_amount_usd", "0")

            # Create transaction record with heleket data
            description = f"Heleket deposit: ${payment_amount_usd} USD"

            # Store webhook data in data_id as JSON
            transaction_data = {
                "heleket_uuid": webhook_data.get("uuid"),
                "order_id": order_id,
                "payment_status": status,
                "payer_currency": webhook_data.get("payer_currency"),
                "network": webhook_data.get("network"),
                "txid": webhook_data.get("txid"),
                "merchant_amount": merchant_amount,
                "payment_amount_usd": payment_amount_usd,
            }

            # Add credits to user account (creates transaction with type='heleket')
            await CreditService.add_credits(
                user_id=user_id,
                amount=merchant_amount,
                description=description,
                db=db,
                transaction_type="heleket",
            )

            # Update the transaction's data_id with heleket webhook data
            from sqlalchemy import update
            result = await db.execute(
                select(Transaction)
                .where(Transaction.user_id == user_id)
                .where(Transaction.type == "heleket")
                .where(Transaction.amount == merchant_amount)
                .order_by(Transaction.timestamp.desc())
                .limit(1)
            )
            transaction = result.scalar_one_or_none()
            if transaction:
                transaction.data_id = json.dumps(transaction_data)
                await db.commit()

            # Recalculate discount tier
            await DiscountService.recalculate_and_cache_discount(user_id, db)

        # Always return success to Heleket
        return {"state": 0}

    except HTTPException:
        raise
    except Exception as e:
        # Log error but return success to avoid retries
        print(f"Webhook processing error: {str(e)}")
        return {"state": 0}
