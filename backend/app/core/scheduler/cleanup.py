import logging
from datetime import datetime, timedelta
from sqlalchemy import delete
from app.core.memory_manager import memory_manager
from app.models.user import Transaction, async_session_maker

logger = logging.getLogger(__name__)


async def cleanup_expired_data():
    """Clean up expired sessions and discount cache entries."""
    try:
        cleaned = memory_manager.cleanup_expired_sessions()
        if cleaned > 0:
            logger.info(f"Cleaned up {cleaned} expired cache entries")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}", exc_info=True)


async def cleanup_old_transactions():
    """Delete purchase transactions older than 24 hours from database."""
    try:
        async with async_session_maker() as db:
            # Delete old purchase transactions using database timestamp
            # Transaction.timestamp < NOW() - INTERVAL '24 hours'
            from sqlalchemy.sql import text

            result = await db.execute(
                delete(Transaction)
                .where(Transaction.type == "purchase")
                .where(text("timestamp < NOW() - INTERVAL '24 hours'"))
            )
            await db.commit()

            deleted_count = result.rowcount
            if deleted_count > 0:
                logger.info(
                    f"Cleaned up {deleted_count} purchase transactions older than 24 hours"
                )
    except Exception as e:
        logger.error(f"Error during transaction cleanup: {e}", exc_info=True)
