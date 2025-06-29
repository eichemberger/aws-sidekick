<template>
  <div class="h-screen bg-gray-900 text-white overflow-y-auto">
    <div class="max-w-4xl mx-auto p-6">
      <!-- Header -->
      <div class="mb-8">
        <div class="flex items-center justify-between mb-6">
          <h1 class="text-2xl font-semibold">AWS Settings</h1>
          <button
            @click="refreshAccount"
            class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors flex items-center gap-2"
            :disabled="awsStore.isLoading"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
            </svg>
            {{ awsStore.isLoading ? 'Refreshing...' : 'Refresh' }}
          </button>
        </div>

        <!-- Connection Status -->
        <div class="bg-gray-800 rounded-lg p-6 mb-6">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-4">
              <div class="w-12 h-12 rounded-full flex items-center justify-center"
                   :class="awsStore.isConnected ? 'bg-green-600' : 'bg-gray-600'">
                <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.004 4.004 0 003 15z"></path>
                </svg>
              </div>
              <div>
                <h3 class="text-lg font-medium text-white">
                  {{ awsStore.isConnected ? 'Connected to AWS' : 'Not Connected' }}
                </h3>
                <p class="text-sm text-gray-400">
                  {{ awsStore.isConnected ? 
                      'Your AWS account is connected and ready' : 
                      'Connect to your AWS account to get started' }}
                </p>
              </div>
            </div>
            <button
              v-if="!awsStore.isConnected"
              @click="connectToAws"
              class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
              :disabled="awsStore.isLoading"
            >
              {{ awsStore.isLoading ? 'Connecting...' : 'Connect' }}
            </button>
          </div>
        </div>

        <!-- Account Information -->
        <div v-if="awsStore.isConnected && awsStore.accountInfo" class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div class="bg-gray-800 rounded-lg p-4">
            <div class="text-sm text-gray-400 mb-1">Account ID</div>
            <div class="text-lg font-mono text-white">{{ awsStore.accountInfo.account_id }}</div>
          </div>
          <div class="bg-gray-800 rounded-lg p-4">
            <div class="text-sm text-gray-400 mb-1">Region</div>
            <div class="text-lg text-white">{{ awsStore.accountInfo.region }}</div>
          </div>
          <div class="bg-gray-800 rounded-lg p-4">
            <div class="text-sm text-gray-400 mb-1">User</div>
            <div class="text-lg text-white truncate">{{ awsStore.accountInfo.user_arn.split('/').pop() }}</div>
          </div>
        </div>
      </div>

      <!-- Quick Actions -->
      <div v-if="awsStore.isConnected">
        <h2 class="text-xl font-semibold mb-4">Quick Actions</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <button
            @click="runAnalysis"
            class="bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-lg p-6 text-left transition-colors"
            :disabled="tasksStore.isLoading"
          >
            <div class="flex items-center gap-3 mb-2">
              <div class="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                </svg>
              </div>
              <h3 class="font-medium text-white">Infrastructure Analysis</h3>
            </div>
            <p class="text-sm text-gray-400">Analyze your AWS resources and usage patterns</p>
          </button>

          <button
            @click="runSecurityAudit"
            class="bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-lg p-6 text-left transition-colors"
            :disabled="tasksStore.isLoading"
          >
            <div class="flex items-center gap-3 mb-2">
              <div class="w-8 h-8 bg-green-600 rounded-lg flex items-center justify-center">
                <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path>
                </svg>
              </div>
              <h3 class="font-medium text-white">Security Audit</h3>
            </div>
            <p class="text-sm text-gray-400">Check security configurations and best practices</p>
          </button>

          <button
            @click="runCostOptimization"
            class="bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-lg p-6 text-left transition-colors"
            :disabled="tasksStore.isLoading"
          >
            <div class="flex items-center gap-3 mb-2">
              <div class="w-8 h-8 bg-yellow-600 rounded-lg flex items-center justify-center">
                <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1"></path>
                </svg>
              </div>
              <h3 class="font-medium text-white">Cost Optimization</h3>
            </div>
            <p class="text-sm text-gray-400">Find ways to reduce your AWS costs</p>
          </button>

          <button
            @click="showCustomTask = true"
            class="bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-lg p-6 text-left transition-colors"
          >
            <div class="flex items-center gap-3 mb-2">
              <div class="w-8 h-8 bg-purple-600 rounded-lg flex items-center justify-center">
                <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path>
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                </svg>
              </div>
              <h3 class="font-medium text-white">Custom Task</h3>
            </div>
            <p class="text-sm text-gray-400">Create a custom AWS operation</p>
          </button>
        </div>
      </div>

      <!-- Error Display -->
      <div v-if="awsStore.error" class="bg-red-900 bg-opacity-20 border border-red-800 rounded-lg p-4 mb-6">
        <div class="flex items-center gap-3">
          <svg class="w-5 h-5 text-red-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
          <div>
            <h3 class="font-medium text-red-400">Connection Error</h3>
            <p class="text-sm text-red-300 mt-1">{{ awsStore.error }}</p>
          </div>
        </div>
      </div>

      <!-- Custom Task Modal -->
      <div v-if="showCustomTask" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-gray-800 rounded-lg p-6 w-96 max-w-full mx-4 border border-gray-700">
          <h3 class="text-lg font-semibold mb-4 text-white">Create Custom Task</h3>
          <form @submit.prevent="executeCustomTask">
            <div class="mb-4">
              <textarea
                v-model="customTaskDescription"
                class="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                rows="4"
                placeholder="Describe what you want to do with your AWS infrastructure..."
                required
              ></textarea>
            </div>
            <div class="flex gap-3 justify-end">
              <button
                type="button"
                @click="showCustomTask = false"
                class="px-4 py-2 border border-gray-600 text-gray-300 rounded-lg hover:bg-gray-700 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                :disabled="!customTaskDescription.trim() || isExecutingCustomTask"
              >
                {{ isExecutingCustomTask ? 'Creating...' : 'Execute Task' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAwsStore } from '@/stores/aws'
import { useTasksStore } from '@/stores/tasks'
import { apiService } from '@/services/api'

const awsStore = useAwsStore()
const tasksStore = useTasksStore()

const showCustomTask = ref(false)
const customTaskDescription = ref('')
const isExecutingCustomTask = ref(false)

const connectToAws = async () => {
  await awsStore.fetchAccountInfo()
}

const refreshAccount = async () => {
  await awsStore.fetchAccountInfo()
}

const runAnalysis = async () => {
  try {
    const task = await tasksStore.executeQuickAction('analyze')
    console.log('Analysis task created:', task.task_id)
  } catch (error) {
    console.error('Failed to run analysis:', error)
  }
}

const runSecurityAudit = async () => {
  try {
    const task = await tasksStore.executeQuickAction('security')
    console.log('Security audit task created:', task.task_id)
  } catch (error) {
    console.error('Failed to run security audit:', error)
  }
}

const runCostOptimization = async () => {
  try {
    const task = await tasksStore.executeQuickAction('costs')
    console.log('Cost optimization task created:', task.task_id)
  } catch (error) {
    console.error('Failed to run cost optimization:', error)
  }
}

const executeCustomTask = async () => {
  if (!customTaskDescription.value.trim()) return

  isExecutingCustomTask.value = true
  try {
    const task = await apiService.executeTask({
      description: customTaskDescription.value
    })
    tasksStore.addTask(task)
    
    customTaskDescription.value = ''
    showCustomTask.value = false
    console.log('Custom task created:', task.task_id)
  } catch (error) {
    console.error('Failed to execute custom task:', error)
  } finally {
    isExecutingCustomTask.value = false
  }
}

onMounted(() => {
  // Try to connect to AWS on component mount
  if (!awsStore.isConnected) {
    awsStore.fetchAccountInfo()
  }
})
</script> 