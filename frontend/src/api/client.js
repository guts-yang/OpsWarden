import axios from 'axios'

// Lazy import to avoid circular dependency (store imports client, client imports store)
let _authStore = null
let _router = null

export function initClient(authStore, router) {
  _authStore = authStore
  _router = router
}

const client = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// Request interceptor: inject Authorization header
client.interceptors.request.use((config) => {
  const token = _authStore?.token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor: unwrap {code, message, data} envelope
client.interceptors.response.use(
  (response) => {
    const { code, message, data } = response.data
    if (code !== undefined && code !== 200) {
      return Promise.reject(new Error(message || '请求失败'))
    }
    // Return data field if envelope present, otherwise return raw response data
    return data !== undefined ? data : response.data
  },
  (error) => {
    if (error.response?.status === 401) {
      _authStore?.logout()
      _router?.push('/login')
      return Promise.reject(new Error('登录已过期，请重新登录'))
    }
    // Extract error message from response body
    const detail = error.response?.data
    const msg =
      detail?.message ||
      (Array.isArray(detail?.detail) ? detail.detail[0]?.msg : detail?.detail) ||
      error.message ||
      '网络错误，请重试'
    return Promise.reject(new Error(msg))
  },
)

export default client
