<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const username = ref('')
const password = ref('')
const showPassword = ref(false)
const loading = ref(false)
const error = ref('')

async function handleLogin() {
  error.value = ''
  if (!username.value || !password.value) {
    error.value = '请输入用户名和密码'
    return
  }
  loading.value = true
  try {
    await auth.login(username.value, password.value)
    router.push('/')
  } catch (e) {
    error.value = e.message || '登录失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-surface-dim flex items-center justify-center p-4">
    <div class="w-full max-w-sm">
      <!-- Logo / Brand -->
      <div class="text-center mb-8">
        <div class="w-14 h-14 bg-primary-500 rounded-2xl flex items-center justify-center mx-auto mb-4">
          <span class="material-symbols-outlined text-white text-3xl">shield</span>
        </div>
        <h1 class="text-xl font-semibold text-on-surface">OpsWarden</h1>
        <p class="text-sm text-on-surface-variant mt-1">AI 运维数字员工平台</p>
      </div>

      <!-- Card -->
      <div class="bg-white rounded-2xl shadow-sm border border-outline p-6">
        <h2 class="text-sm font-semibold text-on-surface mb-5">账号登录</h2>

        <!-- Error -->
        <div
          v-if="error"
          class="flex items-center gap-2 bg-error-container text-error text-xs px-3 py-2 rounded-lg mb-4"
        >
          <span class="material-symbols-outlined text-[16px]">error</span>
          {{ error }}
        </div>

        <form class="space-y-4" @submit.prevent="handleLogin">
          <!-- Username -->
          <div>
            <label class="block text-xs font-medium text-on-surface-variant mb-1.5">用户名</label>
            <div class="relative">
              <span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-[18px] text-on-surface-variant">
                person
              </span>
              <input
                v-model="username"
                type="text"
                placeholder="请输入用户名"
                class="w-full pl-9 pr-4 py-2.5 text-sm border border-outline rounded-lg focus:outline-none focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
                autocomplete="username"
              />
            </div>
          </div>

          <!-- Password -->
          <div>
            <label class="block text-xs font-medium text-on-surface-variant mb-1.5">密码</label>
            <div class="relative">
              <span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-[18px] text-on-surface-variant">
                lock
              </span>
              <input
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                placeholder="请输入密码"
                class="w-full pl-9 pr-10 py-2.5 text-sm border border-outline rounded-lg focus:outline-none focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
                autocomplete="current-password"
              />
              <button
                type="button"
                class="absolute right-3 top-1/2 -translate-y-1/2"
                tabindex="-1"
                @click="showPassword = !showPassword"
              >
                <span class="material-symbols-outlined text-[18px] text-on-surface-variant">
                  {{ showPassword ? 'visibility_off' : 'visibility' }}
                </span>
              </button>
            </div>
          </div>

          <!-- Submit -->
          <button
            type="submit"
            :disabled="loading"
            class="w-full py-2.5 bg-primary-500 text-white text-sm font-medium rounded-lg hover:bg-primary-600 disabled:opacity-60 transition-colors mt-2"
          >
            {{ loading ? '登录中...' : '登录' }}
          </button>
        </form>
      </div>

      <p class="text-center text-xs text-on-surface-variant mt-6">
        OpsWarden · AI-Powered Operations Platform
      </p>
    </div>
  </div>
</template>
