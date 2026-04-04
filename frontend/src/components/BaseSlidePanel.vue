<script setup>
defineProps({
  show: { type: Boolean, default: false },
  title: { type: String, default: '' },
  width: { type: String, default: '400px' },
})
defineEmits(['close'])
</script>

<template>
  <Teleport to="body">
    <!-- Overlay -->
    <Transition name="overlay">
      <div
        v-if="show"
        class="fixed inset-0 z-40 bg-black/20"
        @click="$emit('close')"
      />
    </Transition>
    <!-- Panel -->
    <Transition name="slide">
      <div
        v-if="show"
        class="fixed right-0 top-0 h-full z-50 bg-white shadow-2xl flex flex-col"
        :style="{ width }"
      >
        <div class="flex items-center justify-between px-5 py-4 border-b border-outline">
          <h3 class="text-sm font-semibold text-on-surface">{{ title }}</h3>
          <button
            class="w-7 h-7 flex items-center justify-center rounded hover:bg-surface-container"
            @click="$emit('close')"
          >
            <span class="material-symbols-outlined text-[18px] text-on-surface-variant">close</span>
          </button>
        </div>
        <div class="flex-1 overflow-y-auto p-5">
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
