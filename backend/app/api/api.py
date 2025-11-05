from fastapi import APIRouter
from app.api.endpoints import admin, auth
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

# Custom auth routes with reCAPTCHA (these override the default login/register)
account_router.include_router(auth.router, prefix="/account")

# Default fastapi-users routes (logout, etc.) - login and register are overridden above
auth_router = fastapi_users.get_auth_router(web_auth_backend)
# Remove login route as we have custom one with reCAPTCHA
auth_routes_without_login = APIRouter()
for route in auth_router.routes:
    if route.path != "/login":
        auth_routes_without_login.routes.append(route)

account_router.include_router(auth_routes_without_login, prefix="/account", tags=["account"])

# Password reset routes
account_router.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/account",
    tags=["account"],
)

# User management routes
account_router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/account",
    tags=["account"],
)
