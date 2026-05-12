<script setup>
import { computed, ref, provide } from 'vue'
import { useRoute } from 'vue-router'
import AppSidebar from '@/components/AppSidebar.vue'
import AppHeader from '@/components/AppHeader.vue'

const route = useRoute()

// 侧边栏状态管理
const sidebarCollapsed = ref(false)

// 提供给子组件使用
provide('sidebarCollapsed', sidebarCollapsed)

const pageTitles = {
  Dashboard: '仪表盘',
  Accounts: '账号管理',
  Tickets: '工单管理',
  AiChat: 'AI 智能问答',
  Knowledge: '知识库管理',
}

const title = computed(() => pageTitles[route.name] ?? 'OpsWarden')

const isAiChat = computed(() => route.name === 'AiChat')
</script>

<template>
  <div class="flex h-screen overflow-hidden bg-surface-dim">
    <AppSidebar />
    <div class="flex-1 flex flex-col overflow-hidden min-w-0 transition-all duration-300">
      <AppHeader :title="title" />
      <main
        :class="
          isAiChat
            ? 'flex-1 flex flex-col min-h-0 overflow-hidden'
            : 'flex-1 overflow-auto'
        "
      >
        <div
          :class="
            isAiChat
              ? 'mx-auto w-full flex-1 flex flex-col min-h-0'
              : 'mx-auto w-full min-h-full'
          "
        >
          <RouterView />
        </div>
      </main>
    </div>
  </div>
</template>
