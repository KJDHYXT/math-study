"""统一异常与错误响应。对应文档 04 §0.2。"""
from fastapi import Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    """业务异常，携带 HTTP 状态码与业务错误码。"""

    def __init__(self, status_code: int, detail: str, code: str = "ERR_APP") -> None:
        self.status_code = status_code
        self.detail = detail
        self.code = code
        super().__init__(detail)


def register_exception_handlers(app) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail, "code": exc.code})

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=500, content={"detail": "internal server error", "code": "ERR_INTERNAL"})
