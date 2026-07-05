"""
Celery 每日定时任务
"""
import asyncio
import logging
import os
import sys
from datetime import datetime

# 确保 app 包可以被导入
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.tasks.celery_app import celery_app
from app.utils.helpers import get_today_str, generate_filename, ensure_dir
from app.config import MEDIA_PATH

logger = logging.getLogger(__name__)


@celery_app.task(name="fetch_daily_news", bind=True, max_retries=3, default_retry_delay=60)
def fetch_daily_news(self):
    """
    每日新闻抓取任务 - 每天早上 6:00 执行
    """
    logger.info("===== 开始每日新闻抓取 =====")

    try:
        # 使用 asyncio 运行异步抓取
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def _fetch():
            from app.services.news_fetcher import fetch_news
            return await fetch_news()

        result = loop.run_until_complete(_fetch())
        loop.close()

        logger.info(f"新闻抓取完成: 共 {result['total']} 条, 新增 {result['new']} 条")
        return result

    except Exception as exc:
        logger.error(f"新闻抓取失败: {exc}")
        self.retry(exc=exc)


@celery_app.task(name="generate_daily_broadcast", bind=True, max_retries=2, default_retry_delay=120)
def generate_daily_broadcast(self):
    """
    每日播报生成任务 - 每天早上 6:30 执行
    
    任务链: 读取新闻 → AI生成稿件 → TTS语音 → 视频合成
    """
    logger.info("===== 开始生成每日播报 =====")

    from app.models.database import SessionLocal, News, DailyBroadcast

    db = SessionLocal()
    broadcast = None

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        today_str = get_today_str()
        audio_dir = ensure_dir(str(MEDIA_PATH / "audio"))
        video_dir = ensure_dir(str(MEDIA_PATH / "video"))

        # 1. 创建广播记录
        broadcast = DailyBroadcast(
            title=f"早安电台 - {today_str}",
            broadcast_text="",
            status="generating",
            generated_at=datetime.now(),
        )
        db.add(broadcast)
        db.commit()
        db.refresh(broadcast)

        # 2. 获取最新新闻
        from sqlalchemy import select, desc
        stmt = select(News).order_by(desc(News.created_at)).limit(20)
        result = db.execute(stmt)
        news_records = result.scalars().all()

        if not news_records:
            raise ValueError("无可用新闻数据")

        news_list = [
            {
                "title": n.title,
                "summary": n.summary or "",
                "category": n.category,
                "source": n.source,
            }
            for n in news_records
        ]

        # 3. AI 生成播报稿
        logger.info("调用 AI 生成播报稿...")
        from app.services.ai_writer import generate_broadcast_script
        script = generate_broadcast_script(news_list, date_str=today_str)

        broadcast.broadcast_text = script
        db.commit()

        # 4. TTS 语音
        logger.info("生成 TTS 语音...")
        from app.services.tts_service import text_to_speech
        audio_filename = generate_filename("broadcast", "mp3")
        audio_path = os.path.join(audio_dir, audio_filename)

        async def _tts():
            await text_to_speech(text=script, output_path=audio_path)
        loop.run_until_complete(_tts())

        broadcast.audio_path = audio_path
        db.commit()

        # 5. 视频合成
        logger.info("合成视频...")
        from app.services.video_service import create_video, get_audio_duration
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
            logger.warning(f"视频合成失败（非致命，继续）: {e}")

        # 6. 计算时长
        try:
            broadcast.duration = int(get_audio_duration(audio_path))
        except Exception:
            broadcast.duration = 0

        broadcast.status = "completed"
        db.commit()

        loop.close()
        logger.info(f"每日播报生成完成 #{broadcast.id}")
        return {"status": "completed", "broadcast_id": broadcast.id}

    except Exception as exc:
        logger.error(f"播报生成失败: {exc}")
        if broadcast:
            broadcast.status = "failed"
            db.commit()
        self.retry(exc=exc)

    finally:
        db.close()
