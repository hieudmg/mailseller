import logging
from datetime import datetime
from sqlalchemy import select
from app.core.memory_manager import memory_manager
from app.models.user import UserToken, async_session_maker

logger = logging.getLogger(__name__)


async def sync_all_tokens_to_postgres(last_synced_tokens: dict):
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
                if user_id in last_synced_tokens:
                    if last_synced_tokens[user_id] == memory_token:
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
                    last_synced_tokens[user_id] = memory_token
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
                    last_synced_tokens[user_id] = memory_token

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
