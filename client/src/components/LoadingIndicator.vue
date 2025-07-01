<template>
  <div class="loading-indicator">
    <!-- Subtle Top Progress Bar -->
    <div 
      v-if="isLoading" 
      class="fixed top-0 left-0 right-0 h-0.5 bg-blue-500/10 z-50"
    >
      <div class="h-full bg-gradient-to-r from-blue-500 to-purple-500 animate-pulse-progress"></div>
    </div>

    <!-- Optional Backdrop with Skeleton -->
    <div 
      v-if="showBackdrop && isLoading"
      class="fixed inset-0 bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm z-40 flex items-center justify-center"
    >
      <div class="text-center">
        <div class="inline-flex items-center gap-3 px-6 py-4 bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700">
          <div class="w-5 h-5 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin-smooth"></div>
          <span class="text-gray-700 dark:text-gray-300 font-medium">{{ loadingMessage }}</span>
        </div>
      </div>
    </div>

    <!-- Skeleton Loading for Content -->
    <div v-if="isLoading && showSkeleton" class="space-y-4 p-4">
      <div class="animate-pulse">
        <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2"></div>
        <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-2"></div>
        <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-5/6"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  isLoading: boolean
  loadingMessage?: string
  showBackdrop?: boolean
  showSkeleton?: boolean
}

withDefaults(defineProps<Props>(), {
  loadingMessage: 'Loading...',
  showBackdrop: false,
  showSkeleton: false
})
</script>

<style scoped>
@keyframes pulse-progress {
  0%, 100% {
    opacity: 0.5;
    transform: scaleX(0);
    transform-origin: left;
  }
  50% {
    opacity: 1;
    transform: scaleX(1);
  }
}

@keyframes spin-smooth {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.animate-pulse-progress {
  animation: pulse-progress 2s ease-in-out infinite;
}

.animate-spin-smooth {
  animation: spin-smooth 1s linear infinite;
}

/* Respect user's motion preferences */
@media (prefers-reduced-motion: reduce) {
  .animate-pulse-progress,
  .animate-spin-smooth {
    animation: none;
  }
  
  .animate-pulse-progress {
    opacity: 1;
    transform: scaleX(1);
  }
  
  .animate-spin-smooth::after {
    content: '⏳';
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    background: inherit;
    border: none;
    border-radius: inherit;
  }
}
</style> 