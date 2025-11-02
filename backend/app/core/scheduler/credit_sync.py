import logging
from datetime import datetime
from sqlalchemy import select
from app.core.memory_manager import memory_manager
from app.models.user import UserCredit, async_session_maker

logger = logging.getLogger(__name__)


async def sync_all_credits_to_postgres(last_synced_credits: dict):
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
                if user_id in last_synced_credits:
                    if last_synced_credits[user_id] == memory_credit:
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
                    last_synced_credits[user_id] = memory_credit
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
                    last_synced_credits[user_id] = memory_credit

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
