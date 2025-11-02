import asyncio
import logging
from datetime import datetime
from sqlalchemy import select
from app.core.memory_manager import memory_manager
from app.models.user import UserCredit, UserToken, async_session_maker
from app.services.credit_service import CreditService

logger = logging.getLogger(__name__)

# Configuration
SYNC_INTERVAL_SECONDS = 2  # Sync every X seconds (configurable)


class BackgroundScheduler:
    """Background tasks scheduler for credit synchronization refresh."""

    def __init__(self):
        self._running = False
        self._task = None
        # Track last synced values to avoid redundant writes
        self._last_synced_credits: dict[int, float] = {}
        self._last_synced_tokens: dict[int, str] = {}

    async def load_data_from_postgres(self):
        """
        Load credits and tokens from PostgreSQL to memory on startup.
        This ensures hot data is available immediately after restart.
        """
        logger.info("Loading data from PostgreSQL to memory...")

        async with async_session_maker() as db:
            try:
                # Load all credits from PostgreSQL
                result = await db.execute(select(UserCredit))
                user_credits = result.scalars().all()

                credits_loaded = 0
                for user_credit in user_credits:
                    memory_manager.set_user_credit(
                        user_credit.user_id, user_credit.credits
                    )
                    # Track the loaded value as synced
                    self._last_synced_credits[user_credit.user_id] = user_credit.credits
                    credits_loaded += 1

                logger.info(f"Loaded {credits_loaded} credit records from PostgreSQL")

                # Load all tokens from PostgreSQL
                result = await db.execute(select(UserToken))
                user_tokens = result.scalars().all()

                tokens_loaded = 0
                for user_token in user_tokens:
                    memory_manager.set_user_token(user_token.user_id, user_token.token)
                    # Track the loaded value as synced
                    self._last_synced_tokens[user_token.user_id] = user_token.token
                    tokens_loaded += 1

                logger.info(f"Loaded {tokens_loaded} token records from PostgreSQL")
                logger.info("Data loading from PostgreSQL completed successfully")

            except Exception as e:
                logger.error(f"Error loading data from PostgreSQL: {e}", exc_info=True)

    async def sync_all_credits_to_postgres(self):
        """
        Sync user credits: Memory -> PostgreSQL (one direction).
        Memory is the source of truth for hot data.
        PostgreSQL is synced for durability and backup.

        Only syncs credits that have changed since last sync to reduce database writes.
        Uses batch loading to minimize database queries.
        This handles cases where immediate PostgreSQL writes failed during add_credits or purchase.
        """
        async with async_session_maker() as db:
            try:
                # Get all credits from memory
                all_credits = memory_manager.get_all_credits()
                synced_count = 0
                skipped_count = 0

                # Filter out unchanged credits first (fast in-memory check)
                changed_user_ids = []
                for user_id, memory_credit in all_credits.items():
                    if user_id in self._last_synced_credits:
                        if self._last_synced_credits[user_id] == memory_credit:
                            skipped_count += 1
                            continue
                    changed_user_ids.append(user_id)

                if not changed_user_ids:
                    return

                # Batch load existing records from database
                result = await db.execute(
                    select(UserCredit).where(UserCredit.user_id.in_(changed_user_ids))
                )
                existing_credits = {uc.user_id: uc for uc in result.scalars().all()}

                # Process all changed credits in batch
                new_records = []
                for user_id in changed_user_ids:
                    memory_credit = all_credits[user_id]

                    if user_id in existing_credits:
                        # Update existing record
                        user_credit = existing_credits[user_id]
                        if user_credit.credits != memory_credit:
                            logger.info(
                                f"Syncing user {user_id}: "
                                f"Memory={memory_credit} -> PostgreSQL (was {user_credit.credits})"
                            )
                            user_credit.credits = memory_credit
                            user_credit.updated_at = datetime.utcnow()
                            synced_count += 1
                        # Track the synced value
                        self._last_synced_credits[user_id] = memory_credit
                    else:
                        # Create new record (batch)
                        logger.info(
                            f"Creating new user_credit record for user {user_id} with {memory_credit} credits"
                        )
                        new_records.append(
                            UserCredit(user_id=user_id, credits=memory_credit)
                        )
                        synced_count += 1
                        # Track the synced value
                        self._last_synced_credits[user_id] = memory_credit

                # Bulk insert new records
                if new_records:
                    db.add_all(new_records)

                # Single commit for all changes
                await db.commit()
                if synced_count > 0:
                    logger.info(
                        f"Credit sync completed. Synced: {synced_count}, Skipped: {skipped_count}"
                    )

            except Exception as e:
                logger.error(f"Error during credit sync: {e}", exc_info=True)
                await db.rollback()

    async def sync_all_tokens_to_postgres(self):
        """
        Sync all user tokens from memory to PostgreSQL.
        Only syncs tokens that have changed since last sync to reduce database writes.
        Uses batch loading to minimize database queries.
        """
        async with async_session_maker() as db:
            try:
                # Get all tokens from memory
                all_tokens = memory_manager.get_all_tokens()
                synced_count = 0
                skipped_count = 0

                # Filter out unchanged tokens first (fast in-memory check)
                changed_user_ids = []
                for user_id, memory_token in all_tokens.items():
                    if user_id in self._last_synced_tokens:
                        if self._last_synced_tokens[user_id] == memory_token:
                            skipped_count += 1
                            continue
                    changed_user_ids.append(user_id)

                if not changed_user_ids:
                    return

                # Batch load existing records from database
                result = await db.execute(
                    select(UserToken).where(UserToken.user_id.in_(changed_user_ids))
                )
                existing_tokens = {ut.user_id: ut for ut in result.scalars().all()}

                # Process all changed tokens in batch
                new_records = []
                for user_id in changed_user_ids:
                    memory_token = all_tokens[user_id]

                    if user_id in existing_tokens:
                        # Update existing record
                        user_token = existing_tokens[user_id]
                        if user_token.token != memory_token:
                            logger.info(
                                f"Syncing token for user {user_id}: "
                                f"PostgreSQL token changed in memory"
                            )
                            user_token.token = memory_token
                            user_token.updated_at = datetime.utcnow()
                            synced_count += 1
                        # Track the synced value
                        self._last_synced_tokens[user_id] = memory_token
                    else:
                        # Create new record (batch)
                        logger.info(
                            f"Creating new user_token record for user {user_id}"
                        )
                        new_records.append(
                            UserToken(user_id=user_id, token=memory_token)
                        )
                        synced_count += 1
                        # Track the synced value
                        self._last_synced_tokens[user_id] = memory_token

                # Bulk insert new records
                if new_records:
                    db.add_all(new_records)

                # Single commit for all changes
                await db.commit()
                if synced_count > 0:
                    logger.info(
                        f"Token sync completed. Synced: {synced_count}, Skipped: {skipped_count}"
                    )

            except Exception as e:
                logger.error(f"Error during token sync: {e}", exc_info=True)
                await db.rollback()

    async def cleanup_expired_data(self):
        """Clean up expired sessions and discount cache entries."""
        try:
            cleaned = memory_manager.cleanup_expired_sessions()
            if cleaned > 0:
                logger.info(f"Cleaned up {cleaned} expired cache entries")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}", exc_info=True)

    async def run_periodic_sync(self):
        """Run periodic sync task."""
        self._running = True
        logger.info(
            f"Background scheduler started. Sync interval: {SYNC_INTERVAL_SECONDS}s"
        )

        while self._running:
            try:
                await self.sync_all_credits_to_postgres()
                await self.sync_all_tokens_to_postgres()
                await self.cleanup_expired_data()
            except Exception as e:
                logger.error(f"Error in periodic sync: {e}", exc_info=True)

            await asyncio.sleep(SYNC_INTERVAL_SECONDS)

    async def start(self):
        """Start the background scheduler."""
        self._running = True
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self.run_periodic_sync())
            logger.info("Background credit/token sync task created")

    async def stop(self):
        """Stop the background scheduler."""
        self._running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info("Background scheduler stopped")


# Global instance
scheduler = BackgroundScheduler()
