"""
FastAPI 应用入口 - 早安电台后端服务
"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import APP_DEBUG, APP_HOST, APP_PORT, MEDIA_PATH, LOG_LEVEL
from app.utils.helpers import setup_logging, ensure_dir

# 初始化日志
setup_logging(LOG_LEVEL)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("===== 早安电台后端服务启动中 =====")

    # 确保媒体目录存在
    ensure_dir(str(MEDIA_PATH / "audio"))
    ensure_dir(str(MEDIA_PATH / "video"))
    logger.info(f"媒体目录已就绪: {MEDIA_PATH}")

    # 创建数据库表
    try:
        from app.models.database import engine, Base
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表已就绪")
    except Exception as e:
        logger.warning(f"数据库连接失败，跳过表创建: {e}")

    yield

    # 关闭时
    logger.info("===== 早安电台后端服务关闭 =====")


# 创建 FastAPI 应用
app = FastAPI(
    title="早安电台 API",
    description="AI + 每日新闻早安电台后端服务",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite 开发服务器
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "*",                        # 开发阶段允许所有来源
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务 - 媒体文件
media_dir = str(MEDIA_PATH)
if Path(media_dir).exists():
    app.mount("/media", StaticFiles(directory=media_dir), name="media")
    logger.info(f"静态文件服务已挂载: /media -> {media_dir}")
else:
    logger.warning(f"媒体目录不存在: {media_dir}")


# ============================================
# 健康检查
# ============================================
@app.get("/health", tags=["系统"])
async def health_check():
    """健康检查端点"""
    return {
        "status": "ok",
        "service": "morning-radio",
        "version": "1.0.0",
    }


@app.get("/", tags=["系统"])
async def root():
    """根路径"""
    return {
        "name": "早安电台 API",
        "version": "1.0.0",
        "docs": "/docs",
    }


# ============================================
# 注册路由
# ============================================
from app.api.news import router as news_router
from app.api.radio import router as radio_router
from app.api.user import router as user_router

app.include_router(news_router)
app.include_router(radio_router)
app.include_router(user_router)

logger.info("所有路由已注册")


# ============================================
# 直接启动入口
# ============================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=APP_HOST,
        port=APP_PORT,
        reload=APP_DEBUG,
        log_level=LOG_LEVEL.lower(),
    )
