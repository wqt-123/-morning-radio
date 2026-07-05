<template>
  <div class="news-list-page">
    <div class="page-header">
      <h1 class="page-title">新闻资讯</h1>
      <el-button type="primary" size="small" @click="fetchNews" :loading="loading" round>
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
    </div>

    <!-- 分类标签 + 搜索 -->
    <div class="toolbar glass-card">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索新闻标题..."
        clearable
        class="search-input"
        @input="onSearch"
        @clear="onSearch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <div class="category-tabs">
        <span
          v-for="cat in categoryOptions"
          :key="cat.value"
          class="cat-chip"
          :class="{ active: activeCategory === cat.value }"
          @click="activeCategory = cat.value; fetchNews()"
        >
          {{ cat.label }}
          <small v-if="cat.count > 0">({{ cat.count }})</small>
        </span>
      </div>
    </div>

    <!-- 骨架屏 -->
    <div v-if="loading" class="skeleton-area">
      <el-skeleton v-for="i in 6" :key="i" animated style="margin-bottom:16px">
        <template #template>
          <div style="display:flex;gap:16px">
            <el-skeleton-item variant="image" style="width:200px;height:140px;border-radius:12px" />
            <div style="flex:1">
              <el-skeleton-item variant="text" style="width:80%;height:20px" />
              <el-skeleton-item variant="text" style="width:100%;height:14px;margin-top:8px" />
              <el-skeleton-item variant="text" style="width:60%;height:14px;margin-top:6px" />
            </div>
          </div>
        </template>
      </el-skeleton>
    </div>

    <el-empty v-else-if="filteredNews.length === 0" description="没有找到相关新闻">
      <template #image>
        <el-icon :size="80" color="#667eea"><Document /></el-icon>
      </template>
    </el-empty>

    <template v-else>
      <div class="news-grid">
        <NewsCard
          v-for="(news, idx) in filteredNews"
          :key="news.id"
          :news="news"
          :class="`fade-in-up fade-in-up-delay-${Math.min((idx % 4) + 1, 4)}`"
        />
      </div>

      <!-- 分页 -->
      <div class="pagination-wrap" v-if="total > pageSize">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="total"
          layout="prev, pager, next"
          @current-change="onPageChange"
          background
        />
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Search, Document, Refresh } from '@element-plus/icons-vue'
import { newsApi } from '@/api'
import NewsCard from '@/components/NewsCard.vue'

const allNews = ref([])
const loading = ref(false)
const activeCategory = ref('all')
const searchKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(12)

const categoryMap = { tech: '科技', finance: '财经', sports: '体育', entertainment: '娱乐', domestic: '国内', international: '国际' }

const categoryOptions = [
  { value: 'all', label: '推荐', count: computed(() => allNews.value.length) },
  { value: 'tech', label: '科技', count: computed(() => allNews.value.filter(n => n.category === 'tech').length) },
  { value: 'finance', label: '财经', count: computed(() => allNews.value.filter(n => n.category === 'finance').length) },
  { value: 'domestic', label: '国内', count: computed(() => allNews.value.filter(n => n.category === 'domestic').length) },
  { value: 'international', label: '国际', count: computed(() => allNews.value.filter(n => n.category === 'international').length) },
  { value: 'sports', label: '体育', count: computed(() => allNews.value.filter(n => n.category === 'sports').length) },
  { value: 'entertainment', label: '娱乐', count: computed(() => allNews.value.filter(n => n.category === 'entertainment').length) },
]

const filteredNews = computed(() => {
  let list = allNews.value
  if (activeCategory.value !== 'all') {
    list = list.filter(n => n.category === activeCategory.value)
  }
  if (searchKeyword.value.trim()) {
    const kw = searchKeyword.value.trim().toLowerCase()
    list = list.filter(n => n.title?.toLowerCase().includes(kw) || n.summary?.toLowerCase().includes(kw))
  }
  const start = (currentPage.value - 1) * pageSize.value
  return list.slice(start, start + pageSize.value)
})

const total = computed(() => {
  let list = allNews.value
  if (activeCategory.value !== 'all') list = list.filter(n => n.category === activeCategory.value)
  if (searchKeyword.value.trim()) {
    const kw = searchKeyword.value.trim().toLowerCase()
    list = list.filter(n => n.title?.toLowerCase().includes(kw) || n.summary?.toLowerCase().includes(kw))
  }
  return list.length
})

let searchTimer = null
function onSearch() {
  currentPage.value = 1
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {}, 0)
}

function onPageChange() {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

async function fetchNews() {
  loading.value = true
  currentPage.value = 1
  try {
    const params = {}
    if (activeCategory.value !== 'all') {
      params.category = activeCategory.value
    }
    const res = await newsApi.getToday(params)
    allNews.value = res?.items || (Array.isArray(res) ? res : [])
  } catch {
    allNews.value = []
  } finally {
    loading.value = false
  }
}

onMounted(fetchNews)
</script>

<style scoped>
.news-list-page {
  padding-top: 24px;
  padding-bottom: 40px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.page-title {
  font-size: 1.3rem;
  font-weight: 700;
  color: #e8e8f0;
  margin: 0;
}

.toolbar {
  padding: 16px 20px;
  margin-bottom: 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  border-radius: 12px !important;
}

.search-input {
  max-width: 360px;
}

.category-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.cat-chip {
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 0.82rem;
  color: #9090a8;
  background: rgba(255,255,255,0.04);
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
  border: 1px solid transparent;
}
.cat-chip:hover {
  color: #c0c0d8;
  background: rgba(255,255,255,0.08);
}
.cat-chip.active {
  color: #fff;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-color: transparent;
  font-weight: 500;
}
.cat-chip small {
  font-size: 0.7rem;
  opacity: 0.8;
}

.skeleton-area {
  padding: 0 4px;
}

.news-grid {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.pagination-wrap {
  display: flex;
  justify-content: center;
  margin-top: 32px;
}
</style>
