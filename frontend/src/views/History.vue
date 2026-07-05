<template>
  <div class="history-page">
    <h1 class="page-title">历史播报</h1>

    <div v-if="loading" class="skeleton-area">
      <el-skeleton v-for="i in 4" :key="i" animated style="margin-bottom: 16px;">
        <template #template>
          <el-skeleton-item variant="image" style="width: 100%; height: 120px; border-radius: 12px;" />
        </template>
      </el-skeleton>
    </div>

    <el-empty v-else-if="historyList.length === 0" description="还没有历史播报记录">
      <template #image>
        <el-icon :size="80" color="#667eea"><Clock /></el-icon>
      </template>
    </el-empty>

    <template v-else>
      <div
        v-for="(item, idx) in historyList"
        :key="item.id"
        class="history-item glass-card"
        :class="`fade-in-up fade-in-up-delay-${Math.min((idx % 4) + 1, 4)}`"
        @click="goToPlayer(item.id)"
      >
        <div class="item-left">
          <div class="item-date">
            <span class="date-day">{{ getDay(item.generated_at) }}</span>
            <span class="date-month">{{ getMonth(item.generated_at) }}</span>
          </div>
        </div>
        <div class="item-body">
          <h3 class="item-title">{{ item.title || '早安播报' }}</h3>
          <p class="item-meta">
            <el-icon :size="14"><Timer /></el-icon>
            {{ formatDuration(item.duration) }}
            <span class="meta-divider">|</span>
            {{ formatWeekday(item.generated_at) }}
          </p>
        </div>
        <div class="item-right">
          <el-tag
            :type="item.status === 'completed' ? 'success' : 'warning'"
            size="small"
            effect="dark"
          >
            {{ item.status === 'completed' ? '已完成' : '生成中' }}
          </el-tag>
          <el-icon class="play-icon" :size="20"><VideoPlay /></el-icon>
        </div>
      </div>

      <!-- 分页 -->
      <div class="pagination-wrap" v-if="total > pageSize">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="total"
          layout="prev, pager, next"
          @current-change="fetchHistory"
          background
        />
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Clock, Timer, VideoPlay } from '@element-plus/icons-vue'
import { radioApi } from '@/api'

const router = useRouter()
const historyList = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

function getDay(dateStr) {
  if (!dateStr) return '--'
  return String(new Date(dateStr).getDate()).padStart(2, '0')
}

function getMonth(dateStr) {
  if (!dateStr) return '--'
  return `${new Date(dateStr).getMonth() + 1}月`
}

function formatWeekday(dateStr) {
  if (!dateStr) return ''
  const days = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  return days[new Date(dateStr).getDay()]
}

function formatDuration(seconds) {
  if (!seconds) return '--:--'
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}分${s}秒`
}

function goToPlayer(id) {
  router.push(`/player/${id}`)
}

async function fetchHistory() {
  loading.value = true
  try {
    const res = await radioApi.getHistory({
      page: currentPage.value,
      page_size: pageSize.value
    })
    historyList.value = res?.items || (Array.isArray(res) ? res : [])
    total.value = res?.total || historyList.value.length
  } catch {
    historyList.value = []
  } finally {
    loading.value = false
  }
}

onMounted(fetchHistory)
</script>

<style scoped>
.history-page {
  padding-top: 24px;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  margin-bottom: 12px;
  cursor: pointer;
  border-radius: 14px !important;
}

.item-left {
  flex-shrink: 0;
}

.item-date {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.date-day {
  font-size: 1.3rem;
  font-weight: 700;
  line-height: 1;
}

.date-month {
  font-size: 0.7rem;
  opacity: 0.85;
  margin-top: 2px;
}

.item-body {
  flex: 1;
  min-width: 0;
}

.item-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: #e0e0e0;
  margin-bottom: 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-meta {
  font-size: 0.78rem;
  color: #808090;
  display: flex;
  align-items: center;
  gap: 4px;
}

.meta-divider {
  color: rgba(255, 255, 255, 0.1);
  margin: 0 4px;
}

.item-right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.play-icon {
  color: #667eea;
  opacity: 0;
  transition: opacity 0.2s;
}

.history-item:hover .play-icon {
  opacity: 1;
}

.skeleton-area {
  padding: 0 4px;
}

.pagination-wrap {
  display: flex;
  justify-content: center;
  margin-top: 32px;
}

@media (max-width: 768px) {
  .history-item {
    gap: 12px;
    padding: 14px 16px;
  }

  .item-date {
    width: 48px;
    height: 48px;
  }

  .date-day {
    font-size: 1.1rem;
  }
}
</style>
