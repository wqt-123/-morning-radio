"""
新闻抓取服务 - 支持多个新闻API源
"""
import hashlib
import logging
import time
from datetime import datetime, timedelta
from typing import Optional

import httpx
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.database import News, SessionLocal
from app.config import NEWS_API_KEY, JUHE_NEWS_KEY, TIANXING_API_KEY

logger = logging.getLogger(__name__)

# 分类映射：API返回的分类 → 系统内部分类
CATEGORY_MAP = {
    "technology": "tech",
    "tech": "tech",
    "science": "tech",
    "business": "finance",
    "finance": "finance",
    "economy": "finance",
    "sports": "sports",
    "sport": "sports",
    "entertainment": "entertainment",
    "entertain": "entertainment",
    "general": "domestic",
    "health": "domestic",
    "world": "international",
    "international": "international",
}


def _normalize_category(raw: str) -> str:
    """标准化分类名称"""
    return CATEGORY_MAP.get(raw.lower().strip(), "domestic")


def _compute_hash(title: str, source_url: str) -> str:
    """计算新闻去重哈希"""
    raw = f"{title.strip()}|{source_url.strip()}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def _is_duplicate(db: Session, title: str, source_url: str) -> bool:
    """检查新闻是否已存在"""
    stmt = select(News.id).where(
        News.title == title,
        News.source_url == source_url,
    ).limit(1)
    return db.execute(stmt).scalar() is not None


def _save_news_batch(db: Session, news_list: list[dict]) -> int:
    """批量保存新闻，返回新增数量"""
    count = 0
    for item in news_list:
        title = item.get("title", "").strip()
        source_url = item.get("source_url", "").strip()
        if not title:
            continue
        if _is_duplicate(db, title, source_url):
            continue

        published_at = item.get("published_at")
        if isinstance(published_at, str):
            try:
                published_at = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                published_at = datetime.now()

        news = News(
            title=title,
            summary=item.get("summary", ""),
            content=item.get("content", ""),
            image_url=item.get("image_url", ""),
            source=item.get("source", ""),
            source_url=source_url,
            category=item.get("category", "domestic"),
            published_at=published_at or datetime.now(),
        )
        db.add(news)
        count += 1

    if count > 0:
        db.commit()
        logger.info(f"保存了 {count} 条新新闻")
    return count


# ============================================
# NewsAPI.org 抓取
# ============================================
async def _fetch_from_newsapi(categories: Optional[list[str]] = None) -> list[dict]:
    """从 NewsAPI.org 抓取新闻"""
    if not NEWS_API_KEY or NEWS_API_KEY.startswith("your_"):
        logger.warning("NEWS_API_KEY 未配置，跳过 NewsAPI")
        return []

    if categories is None:
        categories = ["technology", "business", "sports", "entertainment", "general"]

    results = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        for category in categories:
            for attempt in range(3):
                try:
                    resp = await client.get(
                        "https://newsapi.org/v2/top-headlines",
                        params={
                            "country": "cn",
                            "category": category,
                            "apiKey": NEWS_API_KEY,
                            "pageSize": 20,
                        },
                    )
                    if resp.status_code == 429:
                        logger.warning("NewsAPI 速率限制，等待重试...")
                        time.sleep(2 * (attempt + 1))
                        continue

                    resp.raise_for_status()
                    data = resp.json()
                    articles = data.get("articles", [])

                    for article in articles:
                        results.append({
                            "title": article.get("title", ""),
                            "summary": article.get("description", ""),
                            "content": article.get("content", ""),
                            "image_url": article.get("urlToImage", ""),
                            "source": article.get("source", {}).get("name", ""),
                            "source_url": article.get("url", ""),
                            "category": _normalize_category(category),
                            "published_at": article.get("publishedAt"),
                        })
                    break  # 成功则退出重试
                except httpx.HTTPStatusError as e:
                    logger.error(f"NewsAPI 请求失败 [{category}]: {e}")
                    if attempt < 2:
                        time.sleep(1)
                except Exception as e:
                    logger.error(f"NewsAPI 异常 [{category}]: {e}")
                    if attempt < 2:
                        time.sleep(1)

    logger.info(f"NewsAPI 抓取到 {len(results)} 条新闻")
    return results


# ============================================
# 聚合数据 抓取
# ============================================
async def _fetch_from_juhe(categories: Optional[list[str]] = None) -> list[dict]:
    """从聚合数据抓取新闻"""
    if not JUHE_NEWS_KEY or JUHE_NEWS_KEY.startswith("your_"):
        logger.warning("JUHE_NEWS_KEY 未配置，跳过聚合数据")
        return []

    if categories is None:
        categories = ["top"]

    juhe_type_map = {
        "tech": "keji",
        "finance": "caijing",
        "sports": "tiyu",
        "entertainment": "yule",
        "domestic": "guonei",
        "international": "guoji",
        "top": "top",
    }

    results = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        for category in categories:
            juhe_type = juhe_type_map.get(category, "top")
            for attempt in range(3):
                try:
                    resp = await client.get(
                        "http://v.juhe.cn/toutiao/index",
                        params={
                            "type": juhe_type,
                            "key": JUHE_NEWS_KEY,
                        },
                    )
                    resp.raise_for_status()
                    data = resp.json()

                    if data.get("error_code") != 0:
                        logger.warning(f"聚合数据错误: {data.get('reason')}")
                        break

                    articles = data.get("result", {}).get("data", [])
                    for article in articles:
                        results.append({
                            "title": article.get("title", ""),
                            "summary": "",
                            "content": "",
                            "source": article.get("author_name", "聚合数据"),
                            "source_url": article.get("url", ""),
                            "category": _normalize_category(category),
                            "published_at": article.get("date"),
                        })
                    break
                except Exception as e:
                    logger.error(f"聚合数据请求失败 [{category}]: {e}")
                    if attempt < 2:
                        time.sleep(1)

    logger.info(f"聚合数据抓取到 {len(results)} 条新闻")
    return results


# ============================================
# 天行数据 抓取
# ============================================
async def _fetch_from_tianxing(categories: Optional[list[str]] = None) -> list[dict]:
    """从天行数据抓取新闻"""
    if not TIANXING_API_KEY or TIANXING_API_KEY.startswith("your_"):
        logger.warning("TIANXING_API_KEY 未配置，跳过天行数据")
        return []

    if categories is None:
        categories = ["domestic"]

    tianxing_type_map = {
        "tech": "keji",
        "finance": "caijing",
        "sports": "tiyu",
        "entertainment": "yule",
        "domestic": "guonei",
        "international": "world",
    }

    results = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        for category in categories:
            tianxing_type = tianxing_type_map.get(category, "guonei")
            for attempt in range(3):
                try:
                    resp = await client.get(
                        f"https://apis.tianapi.com/{tianxing_type}/index",
                        params={
                            "key": TIANXING_API_KEY,
                            "num": 20,
                        },
                    )
                    resp.raise_for_status()
                    data = resp.json()

                    if data.get("code") != 200:
                        logger.warning(f"天行数据错误: {data.get('msg')}")
                        break

                    articles = data.get("result", {}).get("newslist", [])
                    for article in articles:
                        results.append({
                            "title": article.get("title", ""),
                            "summary": article.get("description", ""),
                            "content": "",
                            "image_url": article.get("picUrl", ""),
                            "source": article.get("source", "天行数据"),
                            "source_url": article.get("url", ""),
                            "category": _normalize_category(category),
                            "published_at": article.get("ctime"),
                        })
                    break
                except Exception as e:
                    logger.error(f"天行数据请求失败 [{category}]: {e}")
                    if attempt < 2:
                        time.sleep(1)

    logger.info(f"天行数据抓取到 {len(results)} 条新闻")
    return results


# ============================================
# RSS 免费新闻源抓取
# ============================================
def _extract_image_url(item) -> str:
    """从 RSS/Atom item 中提取图片 URL"""
    ns = {
        "media": "http://search.yahoo.com/mrss/",
        "atom": "http://www.w3.org/2005/Atom",
    }
    # media:content
    mc = item.find("media:content", ns)
    if mc is None:
        mc = item.find("{http://search.yahoo.com/mrss/}content")
    if mc is not None:
        url = mc.get("url", "") or mc.get("medium", "")
        if url and any(url.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"]):
            return url
    # media:thumbnail
    mt = item.find("media:thumbnail", ns)
    if mt is None:
        mt = item.find("{http://search.yahoo.com/mrss/}thumbnail")
    if mt is not None:
        return mt.get("url", "")
    # enclosure
    enc = item.find("enclosure")
    if enc is not None:
        mime = enc.get("type", "")
        if mime and mime.startswith("image/"):
            return enc.get("url", "")
    # description中提取第一个img
    desc_el = item.find("description")
    if desc_el is None:
        desc_el = item.find("{http://www.w3.org/2005/Atom}summary")
    if desc_el is not None and desc_el.text:
        import re
        m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', desc_el.text, re.I)
        if m:
            return m.group(1)
    return ""


async def _fetch_from_rss(categories: Optional[list[str]] = None) -> list[dict]:
    """从免费 RSS 源抓取新闻（无需 API Key），仅保留最近24小时的新闻"""
    import xml.etree.ElementTree as ET
    from datetime import timezone, timedelta

    now_utc = datetime.now(timezone.utc)
    cutoff_time = now_utc - timedelta(hours=24)  # 只保留24小时内的新闻

    rss_sources = [
        # 人民网 - 国内政治
        {"url": "http://www.people.com.cn/rss/politics.xml", "category": "domestic", "source": "人民网"},
        # 新华网 - 综合
        {"url": "http://www.xinhuanet.com/politics/xhll.xml", "category": "domestic", "source": "新华网"},
        # 36氪快讯 - 科技
        {"url": "https://36kr.com/feed", "category": "tech", "source": "36氪"},
        # 虎嗅 - 科技
        {"url": "https://www.huxiu.com/rss/0.xml", "category": "tech", "source": "虎嗅"},
        # 财新博客
        {"url": "https://feedx.net/rss/caixin.xml", "category": "finance", "source": "财新"},
        # 网易新闻
        {"url": "https://www.163.com/dy/media/T1348647853363.html", "category": "domestic", "source": "网易"},
        # 中国日报
        {"url": "https://feedx.net/rss/chinadaily.xml", "category": "domestic", "source": "中国日报"},
        # IT之家 - 科技
        {"url": "https://www.ithome.com/rss/", "category": "tech", "source": "IT之家"},
        # 环球网
        {"url": "https://feedx.net/rss/huanqiu.xml", "category": "international", "source": "环球网"},
        # 新浪科技
        {"url": "https://feedx.net/rss/sinatech.xml", "category": "tech", "source": "新浪科技"},
        # 澎湃新闻
        {"url": "https://feedx.net/rss/thepaper.xml", "category": "domestic", "source": "澎湃新闻"},
        # 观察者网
        {"url": "https://feedx.net/rss/guancha.xml", "category": "international", "source": "观察者网"},
    ]

    # 只抓取已请求的分类
    if categories:
        rss_sources = [s for s in rss_sources if s["category"] in categories]

    results = []
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        for src in rss_sources:
            try:
                resp = await client.get(src["url"])
                if resp.status_code != 200:
                    continue

                root = ET.fromstring(resp.text)
                # RSS 2.0: channel > item
                items = root.findall(".//item")
                # Atom: entry
                if not items:
                    items = root.findall(".//{http://www.w3.org/2005/Atom}entry")

                for item in items[:10]:
                    title_el = item.find("title")
                    if title_el is None:
                        title_el = item.find("{http://www.w3.org/2005/Atom}title")
                    desc_el = item.find("description")
                    if desc_el is None:
                        desc_el = item.find("{http://www.w3.org/2005/Atom}summary")
                    link_el = item.find("link")
                    if link_el is None:
                        link_el = item.find("{http://www.w3.org/2005/Atom}link")
                    pubdate_el = item.find("pubDate")
                    if pubdate_el is None:
                        pubdate_el = item.find("{http://www.w3.org/2005/Atom}published")
                    if pubdate_el is None:
                        pubdate_el = item.find("{http://www.w3.org/2005/Atom}updated")

                    title = title_el.text.strip() if title_el is not None and title_el.text else ""
                    if not title:
                        continue

                    # 解析发布日期并过滤旧新闻
                    pubdate_str = pubdate_el.text.strip() if pubdate_el is not None and pubdate_el.text else None
                    if pubdate_str:
                        try:
                            # 尝试多种日期格式
                            for fmt in [
                                "%a, %d %b %Y %H:%M:%S %z",
                                "%a, %d %b %Y %H:%M:%S %Z",
                                "%Y-%m-%dT%H:%M:%S%z",
                                "%Y-%m-%dT%H:%M:%SZ",
                                "%Y-%m-%dT%H:%M:%S.%fZ",
                                "%Y-%m-%d %H:%M:%S",
                            ]:
                                try:
                                    pub_date = datetime.strptime(pubdate_str, fmt)
                                    if pub_date.tzinfo is None:
                                        pub_date = pub_date.replace(tzinfo=timezone.utc)
                                    if pub_date < cutoff_time:
                                        title = None  # 标记为跳过
                                    break
                                except ValueError:
                                    continue
                        except Exception:
                            pass  # 无法解析日期则不过滤

                    if title is None:
                        continue

                    image_url = _extract_image_url(item)
                    # 补全相对路径图片 URL
                    if image_url and image_url.startswith("/"):
                        from urllib.parse import urlparse
                        parsed = urlparse(src["url"])
                        image_url = f"{parsed.scheme}://{parsed.netloc}{image_url}"

                    results.append({
                        "title": title,
                        "summary": (desc_el.text.strip()[:200] if desc_el is not None and desc_el.text else ""),
                        "content": "",
                        "image_url": image_url,
                        "source": src["source"],
                        "source_url": link_el.get("href", "") if link_el is not None else "",
                        "category": src["category"],
                        "published_at": datetime.now().isoformat(),
                    })
                logger.info(f"RSS [{src['source']}] 抓取到 {min(len(items), 10)} 条")
            except Exception as e:
                logger.warning(f"RSS [{src['source']}] 抓取失败: {e}")

    return results


# ============================================
# 内置模拟新闻数据（当所有源都不可用时）
# ============================================
def _get_mock_news() -> list[dict]:
    """获取模拟新闻数据，确保系统始终有数据可展示"""
    today_str = datetime.now().strftime("%Y-%m-%d")
    return [
        # 科技类
        {"title": "我国人工智能核心产业规模突破万亿大关", "summary": "工信部最新数据显示，2026年上半年我国人工智能核心产业规模达到1.2万亿元，同比增长38%，大模型应用加速落地，已覆盖制造、医疗、教育等关键领域。", "content": "", "image_url": "https://picsum.photos/seed/ai2026/800/400", "source": "新华社", "source_url": f"mock://news/ai-{today_str}", "category": "tech", "published_at": f"{today_str}T06:00:00"},
        {"title": "中国航天：嫦娥七号探测器成功进入环月轨道", "summary": "国家航天局宣布，嫦娥七号探测器已完成近月制动，成功进入环月轨道，将开展月球南极水资源探测等科学任务，这是我国深空探测的重要里程碑。", "content": "", "image_url": "https://picsum.photos/seed/space26/800/400", "source": "央视新闻", "source_url": f"mock://news/space-{today_str}", "category": "tech", "published_at": f"{today_str}T06:05:00"},
        {"title": "新能源汽车渗透率首次超过60%", "summary": "中国汽车工业协会数据显示，6月新能源汽车零售渗透率达到62.3%，首次突破60%大关。比亚迪、蔚来等自主品牌销量持续领跑，市场加速电动化转型。", "content": "", "image_url": "https://picsum.photos/seed/evcar26/800/400", "source": "界面新闻", "source_url": f"mock://news/ev-{today_str}", "category": "tech", "published_at": f"{today_str}T06:15:00"},
        {"title": "全球首款6G试验芯片发布，下载速度达1Tbps", "summary": "华为联合中国移动发布全球首款6G通信试验芯片，在实验室环境下实现了1Tbps峰值下载速率，较5G提升100倍，预计2030年商用。", "content": "", "image_url": "https://picsum.photos/seed/6gchip/800/400", "source": "科技日报", "source_url": f"mock://news/6g-{today_str}", "category": "tech", "published_at": f"{today_str}T07:00:00"},
        # 财经类
        {"title": "央行宣布降准0.5个百分点 释放长期资金约1万亿元", "summary": "中国人民银行决定自7月15日起下调金融机构存款准备金率0.5个百分点，此举将有效增加金融机构长期资金来源，支持实体经济发展，市场普遍认为这是稳增长的重要信号。", "content": "", "image_url": "https://picsum.photos/seed/finance26/800/400", "source": "第一财经", "source_url": f"mock://news/finance-{today_str}", "category": "finance", "published_at": f"{today_str}T06:02:00"},
        {"title": "A股三大指数全线上涨 创业板指涨超3%", "summary": "受降准预期和外资回流影响，A股三大指数全线上涨，创业板指涨幅超3%，半导体、新能源板块领涨，两市成交额突破1.5万亿元。", "content": "", "image_url": "https://picsum.photos/seed/stock26/800/400", "source": "证券时报", "source_url": f"mock://news/stock-{today_str}", "category": "finance", "published_at": f"{today_str}T08:00:00"},
        {"title": "人民币汇率重返6.9区间 创近半年新高", "summary": "人民币兑美元中间价报6.8972，在岸人民币兑美元汇率突破6.90关口，创近半年来新高。分析人士指出，美联储降息预期和中国经济复苏是主要推动因素。", "content": "", "image_url": "https://picsum.photos/seed/rmb26/800/400", "source": "每日经济新闻", "source_url": f"mock://news/rmb-{today_str}", "category": "finance", "published_at": f"{today_str}T06:30:00"},
        # 国内民生
        {"title": "全国多地持续高温 多地气温突破40℃", "summary": "中央气象台继续发布高温橙色预警，华北、黄淮等地最高气温可达40℃以上。各地已启动防暑降温应急预案，提醒公众注意防暑降温，避免高温时段外出。", "content": "", "image_url": "https://picsum.photos/seed/weather26/800/400", "source": "中国天气网", "source_url": f"mock://news/weather-{today_str}", "category": "domestic", "published_at": f"{today_str}T06:10:00"},
        {"title": "暑期旅游市场持续火爆 热门线路一票难求", "summary": "2026年暑期旅游旺季到来，多个热门旅游城市酒店预订量同比增长超200%，新疆、云南、贵州等长线目的地尤其火爆，部分线路机票已售罄。", "content": "", "image_url": "https://picsum.photos/seed/travel26/800/400", "source": "中国旅游报", "source_url": f"mock://news/travel-{today_str}", "category": "domestic", "published_at": f"{today_str}T07:30:00"},
        {"title": "教育部：2026年高考录取工作全面启动", "summary": "2026年全国高考录取工作已正式启动，今年全国高考报名人数达到1353万人，再创历史新高。各省份将陆续公布各批次录取分数线。", "content": "", "image_url": "https://picsum.photos/seed/edu26/800/400", "source": "中国教育报", "source_url": f"mock://news/edu-{today_str}", "category": "domestic", "published_at": f"{today_str}T06:20:00"},
        # 国际
        {"title": "全球贸易格局持续演变 区域合作成新趋势", "summary": "世界贸易组织最新报告指出，全球贸易格局正在发生深刻变化，RCEP框架下成员国间贸易额持续增长。中国与东盟贸易额同比增长15%，区域经济一体化进程加快。", "content": "", "image_url": "https://picsum.photos/seed/trade26/800/400", "source": "经济日报", "source_url": f"mock://news/trade-{today_str}", "category": "international", "published_at": f"{today_str}T06:30:00"},
        {"title": "G20峰会聚焦全球气候变化与数字经济", "summary": "G20领导人峰会日前在巴西里约热内卢举行，各国就气候变化应对、数字经济治理等议题达成多项共识。中方提出的人工智能治理倡议获得广泛支持。", "content": "", "image_url": "https://picsum.photos/seed/g2026/800/400", "source": "人民日报", "source_url": f"mock://news/g20-{today_str}", "category": "international", "published_at": f"{today_str}T07:00:00"},
        # 体育娱乐
        {"title": "巴黎奥运会倒计时一周年 中国队备战全面提速", "summary": "距离2027巴黎奥运会开幕还有整整一年，中国体育代表团各项目备战进入冲刺阶段。跳水、举重、乒乓球等优势项目已完成主力阵容确定，近期将陆续参加国际热身赛。", "content": "", "image_url": "https://picsum.photos/seed/olympic26/800/400", "source": "体坛周报", "source_url": f"mock://news/sports-{today_str}", "category": "sports", "published_at": f"{today_str}T06:20:00"},
        {"title": "暑期档票房突破50亿元 国产影片占比超八成", "summary": "截至7月2日，2026年暑期档电影票房已突破50亿元，其中国产影片贡献超过80%。科幻题材《星际迷航：新生》和动画电影《大闹天宫2》领跑票房榜。", "content": "", "image_url": "https://picsum.photos/seed/movie26/800/400", "source": "人民日报", "source_url": f"mock://news/movie-{today_str}", "category": "entertainment", "published_at": f"{today_str}T06:25:00"},
        {"title": "中超联赛第15轮：上海海港3-1战胜北京国安", "summary": "中超联赛第15轮焦点战，上海海港主场3-1击败北京国安，武磊梅开二度。此役之后，海港继续领跑积分榜，争冠形势日趋明朗。", "content": "", "image_url": "https://picsum.photos/seed/football26/800/400", "source": "央视体育", "source_url": f"mock://news/football-{today_str}", "category": "sports", "published_at": f"{today_str}T08:30:00"},
    ]


# ============================================
# 主入口
# ============================================
async def fetch_news(
    categories: Optional[list[str]] = None,
    db_session: Optional[Session] = None,
) -> dict:
    """
    从所有已配置的新闻源抓取新闻，去重后存入数据库

    抓取优先级：NewsAPI > 聚合数据 > 天行数据 > RSS > 模拟数据

    Args:
        categories: 要抓取的分类列表
        db_session: 数据库会话（不传则创建新会话）

    Returns:
        {"total": int, "new": int, "sources": dict}
    """
    if categories is None:
        categories = ["tech", "finance", "sports", "entertainment", "domestic", "international"]

    # 并发抓取所有源
    all_results = []

    # NewsAPI
    newsapi_results = await _fetch_from_newsapi(categories)
    all_results.extend(newsapi_results)

    # 聚合数据
    juhe_results = await _fetch_from_juhe(categories)
    all_results.extend(juhe_results)

    # 天行数据
    tianxing_results = await _fetch_from_tianxing(categories)
    all_results.extend(tianxing_results)

    # RSS 免费源
    rss_results = await _fetch_from_rss(categories)
    all_results.extend(rss_results)

    # 如果所有源都没数据，使用模拟数据
    if not all_results:
        logger.warning("所有新闻源无数据，使用内置模拟数据")
        mock_data = _get_mock_news()
        all_results.extend(mock_data)
        # 模拟数据直接入库
        close_db = False
        if db_session is None:
            db_session = SessionLocal()
            close_db = True
        try:
            new_count = _save_news_batch(db_session, mock_data)
            return {
                "total": len(mock_data),
                "new": new_count,
                "sources": {"newsapi": 0, "juhe": 0, "tianxing": 0, "rss": 0, "mock": len(mock_data)},
            }
        finally:
            if close_db:
                db_session.close()

    # 去重：按 (title, source_url) 去重
    seen = set()
    deduped = []
    for item in all_results:
        key = _compute_hash(item["title"], item["source_url"])
        if key not in seen:
            seen.add(key)
            deduped.append(item)

    logger.info(f"去重前 {len(all_results)} 条，去重后 {len(deduped)} 条")

    # 存入数据库
    close_db = False
    if db_session is None:
        db_session = SessionLocal()
        close_db = True

    try:
        new_count = _save_news_batch(db_session, deduped)
        return {
            "total": len(deduped),
            "new": new_count,
            "sources": {
                "newsapi": len(newsapi_results),
                "juhe": len(juhe_results),
                "tianxing": len(tianxing_results),
                "rss": len(rss_results),
            },
        }
    finally:
        if close_db:
            db_session.close()
