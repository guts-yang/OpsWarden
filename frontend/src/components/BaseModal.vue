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
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4 sm:p-6"
        @click.self="$emit('cancel')"
      >
        <div
          class="bg-white rounded-2xl shadow-xl w-full max-w-md mx-3 sm:mx-auto max-h-[90vh] flex flex-col overflow-hidden"
        >
          <div class="px-5 sm:px-6 py-4 border-b border-outline flex-shrink-0">
            <h3 class="text-sm font-semibold text-on-surface">{{ title }}</h3>
          </div>
          <div class="px-5 sm:px-6 py-4 overflow-y-auto flex-1">
            <slot />
          </div>
          <div
            class="px-5 sm:px-6 py-3 border-t border-outline flex flex-col-reverse sm:flex-row sm:justify-end gap-2 flex-shrink-0 pb-safe sm:pb-3"
          >
            <button
              type="button"
              class="w-full sm:w-auto px-4 py-2.5 sm:py-1.5 text-sm rounded-lg border border-outline hover:bg-surface-container active:bg-surface-container transition-colors"
              @click="$emit('cancel')"
            >
              {{ cancelText }}
            </button>
            <button
              type="button"
              class="w-full sm:w-auto px-4 py-2.5 sm:py-1.5 text-sm rounded-lg text-white disabled:opacity-60 transition-colors"
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
