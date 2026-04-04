<script setup>
import { useAuthStore } from '@/stores/auth'
import { ACCOUNT_ROLE } from '@/utils/constants'

defineProps({ title: { type: String, default: '' } })

const auth = useAuthStore()

function getRoleLabel(role) {
  return ACCOUNT_ROLE[role]?.label ?? role
}
</script>

<template>
  <header class="h-14 bg-white border-b border-outline flex items-center justify-between px-6 flex-shrink-0">
    <h1 class="text-sm font-semibold text-on-surface">{{ title }}</h1>
    <div class="flex items-center gap-2">
      <span class="text-xs text-on-surface-variant">{{ getRoleLabel(auth.user?.role) }}</span>
      <div class="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center">
        <span class="text-primary-700 text-xs font-semibold">
          {{ auth.user?.name?.charAt(0) ?? auth.user?.username?.charAt(0) ?? '?' }}
        </span>
      </div>
      <span class="text-sm font-medium text-on-surface">{{ auth.user?.name }}</span>
    </div>
  </header>
</template>
