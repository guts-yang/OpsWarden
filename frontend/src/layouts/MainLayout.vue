<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import AppSidebar from '@/components/AppSidebar.vue'
import AppHeader from '@/components/AppHeader.vue'
import AppBottomTabBar from '@/components/AppBottomTabBar.vue'

const route = useRoute()

const pageTitles = {
  Dashboard: '仪表盘',
  Accounts: '账号管理',
  Tickets: '工单管理',
  AiChat: 'AI 智能问答',
  Knowledge: '知识库管理',
}

const title = computed(() => pageTitles[route.name] ?? 'OpsWarden')
const isAiChat = computed(() => route.name === 'AiChat')

const drawerOpen = ref(false)
function toggleDrawer() {
  drawerOpen.value = !drawerOpen.value
}
function closeDrawer() {
  drawerOpen.value = false
}
// 路由切换时关闭抽屉
watch(() => route.fullPath, () => {
  drawerOpen.value = false
})
</script>

<template>
  <div class="flex h-[100dvh] overflow-hidden bg-surface-dim">
    <!-- 侧边栏：PC 常驻 / 手机 Drawer -->
    <AppSidebar :drawer-open="drawerOpen" @close-drawer="closeDrawer" />

    <div class="flex-1 flex flex-col overflow-hidden min-w-0">
      <AppHeader :title="title" @toggle-drawer="toggleDrawer" />
      <main
        :class="
          isAiChat
            ? 'flex-1 flex flex-col min-h-0 overflow-hidden'
            : 'flex-1 overflow-auto pb-tabbar md:pb-0'
        "
      >
        <div
          :class="
            isAiChat
              ? 'mx-auto w-full max-w-[1440px] flex-1 flex flex-col min-h-0'
              : 'mx-auto w-full max-w-[1440px] min-h-full'
          "
        >
          <RouterView />
        </div>
      </main>
    </div>

    <!-- 底部 Tab Bar：仅手机端显示 -->
    <AppBottomTabBar />
  </div>
</template>
