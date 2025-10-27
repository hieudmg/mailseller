from datetime import datetime, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis_manager import redis_manager
from app.core.config import settings
from app.models.user import User, Transaction


class DiscountService:
    """Service for managing user discount tiers based on 7-day deposits."""

    # Redis key prefix for cached discount
    USER_DISCOUNT_PREFIX = "discount:user:"
    CACHE_TTL = 3600  # 1 hour

    @staticmethod
    async def calculate_user_tier(user_id: int, db: AsyncSession) -> dict:
        """
        Calculate user's tier based on last 7 days deposits.

        Returns:
            {
                "tier_code": "iron"|"bronze"|...,
                "tier_name": "Iron"|"Bronze"|...,
                "tier_discount": 0.0-0.2,
                "deposit_amount": float,
                "next_tier": {...} or None
            }
        """
        # Calculate 7 days ago timestamp
        seven_days_ago = datetime.utcnow() - timedelta(days=7)

        # Query Transaction table for user's deposits in last 7 days
        # Sum amount WHERE amount > 0 AND timestamp >= seven_days_ago
        result = await db.execute(
            select(func.sum(Transaction.amount))
            .where(Transaction.user_id == user_id)
            .where(Transaction.amount > 0)
            .where(Transaction.timestamp >= seven_days_ago)
        )
        deposit_amount = result.scalar() or 0.0

        # Match against RANKS thresholds (weekly_credit field = 7-day deposit threshold)
        ranks_sorted = sorted(
            settings.RANKS.items(), key=lambda x: x[1]["weekly_credit"]
        )

        # Find the tier user belongs to
        current_tier = ranks_sorted[0][1]  # Default to iron
        current_tier_code = ranks_sorted[0][0]
        next_tier = None

        # Find current tier by iterating through all ranks
        for i, (tier_code, tier_info) in enumerate(ranks_sorted):
            if deposit_amount >= tier_info["weekly_credit"]:
                current_tier = tier_info
                current_tier_code = tier_code

        # Find next tier (the tier immediately above current tier)
        for i, (tier_code, tier_info) in enumerate(ranks_sorted):
            if tier_code == current_tier_code:
                # Found current tier, check if next tier exists
                if i + 1 < len(ranks_sorted):
                    next_tier_code, next_tier_info = ranks_sorted[i + 1]
                    next_tier = {
                        "tier_code": next_tier_code,
                        "tier_name": next_tier_info["name"],
                        "tier_discount": next_tier_info["discount"],
                        "required_deposit": next_tier_info["weekly_credit"],
                        "remaining": next_tier_info["weekly_credit"] - deposit_amount,
                    }
                break

        return {
            "tier_code": current_tier_code,
            "tier_name": current_tier["name"],
            "tier_discount": current_tier["discount"],
            "deposit_amount": deposit_amount,
            "next_tier": next_tier,
        }

    @staticmethod
    async def get_user_discount(user_id: int, db: AsyncSession) -> float:
        """
        Get final discount for user (custom or tier-based).
        PERFORMANCE: Checks Redis cache first, only queries DB on cache miss.

        Returns:
            Final discount as float (0.0-1.0)
        """
        # Check Redis cache first (fast path)
        cache_key = f"{DiscountService.USER_DISCOUNT_PREFIX}{user_id}"
        cached_discount = await redis_manager.client.get(cache_key)

        if cached_discount is not None:
            return float(cached_discount)

        # Cache miss - query database
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            # User not found, return 0 discount
            return 0.0

        # Check if custom discount is set
        if user.custom_discount is not None:
            final_discount = user.custom_discount
        else:
            # Calculate tier discount
            tier_info = await DiscountService.calculate_user_tier(user_id, db)
            final_discount = tier_info["tier_discount"]

        # Cache the result
        await redis_manager.client.setex(
            cache_key, DiscountService.CACHE_TTL, final_discount
        )

        return final_discount

    @staticmethod
    async def recalculate_and_cache_discount(user_id: int, db: AsyncSession) -> float:
        """
        Force recalculate discount and update cache.
        Called after admin operations (add credits, set custom discount).

        Returns:
            Final discount as float (0.0-1.0)
        """
        # Query user.custom_discount from DB
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            # User not found, return 0 discount
            return 0.0

        # Check if custom discount is set
        if user.custom_discount is not None:
            final_discount = user.custom_discount
        else:
            # Calculate tier discount
            tier_info = await DiscountService.calculate_user_tier(user_id, db)
            final_discount = tier_info["tier_discount"]

        # Update cache with new value
        cache_key = f"{DiscountService.USER_DISCOUNT_PREFIX}{user_id}"
        await redis_manager.client.setex(
            cache_key, DiscountService.CACHE_TTL, final_discount
        )

        return final_discount

    @staticmethod
    def apply_discount(price: float, discount: float) -> float:
        """Apply discount to price and round to 5 decimals."""
        return round(price * (1 - discount), 5)
