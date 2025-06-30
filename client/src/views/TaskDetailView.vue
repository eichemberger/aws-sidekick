<template>
  <div class="h-screen bg-white dark:bg-gray-900 text-gray-900 dark:text-white overflow-y-auto">
    <div class="max-w-4xl mx-auto p-6">
      <!-- Header with Back Button -->
      <div class="flex items-center gap-4 mb-6">
        <button
          @click="goBack"
          class="flex items-center gap-2 text-secondary hover:text-primary transition-colors"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path>
          </svg>
          Back to Tasks
        </button>
        <div class="h-6 w-px bg-gray-300 dark:bg-gray-600"></div>
        <h1 class="text-2xl font-semibold text-primary">Task Details</h1>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="flex items-center justify-center py-12">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="card p-6 border-red-200 dark:border-red-800">
        <div class="flex items-center gap-3 text-red-700 dark:text-red-400">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
          <span>{{ error }}</span>
        </div>
      </div>

      <!-- Task Details -->
      <div v-else-if="task" class="space-y-6">
        <!-- Task Info Card -->
        <div class="card p-6">
          <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <h3 class="text-sm font-medium text-secondary mb-2">Status</h3>
              <div class="flex items-center gap-2">
                <div class="w-3 h-3 rounded-full" :class="getStatusColor(task.status)"></div>
                <span class="text-primary font-medium">{{ getStatusText(task.status) }}</span>
              </div>
            </div>
            <div>
              <h3 class="text-sm font-medium text-secondary mb-2">Created</h3>
              <p class="text-primary">{{ formatDate(task.created_at) }}</p>
            </div>
            <div v-if="task.completed_at">
              <h3 class="text-sm font-medium text-secondary mb-2">Completed</h3>
              <p class="text-primary">{{ formatDate(task.completed_at) }}</p>
            </div>
            <div v-if="task.duration">
              <h3 class="text-sm font-medium text-secondary mb-2">Duration</h3>
              <p class="text-primary">{{ task.duration.toFixed(2) }}s</p>
            </div>
            <div class="md:col-span-2">
              <h3 class="text-sm font-medium text-secondary mb-2">Task ID</h3>
              <p class="text-primary font-mono text-sm">{{ task.task_id }}</p>
            </div>
          </div>
        </div>

        <!-- Description Card -->
        <div class="card p-6">
          <h3 class="text-lg font-medium text-primary mb-4">Description</h3>
          <p class="text-secondary leading-relaxed">{{ task.description }}</p>
        </div>

        <!-- Result Card -->
        <div v-if="task.result" class="card p-6">
          <h3 class="text-lg font-medium text-primary mb-4">Result</h3>
          <div 
            class="prose prose-gray dark:prose-invert max-w-none"
            v-html="renderedMarkdown"
          ></div>
        </div>

        <!-- Error Card -->
        <div v-if="task.error_message" class="card p-6 border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/10">
          <h3 class="text-lg font-medium text-red-700 dark:text-red-400 mb-4">Error</h3>
          <pre class="text-red-700 dark:text-red-400 bg-red-100 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-4 rounded text-sm overflow-x-auto whitespace-pre-wrap">{{ task.error_message }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { format } from 'date-fns'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import 'highlight.js/styles/github-dark.css'
import { apiService } from '@/services/api'
import type { TaskResponse } from '@/types/api'

const route = useRoute()
const router = useRouter()

const task = ref<TaskResponse | null>(null)
const isLoading = ref(true)
const error = ref<string | null>(null)

// Configure markdown parser with syntax highlighting
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
  highlight: function (str: string, lang: string) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(str, { language: lang }).value
      } catch (error) {
        console.warn('Highlight.js error:', error)
      }
    }
    return '' // use external default escaping
  }
})

const renderedMarkdown = computed(() => {
  if (!task.value?.result) return ''
  try {
    return md.render(task.value.result)
  } catch (error) {
    console.error('Markdown rendering error:', error)
    return `<pre class="text-red-500">Error rendering markdown: ${error}</pre>`
  }
})

const fetchTask = async () => {
  const taskId = route.params.id as string
  if (!taskId) {
    error.value = 'Task ID not provided'
    isLoading.value = false
    return
  }

  try {
    isLoading.value = true
    error.value = null
    
    // Fetch all tasks and find the specific one
    // Since we don't have a direct task endpoint, we'll get it from the tasks list
    const tasks = await apiService.getTasks()
    const foundTask = tasks.find(t => t.task_id === taskId)
    
    if (!foundTask) {
      error.value = 'Task not found'
    } else {
      task.value = foundTask
    }
  } catch (err) {
    console.error('Failed to fetch task:', err)
    error.value = 'Failed to load task details'
  } finally {
    isLoading.value = false
  }
}

const goBack = () => {
  router.push('/tasks')
}

const formatDate = (dateString: string) => {
  try {
    return format(new Date(dateString), 'MMM d, yyyy h:mm a')
  } catch (error) {
    return dateString
  }
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'completed':
      return 'bg-green-400'
    case 'failed':
      return 'bg-red-400'
    case 'in_progress':
      return 'bg-blue-400'
    case 'pending':
    default:
      return 'bg-yellow-400'
  }
}

const getStatusText = (status: string) => {
  return status.charAt(0).toUpperCase() + status.slice(1).replace('_', ' ')
}

onMounted(() => {
  fetchTask()
})
</script>

<style scoped>
/* Custom prose styles for better markdown rendering */
:deep(.prose) {
  @apply text-gray-700 dark:text-gray-300;
}

:deep(.prose h1) {
  @apply text-2xl font-bold text-gray-900 dark:text-white mb-4 mt-6;
}

:deep(.prose h2) {
  @apply text-xl font-semibold text-gray-900 dark:text-white mb-3 mt-5;
}

:deep(.prose h3) {
  @apply text-lg font-medium text-gray-900 dark:text-white mb-2 mt-4;
}

:deep(.prose p) {
  @apply mb-4 leading-relaxed;
}

:deep(.prose ul) {
  @apply mb-4 pl-6;
}

:deep(.prose ol) {
  @apply mb-4 pl-6;
}

:deep(.prose li) {
  @apply mb-1;
}

:deep(.prose code) {
  @apply bg-gray-100 dark:bg-gray-800 px-1 py-0.5 rounded text-sm font-mono;
}

:deep(.prose pre) {
  @apply bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 p-4 rounded-lg overflow-x-auto mb-4;
}

:deep(.prose pre code) {
  @apply bg-transparent p-0;
}

:deep(.prose blockquote) {
  @apply border-l-4 border-gray-300 dark:border-gray-600 pl-4 italic text-gray-600 dark:text-gray-400 mb-4;
}

:deep(.prose table) {
  @apply w-full border-collapse border border-gray-300 dark:border-gray-600 mb-4;
}

:deep(.prose th) {
  @apply border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-800 px-4 py-2 text-left font-medium;
}

:deep(.prose td) {
  @apply border border-gray-300 dark:border-gray-600 px-4 py-2;
}

:deep(.prose a) {
  @apply text-blue-600 dark:text-blue-400 hover:underline;
}
</style> 