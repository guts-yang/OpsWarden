<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const auth = useAuthStore()

const allTabs = [
  { path: '/', icon: 'dashboard', label: '仪表盘', needsStaff: true },
  { path: '/tickets', icon: 'confirmation_number', label: '工单', needsStaff: true },
  { path: '/chat', icon: 'smart_toy', label: 'AI 问答' },
  { path: '/knowledge', icon: 'menu_book', label: '知识库', needsKnowledge: true },
  { path: '/accounts', icon: 'manage_accounts', label: '账号', needsAccounts: true },
]

const tabs = computed(() => {
  const filtered = allTabs.filter((t) => {
    if (t.needsStaff && !auth.canAccessStaffRoutes) return false
    if (t.needsKnowledge && !auth.canAccessKnowledge) return false
    if (t.needsAccounts && !auth.canAccessAccounts) return false
    return true
  })
  // 最多 5 项以符合 iOS HIG
  return filtered.slice(0, 5)
})

function isActive(path) {
  return path === '/' ? route.path === '/' : route.path.startsWith(path)
}
</script>

<template>
  <nav
    v-if="tabs.length > 0"
    class="md:hidden fixed bottom-0 inset-x-0 z-30 bg-white/95 backdrop-blur-md border-t border-outline shadow-[0_-1px_2px_rgba(32,33,36,0.06)] pb-safe"
    aria-label="底部导航"
  >
    <ul class="flex items-stretch justify-around h-16">
      <li v-for="tab in tabs" :key="tab.path" class="flex-1 flex">
        <RouterLink
          :to="tab.path"
          class="relative flex flex-col items-center justify-center gap-0.5 w-full text-[11px] transition-colors active:bg-surface-container/50"
          :class="
            isActive(tab.path)
              ? 'text-primary-600 font-medium'
              : 'text-on-surface-variant'
          "
        >
          <!-- 顶部小色条（active 态） -->
          <span
            v-if="isActive(tab.path)"
            class="absolute top-0 left-1/2 -translate-x-1/2 w-8 h-[3px] rounded-b-full bg-primary-500"
            aria-hidden="true"
          />
          <span
            class="material-symbols-outlined text-[22px]"
            :style="isActive(tab.path) ? 'font-variation-settings: \'FILL\' 1, \'wght\' 500;' : ''"
          >
            {{ tab.icon }}
          </span>
          <span class="leading-tight">{{ tab.label }}</span>
        </RouterLink>
      </li>
    </ul>
  </nav>
</template>
