"""
Routes for the authentication module.
"""

from datetime import datetime

from fastapi import APIRouter, status, Depends
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from sqlmodel.ext.asyncio.session import AsyncSession

from .schemas import (
    UserCreateModel,
    UserLoginModel,
    UserLoginResponseModel,
    RefreshTokenResponseModel,
)
from .service import UserService
from .models import User
from .utils import create_access_token, decode_token, verify_password
from .dependencies import RefreshTokenBearer
from src.db.main import get_session

auth_router = APIRouter()
user_service = UserService()
refresh_token_bearer = RefreshTokenBearer()


@auth_router.post("/signup", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user_account(
    user_data: UserCreateModel, session: AsyncSession = Depends(get_session)
):
    """Creates a new user account."""
    email = user_data.email

    user_exists = await user_service.user_exists(email, session)

    if user_exists:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User with email already exists.",
        )

    new_user = await user_service.create_user(user_data, session)

    return new_user


@auth_router.post(
    "/login", response_model=UserLoginResponseModel, status_code=status.HTTP_200_OK
)
async def login_users(
    login_data: UserLoginModel, session: AsyncSession = Depends(get_session)
):
    """Allows an user to login."""
    email = login_data.email
    password = login_data.password

    user = await user_service.get_user_by_email(email, session)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User/password combination does not match.",
        )

    password_valid = verify_password(password, user.password_hash)

    if not password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User/password combination does not match.",
        )

    access_token = create_access_token(
        user_data={
            "email": user.email,
            "user_uid": str(user.uid),
        }
    )

    refresh_token = create_access_token(
        user_data={
            "email": user.email,
            "user_uid": str(user.uid),
        },
        refresh=True,
    )

    return JSONResponse(
        content={
            "message": "Login successful.",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "email": user.email,
                "uid": str(user.uid),
            },
        }
    )


@auth_router.get(
    "/refresh-token",
    response_model=RefreshTokenResponseModel,
    status_code=status.HTTP_200_OK,
)
async def get_new_access_token(token_details: dict = Depends(refresh_token_bearer)):
    """Gets a new access token from a refresh token."""
    expiry_timestamp = token_details["exp"]

    if datetime.fromtimestamp(expiry_timestamp) <= datetime.now():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token.",
        )

    new_access_token = create_access_token(user_data=token_details["user"])

    return JSONResponse(
        content={
            "access_token": new_access_token,
        },
    )
