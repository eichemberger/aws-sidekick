<template>
  <div class="card hover:shadow-md transition-shadow duration-200">
    <div class="flex items-start justify-between">
      <div class="flex-1">
        <div class="flex items-center space-x-2 mb-2">
          <component 
            :is="statusIcon" 
            class="w-5 h-5" 
            :class="statusIconClass"
          />
          <span class="text-sm font-medium" :class="statusTextClass">
            {{ statusText }}
          </span>
        </div>
        
        <h3 class="text-lg font-medium text-gray-900 mb-2">
          {{ task.description }}
        </h3>
        
        <div class="text-sm text-gray-600 space-y-1">
          <p>
            <span class="font-medium">Created:</span>
            {{ formatDate(task.created_at) }}
          </p>
          <p v-if="task.completed_at">
            <span class="font-medium">Completed:</span>
            {{ formatDate(task.completed_at) }}
          </p>
          <p v-if="task.duration">
            <span class="font-medium">Duration:</span>
            {{ formatDuration(task.duration) }}
          </p>
        </div>
      </div>
      
      <div class="flex-shrink-0 ml-4">
        <button
          @click="$emit('view-details', task)"
          class="btn-secondary text-sm"
        >
          View Details
        </button>
      </div>
    </div>
    
    <!-- Error Message -->
    <div 
      v-if="task.status === 'failed' && task.error_message"
      class="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg"
    >
      <p class="text-sm text-red-800">
        <strong>Error:</strong> {{ task.error_message }}
      </p>
    </div>
    
    <!-- Result Preview -->
    <div 
      v-if="task.status === 'completed' && task.result"
      class="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg"
    >
      <p class="text-sm text-green-800 font-medium mb-2">Result:</p>
      <div class="text-sm text-green-700 max-h-32 overflow-y-auto">
        {{ truncateResult(task.result) }}
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
      return 'text-blue-500 animate-spin'
    case 'pending':
    default:
      return 'text-yellow-500'
  }
})

const statusTextClass = computed(() => {
  switch (props.task.status) {
    case 'completed':
      return 'text-green-700'
    case 'failed':
      return 'text-red-700'
    case 'in_progress':
      return 'text-blue-700'
    case 'pending':
    default:
      return 'text-yellow-700'
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