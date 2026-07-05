"""
Celery 应用配置
"""
from celery import Celery
from celery.schedules import crontab

from app.config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND

# 创建 Celery 实例
celery_app = Celery(
    "morning_radio",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["app.tasks.daily_tasks"],
)

# Celery 配置
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    worker_max_tasks_per_child=200,
    worker_prefetch_multiplier=1,
    task_track_started=True,
    task_time_limit=1800,       # 30 分钟超时
    task_soft_time_limit=1500,  # 25 分钟软超时
)

# 定时任务配置
celery_app.conf.beat_schedule = {
    # 每天早上 6:00 抓取新闻
    "fetch-daily-news": {
        "task": "app.tasks.daily_tasks.fetch_daily_news",
        "schedule": crontab(hour=6, minute=0),
        "options": {"queue": "default"},
    },
    # 每天早上 6:30 生成播报
    "generate-daily-broadcast": {
        "task": "app.tasks.daily_tasks.generate_daily_broadcast",
        "schedule": crontab(hour=6, minute=30),
        "options": {"queue": "default"},
    },
}

# Beat 调度器配置
celery_app.conf.beat_schedule_filename = "celerybeat-schedule"
