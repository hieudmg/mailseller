import asyncio
import logging
from datetime import datetime
from sqlalchemy import select
from app.core.redis_manager import redis_manager
from app.models.user import UserCredit, UserToken, async_session_maker
from app.services.credit_service import CreditService

logger = logging.getLogger(__name__)

# Configuration
SYNC_INTERVAL_SECONDS = 5  # Sync every 5 seconds (configurable)
TYPE_CACHE_INTERVAL_SECONDS = 10  # Refresh type cache every 10 seconds


class BackgroundScheduler:
    """Background tasks scheduler for credit synchronization and type cache refresh."""

    def __init__(self):
        self._running = False
        self._task = None
        self._type_cache_task = None

    async def sync_all_credits_to_postgres(self):
        """
        Sync user credits: Redis -> PostgreSQL (one direction).
        Redis is the source of truth (atomic operations via INCRBY and Lua scripts).
        PostgreSQL is synced for durability and backup.

        This handles cases where immediate PostgreSQL writes failed during add_credits or purchase.
        """
        logger.info("Starting credit sync: Redis -> PostgreSQL")

        async with async_session_maker() as db:
            try:
                # Get all Redis credit keys
                redis_keys = await redis_manager.client.keys(f"{redis_manager.USER_CREDIT_PREFIX}*")
                synced_count = 0

                for key in redis_keys:
                    user_id = int(key.split(":")[-1])
                    redis_credit = await redis_manager.get_user_credit(user_id)

                    # Get or create PostgreSQL record
                    result = await db.execute(
                        select(UserCredit).where(UserCredit.user_id == user_id)
                    )
                    user_credit = result.scalar_one_or_none()

                    if user_credit:
                        # Update if different
                        if user_credit.credits != redis_credit:
                            logger.info(
                                f"Syncing user {user_id}: "
                                f"Redis={redis_credit} -> PostgreSQL (was {user_credit.credits})"
                            )
                            user_credit.credits = redis_credit
                            user_credit.updated_at = datetime.utcnow()
                            synced_count += 1
                    else:
                        # Create new record
                        logger.info(f"Creating new user_credit record for user {user_id} with {redis_credit} credits")
                        new_credit = UserCredit(user_id=user_id, credits=redis_credit)
                        db.add(new_credit)
                        synced_count += 1

                await db.commit()
                logger.info(f"Credit sync completed. Updated/created {synced_count} records.")

            except Exception as e:
                logger.error(f"Error during credit sync: {e}", exc_info=True)
                await db.rollback()

    async def sync_all_tokens_to_postgres(self):
        """Sync all user tokens from Redis to PostgreSQL."""
        logger.info("Starting token sync: Redis -> PostgreSQL")

        async with async_session_maker() as db:
            try:
                # Get all tokens from PostgreSQL
                result = await db.execute(select(UserToken))
                all_tokens = result.scalars().all()

                synced_count = 0
                for user_token in all_tokens:
                    redis_token = await redis_manager.get_user_token(user_token.user_id)

                    # Only update if Redis has different value
                    if redis_token and redis_token != user_token.token:
                        logger.info(
                            f"Syncing token for user {user_token.user_id}: "
                            f"PostgreSQL token changed in Redis"
                        )
                        user_token.token = redis_token
                        user_token.updated_at = datetime.utcnow()
                        synced_count += 1

                # Also check for users in Redis but not in PostgreSQL
                redis_keys = await redis_manager.client.keys(f"{redis_manager.USER_TOKEN_PREFIX}*")
                for key in redis_keys:
                    user_id = int(key.split(":")[-1])
                    # Check if user token exists in PostgreSQL
                    check = await db.execute(
                        select(UserToken).where(UserToken.user_id == user_id)
                    )
                    if not check.scalar_one_or_none():
                        redis_token = await redis_manager.get_user_token(user_id)
                        if redis_token:
                            logger.info(f"Creating new user_token record for user {user_id}")
                            new_token = UserToken(user_id=user_id, token=redis_token)
                            db.add(new_token)
                            synced_count += 1

                await db.commit()
                logger.info(f"Token sync completed. Updated/created {synced_count} records.")

            except Exception as e:
                logger.error(f"Error during token sync: {e}", exc_info=True)
                await db.rollback()

    async def sync_type_cache(self):
        """Refresh the type-to-storage cache from Redis and database."""
        from app.services.type_service import TypeService

        logger.info("Refreshing type cache")

        async with async_session_maker() as db:
            try:
                await TypeService.refresh_cache(db)
                logger.info("Type cache refreshed successfully")
            except Exception as e:
                logger.error(f"Error refreshing type cache: {e}", exc_info=True)

    async def run_periodic_type_cache_refresh(self):
        """Run periodic type cache refresh task."""
        logger.info(f"Type cache refresh scheduler started. Interval: {TYPE_CACHE_INTERVAL_SECONDS}s")

        while self._running:
            try:
                await self.sync_type_cache()
            except Exception as e:
                logger.error(f"Error in type cache refresh: {e}", exc_info=True)

            await asyncio.sleep(TYPE_CACHE_INTERVAL_SECONDS)

    async def run_periodic_sync(self):
        """Run periodic sync task."""
        self._running = True
        logger.info(f"Background scheduler started. Sync interval: {SYNC_INTERVAL_SECONDS}s")

        while self._running:
            try:
                await self.sync_all_credits_to_postgres()
                await self.sync_all_tokens_to_postgres()
            except Exception as e:
                logger.error(f"Error in periodic sync: {e}", exc_info=True)

            await asyncio.sleep(SYNC_INTERVAL_SECONDS)

    async def start(self):
        """Start the background scheduler."""
        self._running = True
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self.run_periodic_sync())
            logger.info("Background credit/token sync task created")
        if self._type_cache_task is None or self._type_cache_task.done():
            self._type_cache_task = asyncio.create_task(self.run_periodic_type_cache_refresh())
            logger.info("Background type cache refresh task created")

    async def stop(self):
        """Stop the background scheduler."""
        self._running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        if self._type_cache_task:
            self._type_cache_task.cancel()
            try:
                await self._type_cache_task
            except asyncio.CancelledError:
                pass

        logger.info("Background scheduler stopped")


# Global instance
scheduler = BackgroundScheduler()
