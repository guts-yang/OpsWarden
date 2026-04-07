<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppSidebar from '@/components/AppSidebar.vue'
import AppHeader from '@/components/AppHeader.vue'

const route = useRoute()

const pageTitles = {
  Dashboard: '仪表盘',
  Accounts: '账号管理',
  Tickets: '工单管理',
  AiChat: 'AI 智能问答',
  Knowledge: '知识库管理',
}

const title = computed(() => pageTitles[route.name] ?? 'OpsWarden')
</script>

<template>
  <div class="flex h-screen overflow-hidden bg-surface-dim">
    <AppSidebar />
    <div class="flex-1 flex flex-col overflow-hidden min-w-0">
      <AppHeader :title="title" />
      <main class="flex-1 overflow-auto">
        <div class="mx-auto w-full max-w-[1440px] min-h-full">
          <RouterView />
        </div>
      </main>
    </div>
  </div>
</template>
