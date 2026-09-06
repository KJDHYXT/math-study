"""认证 API 契约。对应文档 04 §1。"""
from pydantic import BaseModel


class TokenIn(BaseModel):
    token: str


class TokenOut(BaseModel):
    token: str
    valid: bool
