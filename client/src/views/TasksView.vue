<template>
  <div class="h-screen bg-gray-900 text-white overflow-y-auto">
    <div class="max-w-4xl mx-auto p-6">
      <!-- Header -->
      <div class="mb-8">
        <div class="flex items-center justify-between mb-4">
          <h1 class="text-2xl font-semibold">Task Management</h1>
          <button
            @click="showCreateTask = true"
            class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors flex items-center gap-2"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
            </svg>
            New Task
          </button>
        </div>
        
        <!-- Stats -->
        <div class="grid grid-cols-4 gap-4 mb-6">
          <div class="bg-gray-800 rounded-lg p-4">
            <div class="text-2xl font-semibold text-white">{{ tasksStore.taskCount }}</div>
            <div class="text-sm text-gray-400">Total Tasks</div>
          </div>
          <div class="bg-gray-800 rounded-lg p-4">
            <div class="text-2xl font-semibold text-green-400">{{ tasksStore.completedTasks.length }}</div>
            <div class="text-sm text-gray-400">Completed</div>
          </div>
          <div class="bg-gray-800 rounded-lg p-4">
            <div class="text-2xl font-semibold text-red-400">{{ tasksStore.failedTasks.length }}</div>
            <div class="text-sm text-gray-400">Failed</div>
          </div>
          <div class="bg-gray-800 rounded-lg p-4">
            <div class="text-2xl font-semibold text-yellow-400">{{ tasksStore.tasks.filter(t => t.status === 'in_progress' || t.status === 'pending').length }}</div>
            <div class="text-sm text-gray-400">In Progress</div>
          </div>
        </div>

        <!-- Search -->
        <div class="relative">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search tasks..."
            class="w-full bg-gray-800 border border-gray-600 rounded-lg px-4 py-2 pl-10 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <svg class="w-4 h-4 text-gray-400 absolute left-3 top-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
          class="bg-gray-800 border border-gray-700 rounded-lg p-4 hover:bg-gray-750 cursor-pointer transition-colors"
          @click="viewTaskDetails(task)"
        >
          <div class="flex items-start justify-between">
            <div class="flex-1">
              <div class="flex items-center gap-3 mb-2">
                <span class="px-2 py-1 rounded text-xs bg-gray-700 text-gray-300">
                  {{ task.task_type }}
                </span>
                <div class="flex items-center gap-1">
                  <div class="w-2 h-2 rounded-full" :class="getStatusColor(task.status)"></div>
                  <span class="text-sm text-gray-400">
                    {{ getStatusText(task.status) }}
                  </span>
                </div>
              </div>
              <p class="text-white mb-2">{{ task.description }}</p>
              <p class="text-xs text-gray-500">
                {{ formatDate(task.created_at) }}
              </p>
            </div>
            <button
              @click.stop="viewTaskDetails(task)"
              class="text-gray-400 hover:text-white transition-colors"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
              </svg>
            </button>
          </div>
        </div>
        
        <div v-if="filteredTasks.length === 0" class="text-center py-12 text-gray-500">
          {{ tasksStore.tasks.length === 0 ? 'No tasks yet' : 'No tasks match your search' }}
        </div>
      </div>

      <!-- Create Task Modal -->
      <div v-if="showCreateTask" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-gray-800 rounded-lg p-6 w-96 max-w-full mx-4 border border-gray-700">
          <h3 class="text-lg font-semibold mb-4 text-white">Create New Task</h3>
          <form @submit.prevent="createTask">
            <div class="mb-4">
              <textarea
                v-model="newTask.description"
                class="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                rows="4"
                placeholder="Describe what you want to do..."
                required
              ></textarea>
            </div>
            <div class="flex gap-3 justify-end">
              <button
                type="button"
                @click="showCreateTask = false"
                class="px-4 py-2 border border-gray-600 text-gray-300 rounded-lg hover:bg-gray-700 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                :disabled="!newTask.description.trim() || isCreatingTask"
              >
                {{ isCreatingTask ? 'Creating...' : 'Create Task' }}
              </button>
            </div>
          </form>
        </div>
      </div>

      <!-- Task Details Modal -->
      <div v-if="selectedTask" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-gray-800 rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto border border-gray-700">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-white">Task Details</h3>
            <button
              @click="selectedTask = null"
              class="text-gray-400 hover:text-white text-xl"
            >
              ×
            </button>
          </div>
          
          <div class="space-y-4 text-sm">
            <div class="grid grid-cols-2 gap-4">
              <div>
                <span class="text-gray-400">ID:</span>
                <p class="text-white font-mono">{{ selectedTask.task_id }}</p>
              </div>
              <div>
                <span class="text-gray-400">Status:</span>
                <div class="flex items-center gap-2 mt-1">
                  <div class="w-2 h-2 rounded-full" :class="getStatusColor(selectedTask.status)"></div>
                  <span class="text-white">{{ getStatusText(selectedTask.status) }}</span>
                </div>
              </div>
              <div>
                <span class="text-gray-400">Type:</span>
                <p class="text-white">{{ selectedTask.task_type }}</p>
              </div>
              <div>
                <span class="text-gray-400">Created:</span>
                <p class="text-white">{{ formatDate(selectedTask.created_at) }}</p>
              </div>
            </div>
            
            <div>
              <span class="text-gray-400">Description:</span>
              <p class="text-white mt-1">{{ selectedTask.description }}</p>
            </div>
            
            <div v-if="selectedTask.result">
              <span class="text-gray-400">Result:</span>
              <pre class="mt-1 bg-gray-900 border border-gray-600 p-3 rounded text-xs overflow-x-auto text-gray-300">{{ selectedTask.result }}</pre>
            </div>
            
            <div v-if="selectedTask.error_message">
              <span class="text-gray-400">Error:</span>
              <p class="mt-1 text-red-400 bg-red-900 bg-opacity-20 border border-red-800 p-3 rounded">{{ selectedTask.error_message }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { format } from 'date-fns'
import { useTasksStore } from '@/stores/tasks'
import { apiService } from '@/services/api'
import type { TaskResponse } from '@/types/api'

const tasksStore = useTasksStore()

const searchQuery = ref('')
const debouncedSearchQuery = ref('')

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
const selectedTask = ref<TaskResponse | null>(null)
const isCreatingTask = ref(false)

const newTask = ref({
  description: '',
  task_type: ''
})

const filteredTasks = computed(() => {
  let tasks = tasksStore.tasks

  if (debouncedSearchQuery.value) {
    const query = debouncedSearchQuery.value.toLowerCase()
    tasks = tasks.filter(task => 
      task.description.toLowerCase().includes(query) ||
      task.task_id.toLowerCase().includes(query) ||
      task.task_type.toLowerCase().includes(query)
    )
  }

  return tasks.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
})

const createTask = async () => {
  if (!newTask.value.description.trim()) return

  isCreatingTask.value = true
  try {
    const task = await apiService.executeTask({
      description: newTask.value.description,
      task_type: newTask.value.task_type || undefined
    })
    
    tasksStore.addTask(task)
    
    // Reset form
    newTask.value = { description: '', task_type: '' }
    showCreateTask.value = false
  } catch (error) {
    console.error('Failed to create task:', error)
  } finally {
    isCreatingTask.value = false
  }
}

const viewTaskDetails = (task: TaskResponse) => {
  selectedTask.value = task
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