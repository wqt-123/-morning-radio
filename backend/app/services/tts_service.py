"""
TTS 语音生成服务 - 使用 edge-tts
"""
import asyncio
import logging
import os
import tempfile
from pathlib import Path
from typing import Optional

import edge_tts

from app.config import TTS_VOICE

logger = logging.getLogger(__name__)

# 可用音色
VOICE_OPTIONS = {
    "xiaoxiao": "zh-CN-XiaoxiaoNeural",      # 女声，活泼
    "yunxi": "zh-CN-YunxiNeural",            # 男声，温暖
    "xiaoyi": "zh-CN-XiaoyiNeural",          # 女声，知性
    "yunjian": "zh-CN-YunjianNeural",        # 男声，新闻
}


def _split_text(text: str, max_length: int = 500) -> list[str]:
    """
    将长文本按句号/换行分段，确保每段不超过 max_length 字符
    """
    sentences = []
    current = ""

    # 按标点拆分
    for char in text:
        current += char
        if char in "。！？\n！？" and len(current) >= 50:
            sentences.append(current.strip())
            current = ""
        elif len(current) >= max_length:
            sentences.append(current.strip())
            current = ""
    if current.strip():
        sentences.append(current.strip())

    # 合并过短的段落
    merged = []
    buffer = ""
    for s in sentences:
        if len(buffer) + len(s) < max_length:
            buffer += s
        else:
            if buffer:
                merged.append(buffer)
            buffer = s
    if buffer:
        merged.append(buffer)

    return merged if merged else [text]


async def _generate_segment(
    text: str,
    voice: str,
    output_path: str,
    rate: str = "+0%",
) -> None:
    """生成单个语音片段"""
    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=rate,
    )
    await communicate.save(output_path)


async def _merge_audio_files(
    input_paths: list[str],
    output_path: str,
    silence_duration: float = 0.3,
) -> None:
    """
    使用 FFmpeg 合并多个音频文件，并在片段间插入静音

    Args:
        input_paths: 输入音频文件路径列表
        output_path: 输出文件路径
        silence_duration: 片段间静音时长（秒）
    """
    import subprocess
    import json

    # 构建 concat 文件列表
    concat_list = []
    silence_file = None

    try:
        # 生成静音片段
        silence_file = os.path.join(
            tempfile.gettempdir(),
            f"silence_{os.getpid()}.wav",
        )
        subprocess.run(
            [
                "ffmpeg", "-y", "-f", "lavfi",
                "-i", f"anullsrc=r=24000:cl=mono",
                "-t", str(silence_duration),
                "-acodec", "pcm_s16le",
                silence_file,
            ],
            check=True,
            capture_output=True,
        )

        # 构建 concat filter
        for i, path in enumerate(input_paths):
            concat_list.append(f"file '{path}'")
            if i < len(input_paths) - 1:
                concat_list.append(f"file '{silence_file}'")

        concat_text = "\n".join(concat_list)
        concat_list_path = os.path.join(
            tempfile.gettempdir(),
            f"concat_list_{os.getpid()}.txt",
        )
        with open(concat_list_path, "w", encoding="utf-8") as f:
            f.write(concat_text)

        subprocess.run(
            [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", concat_list_path,
                "-acodec", "libmp3lame",
                "-ab", "192k",
                output_path,
            ],
            check=True,
            capture_output=True,
        )

        logger.info(f"合并音频完成: {output_path}")

    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg 合并音频失败: {e.stderr.decode() if e.stderr else e}")
        raise
    finally:
        # 清理临时文件
        for f in [silence_file, concat_list_path]:
            if f and os.path.exists(f):
                try:
                    os.remove(f)
                except OSError:
                    pass


async def text_to_speech(
    text: str,
    output_path: str,
    voice: Optional[str] = None,
    rate: str = "+5%",
) -> str:
    """
    将文本转为语音（MP3）

    Args:
        text: 要转换的文本
        output_path: 输出 MP3 文件路径
        voice: 音色名称
        rate: 语速调整（如 "+10%"）

    Returns:
        生成的 MP3 文件路径
    """
    voice = voice or TTS_VOICE

    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # 分段处理长文本（单段500字，减少拼接断点）
    segments = _split_text(text, max_length=500)
    logger.info(f"文本分为 {len(segments)} 段进行 TTS")

    if len(segments) == 1:
        # 单段直接生成
        await _generate_segment(
            text=segments[0],
            voice=voice,
            output_path=output_path,
            rate=rate,
        )
    else:
        # 多段分别生成再合并
        temp_files = []
        try:
            for i, seg in enumerate(segments):
                temp_path = os.path.join(
                    tempfile.gettempdir(),
                    f"tts_seg_{os.getpid()}_{i}.mp3",
                )
                await _generate_segment(
                    text=seg,
                    voice=voice,
                    output_path=temp_path,
                    rate=rate,
                )
                temp_files.append(temp_path)

            await _merge_audio_files(temp_files, output_path)
        finally:
            # 清理临时分段文件
            for f in temp_files:
                if os.path.exists(f):
                    try:
                        os.remove(f)
                    except OSError:
                        pass

    logger.info(f"TTS 生成完成: {output_path}")
    return output_path
