<script setup>
import { computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const props = defineProps({
  /** 手机端 Drawer 是否打开（PC 端不使用此 prop） */
  drawerOpen: { type: Boolean, default: false },
})
const emit = defineEmits(['close-drawer'])

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const allNavItems = [
  { path: '/', icon: 'dashboard', label: '仪表盘', needsStaff: true },
  { path: '/tickets', icon: 'confirmation_number', label: '工单管理', needsStaff: true },
  { path: '/chat', icon: 'smart_toy', label: 'AI 问答' },
  { path: '/knowledge', icon: 'menu_book', label: '知识库', needsKnowledge: true },
  { path: '/accounts', icon: 'manage_accounts', label: '账号管理', needsAccounts: true },
]

const navItems = computed(() =>
  allNavItems.filter((item) => {
    if (item.needsStaff && !auth.canAccessStaffRoutes) return false
    if (item.needsKnowledge && !auth.canAccessKnowledge) return false
    if (item.needsAccounts && !auth.canAccessAccounts) return false
    return true
  }),
)

function isActive(path) {
  return path === '/' ? route.path === '/' : route.path.startsWith(path)
}

function logout() {
  auth.logout()
  router.push('/login')
}

function handleNav() {
  // 手机端点击导航后自动关闭 Drawer
  emit('close-drawer')
}

// Drawer 打开时锁定 body 滚动
watch(
  () => props.drawerOpen,
  (open) => {
    if (typeof document === 'undefined') return
    if (open) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
  },
)
</script>

<template>
  <!-- 手机端遮罩 -->
  <Transition name="overlay">
    <div
      v-if="drawerOpen"
      class="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm md:hidden"
      @click="$emit('close-drawer')"
    />
  </Transition>

  <!-- 侧边栏：PC 端常驻 sticky 220px；手机端为 Drawer 抽屉，受 drawerOpen 控制 -->
  <aside
    class="bg-white border-r border-outline flex flex-col shadow-shell transition-transform duration-300 ease-out
           md:w-[220px] md:flex-shrink-0 md:h-screen md:sticky md:top-0 md:translate-x-0
           fixed top-0 left-0 z-50 h-[100dvh] w-[80vw] max-w-[280px] pt-safe pl-safe"
    :class="drawerOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'"
    aria-label="主导航"
  >
    <!-- Logo -->
    <div class="flex items-center justify-between gap-2.5 px-4 py-4 border-b border-outline">
      <div class="flex items-center gap-2.5 min-w-0">
        <div class="w-9 h-9 rounded-xl bg-primary-500 flex items-center justify-center shadow-sm shrink-0">
          <span class="material-symbols-outlined text-white text-[22px]">shield</span>
        </div>
        <div class="min-w-0">
          <span class="font-semibold text-on-surface text-sm tracking-tight block leading-tight">OpsWarden</span>
          <span class="text-[10px] text-on-surface-variant leading-tight">运维数字员工</span>
        </div>
      </div>
      <!-- 手机端关闭按钮 -->
      <button
        class="md:hidden tap-target -mr-2 flex items-center justify-center rounded-lg text-on-surface-variant hover:bg-surface-container"
        aria-label="关闭菜单"
        @click="$emit('close-drawer')"
      >
        <span class="material-symbols-outlined text-[22px]">close</span>
      </button>
    </div>

    <!-- Nav -->
    <nav class="flex-1 px-2 py-3 space-y-0.5 overflow-y-auto">
      <RouterLink
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="relative flex items-center gap-3 px-3 py-3 md:py-2.5 rounded-lg text-sm transition-colors"
        :class="
          isActive(item.path)
            ? 'bg-primary-50 text-primary-700 font-medium shadow-sm'
            : 'text-on-surface-variant hover:bg-surface-container active:bg-surface-container'
        "
        @click="handleNav"
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
    <div class="px-2 py-3 border-t border-outline pb-safe">
      <button
        class="flex items-center gap-3 px-3 py-3 md:py-2 rounded-lg text-sm text-on-surface-variant hover:bg-surface-container active:bg-surface-container w-full"
        @click="logout"
      >
        <span class="material-symbols-outlined text-[20px]">logout</span>
        退出登录
      </button>
    </div>
  </aside>
</template>

<style scoped>
.overlay-enter-active,
.overlay-leave-active {
  transition: opacity 0.2s ease;
}
.overlay-enter-from,
.overlay-leave-to {
  opacity: 0;
}
</style>
