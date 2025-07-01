<template>
  <div class="typing-indicator px-4 py-3 rounded-lg mx-4 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
    <div class="flex items-center gap-3">
      <!-- AI Avatar -->
      <div class="w-8 h-8 rounded-full bg-gradient-to-br from-emerald-500 to-green-600 flex items-center justify-center shadow-sm">
        <span class="text-white text-xs font-semibold">AI</span>
      </div>
      
      <!-- Typing Animation -->
      <div class="flex items-center gap-2">
        <div class="flex gap-1">
          <div class="w-2 h-2 bg-emerald-500 rounded-full animate-typing-dot"></div>
          <div class="w-2 h-2 bg-emerald-500 rounded-full animate-typing-dot-delay-1"></div>
          <div class="w-2 h-2 bg-emerald-500 rounded-full animate-typing-dot-delay-2"></div>
        </div>
        <span class="text-gray-600 dark:text-gray-300 text-sm">{{ loadingMessage }}</span>
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

<style scoped>
@keyframes typing-bounce {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.4;
  }
  30% {
    transform: translateY(-4px);
    opacity: 1;
  }
}

.animate-typing-dot {
  animation: typing-bounce 1.4s ease-in-out infinite;
}

.animate-typing-dot-delay-1 {
  animation: typing-bounce 1.4s ease-in-out infinite;
  animation-delay: 0.2s;
}

.animate-typing-dot-delay-2 {
  animation: typing-bounce 1.4s ease-in-out infinite;
  animation-delay: 0.4s;
}

/* Respect reduced motion preferences */
@media (prefers-reduced-motion: reduce) {
  .animate-typing-dot,
  .animate-typing-dot-delay-1,
  .animate-typing-dot-delay-2 {
    animation: none;
    opacity: 0.7;
  }
}
</style> 