<template>
  <div class="broadcast-card glass-card" @click="$emit('click')">
    <div class="card-cover">
      <div class="cover-gradient">
        <span class="cover-date">{{ formatDate(broadcast.generated_at) }}</span>
        <span class="cover-weekday">{{ formatWeekday(broadcast.generated_at) }}</span>
        <el-icon class="cover-icon" :size="40"><VideoPlay /></el-icon>
      </div>
    </div>
    <div class="card-body">
      <h3 class="card-title">{{ broadcast.title || '早安播报' }}</h3>
      <div class="card-info">
        <span class="info-item">
          <el-icon :size="14"><Clock /></el-icon>
          {{ formatDuration(broadcast.duration) }}
        </span>
        <el-tag
          :type="broadcast.status === 'completed' ? 'success' : 'warning'"
          size="small"
          effect="dark"
        >
          {{ broadcast.status === 'completed' ? '已完成' : '生成中' }}
        </el-tag>
      </div>
    </div>
  </div>
</template>

<script setup>
import { VideoPlay, Clock } from '@element-plus/icons-vue'

const props = defineProps({
  broadcast: {
    type: Object,
    required: true,
    default: () => ({
      id: 0,
      title: '',
      duration: 0,
      status: 'completed',
      generated_at: ''
    })
  }
})

defineEmits(['click'])

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日`
}

function formatWeekday(dateStr) {
  if (!dateStr) return ''
  const days = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六']
  return days[new Date(dateStr).getDay()]
}

function formatDuration(seconds) {
  if (!seconds) return '--:--'
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${String(s).padStart(2, '0')}`
}
</script>

<style scoped>
.broadcast-card {
  border-radius: 16px !important;
  overflow: hidden;
  cursor: pointer;
  padding: 0 !important;
}

.card-cover {
  height: 180px;
  position: relative;
  overflow: hidden;
}

.cover-gradient {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #e040fb 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  position: relative;
}

.cover-gradient::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 30% 50%, rgba(255,255,255,0.1) 0%, transparent 60%);
}

.cover-date {
  font-size: 1.1rem;
  font-weight: 600;
  color: #fff;
  position: relative;
  z-index: 1;
}

.cover-weekday {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.8);
  position: relative;
  z-index: 1;
}

.cover-icon {
  color: rgba(255, 255, 255, 0.9);
  position: relative;
  z-index: 1;
  margin-top: 4px;
  filter: drop-shadow(0 2px 8px rgba(0,0,0,0.3));
}

.card-body {
  padding: 16px 18px;
}

.card-title {
  font-size: 1rem;
  font-weight: 600;
  color: #e0e0e0;
  margin-bottom: 10px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.82rem;
  color: #808090;
}
</style>
