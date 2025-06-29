<template>
  <div class="flex items-center space-x-2">
    <div
      class="w-2 h-2 rounded-full"
      :class="statusClass"
    ></div>
    <span class="text-sm text-gray-600">
      {{ statusText }}
    </span>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { apiService } from '@/services/api'

const isHealthy = ref<boolean | null>(null)
const isChecking = ref(false)
let healthInterval: number | null = null

const statusClass = computed(() => {
  if (isChecking.value) return 'bg-yellow-400 animate-pulse'
  if (isHealthy.value === null) return 'bg-gray-400'
  return isHealthy.value ? 'bg-green-400' : 'bg-red-400'
})

const statusText = computed(() => {
  if (isChecking.value) return 'Checking...'
  if (isHealthy.value === null) return 'Unknown'
  return isHealthy.value ? 'API Online' : 'API Offline'
})

const checkHealth = async () => {
  if (isChecking.value) return
  
  isChecking.value = true
  try {
    await apiService.healthCheck()
    isHealthy.value = true
  } catch (error) {
    isHealthy.value = false
  } finally {
    isChecking.value = false
  }
}

onMounted(() => {
  checkHealth()
  // Check health every 30 seconds
  healthInterval = window.setInterval(checkHealth, 30000)
})

onUnmounted(() => {
  if (healthInterval) {
    clearInterval(healthInterval)
  }
})
</script> 