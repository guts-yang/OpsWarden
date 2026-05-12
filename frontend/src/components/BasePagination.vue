<script setup>
import { computed } from 'vue'

const props = defineProps({
  total: { type: Number, required: true },
  page: { type: Number, required: true },
  pageSize: { type: Number, default: 10 },
})
const emit = defineEmits(['update:page'])

const totalPages = computed(() => Math.max(1, Math.ceil(props.total / props.pageSize)))
const start = computed(() => (props.page - 1) * props.pageSize + 1)
const end = computed(() => Math.min(props.page * props.pageSize, props.total))
</script>

<template>
  <div
    v-if="total > 0"
    class="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-2 mt-4"
  >
    <span class="text-xs text-on-surface-variant text-center sm:text-left">
      显示 {{ start }}–{{ end }} / 共 {{ total }} 条
    </span>
    <div class="flex items-center justify-center gap-1.5">
      <button
        type="button"
        class="px-3 py-2 sm:py-1 text-xs rounded-lg sm:rounded border border-outline hover:bg-surface-container active:bg-surface-container disabled:opacity-40 transition-colors"
        :disabled="page <= 1"
        @click="emit('update:page', page - 1)"
      >
        上一页
      </button>
      <span class="px-3 py-2 sm:py-1 text-xs tabular-nums text-on-surface">
        {{ page }} / {{ totalPages }}
      </span>
      <button
        type="button"
        class="px-3 py-2 sm:py-1 text-xs rounded-lg sm:rounded border border-outline hover:bg-surface-container active:bg-surface-container disabled:opacity-40 transition-colors"
        :disabled="page >= totalPages"
        @click="emit('update:page', page + 1)"
      >
        下一页
      </button>
    </div>
  </div>
</template>
