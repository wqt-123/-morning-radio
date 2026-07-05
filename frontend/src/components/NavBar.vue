<template>
  <nav class="navbar glass-card">
    <div class="navbar-inner">
      <router-link to="/" class="logo">
        <span class="logo-icon">🌅</span>
        <span class="logo-text">早安电台</span>
      </router-link>

      <div class="nav-menu-desktop">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="nav-link"
          :class="{ active: isActive(item.path) }"
        >
          <el-icon v-if="item.icon" class="nav-icon"><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </router-link>
      </div>

      <div class="nav-menu-mobile">
        <el-dropdown trigger="click" placement="bottom-end">
          <el-button class="menu-toggle-btn" circle>
            <el-icon :size="20"><Menu /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item
                v-for="item in navItems"
                :key="item.path"
                @click="$router.push(item.path)"
              >
                <el-icon v-if="item.icon"><component :is="item.icon" /></el-icon>
                {{ item.label }}
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { useRoute } from 'vue-router'
import { Headset, Document, Clock, Setting, Menu } from '@element-plus/icons-vue'

const route = useRoute()

const navItems = [
  { path: '/', label: '今日播报', icon: Headset },
  { path: '/news', label: '新闻列表', icon: Document },
  { path: '/history', label: '历史记录', icon: Clock },
  { path: '/settings', label: '设置', icon: Setting }
]

function isActive(path) {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}
</script>

<style scoped>
.navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  height: 64px;
  border-radius: 0 !important;
  border-top: none !important;
  border-left: none !important;
  border-right: none !important;
}

.navbar-inner {
  max-width: 1200px;
  margin: 0 auto;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  text-decoration: none;
  color: #e0e0e0;
}

.logo-icon {
  font-size: 28px;
}

.logo-text {
  font-size: 1.25rem;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea, #764ba2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.nav-menu-desktop {
  display: flex;
  align-items: center;
  gap: 4px;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 10px;
  text-decoration: none;
  color: #a0a0b8;
  font-size: 0.9rem;
  font-weight: 500;
  transition: all 0.25s ease;
}

.nav-link:hover {
  color: #e0e0e0;
  background: rgba(102, 126, 234, 0.1);
}

.nav-link.active {
  color: #667eea;
  background: rgba(102, 126, 234, 0.15);
}

.nav-icon {
  font-size: 16px;
}

.menu-toggle-btn {
  background: rgba(255, 255, 255, 0.06) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  color: #c8c8d0 !important;
}

.menu-toggle-btn:hover {
  background: rgba(102, 126, 234, 0.15) !important;
  border-color: rgba(102, 126, 234, 0.3) !important;
}

.nav-menu-mobile {
  display: none;
}

@media (max-width: 768px) {
  .nav-menu-desktop {
    display: none;
  }

  .nav-menu-mobile {
    display: block;
  }

  .navbar-inner {
    padding: 0 16px;
  }
}
</style>
