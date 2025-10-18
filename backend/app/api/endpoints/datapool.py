from fastapi import APIRouter, Depends, HTTPException
from app.core.redis_manager import redis_manager
from app.models.user import User
from app.users import get_user_from_token

router = APIRouter()




@router.get("/size")
async def get_pool_size(
):
    """Get current size of data pool."""
    size = await redis_manager.get_pool_size()
    return {"pool_size": size}
