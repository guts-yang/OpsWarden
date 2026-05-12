<script setup>
import { computed, ref, onMounted, onUnmounted, inject } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

// 获取主布局中的侧边栏状态
const sidebarCollapsed = inject('sidebarCollapsed', ref(false))

// 响应式状态
const isMobile = ref(false)

// 检测移动端
const checkMobile = () => {
  isMobile.value = window.innerWidth < 768
  // 移动端默认收起侧边栏
  if (isMobile.value) {
    sidebarCollapsed.value = true
  }
}

// 切换侧边栏状态
const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

// 移动端点击内容区域关闭侧边栏
const closeSidebarOnMobile = () => {
  if (isMobile.value && !sidebarCollapsed.value) {
    sidebarCollapsed.value = true
  }
}

// 监听窗口大小变化
onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})

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
</script>

<template>
  <!-- 移动端遮罩层 -->
  <div 
    v-if="isMobile && !sidebarCollapsed"
    class="fixed inset-0 bg-black bg-opacity-50 z-40"
    @click="closeSidebarOnMobile"
  />
  
  <aside 
    class="flex-shrink-0 bg-white border-r border-outline flex flex-col h-screen sticky top-0 shadow-shell transition-all duration-300 z-50"
    :class="[
      isMobile 
        ? sidebarCollapsed 
          ? 'w-[64px]' 
          : 'w-[280px] fixed inset-y-0 left-0'
        : sidebarCollapsed 
          ? 'w-[64px]' 
          : 'w-[220px]'
    ]"
  >
    <!-- Logo 区域 -->
    <div class="flex items-center gap-2.5 px-4 h-[64px] border-b border-outline relative shrink-0">
      <div class="w-9 h-9 rounded-xl bg-primary-500 flex items-center justify-center shadow-sm shrink-0">
        <span class="material-symbols-outlined text-white text-[22px]">shield</span>
      </div>
      <div class="min-w-0 transition-all duration-300 overflow-hidden" :class="sidebarCollapsed ? 'opacity-0 w-0' : 'opacity-100 w-auto'">
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
        class="relative flex items-center rounded-lg text-sm transition-colors group"
        :class="[
          isActive(item.path)
            ? 'bg-primary-50 text-primary-700 font-medium shadow-sm'
            : 'text-on-surface-variant hover:bg-surface-container',
          sidebarCollapsed ? 'justify-center px-2 py-3' : 'gap-3 px-3 py-2.5'
        ]"
        :title="sidebarCollapsed ? item.label : ''"
      >
        <span
          v-if="isActive(item.path) && !sidebarCollapsed"
          class="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 rounded-full bg-primary-500"
          aria-hidden="true"
        />
        <span class="material-symbols-outlined text-[20px] shrink-0">{{ item.icon }}</span>
        <span 
          v-if="!sidebarCollapsed"
          class="transition-opacity duration-300 whitespace-nowrap overflow-hidden"
        >
          {{ item.label }}
        </span>
        
        <!-- 收起状态下的提示工具 -->
        <div 
          v-if="sidebarCollapsed"
          class="absolute left-full ml-2 px-2 py-1 bg-gray-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-50"
        >
          {{ item.label }}
        </div>
      </RouterLink>
    </nav>

    <!-- Footer -->
    <div class="px-2 py-3 border-t border-outline">
      <button
        class="flex items-center rounded-lg text-sm text-on-surface-variant hover:bg-surface-container w-full group relative"
        :class="sidebarCollapsed ? 'justify-center px-2 py-3' : 'gap-3 px-3 py-2'"
        @click="logout"
        :title="sidebarCollapsed ? '退出登录' : ''"
      >
        <span class="material-symbols-outlined text-[20px]">logout</span>
        <span 
          class="transition-opacity duration-300 whitespace-nowrap overflow-hidden"
          :class="sidebarCollapsed ? 'opacity-0 w-0' : 'opacity-100'"
        >
          退出登录
        </span>
        
        <!-- 收起状态下的提示工具 -->
        <div 
          v-if="sidebarCollapsed"
          class="absolute left-full ml-2 px-2 py-1 bg-gray-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-50"
        >
          退出登录
        </div>
      </button>
    </div>
    <!-- 伸缩按钮 - 侧边栏内部右侧中间 -->
    <button
      class="absolute -right-3 top-1/2 -translate-y-1/2 w-6 h-6 rounded-full bg-primary-500 text-white flex items-center justify-center shadow-md hover:bg-primary-600 transition-all duration-300 z-50"
      @click="toggleSidebar"
      :title="sidebarCollapsed ? '展开导航栏' : '收起导航栏'"
    >
      <span class="material-symbols-outlined text-[16px] transition-transform duration-300" :class="sidebarCollapsed ? 'rotate-180' : ''">
        chevron_left
      </span>
    </button>
  </aside>
</template>
