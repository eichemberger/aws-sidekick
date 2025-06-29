<template>
  <div class="px-6 py-8 rounded-2xl mx-4 bg-gray-800/50 border border-gray-700/50">
    <div class="flex gap-4">
      <div class="flex-shrink-0">
        <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center shadow-lg">
          <span class="text-white text-sm font-semibold">AI</span>
        </div>
      </div>
      <div class="flex-1">
        <div class="flex items-center gap-2 mt-2">
          <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
          <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
          <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
          <span class="text-gray-400 text-sm ml-2">{{ loadingMessage }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  loadingMessage: string
}

defineProps<Props>()
</script> 