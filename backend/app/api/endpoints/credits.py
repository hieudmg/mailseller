from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.models.user import User, UserToken, get_async_session, Transaction
from app.services.credit_service import CreditService
from app.users import current_active_user, get_user_from_token
from app.core.redis_manager import redis_manager
from app.core.token_utils import generate_user_token

router = APIRouter()


from fastapi.security import HTTPBearer
from app.users import fastapi_users


bearer_security = HTTPBearer(auto_error=False)
optional_cookie_user = fastapi_users.current_user(active=True, optional=True)


class CreditResponse(BaseModel):
    credits: float


@router.get("/credits", response_model=CreditResponse)
async def get_my_credits(
    user: User = Depends(get_user_from_token),
    db: AsyncSession = Depends(get_async_session),
):
    """Get current user's credit information."""
    return await CreditService.get_user_credits(user.id, db)


@router.get("/purchase")
async def purchase_data(
    amount: int, type: str, token: str, db: AsyncSession = Depends(get_async_session)
):
    """
    Purchase data items using credits.

    Args:
        amount: Number of items to purchase (query parameter)
        type: Data type to purchase (query parameter)
        token: User API token (query parameter)
        db: Database session

    Returns:
        Purchase result with data items and remaining credits
    """
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    if amount > 100:
        raise HTTPException(
            status_code=400, detail="Amount exceeds maximum limit of 100"
        )

    if not type:
        raise HTTPException(status_code=400, detail="Data type is required")

    if not token:
        raise HTTPException(status_code=400, detail="Token is required")

    # Authenticate user by token
    from app.core.redis_manager import redis_manager

    user_id = await redis_manager.get_user_id_by_token(token)

    # Determine which storage the type uses
    from app.services.type_service import TypeService

    type_config = TypeService.get_type_config(type)

    storage = type_config.get("storage")

    if not storage:
        raise HTTPException(
            status_code=404, detail=f"Data type '{type}' not found in any storage"
        )

    # Get user discount (cached in Redis, fast)
    from app.services.discount_service import DiscountService

    discount = await DiscountService.get_user_discount(user_id, db)

    try:
        if storage == "redis":
            result = await CreditService.purchase_data(
                user_id, amount, type, db, discount
            )
        else:  # db storage
            from app.services.pool_service import PoolService

            # Check credit first
            user_credit = await redis_manager.get_user_credit(user_id)
            base_cost: float = amount * type_config.get("price")

            # Apply discount
            cost = DiscountService.apply_discount(base_cost, discount)

            if user_credit < cost:
                raise HTTPException(
                    status_code=402,
                    detail=f"Insufficient credits. You have {user_credit} credits.",
                )

            # Purchase from database
            db_result = await PoolService.purchase_data(user_id, amount, type, db)

            if db_result["status"] == "no_data":
                raise HTTPException(
                    status_code=404,
                    detail=f"No data available in pool for type '{type}'",
                )

            # Deduct credits from Redis
            new_credit = await redis_manager.client.incrbyfloat(
                f"{redis_manager.USER_CREDIT_PREFIX}{user_id}", -cost
            )

            # Create transaction record
            from app.models.user import Transaction
            from app.core.processors.transaction_history import (
                get_transaction_history_processor,
            )
            from datetime import datetime

            transaction = Transaction(
                user_id=user_id,
                amount=-cost,
                type="purchase",
                description=f"Purchased {len(db_result['data'])} data items ({type})",
                data_id=",".join(db_result["data"]),
                timestamp=datetime.utcnow(),
            )

            transaction_history_processor = get_transaction_history_processor()
            transaction_history_processor.add(transaction)

            result = {
                "status": "success",
                "data": db_result["data"],
                "type": type,
                "cost": cost,
                "credit_remaining": new_credit,
            }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise

    if result["status"] == "insufficient_credit":
        raise HTTPException(
            status_code=402,
            detail=f"Insufficient credits. You have {result['credit_remaining']} credits.",
        )
    elif result["status"] == "no_data":
        raise HTTPException(
            status_code=404, detail=f"No data available in pool for type '{type}'"
        )

    return {
        "status": "success",
        "data": result["data"],
        "type": result["type"],
        "cost": result["cost"],
        "credit_remaining": result["credit_remaining"],
    }


@router.get("/transactions")
async def get_my_transactions(
    request: Request,
    page: int = 1,
    limit: int = 20,
    types: Optional[List[str]] = Query(None),  # Filter by multiple transaction types
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get current user's transaction history with pagination and optional filtering.

    Query Parameters:
        - page: Page number (default: 1)
        - limit: Items per page - 20, 50, or 100 (default: 20)
        - types: Filter by transaction types (optional, can pass multiple)
            - 'purchase': Data purchases
            - 'admin_deposit': Admin credit deposits
            - 'heleket': Heleket payment deposits
            - None: All transactions

    Example: /api/transactions?types=heleket&types=admin_deposit

    Supports both bearer token and cookie authentication.
    """
    # Validate limit
    if limit not in [20, 50, 100]:
        limit = 20
    if page < 1:
        page = 1
    offset = (page - 1) * limit

    # Validate types parameter
    valid_types = ["purchase", "admin_deposit", "heleket"]
    if types:
        for t in types:
            if t not in valid_types:
                raise HTTPException(status_code=400, detail=f"Invalid type parameter")

    # Build base query
    from sqlalchemy import func

    base_query = select(Transaction).where(Transaction.user_id == user.id)
    count_query = (
        select(func.count())
        .select_from(Transaction)
        .where(Transaction.user_id == user.id)
    )

    # Apply type filter
    if types:
        base_query = base_query.where(Transaction.type.in_(types))
        count_query = count_query.where(Transaction.type.in_(types))

    # Get total count with filter applied
    total_result = await db.execute(count_query)
    total = total_result.scalar() if total_result else 0

    # Get paginated transactions
    result = await db.execute(
        base_query.order_by(Transaction.timestamp.desc()).offset(offset).limit(limit)
    )
    transactions = result.scalars().all()

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "type_filter": types,
        "transactions": [
            {
                "id": t.id,
                "amount": t.amount,
                "type": t.type,
                "description": t.description,
                "data_id": t.data_id,
                "timestamp": t.timestamp.isoformat(),
            }
            for t in transactions
        ],
    }


@router.get("/token")
async def get_my_token(
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Get current user's API token (cookie auth)."""
    result = await db.execute(select(UserToken).where(UserToken.user_id == user.id))
    user_token = result.scalar_one_or_none()

    if user_token is None:
        raise HTTPException(status_code=404, detail="No API token found for user")

    return {
        "user_id": user.id,
        "token": user_token.token,
        "created_at": user_token.created_at.isoformat(),
        "updated_at": user_token.updated_at.isoformat(),
    }


@router.post("/token/rotate")
async def rotate_my_token(
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Rotate current user's API token (cookie auth). Generates a new token and invalidates the old one. Creates a new token if none exists."""
    # Get existing token
    result = await db.execute(select(UserToken).where(UserToken.user_id == user.id))
    user_token = result.scalar_one_or_none()

    # Generate new token
    new_token = generate_user_token(user.email)

    if user_token is None:
        # Create new token if none exists
        user_token = UserToken(user_id=user.id, token=new_token)
        db.add(user_token)
        await db.commit()
        await db.refresh(user_token)

        # Store new token in Redis
        await redis_manager.set_user_token(user.id, new_token)

        return {
            "user_id": user.id,
            "token": new_token,
            "created_at": user_token.created_at.isoformat(),
            "updated_at": user_token.updated_at.isoformat(),
            "message": "Token created successfully.",
        }

    # Delete old token from Redis
    old_token = user_token.token
    old_token_key = f"{redis_manager.TOKEN_TO_USER_PREFIX}{old_token}"
    await redis_manager.client.delete(old_token_key)

    # Update token in database
    user_token.token = new_token
    await db.commit()
    await db.refresh(user_token)

    # Store new token in Redis
    await redis_manager.set_user_token(user.id, new_token)

    return {
        "user_id": user.id,
        "token": new_token,
        "created_at": user_token.created_at.isoformat(),
        "updated_at": user_token.updated_at.isoformat(),
        "message": "Token rotated successfully. Old token is now invalid.",
    }


@router.get("/tiers")
async def get_all_tiers():
    """
    Get list of all available discount tiers.
    Returns all tiers with their thresholds and discounts.
    """
    from app.core.config import settings

    # Sort tiers by threshold
    tiers_sorted = sorted(settings.RANKS.items(), key=lambda x: x[1]["weekly_credit"])

    return {
        "tiers": [
            {
                "code": tier_code,
                "name": tier_info["name"],
                "discount": tier_info["discount"],
                "threshold": tier_info["weekly_credit"],
            }
            for tier_code, tier_info in tiers_sorted
        ]
    }


@router.get("/tier")
async def get_my_tier(
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get current user's discount tier based on last 7 days deposits.
    Returns tier information, deposit amount, and final discount.
    """
    from app.services.discount_service import DiscountService

    # Calculate tier based on 7-day deposits
    tier_info = await DiscountService.calculate_user_tier(user.id, db)

    # Get custom discount if set
    custom_discount = user.custom_discount

    # Determine final discount (custom overrides tier)
    final_discount = (
        custom_discount if custom_discount is not None else tier_info["tier_discount"]
    )

    return {
        "tier_code": tier_info["tier_code"],
        "tier_name": tier_info["tier_name"],
        "tier_discount": tier_info["tier_discount"],
        "deposit_amount": tier_info["deposit_amount"],
        "next_tier": tier_info["next_tier"],
        "custom_discount": custom_discount,
        "final_discount": final_discount,
        "discount_source": "custom" if custom_discount is not None else "tier",
    }
