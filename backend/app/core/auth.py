"""访问鉴权模块（可选）。

单用户场景：当 `AUTH_ENABLED=true` 时，受保护接口需携带
`Authorization: Bearer <ACCESS_TOKEN>`。本机开发默认关闭（见文档 03 §4.4 / 04 §0.1）。
"""
from fastapi import Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import settings
from .errors import AppError

_bearer = HTTPBearer(auto_error=False)


def verify_token(credentials: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> None:
    """校验 Bearer Token；未开启鉴权时直接放行。"""
    if not settings.auth_enabled:
        return
    if credentials is None or credentials.scheme.lower() != "bearer" or credentials.credentials != settings.access_token:
        raise AppError(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token", code="ERR_AUTH_INVALID")
