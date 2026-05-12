<script setup>
import { computed } from 'vue'

const props = defineProps({
  total: { type: Number, required: true },
  page: { type: Number, required: true },
  pageSize: { type: Number, default: 10 },
})
const emit = defineEmits(['update:page'])

const totalPages = computed(() => Math.ceil(props.total / props.pageSize))
const start = computed(() => (props.page - 1) * props.pageSize + 1)
const end = computed(() => Math.min(props.page * props.pageSize, props.total))
</script>

<template>
  <div v-if="total > 0" class="flex items-center justify-between mt-4">
    <span class="text-xs text-on-surface-variant">
      显示 {{ start }}–{{ end }} / 共 {{ total }} 条
    </span>
    <div class="flex items-center gap-1">
      <button
        class="px-2 py-1 text-xs rounded border border-outline hover:bg-surface-container disabled:opacity-40"
        :disabled="page <= 1"
        @click="emit('update:page', page - 1)"
      >
        上一页
      </button>
      <span class="px-3 py-1 text-xs">{{ page }} / {{ totalPages }}</span>
      <button
        class="px-2 py-1 text-xs rounded border border-outline hover:bg-surface-container disabled:opacity-40"
        :disabled="page >= totalPages"
        @click="emit('update:page', page + 1)"
      >
        下一页
      </button>
    </div>
  </div>
</template>
