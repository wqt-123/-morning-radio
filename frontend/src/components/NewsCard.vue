<template>
  <div class="news-card glass-card" @click="onOpenUrl">
    <div class="card-image" v-if="news.image_url">
      <img :src="news.image_url" :alt="news.title" loading="lazy" />
      <div class="image-overlay">
        <span class="source-badge">{{ news.source }}</span>
      </div>
    </div>

    <div class="card-body" :class="{ 'has-image': news.image_url }">
      <div class="card-meta">
        <span class="meta-category">{{ categoryLabel }}</span>
        <span class="meta-divider">·</span>
        <span class="meta-time">{{ formatTime(news.published_at) }}</span>
      </div>

      <h3 class="card-title">{{ news.title }}</h3>

      <p class="card-summary">{{ news.summary }}</p>

      <div class="card-footer">
        <el-button link type="primary" class="read-btn" @click.stop="onReadDetail">
          阅读全文
          <el-icon><ArrowRight /></el-icon>
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowRight } from '@element-plus/icons-vue'

const props = defineProps({
  news: {
    type: Object,
    required: true,
    default: () => ({
      id: 0,
      title: '',
      summary: '',
      image_url: '',
      source: '',
      source_url: '',
      category: '',
      published_at: ''
    })
  }
})

const router = useRouter()

const categoryLabel = computed(() => {
  const map = {
    tech: '科技',
    finance: '财经',
    sports: '体育',
    entertainment: '娱乐',
    domestic: '国内',
    international: '国际'
  }
  return map[props.news.category] || props.news.category || '综合'
})

function onOpenUrl() {
  if (props.news.source_url) {
    window.open(props.news.source_url, '_blank')
  }
}

function onReadDetail() {
  router.push(`/player/${props.news.id}`)
}

function formatTime(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const now = new Date()
  const diff = now - d
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}
</script>

<style scoped>
.news-card {
  display: flex;
  flex-direction: row;
  margin-bottom: 16px;
  border-radius: 14px !important;
  overflow: hidden;
  cursor: pointer;
  padding: 0;
  background: rgba(30, 32, 42, 0.85) !important;
  transition: all 0.3s ease;
}

.news-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.15);
  background: rgba(40, 43, 56, 0.9) !important;
}

.card-image {
  flex: 0 0 200px;
  width: 200px;
  height: 140px;
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, #1a1a2e, #2d2d44);
}

.card-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.image-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 6px 12px;
  background: linear-gradient(transparent, rgba(0,0,0,0.7));
}

.source-badge {
  font-size: 0.72rem;
  color: #fff;
  opacity: 0.9;
}

.card-body {
  flex: 1;
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-width: 0;
}

.card-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}

.meta-category {
  font-size: 0.75rem;
  color: #667eea;
  font-weight: 600;
}

.meta-divider {
  color: #555;
  font-size: 0.75rem;
}

.meta-time {
  font-size: 0.72rem;
  color: #808090;
}

.card-title {
  font-size: 1.02rem;
  font-weight: 600;
  color: #e8e8f0;
  line-height: 1.5;
  margin: 0 0 8px 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-summary {
  font-size: 0.83rem;
  color: #9090a0;
  line-height: 1.55;
  margin: 0 0 10px 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.read-btn {
  font-size: 0.8rem;
  color: #667eea !important;
  padding: 0;
}

/* 无图样式 */
.news-card:not(:has(.card-image)) {
  border-left: 3px solid #667eea;
}

/* 响应式 */
@media (max-width: 640px) {
  .news-card {
    flex-direction: column;
  }
  .card-image {
    flex: 0 0 auto;
    width: 100%;
    height: 180px;
  }
  .card-body {
    padding: 14px 16px;
  }
}
</style>
