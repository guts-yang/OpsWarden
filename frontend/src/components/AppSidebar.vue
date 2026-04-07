<script setup>
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const navItems = [
  { path: '/', icon: 'dashboard', label: '仪表盘' },
  { path: '/tickets', icon: 'confirmation_number', label: '工单管理' },
  { path: '/chat', icon: 'smart_toy', label: 'AI 问答' },
  { path: '/knowledge', icon: 'menu_book', label: '知识库' },
  { path: '/accounts', icon: 'manage_accounts', label: '账号管理' },
]

function isActive(path) {
  return path === '/' ? route.path === '/' : route.path.startsWith(path)
}

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <aside class="w-[220px] flex-shrink-0 bg-white border-r border-outline flex flex-col h-screen sticky top-0 shadow-shell">
    <!-- Logo -->
    <div class="flex items-center gap-2.5 px-4 py-4 border-b border-outline">
      <div class="w-9 h-9 rounded-xl bg-primary-500 flex items-center justify-center shadow-sm">
        <span class="material-symbols-outlined text-white text-[22px]">shield</span>
      </div>
      <div class="min-w-0">
        <span class="font-semibold text-on-surface text-sm tracking-tight block leading-tight">OpsWarden</span>
        <span class="text-[10px] text-on-surface-variant leading-tight">运维数字员工</span>
      </div>
    </div>

    <!-- Nav -->
    <nav class="flex-1 px-2 py-3 space-y-0.5 overflow-y-auto">
      <RouterLink
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="relative flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors"
        :class="
          isActive(item.path)
            ? 'bg-primary-50 text-primary-700 font-medium shadow-sm'
            : 'text-on-surface-variant hover:bg-surface-container'
        "
      >
        <span
          v-if="isActive(item.path)"
          class="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 rounded-full bg-primary-500"
          aria-hidden="true"
        />
        <span class="material-symbols-outlined text-[20px]">{{ item.icon }}</span>
        {{ item.label }}
      </RouterLink>
    </nav>

    <!-- Footer -->
    <div class="px-2 py-3 border-t border-outline">
      <button
        class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-on-surface-variant hover:bg-surface-container w-full"
        @click="logout"
      >
        <span class="material-symbols-outlined text-[20px]">logout</span>
        退出登录
      </button>
    </div>
  </aside>
</template>
