from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User, get_async_session
from app.services.type_service import TypeService

router = APIRouter()


@router.get("/size")
async def get_pool_size(
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get current size of data pool for all types across all storages.

    Returns:
        Total count and sizes for all types (storage not exposed to users)
    """
    # Get sizes from both Redis and DB
    all_types_with_sizes = await TypeService.get_all_types_with_sizes(db)

    # Extract just the pool sizes, hiding storage information
    sizes = {type_name: info["pool_size"] for type_name, info in all_types_with_sizes.items()}
    total = sum(sizes.values())

    return {
        "total": total,
        "sizes": sizes
    }


@router.get("/types")
async def get_data_types(
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get list of all available data types.

    Returns:
        List of data type names (storage not exposed to users)
    """
    types_with_storage = await TypeService.get_all_types_with_storage(db)
    # Return just the type names as a list
    return {"types": list(types_with_storage.keys())}
