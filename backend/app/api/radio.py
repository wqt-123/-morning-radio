"""
电台相关 API - 生成播报、获取历史、播放音视频
"""
import logging
import os
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from app.models.database import DailyBroadcast, get_db
from app.utils.helpers import get_today_str, generate_filename, ensure_dir
from app.config import MEDIA_PATH

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/radio", tags=["电台播报"])


@router.get("/today", summary="获取今日播报")
async def get_today_broadcast(
    db: Session = Depends(get_db),
):
    """获取今天生成的播报（含音频/视频 URL）"""
    from datetime import date

    today = date.today()
    start = f"{today.isoformat()} 00:00:00"
    end = f"{today.isoformat()} 23:59:59"

    stmt = (
        select(DailyBroadcast)
        .where(
            DailyBroadcast.generated_at >= start,
            DailyBroadcast.generated_at <= end,
        )
        .order_by(desc(DailyBroadcast.generated_at))
        .limit(1)
    )
    result = db.execute(stmt)
    broadcast = result.scalar_one_or_none()

    if broadcast is None:
        return {
            "code": 0,
            "message": "今日暂无播报",
            "data": None,
        }

    return {
        "code": 0,
        "message": "success",
        "data": {
            "id": broadcast.id,
            "title": broadcast.title,
            "broadcast_text": broadcast.broadcast_text,
            "audio_url": f"/api/radio/stream/{os.path.basename(broadcast.audio_path)}" if broadcast.audio_path else None,
            "video_url": f"/api/radio/stream/{os.path.basename(broadcast.video_path)}" if broadcast.video_path else None,
            "duration": broadcast.duration,
            "status": broadcast.status,
            "generated_at": broadcast.generated_at.isoformat() if broadcast.generated_at else None,
        },
    }


@router.get("/history", summary="获取历史播报列表")
async def get_broadcast_history(
    db: Session = Depends(get_db),
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """获取历史播报列表"""
    stmt = (
        select(DailyBroadcast)
        .where(DailyBroadcast.status == "completed")
        .order_by(desc(DailyBroadcast.generated_at))
        .offset(offset)
        .limit(limit)
    )
    result = db.execute(stmt)
    broadcasts = result.scalars().all()

    return {
        "code": 0,
        "message": "success",
        "data": {
            "total": len(broadcasts),
            "items": [
                {
                    "id": b.id,
                    "title": b.title,
                    "duration": b.duration,
                    "audio_url": f"/api/radio/stream/{os.path.basename(b.audio_path)}" if b.audio_path else None,
                    "video_url": f"/api/radio/stream/{os.path.basename(b.video_path)}" if b.video_path else None,
                    "generated_at": b.generated_at.isoformat() if b.generated_at else None,
                }
                for b in broadcasts
            ],
        },
    }


@router.post("/generate", summary="手动生成播报")
async def generate_broadcast(
    db: Session = Depends(get_db),
):
    """
    手动触发播报生成流程：
    新闻抓取 → AI 生成稿件 → TTS 语音 → 视频合成
    """
    import os
    from datetime import datetime
    from app.services.news_fetcher import fetch_news
    from app.services.ai_writer import generate_broadcast_script
    from app.services.tts_service import text_to_speech
    from app.services.video_service import create_video

    # 确保媒体目录存在
    audio_dir = ensure_dir(str(MEDIA_PATH / "audio"))
    video_dir = ensure_dir(str(MEDIA_PATH / "video"))

    today_str = get_today_str()

    # 1. 创建数据库记录
    broadcast = DailyBroadcast(
        title=f"早安电台 - {today_str}",
        broadcast_text="",
        status="generating",
        generated_at=datetime.now(),
    )
    db.add(broadcast)
    db.commit()
    db.refresh(broadcast)

    broadcast_id = broadcast.id
    logger.info(f"开始生成播报 #{broadcast_id}")

    try:
        # 2. 抓取新闻
        logger.info("步骤1: 抓取新闻...")
        fetch_result = await fetch_news()
        logger.info(f"新闻抓取完成: {fetch_result}")

        # 3. 获取新闻用于生成稿件
        from app.models.database import News as NewsModel
        stmt = select(NewsModel).order_by(desc(NewsModel.created_at)).limit(20)
        news_result = db.execute(stmt)
        news_list = [
            {
                "title": n.title,
                "summary": n.summary or "",
                "category": n.category,
                "source": n.source,
            }
            for n in news_result.scalars().all()
        ]

        if not news_list:
            raise ValueError("没有可用新闻数据")

        # 4. AI 生成播报稿
        logger.info("步骤2: AI 生成播报稿...")
        script = generate_broadcast_script(news_list, date_str=today_str)

        broadcast.broadcast_text = script
        db.commit()

        # 5. TTS 语音生成
        logger.info("步骤3: TTS 语音生成...")
        audio_filename = generate_filename("broadcast", "mp3")
        audio_path = os.path.join(audio_dir, audio_filename)
        await text_to_speech(text=script, output_path=audio_path)
        broadcast.audio_path = audio_path
        db.commit()

        # 6. 视频合成
        logger.info("步骤4: 视频合成...")
        video_filename = generate_filename("broadcast", "mp4")
        video_path = os.path.join(video_dir, video_filename)

        try:
            create_video(
                audio_path=audio_path,
                output_path=video_path,
                title_text=f"早安电台 {today_str}",
            )
            broadcast.video_path = video_path
        except Exception as e:
            logger.warning(f"视频合成失败（非致命）: {e}")

        # 7. 计算时长
        from app.services.video_service import get_audio_duration
        try:
            broadcast.duration = int(get_audio_duration(audio_path))
        except Exception:
            broadcast.duration = 0

        broadcast.status = "completed"
        db.commit()

        logger.info(f"播报 #{broadcast_id} 生成完成")

        return {
            "code": 0,
            "message": "播报生成完成",
            "data": {
                "id": broadcast.id,
                "title": broadcast.title,
                "status": broadcast.status,
                "duration": broadcast.duration,
            },
        }

    except Exception as e:
        logger.error(f"播报生成失败 [{broadcast_id}]: {e}")
        broadcast.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=f"播报生成失败: {str(e)}")


@router.get("/stream/{filename}", summary="流媒体播放")
async def stream_media(
    filename: str,
):
    """
    流媒体播放音频/视频文件
    先搜索 audio 目录再搜索 video 目录
    """
    import os

    search_dirs = [
        str(MEDIA_PATH / "audio"),
        str(MEDIA_PATH / "video"),
        str(MEDIA_PATH),
    ]

    for search_dir in search_dirs:
        file_path = os.path.join(search_dir, filename)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            media_type = "video/mp4" if filename.endswith(".mp4") else "audio/mpeg"
            return FileResponse(
                path=file_path,
                media_type=media_type,
                filename=filename,
            )

    raise HTTPException(status_code=404, detail=f"媒体文件不存在: {filename}")
