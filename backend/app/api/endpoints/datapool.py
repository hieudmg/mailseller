# python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import get_async_session
from app.services.pool_service import PoolService
import time
import asyncio

router = APIRouter()

# Simple in-memory cache: stores {'expiry': float, 'value': dict}
_cache = {"expiry": 0.0, "value": None}
_cache_lock = asyncio.Lock()
_CACHE_TTL_SECONDS = 1.0


@router.get("/size")
async def get_pool_size(db: AsyncSession = Depends(get_async_session)):
    """
    Get current size of data pool for all types across all storages.

    Returns:
        Total count and sizes for all types (storage not exposed to users)
    """
    now = time.monotonic()
    # Fast path: return cached value if still valid
    cached = _cache.get("value")
    if cached is not None and now < _cache["expiry"]:
        return cached

    # Acquire lock to refresh cache if another coroutine is not already doing it
    async with _cache_lock:
        # Re-check after acquiring lock
        now = time.monotonic()
        if _cache.get("value") is not None and now < _cache["expiry"]:
            return _cache["value"]

        # Fetch fresh data
        all_types_with_sizes = await PoolService.get_all_types_with_sizes(db)
        sizes = {
            type_name: {
                "pool_size": info["pool_size"],
                "price": info["config"]["price"],
                "code": info["config"]["code"],
                "name": info["config"]["name"],
                "lifetime": info["config"]["lifetime"],
                "protocols": info["config"]["protocols"],
            }
            for type_name, info in all_types_with_sizes.items()
        }
        total = 0
        result = {"total": total, "sizes": sizes}

        # Update cache
        _cache["value"] = result
        _cache["expiry"] = time.monotonic() + _CACHE_TTL_SECONDS

        return result
