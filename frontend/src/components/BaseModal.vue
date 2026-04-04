<script setup>
defineProps({
  show: { type: Boolean, default: false },
  title: { type: String, default: '' },
  confirmText: { type: String, default: '确认' },
  cancelText: { type: String, default: '取消' },
  loading: { type: Boolean, default: false },
  danger: { type: Boolean, default: false },
})
defineEmits(['confirm', 'cancel'])
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="show"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4"
        @click.self="$emit('cancel')"
      >
        <div class="bg-white rounded-xl shadow-xl w-full max-w-md">
          <div class="px-6 py-4 border-b border-outline">
            <h3 class="text-sm font-semibold text-on-surface">{{ title }}</h3>
          </div>
          <div class="px-6 py-4">
            <slot />
          </div>
          <div class="px-6 py-3 border-t border-outline flex justify-end gap-2">
            <button
              class="px-4 py-1.5 text-sm rounded-lg border border-outline hover:bg-surface-container"
              @click="$emit('cancel')"
            >
              {{ cancelText }}
            </button>
            <button
              class="px-4 py-1.5 text-sm rounded-lg text-white disabled:opacity-60"
              :class="danger ? 'bg-error hover:bg-red-700' : 'bg-primary-500 hover:bg-primary-600'"
              :disabled="loading"
              @click="$emit('confirm')"
            >
              {{ loading ? '处理中...' : confirmText }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.15s ease;
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
</style>
