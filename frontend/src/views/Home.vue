<template>
  <div class="home-page">
    <!-- 日期与问候 -->
    <div class="greeting-section fade-in-up">
      <h1 class="greeting-title">
        <span class="gradient-text">{{ greeting }}</span>
      </h1>
      <p class="greeting-date">{{ todayStr }}</p>
    </div>

    <!-- 今日播报卡片 + 生成按钮 -->
    <div class="broadcast-section fade-in-up fade-in-up-delay-1">
      <div v-if="loading.todayBroadcast" class="skeleton-area">
        <el-skeleton animated>
          <template #template>
            <el-skeleton-item variant="image" style="width: 100%; height: 200px; border-radius: 16px;" />
          </template>
        </el-skeleton>
      </div>

      <el-empty
        v-else-if="!todayBroadcast"
        description="今日播报还未生成"
        :image-size="120"
      >
        <template #image>
          <el-icon :size="80" color="#667eea"><Headset /></el-icon>
        </template>
        <el-button class="btn-gradient" @click="handleGenerate" :loading="loading.generating">
          <el-icon><MagicStick /></el-icon>
          生成今日播报
        </el-button>
      </el-empty>

      <template v-else>
        <div class="broadcast-grid">
          <BroadcastCard
            :broadcast="todayBroadcast"
            class="fade-in-up fade-in-up-delay-1"
            @click="goToPlayer(todayBroadcast.id)"
          />
          <div class="broadcast-actions">
            <el-button class="btn-gradient" @click="goToPlayer(todayBroadcast.id)">
              <el-icon><VideoPlay /></el-icon>
              立即收听
            </el-button>
            <el-button class="btn-outline" @click="handleGenerate" :loading="loading.generating">
              <el-icon><Refresh /></el-icon>
              重新生成
            </el-button>
          </div>
        </div>
      </template>
    </div>

    <!-- 内嵌播放器 -->
    <div v-if="todayBroadcast?.audio_url" class="player-section fade-in-up fade-in-up-delay-2">
      <AudioPlayer
        :audio-url="todayBroadcast.audio_url"
        :title="todayBroadcast.title"
      />
    </div>

    <!-- 新闻列表 -->
    <div class="news-section fade-in-up fade-in-up-delay-3">
      <div class="section-header">
        <h2 class="section-title">今日要闻</h2>
        <CategoryTabs
          :categories="categoryOptions"
          v-model="activeCategory"
          @update:model-value="onCategoryChange"
        />
      </div>

      <div v-if="loading.news" class="skeleton-area">
        <el-skeleton v-for="i in 4" :key="i" animated style="margin-bottom: 12px;">
          <template #template>
            <el-skeleton-item variant="text" style="width: 60%; height: 20px;" />
            <el-skeleton-item variant="text" style="width: 100%; height: 14px; margin-top: 8px;" />
            <el-skeleton-item variant="text" style="width: 80%; height: 14px;" />
          </template>
        </el-skeleton>
      </div>

      <el-empty v-else-if="newsList.length === 0" description="暂无新闻" />

      <template v-else>
        <NewsCard
          v-for="(news, idx) in newsList"
          :key="news.id"
          :news="news"
          :class="`fade-in-up fade-in-up-delay-${Math.min(idx + 1, 4)}`"
        />
      </template>

      <div v-if="newsList.length > 0" class="view-all">
        <el-button link type="primary" @click="$router.push('/news')">
          查看全部新闻
          <el-icon><ArrowRight /></el-icon>
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Headset, MagicStick, VideoPlay, Refresh, ArrowRight } from '@element-plus/icons-vue'
import { newsApi, radioApi } from '@/api'
import AudioPlayer from '@/components/AudioPlayer.vue'
import BroadcastCard from '@/components/BroadcastCard.vue'
import NewsCard from '@/components/NewsCard.vue'
import CategoryTabs from '@/components/CategoryTabs.vue'
import { ElMessage } from 'element-plus'

const router = useRouter()

const todayBroadcast = ref(null)
const newsList = ref([])
const activeCategory = ref('all')

const loading = reactive({
  todayBroadcast: true,
  news: true,
  generating: false
})

const categoryOptions = [
  { value: 'all', label: '全部' },
  { value: '科技', label: '科技' },
  { value: '财经', label: '财经' },
  { value: '体育', label: '体育' },
  { value: '娱乐', label: '娱乐' },
  { value: '国内', label: '国内' },
  { value: '国际', label: '国际' }
]

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 6) return '凌晨好'
  if (h < 9) return '早上好'
  if (h < 12) return '上午好'
  if (h < 14) return '中午好'
  if (h < 18) return '下午好'
  return '晚上好'
})

const todayStr = computed(() => {
  const d = new Date()
  const days = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六']
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日 ${days[d.getDay()]}`
})


async function fetchTodayBroadcast() {
  loading.todayBroadcast = true
  try {
    const res = await radioApi.getToday()
    todayBroadcast.value = res
  } catch {
    todayBroadcast.value = null
  } finally {
    loading.todayBroadcast = false
  }
}

async function fetchNews() {
  loading.news = true
  try {
    const params = {}
    if (activeCategory.value !== 'all') {
      params.category = activeCategory.value
    }
    const res = await newsApi.getToday(params)
    newsList.value = res?.items || res?.data?.items || (Array.isArray(res) ? res : [])
  } catch {
    newsList.value = []
  } finally {
    loading.news = false
  }
}

function onCategoryChange() {
  fetchNews()
}

async function handleGenerate() {
  loading.generating = true
  try {
    ElMessage.info('正在生成今日播报，请稍候...')
    const res = await radioApi.generate()
    ElMessage.success('播报生成成功')
    await fetchTodayBroadcast()
  } catch (err) {
    ElMessage.error('播报生成失败: ' + (err.response?.data?.detail || err.message))
  } finally {
    loading.generating = false
  }
}

function goToPlayer(id) {
  router.push(`/player/${id}`)
}

onMounted(() => {
  fetchTodayBroadcast()
  fetchNews()
})
</script>

<style scoped>
.home-page {
  padding-top: 24px;
}

.greeting-section {
  text-align: center;
  margin-bottom: 32px;
}

.greeting-title {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 8px;
}

.greeting-date {
  font-size: 0.95rem;
  color: #808098;
  font-weight: 400;
}

.broadcast-section {
  margin-bottom: 28px;
}

.broadcast-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;
  max-width: 480px;
  margin: 0 auto;
}

.broadcast-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.btn-outline {
  background: transparent !important;
  border: 1px solid rgba(102, 126, 234, 0.4) !important;
  color: #667eea !important;
}

.btn-outline:hover {
  background: rgba(102, 126, 234, 0.1) !important;
  border-color: #667eea !important;
}

.player-section {
  margin-bottom: 32px;
}

.news-section {
  margin-bottom: 40px;
}

.section-header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}

.section-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #e0e0e0;
}

.skeleton-area {
  padding: 0 4px;
}

.view-all {
  text-align: center;
  margin-top: 16px;
}

@media (max-width: 768px) {
  .greeting-title {
    font-size: 1.5rem;
  }

  .broadcast-actions {
    flex-direction: column;
  }
}
</style>
