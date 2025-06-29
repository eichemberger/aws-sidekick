<template>
  <div class="flex items-center space-x-2">
    <div
      class="w-2 h-2 rounded-full"
      :class="statusClass"
    ></div>
    <span class="text-sm text-gray-600">
      {{ statusText }}
    </span>
    <button
      v-if="!awsStore.isConnected"
      @click="connect"
      class="text-xs text-primary-600 hover:text-primary-700 font-medium"
    >
      Connect
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useAwsStore } from '@/stores/aws'

const awsStore = useAwsStore()

const statusClass = computed(() => {
  if (awsStore.isLoading) return 'bg-yellow-400 animate-pulse'
  return awsStore.isConnected ? 'bg-green-400' : 'bg-gray-400'
})

const statusText = computed(() => {
  if (awsStore.isLoading) return 'Connecting...'
  if (awsStore.isConnected && awsStore.accountId) {
    return `AWS: ${awsStore.accountId.slice(-4)}`
  }
  return 'AWS Disconnected'
})

const connect = async () => {
  await awsStore.fetchAccountInfo()
}

onMounted(() => {
  // Try to connect to AWS on component mount
  if (!awsStore.isConnected) {
    connect()
  }
})
</script> 