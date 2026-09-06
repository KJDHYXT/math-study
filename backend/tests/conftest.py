"""pytest 共享配置。

使用独立临时 SQLite 数据库，避免污染真实数据；通过覆盖 get_db 依赖注入测试会话。
"""
import os

# 必须在导入 app（其 settings 在导入时实例化）之前打开测试开关，
# 使 lifespan 跳过建库/种子，避免污染真实 math_study.db。
os.environ["TESTING"] = "true"

import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app import models  # noqa: F401
from app.core.config import settings

# 测试强制关闭鉴权（与 backend/.env 是否开启无关）
settings.auth_enabled = False


@pytest.fixture()
def engine():
    """每个测试独立的 in-memory SQLite（跨连接共享用 StaticPool）。"""
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=eng)
    yield eng
    eng.dispose()


@pytest.fixture()
def db_session(engine):
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client(engine):
    """覆盖 get_db 依赖的 TestClient。"""
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
