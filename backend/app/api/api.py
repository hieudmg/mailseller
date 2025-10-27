from fastapi import APIRouter
from app.api.endpoints import admin
from app.api.endpoints import datapool, credits, payment
from app.models.user import UserRead, UserCreate, UserUpdate
from app.users import fastapi_users, web_auth_backend

api_router = APIRouter()

# Include credit and data pool routes
api_router.include_router(credits.router, prefix="", tags=["credits"])
api_router.include_router(datapool.router, prefix="/datapool", tags=["datapool"])
api_router.include_router(payment.router, prefix="/payment", tags=["payment"])

# Admin routes
admin_router = APIRouter()
admin_router.include_router(admin.router, prefix="/admin", tags=["admin"])

account_router = APIRouter()

account_router.include_router(
    fastapi_users.get_auth_router(web_auth_backend), prefix="/account", tags=["account"]
)
account_router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/account",
    tags=["account"],
)
account_router.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/account",
    tags=["account"],
)
account_router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/account",
    tags=["account"],
)
