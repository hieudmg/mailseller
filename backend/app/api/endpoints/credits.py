from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, Union
from app.models.user import User, UserToken, get_async_session, Transaction
from app.services.credit_service import CreditService
from app.users import current_active_user, get_user_from_token
from app.core.redis_manager import redis_manager
from app.core.token_utils import generate_user_token

router = APIRouter()


from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.users import fastapi_users


bearer_security = HTTPBearer(auto_error=False)
optional_cookie_user = fastapi_users.current_user(active=True, optional=True)


async def get_user_from_either_auth(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_security),
    cookie_user: Optional[User] = Depends(optional_cookie_user),
    db: AsyncSession = Depends(get_async_session)
) -> User:
    """Try to authenticate user using either bearer token or cookie-based auth."""
    # Try bearer token authentication first
    if credentials:
        try:
            return await get_user_from_token(credentials, db)
        except HTTPException:
            pass

    # Try cookie-based authentication
    if cookie_user:
        return cookie_user

    # If both methods fail, raise authentication error
    raise HTTPException(
        status_code=401,
        detail="Could not validate credentials. Please provide either a valid bearer token or valid session cookie."
    )


class CreditResponse(BaseModel):
    credits: int


@router.get("/credits", response_model=CreditResponse)
async def get_my_credits(
    user: User = Depends(get_user_from_token),
    db: AsyncSession = Depends(get_async_session)
):
    """Get current user's credit information."""
    return await CreditService.get_user_credits(user.id, db)




@router.get("/purchase")
async def purchase_data(
    amount: int,
    type: str,
    token: str,
    db: AsyncSession = Depends(get_async_session)
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

    if not type:
        raise HTTPException(status_code=400, detail="Data type is required")

    if not token:
        raise HTTPException(status_code=400, detail="Token is required")

    # Authenticate user by token
    from app.core.redis_manager import redis_manager
    user_id = await redis_manager.get_user_id_by_token(token)

    # Determine which storage the type uses
    from app.services.type_service import TypeService
    storage = TypeService.get_type_storage(type)

    if not storage:
        raise HTTPException(
            status_code=404,
            detail=f"Data type '{type}' not found in any storage"
        )

    try:
        if storage == "redis":
            result = await CreditService.purchase_data(user_id, amount, type, db)
        else:  # db storage
            from app.services.pool_service import PoolService

            # Check credit first
            user_credit = await redis_manager.get_user_credit(user_id)
            cost = amount * redis_manager.CREDIT_PER_ITEM

            if user_credit < cost:
                raise HTTPException(
                    status_code=402,
                    detail=f"Insufficient credits. You have {user_credit} credits."
                )

            # Purchase from database
            db_result = await PoolService.purchase_data(user_id, amount, type, db)

            if db_result["status"] == "no_data":
                raise HTTPException(
                    status_code=404,
                    detail=f"No data available in pool for type '{type}'"
                )

            # Deduct credits from Redis
            new_credit = await redis_manager.client.decrby(
                f"{redis_manager.USER_CREDIT_PREFIX}{user_id}",
                cost
            )

            # Create transaction record
            from app.models.user import Transaction
            from app.core.processors.transaction_history import get_transaction_history_processor
            from datetime import datetime

            transaction = Transaction(
                user_id=user_id,
                amount=-cost,
                description=f"Purchased {len(db_result['data'])} data items ({type})",
                data_id=",".join(db_result["data"]),
                timestamp=datetime.utcnow()
            )

            transaction_history_processor = get_transaction_history_processor()
            transaction_history_processor.add(transaction)

            result = {
                "status": "success",
                "data": db_result["data"],
                "type": type,
                "cost": cost,
                "credit_remaining": new_credit
            }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise

    if result["status"] == "insufficient_credit":
        raise HTTPException(
            status_code=402,
            detail=f"Insufficient credits. You have {result['credit_remaining']} credits."
        )
    elif result["status"] == "no_data":
        raise HTTPException(
            status_code=404,
            detail=f"No data available in pool for type '{type}'"
        )

    return {
        "status": "success",
        "data": result["data"],
        "type": result["type"],
        "cost": result["cost"],
        "credit_remaining": result["credit_remaining"]
    }



@router.get("/transactions")
async def get_my_transactions(
    request: Request,
    page: int = 1,
    limit: int = 20,
    user: User = Depends(get_user_from_either_auth),
    db: AsyncSession = Depends(get_async_session)
):
    """Get current user's transaction history with pagination. Supports both bearer token and cookie authentication."""
    # Validate limit
    if limit not in [20, 50, 100]:
        limit = 20
    if page < 1:
        page = 1
    offset = (page - 1) * limit

    # Get total count
    from sqlalchemy import func
    total_result = await db.execute(
        func.count().select().where(Transaction.user_id == user.id)
    )
    total = total_result.scalar() if total_result else 0

    # Get paginated transactions
    result = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == user.id)
        .order_by(Transaction.timestamp.desc())
        .offset(offset)
        .limit(limit)
    )
    transactions = result.scalars().all()

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "transactions": [
            {
                "id": t.id,
                "amount": t.amount,
                "description": t.description,
                "data_id": t.data_id,
                "timestamp": t.timestamp.isoformat()
            } for t in transactions
        ]
    }


@router.get("/token")
async def get_my_token(
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get current user's API token (cookie auth)."""
    result = await db.execute(
        select(UserToken).where(UserToken.user_id == user.id)
    )
    user_token = result.scalar_one_or_none()

    if user_token is None:
        raise HTTPException(status_code=404, detail="No API token found for user")

    return {
        "user_id": user.id,
        "token": user_token.token,
        "created_at": user_token.created_at.isoformat(),
        "updated_at": user_token.updated_at.isoformat()
    }


@router.post("/token/rotate")
async def rotate_my_token(
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Rotate current user's API token (cookie auth). Generates a new token and invalidates the old one. Creates a new token if none exists."""
    # Get existing token
    result = await db.execute(
        select(UserToken).where(UserToken.user_id == user.id)
    )
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
            "message": "Token created successfully."
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
        "message": "Token rotated successfully. Old token is now invalid."
    }
