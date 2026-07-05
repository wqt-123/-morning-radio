import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue'),
    meta: { title: '早安电台 - 今日播报' }
  },
  {
    path: '/player/:id',
    name: 'Player',
    component: () => import('@/views/Player.vue'),
    meta: { title: '播放详情' },
    props: true
  },
  {
    path: '/news',
    name: 'NewsList',
    component: () => import('@/views/NewsList.vue'),
    meta: { title: '新闻列表' }
  },
  {
    path: '/history',
    name: 'History',
    component: () => import('@/views/History.vue'),
    meta: { title: '历史播报' }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/Settings.vue'),
    meta: { title: '偏好设置' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  }
})

router.afterEach((to) => {
  document.title = to.meta.title || '早安电台 - AI每日新闻'
})

export default router
