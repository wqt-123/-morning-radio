---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: 1ce85845d4b1dbdcc6e0969243bee6b9_cd1effa976fc11f19641525400d9a7a1
    ReservedCode1: m7C9PPerQpSb4Dor9JJPCWpScl3ug89KSuVXiLzy7+lAaC/0x0qNjx+f2p94eX17kUTH0gEOutCBmTwj+2+bkNS4phwkbabv42GwG3fZKAPfVtfwJsRd8jMvmj+reF2XD58neYxw/clyO7RbLXdc3ZNcKkP/k4tlBX/qLGDjsdhoypUrXeHtSFy4jF8=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: 1ce85845d4b1dbdcc6e0969243bee6b9_cd1effa976fc11f19641525400d9a7a1
    ReservedCode2: m7C9PPerQpSb4Dor9JJPCWpScl3ug89KSuVXiLzy7+lAaC/0x0qNjx+f2p94eX17kUTH0gEOutCBmTwj+2+bkNS4phwkbabv42GwG3fZKAPfVtfwJsRd8jMvmj+reF2XD58neYxw/clyO7RbLXdc3ZNcKkP/k4tlBX/qLGDjsdhoypUrXeHtSFy4jF8=
---

# 早安电台 Morning Radio

AI + 每日新闻早安电台项目。每天早上自动抓取新闻，使用 AI 生成播报稿，通过 TTS 合成语音播报，最终生成带背景画面的视频。

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI (Python 3.10+) |
| 数据库 | MySQL 8.0 |
| 异步任务 | Celery + Redis |
| AI 文本生成 | OpenAI / 通义千问 (DashScope) |
| TTS 语音 | edge-tts |
| 视频合成 | FFmpeg + Pillow |
| 前端 | Vue 3 + Vite (待开发) |

## 项目结构

```
morning-radio/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口
│   │   ├── config.py            # 配置管理
│   │   ├── api/                 # API 路由
│   │   │   ├── news.py          # 新闻相关 API
│   │   │   ├── radio.py         # 电台播报 API
│   │   │   └── user.py          # 用户偏好 API
│   │   ├── models/
│   │   │   └── database.py      # SQLAlchemy 模型
│   │   ├── services/
│   │   │   ├── news_fetcher.py  # 新闻抓取服务
│   │   │   ├── ai_writer.py     # AI 播报稿生成
│   │   │   ├── tts_service.py   # TTS 语音合成
│   │   │   └── video_service.py # 视频合成
│   │   ├── tasks/
│   │   │   ├── celery_app.py    # Celery 配置
│   │   │   └── daily_tasks.py   # 定时任务
│   │   └── utils/
│   │       └── helpers.py       # 工具函数
│   ├── .env                     # 环境变量
│   ├── requirements.txt         # Python 依赖
│   └── run.py                   # 启动脚本
├── database/
│   └── init.sql                 # 数据库初始化
└── README.md
```

## 快速启动

### 前置条件

- Python 3.10+
- MySQL 8.0+
- Redis
- FFmpeg (需添加到 PATH)

### 1. 数据库初始化

```bash
mysql -u root -p < database/init.sql
```

### 2. 配置环境变量

编辑 `backend/.env`，填入你的 API 密钥：

```env
DATABASE_URL=mysql+pymysql://root:your_password@127.0.0.1:3306/morning_radio?charset=utf8mb4
OPENAI_API_KEY=your_key_here
NEWS_API_KEY=your_key_here
```

### 3. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 4. 启动 Redis

```bash
redis-server
```

### 5. 启动 FastAPI 服务

```bash
cd backend
python run.py
```

服务启动后访问：
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

### 6. 启动 Celery Worker（可选）

```bash
cd backend
celery -A app.tasks.celery_app worker -l info -P gevent
```

### 7. 启动 Celery Beat（定时任务）

```bash
cd backend
celery -A app.tasks.celery_app beat -l info
```

## API 接口

### 新闻

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/news/today` | 获取今日新闻 |
| GET | `/api/news/category/{category}` | 按分类获取新闻 |
| GET | `/api/news/{news_id}` | 获取新闻详情 |
| POST | `/api/news/fetch` | 手动触发新闻抓取 |

### 电台播报

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/radio/today` | 获取今日播报 |
| GET | `/api/radio/history` | 获取历史播报 |
| POST | `/api/radio/generate` | 手动生成播报 |
| GET | `/api/radio/stream/{filename}` | 流媒体播放 |

### 用户

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/user/preferences` | 获取用户偏好 |
| PUT | `/api/user/preferences` | 更新用户偏好 |

## 定时任务

- **每天 06:00** - 自动抓取新闻
- **每天 06:30** - 自动生成播报（AI 稿件 → TTS 语音 → 视频合成）
*（内容由AI生成，仅供参考）*
