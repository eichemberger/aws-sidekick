<template>
  <div class="card hover:shadow-md transition-all duration-200 group">
    <div class="flex items-start justify-between">
      <div class="flex-1">
        <div class="flex items-center space-x-2 mb-2">
          <div class="relative">
            <component 
              :is="statusIcon" 
              class="w-5 h-5" 
              :class="statusIconClass"
            />
            <!-- Subtle pulse for in-progress tasks instead of spinning -->
            <div 
              v-if="task.status === 'in_progress'"
              class="absolute inset-0 w-5 h-5 rounded-full border-2 border-blue-500/30 animate-ping"
            ></div>
          </div>
          <span class="text-sm font-medium" :class="statusTextClass">
            {{ statusText }}
          </span>
          <span v-if="task.duration" class="text-xs text-gray-500 dark:text-gray-400">
            {{ formatDuration(task.duration) }}
          </span>
        </div>
        
        <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
          {{ task.description }}
        </h3>
        
        <div class="text-sm text-gray-600 dark:text-gray-400 space-y-1">
          <p>
            <span class="font-medium">Created:</span>
            {{ formatDate(task.created_at) }}
          </p>
          <p v-if="task.completed_at">
            <span class="font-medium">Completed:</span>
            {{ formatDate(task.completed_at) }}
          </p>
        </div>
      </div>
      
      <div class="flex-shrink-0 ml-4">
        <button
          @click="$emit('view-details', task)"
          class="btn-secondary text-sm opacity-0 group-hover:opacity-100 transition-opacity duration-200"
        >
          View Details
        </button>
      </div>
    </div>
    
    <!-- Error Message -->
    <div 
      v-if="task.status === 'failed' && task.error_message"
      class="mt-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg"
    >
      <p class="text-sm text-red-800 dark:text-red-200">
        <strong>Error:</strong> {{ task.error_message }}
      </p>
    </div>
    
    <!-- Result Preview -->
    <div 
      v-if="task.status === 'completed' && task.result"
      class="mt-4 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg"
    >
      <p class="text-sm text-green-800 dark:text-green-200 font-medium mb-2">Result:</p>
      <div class="text-sm text-green-700 dark:text-green-300 max-h-32 overflow-y-auto">
        {{ truncateResult(task.result) }}
      </div>
    </div>

    <!-- In Progress Indicator -->
    <div 
      v-if="task.status === 'in_progress'"
      class="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg"
    >
      <div class="flex items-center gap-2">
        <div class="w-4 h-1 bg-blue-200 dark:bg-blue-800 rounded-full overflow-hidden">
          <div class="w-full h-full bg-blue-500 animate-pulse-progress"></div>
        </div>
        <span class="text-sm text-blue-700 dark:text-blue-300">Processing...</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { 
  ClockIcon, 
  CheckCircleIcon, 
  ExclamationCircleIcon,
  PlayIcon
} from '@heroicons/vue/24/outline'
import { format } from 'date-fns'
import type { TaskResponse } from '@/types/api'

interface Props {
  task: TaskResponse
}

interface Emits {
  (e: 'view-details', task: TaskResponse): void
}

const props = defineProps<Props>()
defineEmits<Emits>()

const statusIcon = computed(() => {
  switch (props.task.status) {
    case 'completed':
      return CheckCircleIcon
    case 'failed':
      return ExclamationCircleIcon
    case 'in_progress':
      return PlayIcon
    case 'pending':
    default:
      return ClockIcon
  }
})

const statusIconClass = computed(() => {
  switch (props.task.status) {
    case 'completed':
      return 'text-green-500'
    case 'failed':
      return 'text-red-500'
    case 'in_progress':
      return 'text-blue-500'
    case 'pending':
    default:
      return 'text-yellow-500'
  }
})

const statusTextClass = computed(() => {
  switch (props.task.status) {
    case 'completed':
      return 'text-green-700 dark:text-green-400'
    case 'failed':
      return 'text-red-700 dark:text-red-400'
    case 'in_progress':
      return 'text-blue-700 dark:text-blue-400'
    case 'pending':
    default:
      return 'text-yellow-700 dark:text-yellow-400'
  }
})

const statusText = computed(() => {
  return props.task.status.charAt(0).toUpperCase() + props.task.status.slice(1).replace('_', ' ')
})

const formatDate = (dateString: string) => {
  try {
    return format(new Date(dateString), 'MMM d, yyyy h:mm a')
  } catch (error) {
    return dateString
  }
}

const formatDuration = (seconds: number) => {
  if (seconds < 60) {
    return `${Math.round(seconds)}s`
  } else if (seconds < 3600) {
    return `${Math.round(seconds / 60)}m ${Math.round(seconds % 60)}s`
  } else {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.round((seconds % 3600) / 60)
    return `${hours}h ${minutes}m`
  }
}

const truncateResult = (result: string) => {
  const maxLength = 200
  if (result.length <= maxLength) return result
  return result.substring(0, maxLength) + '...'
}
</script>

<style scoped>
@keyframes pulse-progress {
  0%, 100% {
    opacity: 0.5;
  }
  50% {
    opacity: 1;
  }
}

.animate-pulse-progress {
  animation: pulse-progress 2s ease-in-out infinite;
}

/* Respect reduced motion preferences */
@media (prefers-reduced-motion: reduce) {
  .animate-ping,
  .animate-pulse-progress {
    animation: none;
    opacity: 0.7;
  }
}
</style> 