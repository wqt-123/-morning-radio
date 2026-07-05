<template>
  <div class="player-page">
    <!-- 返回 -->
    <div class="back-bar">
      <el-button link @click="$router.back()" class="back-btn">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>
      <span class="back-title">{{ broadcast?.title || '早安播报' }}</span>
    </div>

    <div v-if="loading" class="loading-area">
      <el-skeleton animated>
        <template #template>
          <el-skeleton-item variant="image" style="width:100%;height:300px;border-radius:16px" />
          <el-skeleton-item variant="text" style="width:70%;height:24px;margin-top:24px" />
          <el-skeleton-item variant="text" style="width:100%;height:100px;margin-top:16px" />
        </template>
      </el-skeleton>
    </div>

    <template v-else-if="broadcast">
      <!-- 视频区域 -->
      <div class="media-area" v-if="broadcast.video_url">
        <div class="video-container">
          <video
            :src="broadcast.video_url"
            controls
            class="video-player"
            playsinline
          ></video>
        </div>
        <!-- 下载按钮组 -->
        <div class="download-bar glass-card">
          <span class="dl-label">下载节目：</span>
          <a :href="broadcast.video_url" download class="dl-btn video-dl">
            <el-icon><VideoCamera /></el-icon> 视频 ({{ fileSize }})
          </a>
          <a v-if="broadcast.audio_url" :href="broadcast.audio_url" download class="dl-btn audio-dl">
            <el-icon><Headset /></el-icon> 音频
          </a>
          <a v-if="broadcast.broadcast_text" :href="textBlobUrl" :download="textFilename" class="dl-btn text-dl">
            <el-icon><Document /></el-icon> 文稿
          </a>
        </div>
      </div>

      <!-- 纯音频模式 -->
      <div v-else class="media-area">
        <div class="audio-visualizer glass-card">
          <div class="visualizer-content">
            <div class="visualizer-ring pulse-glow">
              <el-icon :size="64" color="#667eea"><Headset /></el-icon>
            </div>
            <p class="visualizer-hint">纯音频模式</p>
          </div>
          <div class="download-bar glass-card" style="margin-top:16px;background:transparent">
            <a v-if="broadcast.audio_url" :href="broadcast.audio_url" download class="dl-btn audio-dl">
              <el-icon><Headset /></el-icon> 下载音频
            </a>
            <a v-if="broadcast.broadcast_text" :href="textBlobUrl" :download="textFilename" class="dl-btn text-dl">
              <el-icon><Document /></el-icon> 下载文稿
            </a>
          </div>
        </div>
      </div>

      <!-- 音频播放器 -->
      <div class="audio-section">
        <AudioPlayer
          :audio-url="audioUrl"
          :title="broadcast.title || '早安播报'"
        />
      </div>

      <!-- 播报文稿 -->
      <div class="script-section glass-card">
        <h3 class="script-title">
          <el-icon><Document /></el-icon>
          播报文稿
        </h3>
        <div class="script-content" ref="scriptContent">
          <p v-for="(para, idx) in paragraphs" :key="idx" class="script-para">
            {{ para }}
          </p>
        </div>
      </div>

      <!-- 播报信息 -->
      <div class="info-section glass-card">
        <div class="info-grid">
          <div class="info-item">
            <span class="info-label">日期</span>
            <span class="info-value">{{ formatDate(broadcast.generated_at) }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">时长</span>
            <span class="info-value">{{ formatDuration(broadcast.duration) }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">状态</span>
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

    <el-empty v-else description="播报不存在或已被删除" :image-size="120" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowLeft, Headset, Document, VideoCamera } from '@element-plus/icons-vue'
import { radioApi } from '@/api'
import AudioPlayer from '@/components/AudioPlayer.vue'

const route = useRoute()
const broadcast = ref(null)
const loading = ref(true)

const audioUrl = computed(() => {
  if (!broadcast.value?.audio_url) return ''
  return broadcast.value.audio_url
})

const paragraphs = computed(() => {
  if (!broadcast.value?.broadcast_text) return []
  return broadcast.value.broadcast_text.split('\n').filter(p => p.trim())
})

const fileSize = computed(() => {
  if (broadcast.value?.duration) {
    const mb = Math.round(broadcast.value.duration * 0.12)
    return mb > 1 ? `${mb}MB` : '< 1MB'
  }
  return '下载'
})

const textFilename = computed(() => {
  const d = broadcast.value?.generated_at
  const date = d ? new Date(d).toISOString().slice(0, 10) : 'today'
  return `早安播报_${date}.txt`
})

const textBlobUrl = ref('')

function buildTextBlob() {
  if (!broadcast.value?.broadcast_text) return
  const blob = new Blob([broadcast.value.broadcast_text], { type: 'text/plain;charset=utf-8' })
  if (textBlobUrl.value) URL.revokeObjectURL(textBlobUrl.value)
  textBlobUrl.value = URL.createObjectURL(blob)
}

function formatDate(dateStr) {
  if (!dateStr) return '--'
  const d = new Date(dateStr)
  const days = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  return `${d.getFullYear()}/${d.getMonth() + 1}/${d.getDate()} ${days[d.getDay()]}`
}

function formatDuration(seconds) {
  if (!seconds) return '--:--'
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}分${s}秒`
}

onMounted(async () => {
  try {
    const res = await radioApi.getToday()
    broadcast.value = res
    buildTextBlob()
  } catch {
    broadcast.value = null
  } finally {
    loading.value = false
  }
})

onUnmounted(() => {
  if (textBlobUrl.value) URL.revokeObjectURL(textBlobUrl.value)
})
</script>

<style scoped>
.player-page {
  padding-top: 24px;
  padding-bottom: 40px;
  max-width: 800px;
  margin: 0 auto;
}

.back-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.back-btn {
  color: #9090a8 !important;
  font-size: 0.9rem;
}
.back-btn:hover { color: #667eea !important; }
.back-title {
  font-size: 1rem;
  font-weight: 600;
  color: #c0c0d0;
}

.media-area { margin-bottom: 24px; }

.video-container {
  border-radius: 16px;
  overflow: hidden;
  background: #000;
}
.video-player {
  width: 100%;
  display: block;
  max-height: 480px;
  border-radius: 16px;
}

/* 下载栏 */
.download-bar {
  margin-top: 12px;
  padding: 14px 20px;
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  border-radius: 12px !important;
}
.dl-label {
  font-size: 0.85rem;
  color: #b0b0c0;
  white-space: nowrap;
}
.dl-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 0.82rem;
  font-weight: 500;
  text-decoration: none;
  transition: all 0.2s ease;
  cursor: pointer;
}
.video-dl {
  background: linear-gradient(135deg, #ff6b6b, #ee5a24);
  color: #fff;
}
.video-dl:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(238, 90, 36, 0.3);
}
.audio-dl {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
}
.audio-dl:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}
.text-dl {
  background: rgba(255,255,255,0.08);
  color: #c0c0d0;
  border: 1px solid rgba(255,255,255,0.12);
}
.text-dl:hover {
  background: rgba(255,255,255,0.15);
  color: #fff;
}

.audio-visualizer {
  padding: 60px 20px;
  text-align: center;
}
.visualizer-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}
.visualizer-ring {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(102,126,234,0.15), rgba(118,75,162,0.15));
  border: 2px solid rgba(102,126,234,0.3);
  display: flex;
  align-items: center;
  justify-content: center;
}
.visualizer-hint { color: #707088; font-size: 0.85rem; }

.audio-section { margin-bottom: 24px; }

.script-section {
  padding: 24px;
  margin-bottom: 20px;
}
.script-title {
  font-size: 1.05rem;
  font-weight: 600;
  color: #e0e0e0;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.script-content {
  max-height: 400px;
  overflow-y: auto;
  padding-right: 8px;
}
.script-content::-webkit-scrollbar { width: 4px; }
.script-content::-webkit-scrollbar-thumb { background: rgba(102,126,234,0.3); border-radius: 2px; }

.script-para {
  font-size: 0.92rem;
  color: #b0b0c0;
  line-height: 1.85;
  margin-bottom: 12px;
  text-indent: 2em;
}

.info-section { padding: 20px 24px; margin-bottom: 20px; }
.info-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.info-item { text-align: center; }
.info-label { display: block; font-size: 0.75rem; color: #707080; margin-bottom: 4px; }
.info-value { font-size: 0.92rem; color: #c0c0d0; font-weight: 500; }
.loading-area { padding-top: 20px; }

@media (max-width: 768px) {
  .info-grid { grid-template-columns: 1fr; gap: 12px; }
  .video-player { max-height: 250px; }
  .script-content { max-height: 300px; }
  .download-bar { flex-direction: column; align-items: flex-start; }
}
</style>
