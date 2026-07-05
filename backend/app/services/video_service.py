"""
视频合成服务 - 使用 FFmpeg 合成音频 + 背景图 + 字幕
"""
import logging
import os
import subprocess
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)


def _get_font(size: int = 48) -> Optional[ImageFont.FreeTypeFont]:
    """获取可用的中文字体"""
    font_candidates = [
        "C:/Windows/Fonts/msyh.ttc",        # 微软雅黑
        "C:/Windows/Fonts/simhei.ttf",       # 黑体
        "C:/Windows/Fonts/simsun.ttc",       # 宋体
        "C:/Windows/Fonts/STKAITI.TTF",      # 楷体
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
    ]
    for font_path in font_candidates:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size)
            except Exception:
                continue
    # 回退到默认字体
    logger.warning("未找到中文字体，使用默认字体（可能显示不正常）")
    return ImageFont.load_default()


def generate_background_image(
    output_path: str,
    title_text: str,
    width: int = 1920,
    height: int = 1080,
    bg_color: str = "#1a1a2e",
) -> str:
    """
    使用 Pillow 生成带文字的背景图

    Args:
        output_path: 输出图片路径
        title_text: 标题文字
        width, height: 图片尺寸
        bg_color: 背景颜色

    Returns:
        背景图路径
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # 创建渐变色背景
    image = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(image)

    # 绘制装饰圆
    for r in range(width, 0, -4):
        alpha = int(20 * (1 - r / width))
        color = (41, 98, 255)  # 蓝色
        draw.ellipse(
            [(width // 2 - r // 2, height // 2 - r // 2),
             (width // 2 + r // 2, height // 2 + r // 2)],
            outline=(*color, alpha) if isinstance(color, tuple) else color,
        )

    # 绘制标题文字
    title_font = _get_font(72)
    subtitle_font = _get_font(36)

    # 标题居中
    if title_text:
        # 顶部大标题
        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        title_w = title_bbox[2] - title_bbox[0]
        title_x = (width - title_w) // 2
        title_y = 200
        draw.text((title_x, title_y), title_text, fill="white", font=title_font)

    # 副标题
    subtitle = "早安电台 · 每日新闻速览"
    sub_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
    sub_w = sub_bbox[2] - sub_bbox[0]
    sub_x = (width - sub_w) // 2
    sub_y = 320
    draw.text((sub_x, sub_y), subtitle, fill="#8899aa", font=subtitle_font)

    # 底部装饰线
    line_y = height - 100
    for offset in range(0, width, 40):
        draw.rectangle(
            [(offset, line_y), (offset + 20, line_y + 4)],
            fill="#2962FF",
        )

    # 底部文字
    footer = "Powered by Morning Radio AI"
    footer_font = _get_font(20)
    footer_bbox = draw.textbbox((0, 0), footer, font=footer_font)
    footer_w = footer_bbox[2] - footer_bbox[0]
    draw.text(
        ((width - footer_w) // 2, height - 60),
        footer,
        fill="#556677",
        font=footer_font,
    )

    image.save(output_path, "PNG")
    logger.info(f"背景图已生成: {output_path}")
    return output_path


def get_audio_duration(audio_path: str) -> float:
    """获取音频时长（秒）"""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                audio_path,
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        return float(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError) as e:
        logger.error(f"获取音频时长失败: {e}")
        return 60.0  # 默认60秒


def create_video(
    audio_path: str,
    output_path: str,
    bg_color: str = "#1a1a2e",
    title_text: str = "早安电台",
    add_subtitles: bool = False,
) -> str:
    """
    使用 FFmpeg 合成视频：背景图 + 音频 → MP4

    Args:
        audio_path: 音频文件路径
        output_path: 输出视频路径
        bg_color: 背景颜色
        title_text: 标题文字
        add_subtitles: 是否添加字幕效果

    Returns:
        视频文件路径
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # 1. 生成背景图
    bg_image_path = os.path.join(
        os.path.dirname(output_path),
        f"bg_{os.path.splitext(os.path.basename(output_path))[0]}.png",
    )
    generate_background_image(bg_image_path, title_text, bg_color=bg_color)

    # 2. 获取音频时长
    duration = get_audio_duration(audio_path)

    # 3. FFmpeg 合成
    try:
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", bg_image_path,
            "-i", audio_path,
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-tune", "stillimage",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            "-movflags", "+faststart",
        ]

        if add_subtitles:
            # 使用 drawtext 滤镜添加滚动字幕效果
            subtitle_text = title_text.replace(":", "\\:").replace("'", "\\'")
            font_path = "C:/Windows/Fonts/msyh.ttc"
            if not os.path.exists(font_path):
                font_path = "C:/Windows/Fonts/simhei.ttf"

            drawtext = (
                f"drawtext=fontfile='{font_path}':"
                f"text='{subtitle_text}':"
                f"fontsize=32:fontcolor=white@0.8:"
                f"x=(w-text_w)/2:y=h-120:"
                f"enable='between(t,0,{duration})'"
            )
            cmd.extend(["-vf", drawtext])

        # 在滤镜之后添加输出
        cmd.append(output_path)

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            logger.error(f"FFmpeg 合成失败: {result.stderr}")
            raise RuntimeError(f"视频合成失败: {result.stderr[-500:]}")

        logger.info(f"视频合成完成: {output_path}, 时长: {duration:.1f}秒")
        return output_path

    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg 执行失败: {e}")
        raise
    except FileNotFoundError:
        logger.error("FFmpeg 未安装或不在 PATH 中")
        raise RuntimeError("FFmpeg 未安装，请先安装 FFmpeg 并添加到系统 PATH")


def create_video_with_audio_only(
    audio_path: str,
    output_path: str,
) -> str:
    """
    简易版视频合成：仅音频 + 黑色背景
    适用于 FFmpeg 字体不可用时
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "color=c=0x1a1a2e:s=1920x1080:d=1:r=1",
        "-i", audio_path,
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"视频合成失败: {result.stderr[-500:]}")

    logger.info(f"视频合成完成: {output_path}")
    return output_path
