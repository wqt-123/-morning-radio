"""
AI 内容生成服务 - 调用 OpenAI 兼容接口生成早安播报稿
"""
import logging
from typing import Optional

from openai import OpenAI

from app.config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL, DASHSCOPE_API_KEY

logger = logging.getLogger(__name__)

# System Prompt：早安电台主播
SYSTEM_PROMPT = """你是一位专业的早安电台主播，名叫"小早"。你的声音温暖亲切，语速适中，像一位老朋友在清晨送来的第一声问候。

你的任务是根据当日要闻，生成一段完整的早安播报稿件，时长约5-8分钟。

播报稿结构要求：

1. **开场白**（约150字）：向听众问早安，简单提及今天的日期和星期几，用温暖的语气开启新的一天。可以简单预告今天会聊到哪些方面。

2. **要闻深度播报**（8-12条新闻，每条约200-300字）：
   - 从提供的新闻列表中挑选8-12条最重要的新闻，覆盖不同领域
   - 必须包含：科技类2-3条、财经类2-3条、国内民生2-3条、国际1-2条、体育/娱乐1-2条
   - 每条新闻不只是概括标题，要展开说明背景和影响，像真正的主播一样讲故事
   - 用自然的过渡词串联，如"接下来我们关注..."、"视线转向..."、"再来看一条..."等
   - 科技财经类用词专业但通俗，民生类亲切自然有温度
   - 要有评论感，但保持客观中立

3. **天气与出行提示**（约150字）：结合当前季节给出实用的天气提醒和生活小贴士。

4. **正能量寄语**（约150字）：用一段温暖有力的话激励听众，开启新的一天。

5. **结束语**（约100字）：正式道别，祝福听众。

整体要求：
- 总字数严格控制在2800-4000字（对应约5-8分钟朗读时长）
- 语气温暖亲切，适合朗读，像真正的广播电台节目
- 段落之间有明显停顿，每段开头用不同的引导语
- 避免过于书面化，用口语化但得体的表达
- 不要出现"根据提供的信息"、"以下是XXX"等机器感表达
- 适当使用"听众朋友们"、"各位早安"、"大家早上好"等称谓
- 每条新闻之间留出自然的过渡"""


def _get_client() -> Optional[OpenAI]:
    """获取 OpenAI 客户端（支持通义千问等兼容接口）"""
    # 优先使用 OpenAI
    if OPENAI_API_KEY and not OPENAI_API_KEY.startswith("your_"):
        return OpenAI(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_BASE_URL,
        )

    # 使用通义千问 DashScope
    if DASHSCOPE_API_KEY and not DASHSCOPE_API_KEY.startswith("your_"):
        return OpenAI(
            api_key=DASHSCOPE_API_KEY,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )

    logger.error("未配置任何 AI API Key")
    return None


def generate_broadcast_script(
    news_list: list[dict],
    model: Optional[str] = None,
    date_str: Optional[str] = None,
) -> str:
    """
    根据新闻列表生成早安播报稿

    Args:
        news_list: 新闻列表，每项含 title, summary, category, source
        model: 模型名称（可选，默认使用配置值）
        date_str: 日期字符串，用于开场白（如 "2026年7月3日 星期五"）

    Returns:
        生成的播报稿文本
    """
    client = _get_client()
    if client is None:
        return _generate_fallback_script(news_list, date_str)

    # 构建新闻摘要文本
    news_text_parts = []
    for i, news in enumerate(news_list[:20], 1):
        category = news.get("category", "综合")
        category_cn = {
            "tech": "科技",
            "finance": "财经",
            "sports": "体育",
            "entertainment": "娱乐",
            "domestic": "国内",
            "international": "国际",
        }.get(category, "综合")

        parts = [f"{i}. 【{category_cn}】{news.get('title', '')}"]
        if news.get("summary"):
            parts.append(f"   摘要：{news['summary']}")
        if news.get("source"):
            parts.append(f"   来源：{news['source']}")
        news_text_parts.append("\n".join(parts))

    news_text = "\n\n".join(news_text_parts)

    user_prompt = f"""今天是{date_str or "新的一天"}，以下是今天的要闻：

{news_text}

请根据以上新闻，生成今天的早安播报稿件。"""

    try:
        response = client.chat.completions.create(
            model=model or OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=6000,
        )

        script = response.choices[0].message.content
        logger.info(f"AI 播报稿生成成功，长度：{len(script) if script else 0} 字")
        return script or _generate_fallback_script(news_list, date_str)

    except Exception as e:
        logger.error(f"AI 生成播报稿失败: {e}")
        return _generate_fallback_script(news_list, date_str)


def _generate_fallback_script(news_list: list[dict], date_str: Optional[str] = None) -> str:
    """AI 不可用时的兜底播报稿 - 深度扩展版，生成5-8分钟内容"""
    from datetime import datetime

    today = date_str or datetime.now().strftime("%Y年%m月%d日")
    weekday_map = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    weekday = weekday_map[datetime.now().weekday()]

    # 按分类整理新闻
    categories = {"tech": [], "finance": [], "domestic": [], "international": [], "sports": [], "entertainment": []}
    cat_names = {
        "tech": "科技前沿", "finance": "财经脉搏", "domestic": "国内要闻",
        "international": "国际视野", "sports": "体育赛场", "entertainment": "文娱速递"
    }

    for news in news_list[:20]:
        cat = news.get("category", "domestic")
        if cat in categories:
            categories[cat].append(news)

    lines = []
    # 开场白
    lines.append(f"听众朋友们，大家早上好！今天是{today}，{weekday}。")
    lines.append("")
    lines.append(f"我是小早，欢迎收听今天的早安电台。在这个清新的早晨，让我为您梳理过去24小时里，世界发生了什么，又有哪些值得关注的新闻。")
    lines.append("")
    lines.append("让我们开始今天的节目。")
    lines.append("")
    lines.append("——")
    lines.append("")

    # 各版块播报
    section_transitions = [
        "首先来关注",
        "接下来我们把目光投向",
        "视线转向",
        "再来看",
        "继续关注",
        "下面来看",
    ]

    idx = 0
    for cat, items in categories.items():
        if not items:
            continue
        transition = section_transitions[idx % len(section_transitions)]
        lines.append(f"{transition}{cat_names.get(cat, '综合新闻')}方面的消息。")
        lines.append("")

        for item in items[:4]:  # 每个分类最多4条
            title = item.get("title", "")
            summary = item.get("summary", "")
            source = item.get("source", "")

            lines.append(f"▸ {title}")
            if summary:
                # 扩展摘要，让每条新闻有足够的展开内容
                expanded = summary
                if len(summary) < 80:
                    # 摘要太短，补充一些自然的展开语
                    expanders = [
                        f"这一消息引起了广泛关注。{summary}",
                        f"据了解，{summary}",
                        f"值得关注的是，{summary}",
                        f"业内人士分析认为，{summary}",
                    ]
                    import random
                    expanded = random.choice(expanders)
                lines.append(f"  {expanded}")
            if source:
                lines.append(f"  —— {source}")
            lines.append("")

        idx += 1

    lines.append("——")
    lines.append("")

    # 天气与出行提示
    lines.append("接下来是今天的天气和出行提醒。")
    import random as _random
    season_tips = [
        "盛夏时节，全国多地气温持续走高，建议大家尽量避免中午时段户外活动，多补充水分，注意防暑降温。出门记得做好防晒措施。",
        "当前正值夏季，气温较高。如果您有出行计划，建议随身携带防晒用品和充足的饮用水。驾车出行的朋友请注意检查车辆空调和胎压。",
        "近期天气炎热，提醒老人和儿童尽量减少高温时段外出。同时夏季也是肠道疾病高发期，饮食卫生要格外注意。",
    ]
    lines.append(_random.choice(season_tips))
    lines.append("")

    # 正能量寄语
    lines.append("——")
    lines.append("")
    inspirations = [
        "每一天都是崭新的开始。无论昨天经历了什么，今天太阳照常升起，机会依然在前方等待。愿您带着微笑和信心，拥抱这崭新的一天。",
        "生活就像一场马拉松，不在于起跑多快，而在于能否坚持到最后。愿您在每一个清晨，都能找到前行的力量。记住，您比自己想象的更强大。",
        "有人说，早晨决定了一天的基调。在这个美好的清晨，请给自己一个温暖的拥抱，告诉自己：今天会是美好的一天。保持好心情，好运自然来。",
    ]
    lines.append(_random.choice(inspirations))
    lines.append("")

    # 结束语
    lines.append("——")
    lines.append("")
    lines.append("以上就是今天早安电台的全部内容。感谢您的收听，我是小早。")
    lines.append("")
    lines.append("温馨提醒大家关注天气变化，合理安排出行和工作。祝您今天心情愉快，事事顺心！")
    lines.append("")
    lines.append("我们明天同一时间，不见不散。早安！")

    return "\n".join(lines)
