<template>
  <div class="settings-page">
    <h1 class="page-title">偏好设置</h1>

    <div class="settings-card glass-card fade-in-up">
      <el-form
        ref="formRef"
        :model="form"
        label-width="120px"
        label-position="top"
        class="settings-form"
      >
        <!-- 播报音色 -->
        <el-form-item label="播报音色">
          <el-radio-group v-model="form.voice_type" class="voice-group">
            <el-radio-button value="female" class="voice-option">
              <div class="voice-card">
                <el-icon :size="24"><Microphone /></el-icon>
                <span class="voice-label">女声</span>
                <span class="voice-desc">晓晓 - 温柔亲切</span>
              </div>
            </el-radio-button>
            <el-radio-button value="male" class="voice-option">
              <div class="voice-card">
                <el-icon :size="24"><Microphone /></el-icon>
                <span class="voice-label">男声</span>
                <span class="voice-desc">云希 - 沉稳大气</span>
              </div>
            </el-radio-button>
          </el-radio-group>
        </el-form-item>

        <!-- 感兴趣的新闻分类 -->
        <el-form-item label="感兴趣的新闻分类">
          <el-checkbox-group v-model="form.preferred_categories" class="category-group">
            <el-checkbox
              v-for="cat in categoryOptions"
              :key="cat.value"
              :value="cat.value"
              :label="cat.value"
              border
              class="category-checkbox"
            >
              <span class="cat-emoji">{{ cat.icon }}</span>
              {{ cat.label }}
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>

        <!-- 自动生成 -->
        <el-form-item label="自动生成播报">
          <el-switch
            v-model="form.auto_generate"
            active-text="每天早上自动生成"
            inactive-text="手动触发"
            class="auto-switch"
          />
        </el-form-item>

        <!-- 操作按钮 -->
        <el-form-item>
          <div class="form-actions">
            <el-button class="btn-gradient" @click="handleSave" :loading="saving">
              <el-icon><Check /></el-icon>
              保存设置
            </el-button>
            <el-button @click="handleReset" :disabled="saving">恢复默认</el-button>
          </div>
        </el-form-item>
      </el-form>
    </div>

    <!-- 关于 -->
    <div class="about-card glass-card fade-in-up fade-in-up-delay-1">
      <h3 class="about-title">关于早安电台</h3>
      <p class="about-desc">
        早安电台是一个基于 AI 技术的每日新闻播报应用。每天清晨自动为您抓取最新要闻，
        AI 主播用温暖的声音为您播报，让您在通勤路上轻松获取信息。
      </p>
      <div class="about-info">
        <span>版本 1.0.0</span>
        <span class="dot">·</span>
        <span>Powered by AI + Edge-TTS + FFmpeg</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Microphone, Check } from '@element-plus/icons-vue'
import { userApi } from '@/api'
import { ElMessage } from 'element-plus'

const formRef = ref(null)
const saving = ref(false)

const form = reactive({
  voice_type: 'female',
  preferred_categories: ['科技', '财经', '国内'],
  auto_generate: true
})

const defaultForm = {
  voice_type: 'female',
  preferred_categories: ['科技', '财经', '国内'],
  auto_generate: true
}

const categoryOptions = [
  { value: '科技', label: '科技', icon: '💻' },
  { value: '财经', label: '财经', icon: '📈' },
  { value: '体育', label: '体育', icon: '⚽' },
  { value: '娱乐', label: '娱乐', icon: '🎬' },
  { value: '国内', label: '国内', icon: '🇨🇳' },
  { value: '国际', label: '国际', icon: '🌍' }
]

async function loadPreferences() {
  try {
    const res = await userApi.getPreferences()
    if (res && Object.keys(res).length > 0) {
      form.voice_type = res.voice_type || defaultForm.voice_type
      form.preferred_categories = Array.isArray(res.preferred_categories)
        ? res.preferred_categories
        : defaultForm.preferred_categories
      form.auto_generate = res.auto_generate ?? defaultForm.auto_generate
    }
  } catch {
    // 使用默认值
  }
}

async function handleSave() {
  saving.value = true
  try {
    await userApi.updatePreferences({
      voice_type: form.voice_type,
      preferred_categories: form.preferred_categories,
      auto_generate: form.auto_generate
    })
    ElMessage.success('设置已保存')
  } catch (err) {
    ElMessage.error('保存失败: ' + (err.response?.data?.detail || err.message))
  } finally {
    saving.value = false
  }
}

function handleReset() {
  Object.assign(form, defaultForm)
  ElMessage.info('已恢复默认设置（需点击保存生效）')
}

onMounted(loadPreferences)
</script>

<style scoped>
.settings-page {
  padding-top: 24px;
  max-width: 700px;
  margin: 0 auto;
}

.settings-card {
  padding: 28px 32px;
  margin-bottom: 24px;
}

.settings-form {
  --el-form-label-font-size: 0.88rem;
}

.voice-group {
  width: 100%;
}

.voice-option {
  flex: 1;
}

.voice-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 12px 20px;
}

.voice-label {
  font-weight: 600;
  font-size: 0.9rem;
}

.voice-desc {
  font-size: 0.75rem;
  color: #808098;
}

.category-group {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.category-checkbox {
  margin-right: 0 !important;
}

.cat-emoji {
  margin-right: 4px;
}

.auto-switch {
  --el-switch-on-color: #667eea;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 8px;
}

.about-card {
  padding: 24px 28px;
}

.about-title {
  font-size: 1rem;
  font-weight: 600;
  color: #e0e0e0;
  margin-bottom: 12px;
}

.about-desc {
  font-size: 0.85rem;
  color: #9090a8;
  line-height: 1.7;
  margin-bottom: 12px;
}

.about-info {
  font-size: 0.78rem;
  color: #707088;
}

.dot {
  margin: 0 8px;
  color: rgba(255, 255, 255, 0.15);
}

@media (max-width: 768px) {
  .settings-card {
    padding: 20px 16px;
  }

  .voice-group {
    flex-direction: column;
  }
}
</style>
