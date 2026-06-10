from __future__ import annotations

import logging

from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response
from pydantic import ValidationError

from app_platform.config.settings import settings
from app_platform.db.runtime import get_db, get_db_optional
from app_platform.web.rate_limit import limiter
from contexts.identity_access.contracts.models import TokenResponse, UserResponse as AuthUserResponse
from app_platform.auth.current_user import get_current_user

from contexts.identity.infrastructure import service
from contexts.identity.infrastructure.auth_session_service import (
    REFRESH_TOKEN_EXPIRE_SECONDS,
)
from contexts.identity.contracts.schemas import ChangePasswordRequest, LoginRequest


auth_router = APIRouter(prefix="/auth", tags=["Authentication & RBAC"])
logger = logging.getLogger(__name__)
REFRESH_COOKIE_NAME = "iems_refresh_token"


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
        domain=settings.refresh_cookie_domain,
        max_age=REFRESH_TOKEN_EXPIRE_SECONDS,
        path="/api/auth",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
        domain=settings.refresh_cookie_domain,
        path="/api/auth",
    )


@auth_router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    response: Response,
    credentials: dict | None = Body(default=None),
    db=Depends(get_db_optional),
):
    payload: dict = {}

    if isinstance(credentials, dict):
        payload = credentials
    else:
        try:
            payload = await request.json()
            if not isinstance(payload, dict):
                payload = {}
        except Exception:
            logger.debug("Login request did not include JSON body", exc_info=True)
            payload = {}

        if not payload:
            try:
                form = await request.form()
                payload = dict(form)
            except Exception:
                logger.debug("Login request did not include form body", exc_info=True)
                payload = {}

    nested = payload.get("credentials") if isinstance(payload, dict) else None
    source = nested if isinstance(nested, dict) else payload
    normalized = {
        "email": str(source.get("email") or source.get("username") or "").strip().lower(),
        "password": str(source.get("password") or ""),
    }

    try:
        login_data = LoginRequest.model_validate(normalized)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc

    auth_result = await service.login(db, login_data.model_dump())

    refresh_token = getattr(auth_result, "refresh_token", None)
    if refresh_token:
        _set_refresh_cookie(response, refresh_token)
        auth_result = auth_result.model_copy(update={"refresh_token": None})

    return auth_result


@auth_router.get("/login", include_in_schema=False)
async def login_method_hint():
    raise HTTPException(status_code=405, detail="Use POST /api/auth/login")


@auth_router.get("/me", response_model=AuthUserResponse)
async def get_me(db=Depends(get_db_optional), current_user: dict = Depends(get_current_user)):
    return await service.me_from_token(db, current_user)


@auth_router.get("/module-access")
async def get_module_access(db=Depends(get_db_optional), current_user: dict = Depends(get_current_user)):
    return await service.get_module_access(db, current_user)


@auth_router.get("/rbac-matrix")
async def get_rbac_matrix():
    return service.get_rbac_matrix()


@auth_router.post("/change-password")
@limiter.limit("5/minute")
async def change_own_password(
    request: Request,
    payload: dict | None = Body(default=None),
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Self-service password change (required after auto-provisioned temp password)."""
    data: dict = {}

    if isinstance(payload, dict):
        data = payload
    else:
        try:
            parsed = await request.json()
            if isinstance(parsed, dict):
                data = parsed
        except Exception:
            data = {}

        if not data:
            try:
                form = await request.form()
                data = dict(form)
            except Exception:
                data = {}

    current_password = (
        data.get("current_password")
        or data.get("currentPassword")
        or data.get("old_password")
        or data.get("oldPassword")
    )
    new_password = data.get("new_password") or data.get("newPassword")

    if not current_password or not new_password:
        raise HTTPException(
            status_code=400,
            detail="current_password and new_password are required",
        )

    password_data = ChangePasswordRequest(
        current_password=str(current_password),
        new_password=str(new_password),
    )
    return await service.change_own_password(db, password_data, current_user=current_user)


@auth_router.post("/reset-temp-password")
@limiter.limit("5/minute")
async def reset_temp_password(
    request: Request,
    payload: dict,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Reset an employee's password to a new temp value. Data Entry / HOD / SYSTEM_ADMIN only."""
    email = payload.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="email is required")
    return await service.reset_employee_temp_password(db, email, current_user=current_user)


@auth_router.post("/refresh")
@limiter.limit("10/minute")
async def refresh_token(
    request: Request,
    response: Response,
    payload: dict | None = Body(default=None),
    db=Depends(get_db),
):
    """Exchange a valid refresh token for a new access + refresh token pair."""
    refresh = (payload or {}).get("refresh_token") or request.cookies.get(
        REFRESH_COOKIE_NAME
    )
    if not refresh:
        raise HTTPException(status_code=400, detail="refresh_token is required")
    auth_result = await service.refresh_access_token(db, refresh)

    new_refresh = auth_result.get("refresh_token") if isinstance(auth_result, dict) else None
    if new_refresh:
        _set_refresh_cookie(response, new_refresh)
        auth_result["refresh_token"] = None

    return auth_result


@auth_router.get("/refresh", include_in_schema=False)
async def refresh_method_hint():
    raise HTTPException(status_code=405, detail="Use POST /api/auth/refresh")


@auth_router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    payload: dict | None = Body(default=None),
    db=Depends(get_db_optional),
):
    """Revoke the refresh token, ending the session."""
    refresh = (payload or {}).get("refresh_token") or request.cookies.get(
        REFRESH_COOKIE_NAME
    )
    result = await service.logout(db, refresh)
    _clear_refresh_cookie(response)
    return result


@auth_router.get("/logout", include_in_schema=False)
async def logout_method_hint():
    raise HTTPException(status_code=405, detail="Use POST /api/auth/logout")
