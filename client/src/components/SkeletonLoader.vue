<template>
  <div class="skeleton-loader" :class="containerClass">
    <!-- Message List Skeleton -->
    <div v-if="type === 'messages'" class="space-y-6">
      <div v-for="i in count" :key="i" class="flex gap-4">
        <div class="w-10 h-10 bg-gray-200 dark:bg-gray-700 rounded-xl animate-pulse"></div>
        <div class="flex-1 space-y-2">
          <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-3/4"></div>
          <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-1/2"></div>
          <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-5/6"></div>
        </div>
      </div>
    </div>

    <!-- Task List Skeleton -->
    <div v-else-if="type === 'tasks'" class="space-y-4">
      <div v-for="i in count" :key="i" class="p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <div class="flex items-center gap-2 mb-2">
              <div class="w-5 h-5 bg-gray-200 dark:bg-gray-700 rounded-full animate-pulse"></div>
              <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-20"></div>
            </div>
            <div class="h-5 bg-gray-200 dark:bg-gray-700 rounded animate-pulse mb-2"></div>
            <div class="h-3 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-32"></div>
          </div>
          <div class="w-20 h-8 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"></div>
        </div>
      </div>
    </div>

    <!-- Text Lines Skeleton -->
    <div v-else-if="type === 'text'" class="space-y-2">
      <div v-for="i in count" :key="i" 
           :class="[
             'h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse',
             i === count ? 'w-2/3' : 'w-full'
           ]"></div>
    </div>

    <!-- Card Skeleton -->
    <div v-else-if="type === 'card'" class="p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
      <div class="h-6 bg-gray-200 dark:bg-gray-700 rounded animate-pulse mb-3"></div>
      <div class="space-y-2">
        <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"></div>
        <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-3/4"></div>
      </div>
    </div>

    <!-- Custom Skeleton -->
    <div v-else class="space-y-2">
      <div v-for="i in count" :key="i" 
           class="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"
           :style="{ width: getRandomWidth() }"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  type?: 'messages' | 'tasks' | 'text' | 'card' | 'custom'
  count?: number
  containerClass?: string
}

const props = withDefaults(defineProps<Props>(), {
  type: 'text',
  count: 3,
  containerClass: ''
})

const getRandomWidth = () => {
  const widths = ['100%', '90%', '80%', '70%', '85%', '95%']
  return widths[Math.floor(Math.random() * widths.length)]
}
</script>

<style scoped>
/* Respect reduced motion preferences */
@media (prefers-reduced-motion: reduce) {
  .animate-pulse {
    animation: none;
    opacity: 0.6;
  }
}
</style> 