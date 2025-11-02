import asyncio
import logging
from typing import Callable, Awaitable

logger = logging.getLogger(__name__)

# Configuration
SYNC_INTERVAL_SECONDS = 5  # Sync every X seconds (configurable)


class BackgroundScheduler:
    """Background tasks scheduler for credit synchronization refresh."""

    def __init__(self):
        self._running = False
        self._task = None
        self._tasks: list[dict] = []
        # Track last synced values to avoid redundant writes
        self._last_synced_credits: dict[int, float] = {}
        self._last_synced_tokens: dict[int, str] = {}

    def register_task(
        self, name: str, interval: int, func: Callable[[], Awaitable[None]]
    ):
        """
        Register a task to run at specified interval.

        Args:
            name: Task name for logging
            interval: Interval in seconds
            func: Async function to execute
        """
        self._tasks.append(
            {
                "name": name,
                "interval": interval,
                "func": func,
                "timer": 0,  # Initialize timer to 0 (will run on first cycle)
            }
        )
        logger.info(f"Registered task '{name}' with {interval}s interval")

    async def load_data_from_postgres(self):
        """
        Load credits and tokens from PostgreSQL to memory on startup.
        This ensures hot data is available immediately after restart.
        """
        from app.core.scheduler.data_loader import load_data_from_postgres

        await load_data_from_postgres(
            self._last_synced_credits, self._last_synced_tokens
        )

    async def run_periodic_sync(self):
        """Run periodic sync task."""
        self._running = True
        logger.info(
            f"Background scheduler started. Sync interval: {SYNC_INTERVAL_SECONDS}s"
        )

        while self._running:
            try:
                # Execute tasks based on their countdown timers
                for task in self._tasks:
                    # Decrement timer
                    task["timer"] -= SYNC_INTERVAL_SECONDS

                    # If timer reached zero or below, run the task and reset timer
                    if task["timer"] <= 0:
                        logger.debug(f"Running task '{task['name']}'")
                        await task["func"]()
                        task["timer"] = task["interval"]  # Reset to interval
            except Exception as e:
                logger.error(f"Error in periodic sync: {e}", exc_info=True)

            await asyncio.sleep(SYNC_INTERVAL_SECONDS)

    async def start(self):
        await self.load_data_from_postgres()
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


# Register tasks
async def _credit_sync_task():
    """Sync user credits from memory to PostgreSQL."""
    from app.core.scheduler.credit_sync import sync_all_credits_to_postgres

    await sync_all_credits_to_postgres(scheduler._last_synced_credits)


async def _token_sync_task():
    """Sync user tokens from memory to PostgreSQL."""
    from app.core.scheduler.token_sync import sync_all_tokens_to_postgres

    await sync_all_tokens_to_postgres(scheduler._last_synced_tokens)


async def _cleanup_task():
    """Clean up expired sessions and discount cache entries."""
    from app.core.scheduler.cleanup import cleanup_expired_data

    await cleanup_expired_data()


async def _cleanup_transactions_task():
    """Clean up old purchase transactions from database."""
    from app.core.scheduler.cleanup import cleanup_old_transactions

    await cleanup_old_transactions()


scheduler.register_task("credit_sync", SYNC_INTERVAL_SECONDS, _credit_sync_task)
scheduler.register_task("token_sync", SYNC_INTERVAL_SECONDS, _token_sync_task)
scheduler.register_task("cleanup", SYNC_INTERVAL_SECONDS, _cleanup_task)
scheduler.register_task("cleanup_transactions", 60, _cleanup_transactions_task)  # Every minute
