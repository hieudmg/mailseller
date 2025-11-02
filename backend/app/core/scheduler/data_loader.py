import logging
from sqlalchemy import select
from app.core.memory_manager import memory_manager
from app.models.user import UserCredit, UserToken, async_session_maker

logger = logging.getLogger(__name__)


async def load_data_from_postgres(last_synced_credits: dict, last_synced_tokens: dict):
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
                last_synced_credits[user_credit.user_id] = user_credit.credits
                credits_loaded += 1

            logger.info(f"Loaded {credits_loaded} credit records from PostgreSQL")

            # Load all tokens from PostgreSQL
            result = await db.execute(select(UserToken))
            user_tokens = result.scalars().all()

            tokens_loaded = 0
            for user_token in user_tokens:
                memory_manager.set_user_token(user_token.user_id, user_token.token)
                # Track the loaded value as synced
                last_synced_tokens[user_token.user_id] = user_token.token
                tokens_loaded += 1

            logger.info(f"Loaded {tokens_loaded} token records from PostgreSQL")
            logger.info("Data loading from PostgreSQL completed successfully")

        except Exception as e:
            logger.error(f"Error loading data from PostgreSQL: {e}", exc_info=True)
