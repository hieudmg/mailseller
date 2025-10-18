from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional
from app.models.user import User, get_async_session
from app.services.credit_service import CreditService
from app.core.redis_manager import redis_manager
from app.core.config import settings
from sqlalchemy import select

router = APIRouter()
security = HTTPBearer()


def verify_admin_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify admin token from Authorization header."""
    if credentials.credentials != settings.ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid admin token")
    return credentials.credentials


class AddCreditsRequest(BaseModel):
    email: str
    amount: int
    description: Optional[str] = "Admin credit addition"


class AddDataRequest(BaseModel):
    data_items: List[str]


class UpdateCreditCostRequest(BaseModel):
    cost_per_item: int


@router.post("/credits/add")
async def add_credits(
    request: AddCreditsRequest,
    db: AsyncSession = Depends(get_async_session),
    _: str = Depends(verify_admin_token)
):
    """
    Add credits to a user account (admin operation).
    Requires ADMIN_TOKEN in Authorization header.
    """
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    # get user by email
    result = await db.execute(
        select(User).where(User.email == request.email)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_balance = await CreditService.add_credits(
        user.id,
        request.amount,
        request.description,
        db
    )

    return {
        "email": request.email,
        "amount_added": request.amount,
        "new_balance": new_balance,
        "description": request.description
    }


@router.post("/datapool/add")
async def add_data_to_pool(
    request: AddDataRequest,
    _: str = Depends(verify_admin_token)
):
    """
    Add data items to the pool (admin operation).
    Requires ADMIN_TOKEN in Authorization header.
    """
    if not request.data_items:
        raise HTTPException(status_code=400, detail="No data items provided")

    added_count = await redis_manager.add_data_to_pool(request.data_items)

    return {
        "added": added_count,
        "total_pool_size": await redis_manager.get_pool_size()
    }


@router.post("/datapool/config/cost")
async def update_credit_cost(
    request: UpdateCreditCostRequest,
    _: str = Depends(verify_admin_token)
):
    """
    Update credit cost per item (admin operation).
    Requires ADMIN_TOKEN in Authorization header.
    """
    if request.cost_per_item <= 0:
        raise HTTPException(status_code=400, detail="Cost must be positive")

    redis_manager.CREDIT_PER_ITEM = request.cost_per_item

    return {
        "cost_per_item": request.cost_per_item,
        "message": "Credit cost updated successfully"
    }


@router.get("/datapool/config/cost")
async def get_credit_cost(
    _: str = Depends(verify_admin_token)
):
    """
    Get current credit cost per item (admin operation).
    Requires ADMIN_TOKEN in Authorization header.
    """
    return {"cost_per_item": redis_manager.CREDIT_PER_ITEM}
