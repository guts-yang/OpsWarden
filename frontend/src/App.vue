<template>
  <RouterView v-slot="{ Component }">
    <KeepAlive include="AiChatView">
      <component :is="Component" />
    </KeepAlive>
  </RouterView>
</template>
