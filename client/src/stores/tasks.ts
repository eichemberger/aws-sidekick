import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { TaskResponse } from '@/types/api'
import { apiService } from '@/services/api'

export const useTasksStore = defineStore('tasks', () => {
  const tasks = ref<TaskResponse[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const taskCount = computed(() => tasks.value.length)
  const recentTasks = computed(() => 
    tasks.value
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
      .slice(0, 10)
  )
  const completedTasks = computed(() => 
    tasks.value.filter(task => task.status === 'completed')
  )
  const failedTasks = computed(() => 
    tasks.value.filter(task => task.status === 'failed')
  )

  const fetchTasks = async (limit = 20, offset = 0) => {
    isLoading.value = true
    error.value = null

    try {
      const fetchedTasks = await apiService.getTasks(limit, offset)
      if (offset === 0) {
        tasks.value = fetchedTasks
      } else {
        tasks.value.push(...fetchedTasks)
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch tasks'
    } finally {
      isLoading.value = false
    }
  }

  const getTask = async (taskId: string): Promise<TaskResponse | null> => {
    try {
      const task = await apiService.getTask(taskId)
      
      // Update existing task in store
      const index = tasks.value.findIndex(t => t.task_id === taskId)
      if (index !== -1) {
        tasks.value[index] = task
      } else {
        tasks.value.unshift(task)
      }
      
      return task
    } catch (err) {
      console.error('Failed to get task:', err)
      return null
    }
  }

  const executeQuickAction = async (action: 'analyze' | 'security' | 'costs') => {
    isLoading.value = true
    error.value = null

    try {
      let task: TaskResponse

      switch (action) {
        case 'analyze':
          task = await apiService.analyzeAws()
          break
        case 'security':
          task = await apiService.performSecurityAudit()
          break
        case 'costs':
          task = await apiService.optimizeCosts()
          break
        default:
          throw new Error('Unknown action')
      }

      tasks.value.unshift(task)
      return task
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to execute action'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const addTask = (task: TaskResponse) => {
    const index = tasks.value.findIndex(t => t.task_id === task.task_id)
    if (index !== -1) {
      tasks.value[index] = task
    } else {
      tasks.value.unshift(task)
    }
  }

  const clearTasks = () => {
    tasks.value = []
    error.value = null
  }

  return {
    tasks,
    isLoading,
    error,
    taskCount,
    recentTasks,
    completedTasks,
    failedTasks,
    fetchTasks,
    getTask,
    executeQuickAction,
    addTask,
    clearTasks
  }
}) 