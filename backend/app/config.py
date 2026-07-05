"""
早安电台 - 配置管理模块
从 .env 文件读取所有配置项
"""
import os
import logging
from pathlib import Path
from typing import Optional


# 项目根目录（backend/ 目录）
BASE_DIR = Path(__file__).resolve().parent.parent


def _load_env_file():
    """加载 .env 文件到环境变量（简单实现，无需 python-dotenv）"""
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        logging.warning(f".env 文件不存在: {env_path}")
        return

    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


# 模块加载时读取 .env
_load_env_file()


def _env(key: str, default: str = "") -> str:
    """从环境变量读取配置"""
    return os.environ.get(key, default)


# ============================================
# 数据库配置
# ============================================
DATABASE_URL: str = _env(
    "DATABASE_URL",
    "mysql+pymysql://root:root@127.0.0.1:3306/morning_radio?charset=utf8mb4",
)

# ============================================
# Redis / Celery 配置
# ============================================
REDIS_URL: str = _env("REDIS_URL", "redis://127.0.0.1:6379/0")
CELERY_BROKER_URL: str = _env("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0")
CELERY_RESULT_BACKEND: str = _env("CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/1")

# ============================================
# AI 配置
# ============================================
OPENAI_API_KEY: str = _env("OPENAI_API_KEY", "")
OPENAI_BASE_URL: str = _env("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL: str = _env("OPENAI_MODEL", "gpt-3.5-turbo")

DASHSCOPE_API_KEY: str = _env("DASHSCOPE_API_KEY", "")

# ============================================
# 新闻 API 配置
# ============================================
NEWS_API_KEY: str = _env("NEWS_API_KEY", "")
JUHE_NEWS_KEY: str = _env("JUHE_NEWS_KEY", "")
TIANXING_API_KEY: str = _env("TIANXING_API_KEY", "")

# ============================================
# TTS 配置
# ============================================
TTS_VOICE: str = _env("TTS_VOICE", "zh-CN-XiaoxiaoNeural")

# ============================================
# 应用配置
# ============================================
APP_HOST: str = _env("APP_HOST", "0.0.0.0")
APP_PORT: int = int(_env("APP_PORT", "8000"))
APP_DEBUG: bool = _env("APP_DEBUG", "true").lower() == "true"

# ============================================
# 媒体文件目录
# ============================================
MEDIA_DIR: str = _env("MEDIA_DIR", "./media")
MEDIA_PATH: Path = BASE_DIR / MEDIA_DIR

# ============================================
# 日志配置
# ============================================
LOG_LEVEL: str = _env("LOG_LEVEL", "INFO")
