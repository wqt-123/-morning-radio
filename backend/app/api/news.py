"""
新闻相关 API
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session

from app.models.database import News, get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/news", tags=["新闻"])


@router.get("/today", summary="获取今日新闻列表")
async def get_today_news(
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200, description="返回数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
):
    """获取今日入库的新闻列表"""
    from datetime import date

    today = date.today()
    start_of_day = f"{today.isoformat()} 00:00:00"
    end_of_day = f"{today.isoformat()} 23:59:59"

    stmt = (
        select(News)
        .where(News.created_at >= start_of_day, News.created_at <= end_of_day)
        .order_by(desc(News.published_at))
        .offset(offset)
        .limit(limit)
    )
    result = db.execute(stmt)
    news_list = result.scalars().all()

    return {
        "code": 0,
        "message": "success",
        "data": {
            "total": len(news_list),
            "items": [
                {
                    "id": n.id,
                    "title": n.title,
                    "summary": n.summary,
                    "image_url": n.image_url,
                    "source": n.source,
                    "source_url": n.source_url,
                    "category": n.category,
                    "published_at": n.published_at.isoformat() if n.published_at else None,
                }
                for n in news_list
            ],
        },
    }


@router.get("/category/{category}", summary="按分类获取新闻")
async def get_news_by_category(
    category: str,
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    days: int = Query(7, ge=1, le=30, description="最近N天"),
):
    """按分类获取新闻"""
    from datetime import datetime, timedelta

    valid_categories = ["tech", "finance", "sports", "entertainment", "domestic", "international"]
    if category not in valid_categories:
        raise HTTPException(status_code=400, detail=f"不支持的分类: {category}")

    since = datetime.now() - timedelta(days=days)

    stmt = (
        select(News)
        .where(News.category == category, News.created_at >= since)
        .order_by(desc(News.published_at))
        .offset(offset)
        .limit(limit)
    )
    result = db.execute(stmt)
    news_list = result.scalars().all()

    return {
        "code": 0,
        "message": "success",
        "data": {
            "category": category,
            "total": len(news_list),
            "items": [
                {
                    "id": n.id,
                    "title": n.title,
                    "summary": n.summary,
                    "image_url": n.image_url,
                    "source": n.source,
                    "source_url": n.source_url,
                    "category": n.category,
                    "published_at": n.published_at.isoformat() if n.published_at else None,
                }
                for n in news_list
            ],
        },
    }


@router.get("/{news_id}", summary="获取新闻详情")
async def get_news_detail(
    news_id: int,
    db: Session = Depends(get_db),
):
    """获取单条新闻的详细信息"""
    stmt = select(News).where(News.id == news_id)
    result = db.execute(stmt)
    news = result.scalar_one_or_none()

    if news is None:
        raise HTTPException(status_code=404, detail="新闻不存在")

    return {
        "code": 0,
        "message": "success",
        "data": {
            "id": news.id,
            "title": news.title,
            "summary": news.summary,
            "content": news.content,
            "image_url": news.image_url,
            "source": news.source,
            "source_url": news.source_url,
            "category": news.category,
            "published_at": news.published_at.isoformat() if news.published_at else None,
            "created_at": news.created_at.isoformat() if news.created_at else None,
        },
    }


@router.post("/fetch", summary="手动触发新闻抓取")
async def trigger_news_fetch(
    categories: Optional[list[str]] = None,
):
    """手动触发新闻抓取任务"""
    from app.services.news_fetcher import fetch_news

    try:
        result = await fetch_news(categories=categories)
        return {
            "code": 0,
            "message": "新闻抓取完成",
            "data": result,
        }
    except Exception as e:
        logger.error(f"新闻抓取失败: {e}")
        raise HTTPException(status_code=500, detail=f"新闻抓取失败: {str(e)}")
