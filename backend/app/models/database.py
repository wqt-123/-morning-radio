"""
SQLAlchemy 模型定义与数据库连接模块
"""
import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, DateTime, JSON, Enum as SAEnum,
    Index, event, text
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.pool import QueuePool

from app.config import DATABASE_URL

import logging

logger = logging.getLogger(__name__)

# ============================================
# 引擎与会话工厂
# ============================================
SQL_ECHO = False

# 将 mysql+pymysql 转为 pymysql 方言（SQLAlchemy 2.x 兼容）
_db_url = DATABASE_URL
if "mysql+pymysql" in _db_url:
    pass  # 已使用 pymysql 驱动

engine = create_engine(
    _db_url,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    pool_pre_ping=True,
    echo=SQL_ECHO,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db() -> Session:
    """FastAPI 依赖注入：获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================
# 数据模型
# ============================================

class News(Base):
    """新闻表"""
    __tablename__ = "news"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False, comment="新闻标题")
    summary = Column(Text, nullable=True, comment="新闻摘要")
    content = Column(Text, nullable=True, comment="新闻正文")
    image_url = Column(String(1000), nullable=True, comment="新闻配图URL")
    source = Column(String(200), nullable=True, comment="新闻来源")
    source_url = Column(String(1000), nullable=True, comment="原文链接")
    category = Column(String(50), nullable=True, comment="分类: tech/finance/sports/entertainment/domestic/international")
    published_at = Column(DateTime, nullable=True, comment="发布时间")
    created_at = Column(DateTime, default=datetime.datetime.now, comment="入库时间")

    __table_args__ = (
        Index("idx_news_category", "category"),
        Index("idx_news_published_at", "published_at"),
        Index("idx_news_created_at", "created_at"),
        {"comment": "新闻表"},
    )


class NewsCategory(Base):
    """新闻分类表"""
    __tablename__ = "news_category"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False, comment="分类标识")
    display_name = Column(String(100), nullable=False, comment="显示名称")
    icon = Column(String(200), nullable=True, comment="图标")

    __table_args__ = (
        {"comment": "新闻分类表"},
    )


class DailyBroadcast(Base):
    """每日播报表"""
    __tablename__ = "daily_broadcast"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False, comment="播报标题")
    broadcast_text = Column(Text, nullable=True, comment="播报稿件全文")
    audio_path = Column(String(1000), nullable=True, comment="音频文件路径")
    video_path = Column(String(1000), nullable=True, comment="视频文件路径")
    bg_image_path = Column(String(1000), nullable=True, comment="背景图路径")
    duration = Column(Integer, nullable=True, comment="时长（秒）")
    status = Column(String(50), default="pending", comment="状态: pending/generating/completed/failed")
    generated_at = Column(DateTime, nullable=True, comment="生成时间")
    created_at = Column(DateTime, default=datetime.datetime.now, comment="创建时间")

    __table_args__ = (
        Index("idx_broadcast_status", "status"),
        Index("idx_broadcast_generated_at", "generated_at"),
        {"comment": "每日播报表"},
    )


class UserPreference(Base):
    """用户偏好表"""
    __tablename__ = "user_preference"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), unique=True, nullable=False, comment="用户ID")
    preferred_categories = Column(JSON, nullable=True, comment="偏好分类列表")
    voice_type = Column(String(100), default="zh-CN-XiaoxiaoNeural", comment="偏好音色")
    created_at = Column(DateTime, default=datetime.datetime.now, comment="创建时间")

    __table_args__ = (
        {"comment": "用户偏好表"},
    )
