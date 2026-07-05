"""
用户相关 API - 偏好设置
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.models.database import UserPreference, get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/user", tags=["用户"])


class PreferenceUpdate(BaseModel):
    """用户偏好更新请求"""
    preferred_categories: Optional[list[str]] = None
    voice_type: Optional[str] = None


@router.get("/preferences", summary="获取用户偏好")
async def get_preferences(
    user_id: str = "default_user",
    db: Session = Depends(get_db),
):
    """获取指定用户的偏好设置"""
    from sqlalchemy import select

    stmt = select(UserPreference).where(UserPreference.user_id == user_id)
    result = db.execute(stmt)
    pref = result.scalar_one_or_none()

    if pref is None:
        # 返回默认偏好
        return {
            "code": 0,
            "message": "success",
            "data": {
                "user_id": user_id,
                "preferred_categories": ["tech", "finance", "domestic"],
                "voice_type": "zh-CN-XiaoxiaoNeural",
            },
        }

    return {
        "code": 0,
        "message": "success",
        "data": {
            "user_id": pref.user_id,
            "preferred_categories": pref.preferred_categories or [],
            "voice_type": pref.voice_type,
        },
    }


@router.put("/preferences", summary="更新用户偏好")
async def update_preferences(
    body: PreferenceUpdate,
    user_id: str = "default_user",
    db: Session = Depends(get_db),
):
    """更新用户偏好设置"""
    from sqlalchemy import select
    from datetime import datetime

    stmt = select(UserPreference).where(UserPreference.user_id == user_id)
    result = db.execute(stmt)
    pref = result.scalar_one_or_none()

    if pref is None:
        # 创建新偏好
        pref = UserPreference(
            user_id=user_id,
            preferred_categories=body.preferred_categories or [],
            voice_type=body.voice_type or "zh-CN-XiaoxiaoNeural",
        )
        db.add(pref)
    else:
        # 更新已有偏好
        if body.preferred_categories is not None:
            pref.preferred_categories = body.preferred_categories
        if body.voice_type is not None:
            pref.voice_type = body.voice_type

    db.commit()
    db.refresh(pref)

    return {
        "code": 0,
        "message": "偏好更新成功",
        "data": {
            "user_id": pref.user_id,
            "preferred_categories": pref.preferred_categories,
            "voice_type": pref.voice_type,
        },
    }
