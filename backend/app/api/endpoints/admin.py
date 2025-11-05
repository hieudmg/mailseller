from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional
from app.models.user import User, get_async_session
from app.services.credit_service import CreditService
from app.services.type_service import TypeService
from app.core.memory_manager import memory_manager
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


class SetDiscountRequest(BaseModel):
    email: str
    discount: Optional[float] = None  # None to clear, 0.0-1.0 to set


class SetPasswordRequest(BaseModel):
    email: str
    new_password: str


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
        user.id, request.amount, request.description, db, transaction_type="admin_deposit"
    )

    # Recalculate and cache discount after adding credits
    from app.services.discount_service import DiscountService

    new_discount = await DiscountService.recalculate_and_cache_discount(user.id, db)

    return {
        "email": request.email,
        "amount_added": request.amount,
        "new_balance": new_balance,
        "new_discount": new_discount,
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
            storage = type_config.get("storage")

            if storage == "memory":
                # Add to memory pool
                added_count = memory_manager.add_data_to_pool(
                    data_group.items, data_type=data_group.type
                )
                pool_size = memory_manager.get_pool_size(data_group.type)
            else:  # db
                # Add to database pool
                from app.models.user import DataPool
                from sqlalchemy import select
                from sqlalchemy.exc import IntegrityError

                added_count = 0
                for item in data_group.items:
                    try:
                        # Check if item already exists
                        result_check = await db.execute(
                            select(DataPool).where(DataPool.data == item)
                        )
                        existing = result_check.scalar_one_or_none()

                        if not existing:
                            new_item = DataPool(type=data_group.type, data=item)
                            db.add(new_item)
                            added_count += 1
                    except IntegrityError:
                        # Item already exists (race condition), skip
                        await db.rollback()
                        continue

                await db.commit()

                # Get pool size from database
                from app.services.pool_service import PoolService
                pool_size = await PoolService.get_pool_size(data_group.type, db)

            results.append(
                {
                    "type": data_group.type,
                    "storage": storage,
                    "added": added_count,
                    "pool_size": pool_size,
                }
            )

            total_added += added_count

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    return {"total_added": total_added, "results": results}


@router.post("/discount/set")
async def set_custom_discount(
    request: SetDiscountRequest,
    db: AsyncSession = Depends(get_async_session),
    _: str = Depends(verify_admin_token),
):
    """
    Set or clear custom discount for user (admin operation).
    Requires ADMIN_TOKEN in Authorization header.

    Custom discount overrides tier-based discount when set.

    Args:
        email: User email
        discount: Discount value (0.0-1.0, e.g., 0.15 = 15% off) or null to clear

    Examples:
        - Set 15% discount: {"email": "user@example.com", "discount": 0.15}
        - Clear discount: {"email": "user@example.com", "discount": null}
    """
    # Validate discount value
    if request.discount is not None:
        if request.discount < 0.0 or request.discount > 1.0:
            raise HTTPException(
                status_code=400,
                detail="Discount must be between 0.0 and 1.0 (e.g., 0.15 = 15% off)",
            )

    # Find user by email
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update custom discount (can be set or cleared to None)
    user.custom_discount = request.discount
    await db.commit()

    # Recalculate and cache discount
    from app.services.discount_service import DiscountService

    new_discount = await DiscountService.recalculate_and_cache_discount(user.id, db)

    # Get tier info for response
    tier_info = await DiscountService.calculate_user_tier(user.id, db)

    return {
        "status": "success",
        "email": request.email,
        "custom_discount": user.custom_discount,
        "final_discount": new_discount,
        "tier_info": tier_info,
        "message": (
            f"Custom discount set to {user.custom_discount * 100}%"
            if request.discount is not None
            else "Custom discount cleared, using tier-based discount"
        ),
    }


@router.post("/password/set")
async def set_user_password(
    request: SetPasswordRequest,
    db: AsyncSession = Depends(get_async_session),
    _: str = Depends(verify_admin_token),
):
    """
    Set a user's password (admin operation).
    Requires ADMIN_TOKEN in Authorization header.

    Args:
        email: User email
        new_password: New password for the user

    Example:
        {"email": "user@example.com", "new_password": "newpassword123"}
    """
    # Validate password
    if len(request.new_password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters",
        )

    # Find user by email
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Hash the new password
    from fastapi_users.password import PasswordHelper

    password_helper = PasswordHelper()
    new_hashed_password = password_helper.hash(request.new_password)

    # Update user password
    user.hashed_password = new_hashed_password
    await db.commit()

    return {
        "status": "success",
        "email": request.email,
        "message": f"Password updated successfully for {request.email}",
    }
