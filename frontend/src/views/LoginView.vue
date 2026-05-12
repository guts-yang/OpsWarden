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
    router.push(auth.user?.role === 'user' ? '/chat' : '/')
  } catch (e) {
    error.value = e.message || '登录失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div
    class="min-h-[100dvh] flex items-center justify-center p-4 sm:p-6 pt-safe pb-safe bg-gradient-to-br from-surface-dim via-white to-primary-50/40"
  >
    <div class="w-full max-w-[92vw] sm:max-w-[400px]">
      <!-- Logo / Brand -->
      <div class="text-center mb-6 sm:mb-8">
        <div
          class="w-14 h-14 sm:w-16 sm:h-16 bg-primary-500 rounded-3xl flex items-center justify-center mx-auto mb-3 sm:mb-4 shadow-lift ring-4 ring-primary-500/10"
        >
          <span class="material-symbols-outlined text-white text-[2rem] sm:text-[2.25rem]">shield</span>
        </div>
        <h1 class="text-xl font-semibold text-on-surface tracking-tight">OpsWarden</h1>
        <p class="text-sm text-on-surface-variant mt-1.5">AI 运维数字员工平台</p>
      </div>

      <!-- Card -->
      <div class="ops-card rounded-3xl p-5 sm:p-8 shadow-lift ring-1 ring-outline-variant/60">
        <h2 class="text-sm font-semibold text-on-surface mb-1">账号登录</h2>
        <p class="text-xs text-on-surface-variant mb-5">使用运维账号进入控制台</p>

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
                class="w-full pl-9 pr-4 py-3 sm:py-2.5 text-sm ops-input min-h-[44px]"
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
                class="w-full pl-9 pr-10 py-3 sm:py-2.5 text-sm ops-input min-h-[44px]"
                autocomplete="current-password"
              />
              <button
                type="button"
                class="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 flex items-center justify-center"
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
            class="w-full py-3 sm:py-2.5 min-h-[44px] bg-primary-500 text-white text-sm font-medium rounded-xl hover:bg-primary-600 active:bg-primary-700 disabled:opacity-60 transition-all shadow-sm hover:shadow-md mt-2"
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
