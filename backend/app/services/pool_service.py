from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis_manager import redis_manager
from app.models.user import DataPool, DataPoolSold
from app.services.type_service import TypeService


class PoolService:
    """Service for managing database pool operations."""

    @staticmethod
    async def get_pool_size(data_type: str, db: AsyncSession) -> int:
        """
        Get number of unsold items in database pool for a specific type.

        Args:
            data_type: Type of data
            db: Database session

        Returns:
            Number of unsold items in the pool
        """
        # Count items that haven't been sold (no record in data_pool_sold)
        result = await db.execute(
            select(func.count(DataPool.id))
            .outerjoin(DataPoolSold, DataPool.id == DataPoolSold.pool_id)
            .where(DataPool.type == data_type)
            .where(DataPoolSold.pool_id.is_(None))
        )
        return result.scalar() or 0

    @staticmethod
    async def get_all_pool_sizes(db: AsyncSession) -> dict[str, int]:
        """
        Get sizes for all data types in database pool.

        Args:
            db: Database session

        Returns:
            Dictionary mapping data type names to their pool sizes
        """
        # Get all types with their unsold counts
        result = await db.execute(
            select(DataPool.type, func.count(DataPool.id))
            .outerjoin(DataPoolSold, DataPool.id == DataPoolSold.pool_id)
            .where(DataPoolSold.pool_id.is_(None))
            .group_by(DataPool.type)
        )

        sizes = {}
        for row in result:
            sizes[row[0]] = row[1]

        return sizes

    @staticmethod
    async def purchase_data(
        user_id: int, amount: int, data_type: str, db: AsyncSession
    ) -> dict:
        """
        Atomically purchase data items from database pool.

        Args:
            user_id: User ID
            amount: Number of items to purchase
            data_type: Type of data to purchase
            db: Database session

        Returns:
            dict: {
                "status": "success"|"no_data",
                "data": [...],  # purchased data items
                "type": str  # data type purchased
            }
        """
        from sqlalchemy import and_
        from sqlalchemy.exc import IntegrityError

        # Strategy: Use a subquery to find unsold items, then lock only those
        # This ensures we don't try to lock already-sold items

        # Get more candidates than needed to account for concurrent purchases
        candidate_amount = min(amount * 3, 1000)  # Cap at 1000 to avoid huge queries

        # Subquery to find IDs of sold items
        sold_ids_subquery = select(DataPoolSold.pool_id).subquery()

        # Select unsold items and lock them
        # Use skip_locked=True to allow concurrent purchases without blocking
        result = await db.execute(
            select(DataPool.id, DataPool.data)
            .where(DataPool.type == data_type)
            .where(DataPool.id.notin_(sold_ids_subquery))
            .limit(candidate_amount)
            .with_for_update(skip_locked=True)
        )
        candidates = result.all()

        if not candidates:
            return {"status": "no_data", "type": data_type}

        # Take only the amount needed
        items_to_purchase = candidates[:amount]

        # Mark items as sold using bulk insert
        purchased_data = [data for pool_id, data in items_to_purchase]
        sold_records = [
            DataPoolSold(pool_id=pool_id, user_id=user_id)
            for pool_id, data in items_to_purchase
        ]
        db.add_all(sold_records)

        try:
            await db.commit()
        except IntegrityError as e:
            # Handle rare race condition where item was sold between SELECT and INSERT
            await db.rollback()
            # Retry once with a fresh transaction
            return await PoolService.purchase_data(user_id, amount, data_type, db)

        return {"status": "success", "data": purchased_data, "type": data_type}

    @staticmethod
    async def get_user_purchased_data(user_id: int, db: AsyncSession) -> list[str]:
        """
        Get all data items purchased by a user.

        Args:
            user_id: User ID
            db: Database session

        Returns:
            List of purchased data items
        """
        result = await db.execute(
            select(DataPool.data)
            .join(DataPoolSold, DataPool.id == DataPoolSold.pool_id)
            .where(DataPoolSold.user_id == user_id)
            .order_by(DataPoolSold.sold_at.desc())
        )

        return [row[0] for row in result]

    @staticmethod
    async def get_all_types_with_sizes(db: AsyncSession) -> dict:
        """
        Get all types with their storage and pool sizes.

        Args:
            db: Database session

        Returns:
            Dict with type information including sizes
        """
        result = {}

        for type_name, storage in TypeService.get_all_types().items():
            if storage.get("storage") == "redis":
                size = await redis_manager.get_pool_size(type_name)
            else:  # db
                size = await PoolService.get_pool_size(type_name, db)
            result[type_name] = {"pool_size": size, "config": storage}

        return result
