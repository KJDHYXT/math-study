"""认证路由。对应文档 04 §1。"""
from fastapi import APIRouter, status
from ..core.errors import AppError

from ..core.config import settings
from ..schemas.auth import TokenIn, TokenOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenOut)
def login(payload: TokenIn) -> TokenOut:
    if payload.token != settings.access_token:
        raise AppError(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="invalid token", code="ERR_AUTH_INVALID")
    # 单用户简化：口令即令牌；前端将其作为 Bearer token 携带。
    return TokenOut(token=settings.access_token, valid=True)


@router.get("/verify", response_model=TokenOut)
def verify() -> TokenOut:
    return TokenOut(token=settings.access_token, valid=True)
