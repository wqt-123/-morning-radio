"""
工具函数模块
"""
import datetime
import hashlib
import logging
import os
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def setup_logging(level: str = "INFO") -> None:
    """配置全局日志"""
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def get_today_str() -> str:
    """获取今天的日期字符串，含星期"""
    now = datetime.datetime.now()
    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    weekday_str = weekdays[now.weekday()]
    return f"{now.year}年{now.month}月{now.day}日 {weekday_str}"


def get_today_date() -> datetime.date:
    """获取今天的日期"""
    return datetime.date.today()


def get_date_range(days: int = 7) -> tuple[datetime.datetime, datetime.datetime]:
    """获取从今天往前推 N 天的日期范围"""
    end = datetime.datetime.now().replace(hour=23, minute=59, second=59)
    start = end - datetime.timedelta(days=days)
    return start, end


def ensure_dir(dir_path: str) -> str:
    """确保目录存在"""
    os.makedirs(dir_path, exist_ok=True)
    return dir_path


def generate_filename(prefix: str, ext: str, date_prefix: bool = True) -> str:
    """
    生成带时间戳的文件名

    Args:
        prefix: 文件名前缀
        ext: 文件扩展名
        date_prefix: 是否包含日期前缀

    Returns:
        "broadcast_20260703_143025.mp3"
    """
    now = datetime.datetime.now()
    if date_prefix:
        return f"{prefix}_{now.strftime('%Y%m%d_%H%M%S')}.{ext}"
    return f"{prefix}_{now.strftime('%H%M%S')}.{ext}"


def md5_hash(text: str) -> str:
    """计算字符串的 MD5 哈希"""
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def truncate_text(text: str, max_length: int = 200) -> str:
    """截断文本"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def safe_filename(filename: str) -> str:
    """清理文件名中的非法字符"""
    return re.sub(r'[<>:"/\\|?*]', "_", filename)


def get_media_url(base_url: str, file_path: str, media_dir: str) -> str:
    """
    将本地文件路径转换为媒体访问 URL

    Args:
        base_url: 服务器基础 URL
        file_path: 文件在磁盘上的绝对路径
        media_dir: 媒体文件根目录

    Returns:
        可访问的 URL
    """
    try:
        # 尝试计算相对路径
        rel_path = os.path.relpath(file_path, media_dir)
        rel_path = rel_path.replace("\\", "/")
        return f"{base_url.rstrip('/')}/media/{rel_path}"
    except ValueError:
        # 不在 media_dir 下的情况，返回文件名
        return f"{base_url.rstrip('/')}/media/{os.path.basename(file_path)}"
