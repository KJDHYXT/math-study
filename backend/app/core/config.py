"""应用配置模块。

读取环境变量 / `.env`，提供全局配置对象。对应文档 03 §4.5。
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局配置。字段名与环境变量（大写）一一对应。"""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # 数据库
    database_url: str = "sqlite:///./math_study.db"

    # 鉴权（可关闭以简化本机开发）
    auth_enabled: bool = False
    access_token: str = "dev-secret-token"  # 用户设置的口令 / 令牌

    # CORS
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # 图片提取（可选）：为「从图片提取核心思路/步骤」配置一个 OpenAI 兼容的视觉接口。
    # 用 DeepSeek 视觉模型时，model 必须为 deepseek-v4-flash-vision-exp（其它模型会报
    # "This model does not support image"）。若未配置 LLM_API_KEY，则 `/api/questions/extract` 返回提示，由用户手动填写。
    llm_api_key: str = ""
    llm_base_url: str = "https://api.deepseek.com"
    llm_model: str = "deepseek-v4-flash-vision-exp"
    # 上传图片的存储目录（相对后端运行目录）
    upload_dir: str = "uploads"
    # 前端构建产物目录（云端同源托管时用于 SPA 兜底；本地开发可不设置）
    frontend_dist: str = "../frontend/dist"

    # 应用信息
    app_name: str = "数学学硕备考 · 学习与复习专区"
    # 测试模式：为 true 时跳过启动建库/种子，避免污染真实数据
    testing: bool = False

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
