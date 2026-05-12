<script setup>
import { useAuthStore } from '@/stores/auth'
import { ACCOUNT_ROLE } from '@/utils/constants'
import { inject, ref, onMounted, onUnmounted } from 'vue'

defineProps({ title: { type: String, default: '' } })

const auth = useAuthStore()

// 获取侧边栏状态
const sidebarCollapsed = inject('sidebarCollapsed')



// 切换侧边栏
const toggleSidebar = () => {
  if (sidebarCollapsed) {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }
}



function getRoleLabel(role) {
  return ACCOUNT_ROLE[role]?.label ?? role
}
</script>

<template>
  <header
    class="h-14 bg-white/95 backdrop-blur-sm border-b border-outline flex items-center justify-between px-6 flex-shrink-0 z-10 shadow-shell"
  >
    <div class="flex items-center gap-3 min-w-0">
      <h1 class="text-sm font-semibold text-on-surface truncate">{{ title }}</h1>
      <span class="hidden sm:inline-block h-4 w-px bg-outline shrink-0" aria-hidden="true" />
      <span class="hidden sm:inline text-xs text-on-surface-variant truncate">控制台</span>
    </div>
    <div class="flex items-center gap-3 pl-2">
      <span
        class="text-[11px] uppercase tracking-wide text-on-surface-variant px-2 py-0.5 rounded-md bg-surface-container border border-outline-variant"
      >
        {{ getRoleLabel(auth.user?.role) }}
      </span>
      <div class="flex items-center gap-2 min-w-0">
        <div
          class="w-9 h-9 rounded-full bg-gradient-to-br from-primary-100 to-primary-200 flex items-center justify-center ring-2 ring-white shadow-sm"
        >
          <span class="text-primary-800 text-xs font-semibold">
            {{ auth.user?.name?.charAt(0) ?? auth.user?.username?.charAt(0) ?? '?' }}
          </span>
        </div>
        <span class="text-sm font-medium text-on-surface truncate max-w-[8rem] sm:max-w-[12rem]">
          {{ auth.user?.name || auth.user?.username }}
        </span>
      </div>
    </div>
  </header>
</template>
