import os
import redis.asyncio as redis
from typing import Optional
from app.core.config import settings
from app.services.type_service import TypeService


class RedisManager:
    """Redis connection manager for credit and data pool operations."""

    _instance: Optional["RedisManager"] = None
    _client: Optional[redis.Redis] = None

    # Redis key prefixes
    USER_CREDIT_PREFIX = "credit:user:"
    DATA_POOL_TYPE_PREFIX = "data:pool:type:"  # Typed pool: data:pool:type:{type}
    DATA_SOLD_PREFIX = "data:sold:"
    USER_TOKEN_PREFIX = "token:user:"
    TOKEN_TO_USER_PREFIX = "token:lookup:"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def connect(self):
        """Initialize Redis connection."""
        if self._client is None:
            self._client = await redis.from_url(
                settings.REDIS_URL, encoding="utf-8", decode_responses=True
            )

    async def disconnect(self):
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None

    @property
    def client(self) -> redis.Redis:
        """Get Redis client instance."""
        if self._client is None:
            raise RuntimeError("Redis client not initialized. Call connect() first.")
        return self._client

    # Lua script for atomic purchase operation with data type support
    # Returns: {status: "success"|"insufficient_credit"|"no_data", data: [...], credit_remaining: int}
    PURCHASE_SCRIPT = """
        local user_key = KEYS[1]
        local data_pool_key = KEYS[2]
        local sold_key = KEYS[3]

        local amount = tonumber(ARGV[1])
        local cost_per_item = tonumber(ARGV[2])
        local discount = tonumber(ARGV[3]) or 0

        -- Apply discount to cost per item
        local discounted_cost_per_item = cost_per_item * (1 - discount)

        local user_credit = tonumber(redis.call('GET', user_key) or 0)
        local total_cost = amount * discounted_cost_per_item

        -- Check if user has enough credit
        if user_credit < total_cost then
            return cjson.encode({status="insufficient_credit", credit_remaining=user_credit})
        end

        -- Pop items from data pool
        local data = redis.call('SPOP', data_pool_key, amount)

        if #data == 0 then
            return cjson.encode({status="no_data", credit_remaining=user_credit})
        end

        -- Deduct credit with discounted cost
        local actual_cost = #data * discounted_cost_per_item
        local new_credit = redis.call('INCRBYFLOAT', user_key, -actual_cost)
        new_credit = math.floor(new_credit * 1e5 + 0.5) / 1e5

        -- save the rounded credit back
        redis.call('SET', user_key, new_credit)

        -- Mark data as sold to user
        for i, item in ipairs(data) do
            redis.call('SADD', sold_key, item)
        end

        return cjson.encode({status="success", data=data, credit_remaining=new_credit, cost=actual_cost})
    """

    async def load_lua_scripts(self):
        """Load and register Lua scripts."""
        self.purchase_script_sha = await self.client.script_load(self.PURCHASE_SCRIPT)

    async def get_user_credit(self, user_id: int) -> float:
        """Get user credit from Redis."""
        key = f"{self.USER_CREDIT_PREFIX}{user_id}"
        credit = await self.client.get(key)
        return float(credit) if credit else 0

    async def set_user_credit(self, user_id: int, credit: int):
        """Set user credit in Redis."""
        key = f"{self.USER_CREDIT_PREFIX}{user_id}"
        await self.client.set(key, credit)

    async def increment_user_credit(self, user_id: int, amount: float) -> float:
        """Increment user credit in Redis."""
        key = f"{self.USER_CREDIT_PREFIX}{user_id}"
        return await self.client.incrbyfloat(key, amount)

    async def add_data_to_pool(
        self,
        data_items: list[str],
        data_type: str,
        storage: str = "redis",
        db_session=None,
    ) -> int:
        """
        Add data items to the pool.

        Args:
            data_items: List of data items to add
            data_type: Type of data (e.g., 'gmail', 'hotmail') - REQUIRED
            storage: Storage type ('redis' or 'db')
            db_session: Database session (required if storage='db')

        Returns:
            Number of items actually added (excludes duplicates)
        """
        if not data_items:
            return 0

        if not data_type:
            raise ValueError("Data type is required")

        if storage == "redis":
            pool_key = f"{self.DATA_POOL_TYPE_PREFIX}{data_type}"
            return await self.client.sadd(pool_key, *data_items)
        elif storage == "db":
            if db_session is None:
                raise ValueError("Database session is required for storage='db'")

            # Import here to avoid circular dependency
            from app.models.user import DataPool
            from sqlalchemy import select
            from sqlalchemy.exc import IntegrityError

            added_count = 0
            for item in data_items:
                try:
                    # Check if item already exists
                    result = await db_session.execute(
                        select(DataPool).where(DataPool.data == item)
                    )
                    existing = result.scalar_one_or_none()

                    if not existing:
                        new_item = DataPool(type=data_type, data=item)
                        db_session.add(new_item)
                        added_count += 1
                except IntegrityError:
                    # Item already exists (race condition), skip
                    await db_session.rollback()
                    continue

            await db_session.commit()
            return added_count
        else:
            raise ValueError(
                f"Storage type '{storage}' not supported. Use 'redis' or 'db'."
            )

    async def get_pool_size(self, data_type: str) -> int:
        """
        Get number of items in data pool.

        Args:
            data_type: Type of data - REQUIRED

        Returns:
            Number of items in the specified pool
        """
        if not data_type:
            raise ValueError("Data type is required")

        pool_key = f"{self.DATA_POOL_TYPE_PREFIX}{data_type}"
        return await self.client.scard(pool_key)

    async def get_all_pool_sizes(self) -> dict[str, int]:
        """
        Get sizes for all data type pools.

        Returns:
            Dictionary mapping data type names to their pool sizes
        """
        keys = await self.client.keys(f"{self.DATA_POOL_TYPE_PREFIX}*")
        result = {}

        prefix_len = len(self.DATA_POOL_TYPE_PREFIX)
        for key in keys:
            data_type = key[prefix_len:]
            size = await self.client.scard(key)
            result[data_type] = size

        return result

    async def purchase_data(
        self, user_id: int, amount: int, data_type: str, discount: float = 0.0
    ) -> dict:
        """
        Atomically purchase data items for a user.

        Args:
            user_id: User ID
            amount: Number of items to purchase
            data_type: Type of data to purchase (e.g., 'gmail', 'hotmail') - REQUIRED
            discount: Discount to apply (0.0-1.0, e.g., 0.15 = 15% off)

        Returns:
            dict: {
                "status": "success"|"insufficient_credit"|"no_data",
                "data": [...],  # purchased data items
                "credit_remaining": int,
                "cost": int,  # actual cost (after discount)
                "type": str  # data type purchased
            }
        """
        if not data_type:
            raise ValueError("Data type is required")

        type_config = TypeService.get_type_config(data_type)

        user_key = f"{self.USER_CREDIT_PREFIX}{user_id}"
        sold_key = f"{self.DATA_SOLD_PREFIX}{user_id}"
        pool_key = f"{self.DATA_POOL_TYPE_PREFIX}{data_type}"

        result = await self.client.evalsha(
            self.purchase_script_sha,
            3,
            user_key,
            pool_key,
            sold_key,
            amount,
            type_config.get("price"),
            discount,
        )

        import json

        result_data = json.loads(result)
        result_data["type"] = data_type  # Add type to response
        return result_data

    async def get_user_purchased_data(self, user_id: int) -> list[str]:
        """Get all data items purchased by a user."""
        sold_key = f"{self.DATA_SOLD_PREFIX}{user_id}"
        return await self.client.smembers(sold_key)

    # User token methods
    async def set_user_token(self, user_id: int, token: str):
        """Store user token in Redis for fast authentication."""
        user_key = f"{self.USER_TOKEN_PREFIX}{user_id}"
        token_key = f"{self.TOKEN_TO_USER_PREFIX}{token}"

        # Store bidirectional mapping: user_id -> token and token -> user_id
        await self.client.set(user_key, token)
        await self.client.set(token_key, user_id)

    async def get_user_token(self, user_id: int) -> Optional[str]:
        """Get user's token from Redis."""
        user_key = f"{self.USER_TOKEN_PREFIX}{user_id}"
        return await self.client.get(user_key)

    async def get_user_id_by_token(self, token: str) -> Optional[int]:
        """Get user_id by token from Redis."""
        token_key = f"{self.TOKEN_TO_USER_PREFIX}{token}"
        user_id = await self.client.get(token_key)
        return int(user_id) if user_id else None


# Global instance
redis_manager = RedisManager()
