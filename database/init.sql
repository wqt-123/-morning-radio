-- ============================================
-- 早安电台 - MySQL 数据库初始化脚本
-- ============================================

-- 创建数据库
CREATE DATABASE IF NOT EXISTS morning_radio
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE morning_radio;

-- ============================================
-- 新闻表
-- ============================================
CREATE TABLE IF NOT EXISTS news (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '新闻ID',
    title VARCHAR(500) NOT NULL COMMENT '新闻标题',
    summary TEXT COMMENT '新闻摘要',
    content LONGTEXT COMMENT '新闻正文',
    source VARCHAR(200) COMMENT '新闻来源',
    source_url VARCHAR(1000) COMMENT '原文链接',
    category VARCHAR(50) COMMENT '分类: tech/finance/sports/entertainment/domestic/international',
    published_at DATETIME COMMENT '发布时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '入库时间',

    INDEX idx_news_category (category),
    INDEX idx_news_published_at (published_at),
    INDEX idx_news_created_at (created_at),
    INDEX idx_news_title (title(100))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='新闻表';

-- ============================================
-- 新闻分类表
-- ============================================
CREATE TABLE IF NOT EXISTS news_category (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '分类ID',
    name VARCHAR(50) NOT NULL UNIQUE COMMENT '分类标识',
    display_name VARCHAR(100) NOT NULL COMMENT '显示名称',
    icon VARCHAR(200) COMMENT '图标',

    UNIQUE KEY uk_category_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='新闻分类表';

-- 插入默认分类数据
INSERT INTO news_category (name, display_name, icon) VALUES
    ('tech', '科技', '💻'),
    ('finance', '财经', '💰'),
    ('sports', '体育', '⚽'),
    ('entertainment', '娱乐', '🎬'),
    ('domestic', '国内', '🇨🇳'),
    ('international', '国际', '🌍')
ON DUPLICATE KEY UPDATE
    display_name = VALUES(display_name),
    icon = VALUES(icon);

-- ============================================
-- 每日播报表
-- ============================================
CREATE TABLE IF NOT EXISTS daily_broadcast (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '播报ID',
    title VARCHAR(500) NOT NULL COMMENT '播报标题',
    broadcast_text LONGTEXT COMMENT '播报稿件全文',
    audio_path VARCHAR(1000) COMMENT '音频文件路径',
    video_path VARCHAR(1000) COMMENT '视频文件路径',
    bg_image_path VARCHAR(1000) COMMENT '背景图路径',
    duration INT COMMENT '时长（秒）',
    status VARCHAR(50) DEFAULT 'pending' COMMENT '状态: pending/generating/completed/failed',
    generated_at DATETIME COMMENT '生成时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    INDEX idx_broadcast_status (status),
    INDEX idx_broadcast_generated_at (generated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='每日播报表';

-- ============================================
-- 用户偏好表
-- ============================================
CREATE TABLE IF NOT EXISTS user_preference (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'ID',
    user_id VARCHAR(100) NOT NULL UNIQUE COMMENT '用户ID',
    preferred_categories JSON COMMENT '偏好分类列表',
    voice_type VARCHAR(100) DEFAULT 'zh-CN-XiaoxiaoNeural' COMMENT '偏好音色',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    UNIQUE KEY uk_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户偏好表';

-- ============================================
-- 完成
-- ============================================
SELECT '数据库初始化完成!' AS status;
