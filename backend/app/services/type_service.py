from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from app.models.user import DataPool
from app.core.redis_manager import redis_manager

_cache: dict[str, str] = {}  # {type_name: storage}

class TypeService:
    """Service for managing and validating data types across storages."""

    @staticmethod
    def get_type_storage(data_type: str) -> str | None:
        """
        Determine which storage a type uses by checking the in-memory cache.
        Cache is refreshed by background scheduler.
        This is a synchronous method for instant lookups without async overhead.

        Args:
            data_type: Type name

        Returns:
            'redis', 'db', or None if type doesn't exist anywhere
        """
        # Always read from cache - no DB queries, no async overhead
        global _cache
        return _cache.get(data_type)

    @staticmethod
    async def refresh_cache(db: AsyncSession) -> None:
        """
        Public method to refresh the type cache.
        Called by background scheduler.

        Args:
            db: Database session
        """
        await TypeService._refresh_cache(db)

    @staticmethod
    async def _refresh_cache(db: AsyncSession) -> None:
        """
        Refresh the in-memory cache of type-to-storage mappings.

        Args:
            db: Database session
        """
        cache = {}

        # Get Redis types
        redis_types = await redis_manager.get_all_data_types()
        for type_name in redis_types:
            cache[type_name] = "redis"

        # Get DB types
        result = await db.execute(
            select(DataPool.type).distinct()
        )
        for row in result:
            type_name = row[0]
            if type_name not in cache:  # Avoid overwriting if somehow in both
                cache[type_name] = "db"

        # Update cache
        global _cache
        _cache = cache

    @staticmethod
    async def validate_type_storage(data_type: str, requested_storage: str, db: AsyncSession) -> None:
        """
        Validate that a type uses consistent storage across all entries.

        Args:
            data_type: Type name
            requested_storage: Requested storage type ('redis' or 'db')
            db: Database session

        Raises:
            ValueError: If type already exists with different storage
        """
        existing_storage = TypeService.get_type_storage(data_type)

        if existing_storage and existing_storage != requested_storage:
            raise ValueError(
                f"Type '{data_type}' already exists in '{existing_storage}' storage. "
                f"Cannot add to '{requested_storage}' storage. Types must use consistent storage."
            )

    @staticmethod
    async def get_all_types_with_storage(db: AsyncSession) -> dict:
        """
        Get all types from both Redis and DB with their storage locations.

        Args:
            db: Database session

        Returns:
            Dict mapping type names to storage type
        """
        result = {}

        # Get Redis types
        redis_types = await redis_manager.get_all_data_types()
        for type_name in redis_types:
            result[type_name] = "redis"

        # Get DB types
        db_result = await db.execute(
            select(DataPool.type).distinct()
        )
        for row in db_result:
            type_name = row[0]
            if type_name not in result:  # Avoid overwriting if somehow in both
                result[type_name] = "db"

        return result

    @staticmethod
    async def get_all_types_with_sizes(db: AsyncSession) -> dict:
        """
        Get all types with their storage and pool sizes.

        Args:
            db: Database session

        Returns:
            Dict with type information including sizes
        """
        from app.services.pool_service import PoolService

        result = {}

        # Get Redis types and sizes
        redis_sizes = await redis_manager.get_all_pool_sizes()
        for type_name, size in redis_sizes.items():
            result[type_name] = {
                "storage": "redis",
                "pool_size": size
            }

        # Get DB types and sizes
        db_sizes = await PoolService.get_all_pool_sizes(db)
        for type_name, size in db_sizes.items():
            if type_name not in result:  # Avoid overwriting if somehow in both
                result[type_name] = {
                    "storage": "db",
                    "pool_size": size
                }

        return result
