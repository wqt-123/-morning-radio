import axios from 'axios'
import { ElMessage } from 'element-plus'

const http = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
http.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
http.interceptors.response.use(
  (response) => {
    const body = response.data
    // 自动解包 {code, message, data} 标准格式
    if (body && typeof body === 'object' && 'code' in body && 'data' in body) {
      return body.data
    }
    return body
  },
  (error) => {
    const message = error.response?.data?.detail || error.message || '请求失败'
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

// ===== 新闻相关 API =====
export const newsApi = {
  /** 获取今日新闻列表 */
  getToday(params) {
    return http.get('/news/today', { params })
  },
  /** 按分类获取新闻 */
  getByCategory(category, params) {
    return http.get(`/news/category/${category}`, { params })
  },
  /** 获取新闻详情 */
  getDetail(newsId) {
    return http.get(`/news/${newsId}`)
  },
  /** 手动触发新闻抓取 */
  fetchNews() {
    return http.post('/news/fetch')
  }
}

// ===== 播报相关 API =====
export const radioApi = {
  /** 获取今日播报 */
  getToday() {
    return http.get('/radio/today')
  },
  /** 获取历史播报列表 */
  getHistory(params) {
    return http.get('/radio/history', { params })
  },
  /** 手动生成播报 */
  generate() {
    return http.post('/radio/generate')
  },
  /** 流媒体播放地址 */
  getStreamUrl(filename) {
    return `/api/radio/stream/${filename}`
  }
}

// ===== 用户偏好 API =====
export const userApi = {
  /** 获取用户偏好 */
  getPreferences() {
    return http.get('/user/preferences')
  },
  /** 更新用户偏好 */
  updatePreferences(data) {
    return http.put('/user/preferences', data)
  }
}

export default http
