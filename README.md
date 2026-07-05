# 早安电台 (Morning Radio)

AI 驱动的每日新闻播报系统。自动聚合 RSS 新闻，通过大语言模型生成播报稿，语音合成 + 视频合成，打造专属早安电台。

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI + Celery + Redis |
| AI 撰稿 | 通义千问 (DashScope API, qwen-plus) |
| 语音合成 | Edge-TTS |
| 视频合成 | MoviePy + PIL |
| 前端 | Vue 3 + Vite + Element Plus |
| 数据库 | MySQL 8.0 |
| 部署 | Nginx + NSSM (Windows 服务) |
