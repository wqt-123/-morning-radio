"""
启动脚本 - 使用 uvicorn 启动 FastAPI 应用
"""
import sys
import os

# 确保 backend 目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn
from app.config import APP_HOST, APP_PORT, APP_DEBUG, LOG_LEVEL

if __name__ == "__main__":
    print("=" * 60)
    print("  早安电台 Morning Radio - 后端服务")
    print("=" * 60)
    print(f"  地址: http://{APP_HOST}:{APP_PORT}")
    print(f"  文档: http://{APP_HOST}:{APP_PORT}/docs")
    print(f"  调试: {'开启' if APP_DEBUG else '关闭'}")
    print("=" * 60)

    uvicorn.run(
        "app.main:app",
        host=APP_HOST,
        port=APP_PORT,
        reload=APP_DEBUG,
        log_level=LOG_LEVEL.lower(),
    )
