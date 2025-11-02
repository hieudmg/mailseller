from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.processors.transaction_history import get_transaction_history_processor
from app.core.memory_manager import memory_manager
from app.models.user import UserCredit, Transaction, User


class CreditService:
    """Service for managing user credits and transactions."""

    @staticmethod
    async def sync_credit_to_memory(user_id: int, db: AsyncSession):
        """Sync user credit from PostgreSQL to memory."""
        result = await db.execute(
            select(UserCredit).where(UserCredit.user_id == user_id)
        )
        user_credit = result.scalar_one_or_none()

        if user_credit:
            memory_manager.set_user_credit(user_id, user_credit.credits)
        else:
            # Initialize credit if not exists
            new_credit = UserCredit(user_id=user_id, credits=0)
            db.add(new_credit)
            await db.commit()
            memory_manager.set_user_credit(user_id, 0)

    @staticmethod
    async def sync_credit_to_postgres(user_id: int, db: AsyncSession):
        """Sync user credit from memory to PostgreSQL."""
        memory_credit = memory_manager.get_user_credit(user_id)

        result = await db.execute(
            select(UserCredit).where(UserCredit.user_id == user_id)
        )
        user_credit = result.scalar_one_or_none()

        if user_credit:
            user_credit.credits = memory_credit
            user_credit.updated_at = datetime.utcnow()
        else:
            new_credit = UserCredit(user_id=user_id, credits=memory_credit)
            db.add(new_credit)

        await db.commit()

    @staticmethod
    async def add_credits(
        user_id: int,
        amount: float,
        description: str,
        db: AsyncSession,
        transaction_type: str = "admin_deposit"
    ):
        """
        Add credits to user account (top-up).
        Uses memory manager as source of truth, then syncs to PostgreSQL.

        Args:
            user_id: User ID
            amount: Amount to add
            description: Transaction description
            db: Database session
            transaction_type: Type of transaction ('admin_deposit', 'heleket')
        """
        # Increment in memory (source of truth)
        new_balance = memory_manager.increment_user_credit(user_id, amount)

        # Create transaction record
        transaction = Transaction(
            user_id=user_id,
            amount=amount,
            type=transaction_type,
            description=description,
            timestamp=datetime.utcnow(),
        )
        db.add(transaction)

        # Update PostgreSQL with exact value from memory (don't calculate)
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
        user_id: int,
        amount: int,
        data_type: str,
        db: AsyncSession = None,
        discount: float = 0.0,
    ) -> dict:
        """
        Purchase data items for user.
        Returns purchase result with data items.
        Memory-first for speed, then immediately sync to PostgreSQL for durability.

        Args:
            user_id: User ID
            amount: Number of items to purchase
            data_type: Type of data to purchase (e.g., 'short_gmail', 'short_hotmail') - REQUIRED
            db: Database session
            discount: Discount to apply (0.0-1.0, e.g., 0.15 = 15% off)

        Returns:
            Purchase result dict
        """
        if not data_type:
            raise ValueError("Data type is required")

        # Get price from type config
        from app.services.type_service import TypeService
        type_config = TypeService.get_type_config(data_type)
        if not type_config:
            raise ValueError(f"Data type '{data_type}' not found")

        # Atomic purchase via memory manager (credit deducted with discount applied)
        result = memory_manager.purchase_data(
            user_id, amount, data_type, type_config["price"], discount
        )

        # If purchase succeeded, sync to PostgreSQL immediately
        if result["status"] == "success" and db is not None:
            try:
                # Create transaction record
                transaction = Transaction(
                    user_id=user_id,
                    amount=-result["cost"],  # Negative for purchase
                    type="purchase",
                    description=f"Purchased {len(result['data'])} data items ({data_type})",
                    data_id=",".join(result["data"]),
                    timestamp=datetime.utcnow(),
                )

                transaction_history_processor = get_transaction_history_processor()
                transaction_history_processor.add(transaction)
            except Exception as e:
                # Log error but don't fail purchase (already succeeded in memory)
                import logging

                logging.error(
                    f"Failed to sync purchase to PostgreSQL for user {user_id}: {e}"
                )
                # Scheduler will fix credit balance, but transaction record may be lost
                await db.rollback()

        return result

    @staticmethod
    async def get_user_credits(user_id: int, db: AsyncSession) -> dict:
        """Get user credits from memory (hot data)."""
        memory_credit = memory_manager.get_user_credit(user_id)

        return {"credits": memory_credit}

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
