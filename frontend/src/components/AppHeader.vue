<script setup>
import { useAuthStore } from '@/stores/auth'
import { ACCOUNT_ROLE } from '@/utils/constants'

defineProps({
  title: { type: String, default: '' },
})
defineEmits(['toggle-drawer'])

const auth = useAuthStore()

function getRoleLabel(role) {
  return ACCOUNT_ROLE[role]?.label ?? role
}
</script>

<template>
  <header
    class="h-14 bg-white/95 backdrop-blur-sm border-b border-outline flex items-center justify-between px-3 md:px-6 flex-shrink-0 z-10 shadow-shell pt-safe"
  >
    <div class="flex items-center gap-2 md:gap-3 min-w-0">
      <!-- 手机端汉堡按钮 -->
      <button
        type="button"
        class="md:hidden tap-target -ml-1 flex items-center justify-center rounded-lg text-on-surface-variant hover:bg-surface-container active:bg-surface-container"
        aria-label="打开菜单"
        @click="$emit('toggle-drawer')"
      >
        <span class="material-symbols-outlined text-[24px]">menu</span>
      </button>
      <h1 class="text-sm font-semibold text-on-surface truncate">{{ title }}</h1>
      <span class="hidden sm:inline-block h-4 w-px bg-outline shrink-0" aria-hidden="true" />
      <span class="hidden sm:inline text-xs text-on-surface-variant truncate">控制台</span>
    </div>
    <div class="flex items-center gap-2 md:gap-3 pl-2">
      <span
        class="hidden sm:inline-block text-[11px] uppercase tracking-wide text-on-surface-variant px-2 py-0.5 rounded-md bg-surface-container border border-outline-variant"
      >
        {{ getRoleLabel(auth.user?.role) }}
      </span>
      <div class="flex items-center gap-2 min-w-0">
        <div
          class="w-9 h-9 rounded-full bg-gradient-to-br from-primary-100 to-primary-200 flex items-center justify-center ring-2 ring-white shadow-sm shrink-0"
        >
          <span class="text-primary-800 text-xs font-semibold">
            {{ auth.user?.name?.charAt(0) ?? auth.user?.username?.charAt(0) ?? '?' }}
          </span>
        </div>
        <span class="hidden sm:inline text-sm font-medium text-on-surface truncate max-w-[8rem] md:max-w-[12rem]">
          {{ auth.user?.name || auth.user?.username }}
        </span>
      </div>
    </div>
  </header>
</template>
