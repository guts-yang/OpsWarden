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
  <aside class="w-[200px] flex-shrink-0 bg-white border-r border-outline flex flex-col h-screen sticky top-0">
    <!-- Logo -->
    <div class="flex items-center gap-2 px-4 py-4 border-b border-outline">
      <span class="material-symbols-outlined text-primary-500">shield</span>
      <span class="font-semibold text-on-surface text-sm tracking-wide">OpsWarden</span>
    </div>

    <!-- Nav -->
    <nav class="flex-1 px-2 py-3 space-y-0.5 overflow-y-auto">
      <RouterLink
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors"
        :class="
          isActive(item.path)
            ? 'bg-primary-50 text-primary-700 font-medium'
            : 'text-on-surface-variant hover:bg-surface-container'
        "
      >
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
