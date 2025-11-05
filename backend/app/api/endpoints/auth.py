from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import Optional

from app.models.user import UserRead, UserCreate, User
from app.users import fastapi_users, web_auth_backend, get_user_manager, UserManager, current_active_user
from app.services.recaptcha_service import recaptcha_service

router = APIRouter()


class LoginRequest(BaseModel):
    """Login request with reCAPTCHA token"""

    username: str  # fastapi-users uses 'username' field for email in OAuth2PasswordRequestForm
    password: str
    recaptcha_token: str


class RegisterRequest(UserCreate):
    """Register request with reCAPTCHA token"""

    recaptcha_token: str


class ChangePasswordRequest(BaseModel):
    """Change password request"""

    password: str  # Current password
    new_password: str  # New password


def get_client_ip(request: Request) -> Optional[str]:
    """Extract client IP from request headers or connection"""
    # Check X-Forwarded-For header (when behind proxy/nginx)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs, get the first one
        return forwarded_for.split(",")[0].strip()

    # Check X-Real-IP header (alternative proxy header)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Fall back to direct connection IP
    if request.client:
        return request.client.host

    return None


@router.post("/login", tags=["account"])
async def login_with_recaptcha(
    request: Request,
    login_data: LoginRequest,
    user_manager: UserManager = Depends(get_user_manager),
):
    """
    Login endpoint with reCAPTCHA v2 verification
    """
    # Verify reCAPTCHA token
    client_ip = get_client_ip(request)
    is_valid, error_message = await recaptcha_service.verify_token(
        login_data.recaptcha_token, client_ip
    )

    if not is_valid:
        raise HTTPException(
            status_code=400, detail=error_message or "reCAPTCHA verification failed"
        )

    # Create OAuth2 form data for fastapi-users authentication
    credentials = OAuth2PasswordRequestForm(
        username=login_data.username,
        password=login_data.password,
        scope="",
        grant_type="password",
    )

    # Authenticate user
    user = await user_manager.authenticate(credentials)

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=400,
            detail="Incorrect email or password",
        )

    # Create authentication response using the backend's login method
    response = await web_auth_backend.login(web_auth_backend.get_strategy(), user)

    return response


@router.post("/register", response_model=UserRead, tags=["account"])
async def register_with_recaptcha(
    request: Request,
    register_data: RegisterRequest,
    user_manager: UserManager = Depends(get_user_manager),
):
    """
    Register endpoint with reCAPTCHA v2 verification
    """
    # Verify reCAPTCHA token
    client_ip = get_client_ip(request)
    is_valid, error_message = await recaptcha_service.verify_token(
        register_data.recaptcha_token, client_ip
    )

    if not is_valid:
        raise HTTPException(
            status_code=400, detail=error_message or "reCAPTCHA verification failed"
        )

    # Remove recaptcha_token from the data before creating user
    user_create_data = UserCreate(
        email=register_data.email,
        password=register_data.password,
        is_active=(
            register_data.is_active if hasattr(register_data, "is_active") else True
        ),
        is_superuser=False,
        is_verified=False,
    )

    # Use fastapi-users registration logic
    try:
        user = await user_manager.create(user_create_data, safe=True, request=request)
        return UserRead.model_validate(user)
    except Exception as e:
        # Handle registration errors (email already exists, etc.)
        raise HTTPException(status_code=400, detail=str(e) or "Registration failed")


@router.post("/reset-password", tags=["account"])
async def change_password(
    request: Request,
    password_data: ChangePasswordRequest,
    user: User = Depends(current_active_user),
    user_manager: UserManager = Depends(get_user_manager),
):
    """
    Change password endpoint for authenticated users
    Requires current password for verification
    """
    from fastapi_users.password import PasswordHelper

    password_helper = PasswordHelper()

    # Verify current password
    valid, updated_password_hash = password_helper.verify_and_update(
        password_data.password, user.hashed_password
    )

    if not valid:
        raise HTTPException(
            status_code=400,
            detail="Incorrect current password",
        )

    # Validate new password
    if len(password_data.new_password) < 8:
        raise HTTPException(
            status_code=400,
            detail="New password must be at least 8 characters",
        )

    # Hash new password
    new_hashed_password = password_helper.hash(password_data.new_password)

    # Update user password in database
    await user_manager.user_db.update(user, {"hashed_password": new_hashed_password})

    return {"message": "Password changed successfully"}
