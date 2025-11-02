from datetime import datetime, timedelta
from typing import Optional
import random
import string


class MemoryManager:
    """In-memory data manager for credits, pools, tokens, discounts, and sessions."""

    _instance: Optional["MemoryManager"] = None

    # Storage dictionaries
    _credits: dict[int, float] = {}
    _pools: dict[str, set[str]] = {}
    _sold_data: dict[int, set[str]] = {}
    _user_tokens: dict[int, str] = {}  # user_id -> token
    _token_lookup: dict[str, int] = {}  # token -> user_id
    _discount_cache: dict[int, tuple[float, datetime]] = {}  # user_id -> (discount, expiry)
    _auth_sessions: dict[str, tuple[int, datetime]] = {}  # session_token -> (user_id, expiry)

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # ==================== Credit Operations ====================

    def get_user_credit(self, user_id: int) -> float:
        """Get user credit balance."""
        return self._credits.get(user_id, 0.0)

    def set_user_credit(self, user_id: int, credit: float):
        """Set user credit balance."""
        self._credits[user_id] = round(credit, 5)

    def increment_user_credit(self, user_id: int, amount: float) -> float:
        """Increment user credit and return new balance."""
        current = self._credits.get(user_id, 0.0)
        new_balance = round(current + amount, 5)
        self._credits[user_id] = new_balance
        return new_balance

    def get_all_credits(self) -> dict[int, float]:
        """Get all user credits (for syncing to database)."""
        return self._credits.copy()

    # ==================== Data Pool Operations ====================

    def add_data_to_pool(self, data_items: list[str], data_type: str) -> int:
        """
        Add data items to pool.

        Args:
            data_items: List of data items to add
            data_type: Type of data (e.g., 'short_gmail', 'short_hotmail')

        Returns:
            Number of items actually added (excludes duplicates)
        """
        if not data_items:
            return 0

        if not data_type:
            raise ValueError("Data type is required")

        if data_type not in self._pools:
            self._pools[data_type] = set()

        initial_size = len(self._pools[data_type])
        self._pools[data_type].update(data_items)
        return len(self._pools[data_type]) - initial_size

    def get_pool_size(self, data_type: str) -> int:
        """Get number of items in pool for a specific type."""
        if not data_type:
            raise ValueError("Data type is required")
        return len(self._pools.get(data_type, set()))

    def get_all_pool_sizes(self) -> dict[str, int]:
        """Get sizes for all pool types."""
        return {data_type: len(items) for data_type, items in self._pools.items()}

    def purchase_data(
        self, user_id: int, amount: int, data_type: str, cost_per_item: float, discount: float = 0.0
    ) -> dict:
        """
        Atomically purchase data items for a user.

        Args:
            user_id: User ID
            amount: Number of items to purchase
            data_type: Type of data to purchase
            cost_per_item: Base price per item
            discount: Discount to apply (0.0-1.0)

        Returns:
            dict with status, data, credit_remaining, cost, type
        """
        if not data_type:
            raise ValueError("Data type is required")

        # Calculate discounted cost
        discounted_cost_per_item = cost_per_item * (1 - discount)
        total_cost = amount * discounted_cost_per_item

        # Check credit
        user_credit = self.get_user_credit(user_id)
        if user_credit < total_cost:
            return {
                "status": "insufficient_credit",
                "credit_remaining": user_credit,
            }

        # Check if pool exists and has data
        if data_type not in self._pools or len(self._pools[data_type]) == 0:
            return {"status": "no_data", "credit_remaining": user_credit}

        # Pop items from pool
        available = min(amount, len(self._pools[data_type]))
        if available == 0:
            return {"status": "no_data", "credit_remaining": user_credit}

        purchased_items = []
        for _ in range(available):
            if self._pools[data_type]:
                item = self._pools[data_type].pop()
                purchased_items.append(item)

        # Calculate actual cost based on items purchased
        actual_cost = len(purchased_items) * discounted_cost_per_item
        actual_cost = round(actual_cost, 5)

        # Deduct credit
        new_credit = self.increment_user_credit(user_id, -actual_cost)

        # Track sold data
        if user_id not in self._sold_data:
            self._sold_data[user_id] = set()
        self._sold_data[user_id].update(purchased_items)

        return {
            "status": "success",
            "data": purchased_items,
            "credit_remaining": new_credit,
            "cost": actual_cost,
            "type": data_type,
        }

    def get_user_purchased_data(self, user_id: int) -> list[str]:
        """Get all data items purchased by a user."""
        return list(self._sold_data.get(user_id, set()))

    # ==================== Token Operations ====================

    def set_user_token(self, user_id: int, token: str):
        """Store user token for fast authentication (bidirectional)."""
        # Remove old token if exists
        if user_id in self._user_tokens:
            old_token = self._user_tokens[user_id]
            self._token_lookup.pop(old_token, None)

        # Store new token
        self._user_tokens[user_id] = token
        self._token_lookup[token] = user_id

    def get_user_token(self, user_id: int) -> Optional[str]:
        """Get user's token."""
        return self._user_tokens.get(user_id)

    def get_user_id_by_token(self, token: str) -> Optional[int]:
        """Get user_id by token."""
        return self._token_lookup.get(token)

    def get_all_tokens(self) -> dict[int, str]:
        """Get all user tokens (for syncing to database)."""
        return self._user_tokens.copy()

    # ==================== Discount Cache Operations ====================

    def get_discount(self, user_id: int) -> Optional[float]:
        """
        Get cached discount for user (with TTL check).
        Returns None if not cached or expired.
        """
        if user_id not in self._discount_cache:
            return None

        discount, expiry = self._discount_cache[user_id]
        if datetime.utcnow() > expiry:
            # Expired, remove from cache
            del self._discount_cache[user_id]
            return None

        return discount

    def set_discount(self, user_id: int, discount: float, ttl_seconds: int = 3600):
        """Set cached discount for user with TTL."""
        expiry = datetime.utcnow() + timedelta(seconds=ttl_seconds)
        self._discount_cache[user_id] = (discount, expiry)

    # ==================== Authentication Session Operations ====================

    def create_session(self, session_token: str, user_id: int, ttl_seconds: int = 3600) -> str:
        """Create authentication session with TTL."""
        expiry = datetime.utcnow() + timedelta(seconds=ttl_seconds)
        self._auth_sessions[session_token] = (user_id, expiry)
        return session_token

    def get_session(self, session_token: str) -> Optional[int]:
        """
        Get user_id from session token (with TTL check).
        Returns None if not found or expired.
        """
        if session_token not in self._auth_sessions:
            return None

        user_id, expiry = self._auth_sessions[session_token]
        if datetime.utcnow() > expiry:
            # Expired, remove from cache
            del self._auth_sessions[session_token]
            return None

        return user_id

    def delete_session(self, session_token: str):
        """Delete authentication session."""
        self._auth_sessions.pop(session_token, None)

    def cleanup_expired_sessions(self):
        """Remove expired sessions and discount cache entries."""
        now = datetime.utcnow()

        # Cleanup expired sessions
        expired_sessions = [
            token for token, (_, expiry) in self._auth_sessions.items() if now > expiry
        ]
        for token in expired_sessions:
            del self._auth_sessions[token]

        # Cleanup expired discount cache
        expired_discounts = [
            user_id for user_id, (_, expiry) in self._discount_cache.items() if now > expiry
        ]
        for user_id in expired_discounts:
            del self._discount_cache[user_id]

        return len(expired_sessions) + len(expired_discounts)


# Global instance
memory_manager = MemoryManager()
