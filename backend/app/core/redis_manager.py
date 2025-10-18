import os
import redis.asyncio as redis
from typing import Optional
from app.core.config import settings


class RedisManager:
    """Redis connection manager for credit and data pool operations."""

    _instance: Optional["RedisManager"] = None
    _client: Optional[redis.Redis] = None

    # Redis key prefixes
    USER_CREDIT_PREFIX = "credit:user:"
    DATA_POOL_PREFIX = "data:pool"
    DATA_SOLD_PREFIX = "data:sold:"
    USER_TOKEN_PREFIX = "token:user:"
    TOKEN_TO_USER_PREFIX = "token:lookup:"

    # Configuration
    CREDIT_PER_ITEM = 1  # Cost per data item (configurable by admin later)

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def connect(self):
        """Initialize Redis connection."""
        if self._client is None:
            self._client = await redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
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

    # Lua script for atomic purchase operation
    # Returns: {status: "success"|"insufficient_credit"|"no_data", data: [...], credit_remaining: int}
    PURCHASE_SCRIPT = """
        local user_key = KEYS[1]
        local data_pool_key = KEYS[2]
        local sold_key = KEYS[3]

        local amount = tonumber(ARGV[1])
        local cost_per_item = tonumber(ARGV[2])

        local user_credit = tonumber(redis.call('GET', user_key) or 0)
        local total_cost = amount * cost_per_item

        -- Check if user has enough credit
        if user_credit < total_cost then
            return cjson.encode({status="insufficient_credit", credit_remaining=user_credit})
        end

        -- Pop items from data pool
        local data = redis.call('SPOP', data_pool_key, amount)

        if #data == 0 then
            return cjson.encode({status="no_data", credit_remaining=user_credit})
        end

        -- Deduct credit
        local actual_cost = #data * cost_per_item
        local new_credit = redis.call('DECRBY', user_key, actual_cost)

        -- Mark data as sold to user
        for i, item in ipairs(data) do
            redis.call('SADD', sold_key, item)
        end

        return cjson.encode({status="success", data=data, credit_remaining=new_credit, cost=actual_cost})
    """

    async def load_lua_scripts(self):
        """Load and register Lua scripts."""
        self.purchase_script_sha = await self.client.script_load(self.PURCHASE_SCRIPT)

    async def get_user_credit(self, user_id: int) -> int:
        """Get user credit from Redis."""
        key = f"{self.USER_CREDIT_PREFIX}{user_id}"
        credit = await self.client.get(key)
        return int(credit) if credit else 0

    async def set_user_credit(self, user_id: int, credit: int):
        """Set user credit in Redis."""
        key = f"{self.USER_CREDIT_PREFIX}{user_id}"
        await self.client.set(key, credit)

    async def increment_user_credit(self, user_id: int, amount: int) -> int:
        """Increment user credit in Redis."""
        key = f"{self.USER_CREDIT_PREFIX}{user_id}"
        return await self.client.incrby(key, amount)

    async def add_data_to_pool(self, data_items: list[str]) -> int:
        """Add data items to the pool."""
        if not data_items:
            return 0
        return await self.client.sadd(self.DATA_POOL_PREFIX, *data_items)

    async def get_pool_size(self) -> int:
        """Get number of items in data pool."""
        return await self.client.scard(self.DATA_POOL_PREFIX)

    async def purchase_data(self, user_id: int, amount: int) -> dict:
        """
        Atomically purchase data items for a user.

        Returns:
            dict: {
                "status": "success"|"insufficient_credit"|"no_data",
                "data": [...],  # purchased data items
                "credit_remaining": int,
                "cost": int  # actual cost
            }
        """
        user_key = f"{self.USER_CREDIT_PREFIX}{user_id}"
        sold_key = f"{self.DATA_SOLD_PREFIX}{user_id}"

        result = await self.client.evalsha(
            self.purchase_script_sha,
            3,
            user_key,
            self.DATA_POOL_PREFIX,
            sold_key,
            amount,
            self.CREDIT_PER_ITEM
        )

        import json
        return json.loads(result)

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
