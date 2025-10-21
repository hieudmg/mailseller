from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional
from app.models.user import User, get_async_session
from app.services.credit_service import CreditService
from app.services.type_service import TypeService
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
    amount: float
    description: Optional[str] = "Admin credit addition"


class DataTypeItems(BaseModel):
    type: str  # Data type: gmail, hotmail, etc.
    items: List[str]  # Data items for this type


class UpdateCreditCostRequest(BaseModel):
    cost_per_item: int


@router.post("/credits/add")
async def add_credits(
    request: AddCreditsRequest,
    db: AsyncSession = Depends(get_async_session),
    _: str = Depends(verify_admin_token),
):
    """
    Add credits to a user account (admin operation).
    Requires ADMIN_TOKEN in Authorization header.
    """
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    # get user by email
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_balance = await CreditService.add_credits(
        user.id, request.amount, request.description, db
    )

    return {
        "email": request.email,
        "amount_added": request.amount,
        "new_balance": new_balance,
        "description": request.description,
    }


@router.post("/datapool/add")
async def add_data_to_pool(
    data: List[DataTypeItems],
    _: str = Depends(verify_admin_token),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Add data items to the pool (admin operation).
    Requires ADMIN_TOKEN in Authorization header.

    Args:
        data: JSON array of {type, items, storage} objects

    Returns:
        Summary of items added per type and updated pool sizes

    Example request (direct JSON array):
        [
            {"type": "gmail", "items": ["user1@gmail.com", "user2@gmail.com"]},
            {"type": "hotmail", "items": ["user3@hotmail.com"]}
        ]
    """
    if not data:
        raise HTTPException(status_code=400, detail="No data provided")

    results = []
    total_added = 0

    for data_group in data:
        if not data_group.type:
            raise HTTPException(
                status_code=400, detail="Data type is required for all entries"
            )

        type_config = TypeService.get_type_config(data_group.type)
        if not type_config:
            raise HTTPException(
                status_code=404,
                detail=f"Data type '{data_group.type}' not found in configuration",
            )

        if not data_group.items:
            raise HTTPException(
                status_code=400,
                detail=f"No data items provided for type '{data_group.type}'",
            )

    for data_group in data:
        try:
            type_config = TypeService.get_type_config(data_group.type)
            added_count = await redis_manager.add_data_to_pool(
                data_group.items,
                data_type=data_group.type,
                storage=type_config.get("storage"),
                db_session=db if type_config.get("storage") == "db" else None,
            )

            # Get pool size based on storage type
            if type_config.get("storage") == "redis":
                pool_size = await redis_manager.get_pool_size(data_group.type)
            else:  # db
                from app.services.pool_service import PoolService

                pool_size = await PoolService.get_pool_size(data_group.type, db)

            results.append(
                {
                    "type": data_group.type,
                    "storage": type_config.get("storage"),
                    "added": added_count,
                    "pool_size": pool_size,
                }
            )

            total_added += added_count

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    return {"total_added": total_added, "results": results}
