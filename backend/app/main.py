"""FastAPI 应用入口。对应文档 03 §3、文档 06 T-0.1。

统一前缀 /api，装配各路由，启动时初始化数据库与种子。
"""
from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .core.config import settings
from .core.errors import register_exception_handlers
from .init_db import init_db, seed_if_empty
from .db import SessionLocal
from .routers import (
    auth, subjects, knowledge, notes, questions, quiz, cards, search, entries, review,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not settings.testing:
        init_db()
        db = SessionLocal()
        try:
            seed_if_empty(db)
        finally:
            db.close()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok", "app": settings.app_name}


for r in (auth.router, subjects.router, knowledge.router, notes.notes_router,
          notes.tags_router, questions.router, quiz.router, cards.router, search.router,
          entries.router, review.router):
    app.include_router(r)

# 挂载上传的题目图片，使其可通过 /uploads/<文件名> 访问
os.makedirs(settings.upload_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

# 同源托管前端（云端部署时）；SPA 深链回退到 index.html
_dist = os.path.abspath(settings.frontend_dist)


@app.get("/{full_path:path}", include_in_schema=False)
def spa(full_path: str):
    if os.path.isdir(_dist):
        file = os.path.join(_dist, full_path)
        if full_path and os.path.isfile(file):
            return FileResponse(file)
        index = os.path.join(_dist, "index.html")
        if os.path.isfile(index):
            return FileResponse(index)
    return {"detail": "frontend not built", "code": "ERR_NO_FRONTEND"}
