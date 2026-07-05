<template>
  <div class="audio-player" :class="{ mini: isMini, expanded: !isMini }">
    <div class="player-inner">
      <!-- 迷你模式 -->
      <template v-if="isMini">
        <button class="control-btn" @click="togglePlay">
          <el-icon :size="20">
            <VideoPause v-if="isPlaying" />
            <VideoPlay v-else />
          </el-icon>
        </button>
        <div class="mini-info">
          <span class="mini-title">{{ title || '早安播报' }}</span>
          <span class="mini-time">{{ currentTimeStr }} / {{ durationStr }}</span>
        </div>
        <button class="control-btn small" @click="isMini = false">
          <el-icon :size="16"><FullScreen /></el-icon>
        </button>
      </template>

      <!-- 展开模式 -->
      <template v-else>
        <div class="expanded-header">
          <h4 class="player-title">{{ title || '早安播报' }}</h4>
          <button class="control-btn small" @click="isMini = true">
            <el-icon :size="16"><Minus /></el-icon>
          </button>
        </div>

        <!-- 进度条 -->
        <div class="progress-bar" ref="progressBar" @click="seekAudio">
          <div class="progress-track">
            <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
            <div
              class="progress-thumb"
              :style="{ left: progressPercent + '%' }"
              @mousedown.prevent="startDrag"
            ></div>
          </div>
        </div>

        <div class="time-display">
          <span>{{ currentTimeStr }}</span>
          <span>{{ durationStr }}</span>
        </div>

        <!-- 控制按钮 -->
        <div class="controls-row">
          <button class="control-btn" @click="skipTime(-15)" title="后退15秒">
            <el-icon :size="18"><DArrowLeft /></el-icon>
          </button>
          <button class="control-btn play-btn pulse-glow" @click="togglePlay">
            <el-icon :size="28">
              <VideoPause v-if="isPlaying" />
              <VideoPlay v-else />
            </el-icon>
          </button>
          <button class="control-btn" @click="skipTime(15)" title="前进15秒">
            <el-icon :size="18"><DArrowRight /></el-icon>
          </button>
        </div>

        <!-- 音量控制 -->
        <div class="volume-row">
          <el-icon :size="16" class="volume-icon" @click="toggleMute">
            <Mute v-if="isMuted || volume === 0" />
            <Microphone v-else />
          </el-icon>
          <el-slider
            v-model="volume"
            :min="0"
            :max="100"
            class="volume-slider"
            @input="setVolume"
          />
          <span class="speed-label" @click="cycleSpeed">{{ playbackRate }}x</span>
        </div>
      </template>
    </div>

    <!-- 隐藏的 audio 元素 -->
    <audio
      ref="audioRef"
      :src="audioUrl"
      @timeupdate="onTimeUpdate"
      @loadedmetadata="onLoadedMetadata"
      @ended="onEnded"
      @error="onError"
      preload="metadata"
    ></audio>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { VideoPlay, VideoPause, FullScreen, Minus, DArrowLeft, DArrowRight, Mute, Microphone } from '@element-plus/icons-vue'

const props = defineProps({
  audioUrl: { type: String, default: '' },
  title: { type: String, default: '' }
})

const audioRef = ref(null)
const isPlaying = ref(false)
const isMini = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const volume = ref(80)
const isMuted = ref(false)
const playbackRate = ref(1)
const isDragging = ref(false)
const progressBar = ref(null)

const currentTimeStr = computed(() => formatTime(currentTime.value))
const durationStr = computed(() => formatTime(duration.value))
const progressPercent = computed(() => {
  if (duration.value === 0) return 0
  return (currentTime.value / duration.value) * 100
})

function formatTime(sec) {
  if (!sec || isNaN(sec)) return '00:00'
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

function togglePlay() {
  const audio = audioRef.value
  if (!audio) return
  if (isPlaying.value) {
    audio.pause()
  } else {
    audio.play().catch(() => {})
  }
}

function skipTime(seconds) {
  const audio = audioRef.value
  if (!audio) return
  audio.currentTime = Math.max(0, Math.min(audio.duration, audio.currentTime + seconds))
}

function setVolume() {
  const audio = audioRef.value
  if (!audio) return
  audio.volume = volume.value / 100
  isMuted.value = volume.value === 0
}

function toggleMute() {
  const audio = audioRef.value
  if (!audio) return
  if (isMuted.value) {
    volume.value = volume.value || 60
    audio.volume = volume.value / 100
    isMuted.value = false
  } else {
    audio.volume = 0
    isMuted.value = true
  }
}

function cycleSpeed() {
  const rates = [0.75, 1, 1.25, 1.5, 2]
  const idx = rates.indexOf(playbackRate.value)
  playbackRate.value = rates[(idx + 1) % rates.length]
  if (audioRef.value) {
    audioRef.value.playbackRate = playbackRate.value
  }
}

function seekAudio(e) {
  const rect = e.currentTarget.getBoundingClientRect()
  const ratio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width))
  const audio = audioRef.value
  if (!audio) return
  audio.currentTime = ratio * duration.value
}

function startDrag(e) {
  isDragging.value = true
  const onMove = (ev) => {
    if (!isDragging.value || !progressBar.value) return
    const rect = progressBar.value.getBoundingClientRect()
    const ratio = Math.max(0, Math.min(1, (ev.clientX - rect.left) / rect.width))
    if (audioRef.value) {
      audioRef.value.currentTime = ratio * duration.value
    }
  }
  const onUp = () => {
    isDragging.value = false
    document.removeEventListener('mousemove', onMove)
    document.removeEventListener('mouseup', onUp)
  }
  document.addEventListener('mousemove', onMove)
  document.addEventListener('mouseup', onUp)
}

function onTimeUpdate() {
  if (!audioRef.value || isDragging.value) return
  currentTime.value = audioRef.value.currentTime
}

function onLoadedMetadata() {
  if (!audioRef.value) return
  duration.value = audioRef.value.duration
  audioRef.value.volume = volume.value / 100
}

function onEnded() {
  isPlaying.value = false
  currentTime.value = 0
}

function onError() {
  isPlaying.value = false
}

watch(isPlaying, (val) => {
  if (val) {
    document.title = `正在播放: ${props.title || '早安播报'}`
  } else {
    document.title = '早安电台 - AI每日新闻'
  }
})

watch(() => props.audioUrl, () => {
  currentTime.value = 0
  duration.value = 0
  isPlaying.value = false
})

onMounted(() => {
  const audio = audioRef.value
  if (!audio) return
  audio.addEventListener('play', () => { isPlaying.value = true })
  audio.addEventListener('pause', () => { isPlaying.value = false })
})

onBeforeUnmount(() => {
  if (audioRef.value) {
    audioRef.value.pause()
    audioRef.value.src = ''
  }
})
</script>

<style scoped>
.audio-player {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  transition: all 0.3s ease;
}

.player-inner {
  padding: 14px 18px;
}

/* 迷你模式 */
.audio-player.mini .player-inner {
  display: flex;
  align-items: center;
  gap: 12px;
}

.mini-info {
  flex: 1;
  min-width: 0;
}

.mini-title {
  display: block;
  font-size: 0.85rem;
  font-weight: 600;
  color: #e0e0e0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.mini-time {
  font-size: 0.72rem;
  color: #707080;
}

/* 展开模式 */
.expanded-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}

.player-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: #e0e0e0;
}

/* 进度条 */
.progress-bar {
  width: 100%;
  cursor: pointer;
  padding: 6px 0;
}

.progress-track {
  position: relative;
  width: 100%;
  height: 5px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
  overflow: visible;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2);
  border-radius: 3px;
  transition: width 0.1s linear;
}

.progress-thumb {
  position: absolute;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 14px;
  height: 14px;
  background: #fff;
  border-radius: 50%;
  box-shadow: 0 1px 6px rgba(0, 0, 0, 0.3);
  opacity: 0;
  transition: opacity 0.2s;
}

.progress-bar:hover .progress-thumb {
  opacity: 1;
}

.time-display {
  display: flex;
  justify-content: space-between;
  font-size: 0.72rem;
  color: #707080;
  margin-top: 4px;
  margin-bottom: 12px;
}

/* 控制按钮 */
.controls-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
  margin-bottom: 12px;
}

.control-btn {
  background: none;
  border: none;
  color: #c0c0d0;
  cursor: pointer;
  padding: 6px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.control-btn:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.08);
}

.control-btn.small {
  padding: 4px;
}

.play-btn {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #667eea, #764ba2) !important;
  color: #fff !important;
  border-radius: 50% !important;
}

.play-btn:hover {
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.5);
}

/* 音量 */
.volume-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.volume-icon {
  color: #9090a8;
  cursor: pointer;
  flex-shrink: 0;
}

.volume-slider {
  flex: 1;
}

.speed-label {
  font-size: 0.78rem;
  color: #667eea;
  cursor: pointer;
  font-weight: 600;
  min-width: 32px;
  text-align: right;
  user-select: none;
}

.speed-label:hover {
  color: #7b93f0;
}
</style>
