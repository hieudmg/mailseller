from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.processors.transaction_history import get_transaction_history_processor
from app.core.redis_manager import redis_manager
from app.models.user import UserCredit, Transaction, User


class CreditService:
    """Service for managing user credits and transactions."""

    @staticmethod
    async def sync_credit_to_redis(user_id: int, db: AsyncSession):
        """Sync user credit from PostgreSQL to Redis."""
        result = await db.execute(
            select(UserCredit).where(UserCredit.user_id == user_id)
        )
        user_credit = result.scalar_one_or_none()

        if user_credit:
            await redis_manager.set_user_credit(user_id, user_credit.credits)
        else:
            # Initialize credit if not exists
            new_credit = UserCredit(user_id=user_id, credits=0)
            db.add(new_credit)
            await db.commit()
            await redis_manager.set_user_credit(user_id, 0)

    @staticmethod
    async def sync_credit_to_postgres(user_id: int, db: AsyncSession):
        """Sync user credit from Redis to PostgreSQL."""
        redis_credit = await redis_manager.get_user_credit(user_id)

        result = await db.execute(
            select(UserCredit).where(UserCredit.user_id == user_id)
        )
        user_credit = result.scalar_one_or_none()

        if user_credit:
            user_credit.credits = redis_credit
            user_credit.updated_at = datetime.utcnow()
        else:
            new_credit = UserCredit(user_id=user_id, credits=redis_credit)
            db.add(new_credit)

        await db.commit()

    @staticmethod
    async def add_credits(
        user_id: int, amount: float, description: str, db: AsyncSession
    ):
        """
        Add credits to user account (top-up).
        Uses Redis INCRBY (atomic) as source of truth, then syncs to PostgreSQL.
        No race conditions because Redis INCRBY is atomic.
        """
        # Atomic increment in Redis (source of truth, no race conditions)
        new_balance = await redis_manager.increment_user_credit(user_id, amount)

        # Create transaction record
        transaction = Transaction(
            user_id=user_id,
            amount=amount,
            description=description,
            timestamp=datetime.utcnow(),
        )
        db.add(transaction)

        # Update PostgreSQL with exact value from Redis (don't calculate)
        result = await db.execute(
            select(UserCredit).where(UserCredit.user_id == user_id)
        )
        user_credit = result.scalar_one_or_none()

        if user_credit:
            user_credit.credits = new_balance
            user_credit.updated_at = datetime.utcnow()
        else:
            user_credit = UserCredit(user_id=user_id, credits=new_balance)
            db.add(user_credit)

        await db.commit()

        return new_balance

    @staticmethod
    async def purchase_data(
        user_id: int, amount: int, data_type: str, db: AsyncSession = None
    ) -> dict:
        """
        Purchase data items for user.
        Returns purchase result with data items.
        Redis-first for speed, then immediately sync to PostgreSQL for durability.

        Args:
            user_id: User ID
            amount: Number of items to purchase
            data_type: Type of data to purchase (e.g., 'gmail', 'hotmail') - REQUIRED
            db: Database session

        Returns:
            Purchase result dict
        """
        if not data_type:
            raise ValueError("Data type is required")

        # Atomic purchase via Lua script (credit deducted in Redis)
        result = await redis_manager.purchase_data(user_id, amount, data_type)

        # If purchase succeeded, sync to PostgreSQL immediately
        if result["status"] == "success" and db is not None:
            try:
                # Create transaction record
                transaction = Transaction(
                    user_id=user_id,
                    amount=-result["cost"],  # Negative for purchase
                    description=f"Purchased {len(result['data'])} data items ({data_type})",
                    data_id=",".join(result["data"]),
                    timestamp=datetime.utcnow(),
                )

                transaction_history_processor = get_transaction_history_processor()
                transaction_history_processor.add(transaction)
            except Exception as e:
                # Log error but don't fail purchase (already succeeded in Redis)
                import logging

                logging.error(
                    f"Failed to sync purchase to PostgreSQL for user {user_id}: {e}"
                )
                # Scheduler will fix credit balance, but transaction record may be lost
                await db.rollback()

        return result

    @staticmethod
    async def get_user_credits(user_id: int, db: AsyncSession) -> dict:
        """Get user credits from both Redis (hot) and PostgreSQL (cold)."""
        redis_credit = await redis_manager.get_user_credit(user_id)

        return {"credits": redis_credit}

    @staticmethod
    async def get_transactions(user_id: int, db: AsyncSession, limit: int = 50):
        """Get user transaction history."""
        result = await db.execute(
            select(Transaction)
            .where(Transaction.user_id == user_id)
            .order_by(Transaction.timestamp.desc())
            .limit(limit)
        )
        return result.scalars().all()
