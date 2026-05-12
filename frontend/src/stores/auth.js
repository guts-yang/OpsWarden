import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'
import { clearChatSessionStorage } from '@/utils/chatSessionStorage'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('ow_token') || null)
  const user = ref(JSON.parse(localStorage.getItem('ow_user') || 'null'))

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isOperator = computed(
    () => user.value?.role === 'admin' || user.value?.role === 'operator',
  )
  const canAccessKnowledge = computed(
    () => user.value?.role === 'admin' || user.value?.role === 'operator',
  )
  const canAccessAccounts = computed(() => user.value?.role === 'admin')
  const canAccessStaffRoutes = computed(
    () => user.value?.role === 'admin' || user.value?.role === 'operator',
  )

  async function login(username, password) {
    const data = await authApi.login(username, password)
    token.value = data.access_token
    user.value = {
      id: data.user_id,
      username: data.username,
      name: data.name,
      role: data.role,
    }
    localStorage.setItem('ow_token', token.value)
    localStorage.setItem('ow_user', JSON.stringify(user.value))
  }

  function logout() {
    const uid = user.value?.id
    if (uid != null) clearChatSessionStorage(uid)
    token.value = null
    user.value = null
    localStorage.removeItem('ow_token')
    localStorage.removeItem('ow_user')
  }

  return {
    token,
    user,
    isLoggedIn,
    isAdmin,
    isOperator,
    canAccessKnowledge,
    canAccessAccounts,
    canAccessStaffRoutes,
    login,
    logout,
  }
})
