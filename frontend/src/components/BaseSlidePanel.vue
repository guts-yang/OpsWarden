<script setup>
import { computed, watch } from 'vue'

const props = defineProps({
  show: { type: Boolean, default: false },
  title: { type: String, default: '' },
  /** PC 端宽度；手机端始终全屏 100% */
  width: { type: String, default: '400px' },
})
defineEmits(['close'])

// 仅 PC 端应用 width 样式
const pcStyle = computed(() => ({ '--panel-w': props.width }))

// 打开时锁定 body 滚动（仅手机端有效）
watch(
  () => props.show,
  (open) => {
    if (typeof document === 'undefined') return
    if (open && window.matchMedia('(max-width: 767px)').matches) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
  },
)
</script>

<template>
  <Teleport to="body">
    <!-- Overlay -->
    <Transition name="overlay">
      <div
        v-if="show"
        class="fixed inset-0 z-40 bg-black/30 backdrop-blur-sm"
        @click="$emit('close')"
      />
    </Transition>
    <!-- Panel：手机端全屏覆盖；PC 端右侧滑入固定宽度 -->
    <Transition name="slide">
      <div
        v-if="show"
        class="fixed top-0 right-0 z-50 bg-white shadow-2xl flex flex-col
               h-[100dvh] w-full
               md:w-[var(--panel-w)] md:max-w-[90vw]"
        :style="pcStyle"
      >
        <div
          class="flex items-center justify-between gap-2 px-3 md:px-5 py-3 md:py-4 border-b border-outline flex-shrink-0 pt-safe"
        >
          <!-- 手机端返回箭头 + 标题；PC 端仅标题 -->
          <button
            class="md:hidden tap-target -ml-1 flex items-center justify-center rounded-lg text-on-surface-variant hover:bg-surface-container active:bg-surface-container"
            aria-label="返回"
            @click="$emit('close')"
          >
            <span class="material-symbols-outlined text-[22px]">arrow_back</span>
          </button>
          <h3 class="flex-1 text-sm font-semibold text-on-surface truncate">{{ title }}</h3>
          <!-- PC 端关闭按钮 -->
          <button
            class="hidden md:flex w-7 h-7 items-center justify-center rounded hover:bg-surface-container"
            aria-label="关闭"
            @click="$emit('close')"
          >
            <span class="material-symbols-outlined text-[18px] text-on-surface-variant">close</span>
          </button>
        </div>
        <div class="flex-1 overflow-y-auto p-4 md:p-5 pb-safe">
          <slot />
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.overlay-enter-active,
.overlay-leave-active {
  transition: opacity 0.2s ease;
}
.overlay-enter-from,
.overlay-leave-to {
  opacity: 0;
}
.slide-enter-active,
.slide-leave-active {
  transition: transform 0.25s ease;
}
.slide-enter-from,
.slide-leave-to {
  transform: translateX(100%);
}
</style>
