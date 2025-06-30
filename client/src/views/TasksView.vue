<template>
  <div class="h-screen bg-white dark:bg-gray-900 text-gray-900 dark:text-white overflow-y-auto">
    <div class="max-w-4xl mx-auto p-6">
      <!-- Header -->
      <div class="mb-8">
        <div class="flex items-center justify-between mb-4">
          <h1 class="text-2xl font-semibold text-primary">Task Management</h1>
          <button
            @click="showCreateTask = true"
            class="btn-primary flex items-center gap-2"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
            </svg>
            New Task
          </button>
        </div>
        
        <!-- Stats -->
        <div class="grid grid-cols-4 gap-4 mb-6">
          <div class="card p-4">
            <div class="text-2xl font-semibold text-primary">{{ tasksStore.taskCount }}</div>
            <div class="text-sm text-secondary">Total Tasks</div>
          </div>
          <div class="card p-4">
            <div class="text-2xl font-semibold text-green-600 dark:text-green-400">{{ tasksStore.completedTasks.length }}</div>
            <div class="text-sm text-secondary">Completed</div>
          </div>
          <div class="card p-4">
            <div class="text-2xl font-semibold text-red-600 dark:text-red-400">{{ tasksStore.failedTasks.length }}</div>
            <div class="text-sm text-secondary">Failed</div>
          </div>
          <div class="card p-4">
            <div class="text-2xl font-semibold text-yellow-600 dark:text-yellow-400">{{ tasksStore.tasks.filter(t => t.status === 'in_progress' || t.status === 'pending').length }}</div>
            <div class="text-sm text-secondary">In Progress</div>
          </div>
        </div>

        <!-- Quick Task Input -->
        <div class="mb-6">
          <div class="relative">
            <input
              v-model="quickTaskDescription"
              @keydown.enter="handleQuickTaskEnter"
              type="text"
              placeholder="Type a task and press Enter to create it quickly..."
              class="input-field pl-10 pr-20"
              :disabled="isCreatingQuickTask"
            />
            <svg class="w-4 h-4 text-gray-400 dark:text-gray-500 absolute left-3 top-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
            </svg>
            <button
              @click="createQuickTask"
              :disabled="!quickTaskDescription.trim() || isCreatingQuickTask"
              class="absolute right-2 top-1.5 px-3 py-1 bg-primary text-white rounded text-sm hover:bg-primary-dark disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {{ isCreatingQuickTask ? '...' : 'Add' }}
            </button>
          </div>
        </div>

        <!-- Search -->
        <div class="relative">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search tasks..."
            class="input-field pl-10"
          />
          <svg class="w-4 h-4 text-gray-400 dark:text-gray-500 absolute left-3 top-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
          </svg>
        </div>
      </div>

      <!-- Task List -->
      <div class="space-y-3">
        <div 
          v-for="task in filteredTasks"
          :key="task.task_id"
          v-memo="[task.task_id, task.status, task.description, task.created_at]"
          class="card p-4 hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer transition-colors"
          @click="navigateToTask(task.task_id)"
        >
          <div class="flex items-start justify-between">
            <div class="flex-1">
              <div class="flex items-center gap-3 mb-2">
                <div class="flex items-center gap-1">
                  <div class="w-2 h-2 rounded-full" :class="getStatusColor(task.status)"></div>
                  <span class="text-sm text-secondary">
                    {{ getStatusText(task.status) }}
                  </span>
                </div>
                <span v-if="task.duration" class="text-xs text-gray-500 dark:text-gray-400">
                  {{ task.duration.toFixed(1) }}s
                </span>
              </div>
              <p class="text-primary mb-2">{{ task.description }}</p>
              <p class="text-xs text-muted">
                {{ formatDate(task.created_at) }}
              </p>
            </div>
            <button
              @click.stop="navigateToTask(task.task_id)"
              class="text-secondary hover:text-primary transition-colors"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
              </svg>
            </button>
          </div>
        </div>
        
        <div v-if="filteredTasks.length === 0" class="text-center py-12 text-muted">
          {{ tasksStore.tasks.length === 0 ? 'No tasks yet' : 'No tasks match your search' }}
        </div>
      </div>

      <!-- Create Task Modal -->
      <div v-if="showCreateTask" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="card p-6 w-96 max-w-full mx-4">
          <h3 class="text-lg font-semibold mb-4 text-primary">Create New Task</h3>
          <form @submit.prevent="createTask">
            <div class="mb-4">
              <textarea
                ref="taskTextarea"
                v-model="newTask.description"
                @keydown="handleTextareaKeydown"
                class="input-field"
                rows="4"
                placeholder="Describe what you want to do... (Enter to submit, Shift+Enter for new line)"
                required
              ></textarea>
              <div class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Press Enter to submit, Shift+Enter for new line
              </div>
            </div>
            <div class="flex gap-3 justify-end">
              <button
                type="button"
                @click="showCreateTask = false"
                class="btn-secondary"
              >
                Cancel
              </button>
              <button
                type="submit"
                class="btn-primary"
                :disabled="!newTask.description.trim() || isCreatingTask"
              >
                {{ isCreatingTask ? 'Creating...' : 'Create Task' }}
              </button>
            </div>
          </form>
        </div>
      </div>


    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { format } from 'date-fns'
import { useRouter } from 'vue-router'
import { useTasksStore } from '@/stores/tasks'
import { apiService } from '@/services/api'
import type { TaskResponse } from '@/types/api'

const router = useRouter()
const tasksStore = useTasksStore()

const searchQuery = ref('')
const debouncedSearchQuery = ref('')
const quickTaskDescription = ref('')
const isCreatingQuickTask = ref(false)
const taskTextarea = ref<HTMLTextAreaElement>()

// Debounce search input for better performance
let searchTimeout: ReturnType<typeof setTimeout> | null = null
watch(searchQuery, (newValue) => {
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }
  searchTimeout = setTimeout(() => {
    debouncedSearchQuery.value = newValue
  }, 300) // 300ms debounce
})
const showCreateTask = ref(false)
const isCreatingTask = ref(false)

const newTask = ref({
  description: ''
})

const filteredTasks = computed(() => {
  let tasks = tasksStore.tasks

  if (debouncedSearchQuery.value) {
    const query = debouncedSearchQuery.value.toLowerCase()
    tasks = tasks.filter(task => 
      task.description.toLowerCase().includes(query) ||
      task.task_id.toLowerCase().includes(query) ||
      task.status.toLowerCase().includes(query)
    )
  }

  return tasks.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
})

const createTask = async () => {
  if (!newTask.value.description.trim()) return

  isCreatingTask.value = true
  try {
    const task = await apiService.executeTask({
      description: newTask.value.description
    })
    
    tasksStore.addTask(task)
    
    // Reset form
    newTask.value = { description: '' }
    showCreateTask.value = false
  } catch (error) {
    console.error('Failed to create task:', error)
  } finally {
    isCreatingTask.value = false
  }
}

const createQuickTask = async () => {
  if (!quickTaskDescription.value.trim()) return

  isCreatingQuickTask.value = true
  try {
    const task = await apiService.executeTask({
      description: quickTaskDescription.value
    })
    
    tasksStore.addTask(task)
    
    // Reset input
    quickTaskDescription.value = ''
  } catch (error) {
    console.error('Failed to create quick task:', error)
  } finally {
    isCreatingQuickTask.value = false
  }
}

const handleQuickTaskEnter = (event: KeyboardEvent) => {
  if (!event.shiftKey) {
    event.preventDefault()
    createQuickTask()
  }
}

const handleTextareaKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    createTask()
  }
}

const navigateToTask = (taskId: string) => {
  router.push(`/tasks/${taskId}`)
}

const formatDate = (dateString: string) => {
  try {
    return format(new Date(dateString), 'MMM d, h:mm a')
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
  tasksStore.fetchTasks()
})
</script> 