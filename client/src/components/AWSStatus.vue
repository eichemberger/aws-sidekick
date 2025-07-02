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
      v-if="!isConnected"
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

const isConnected = computed(() => awsStore.accountInfo !== null)

const statusClass = computed(() => {
  if (awsStore.isAccountLoading) return 'bg-yellow-400 animate-pulse'
  return isConnected.value ? 'bg-green-400' : 'bg-gray-400'
})

const statusText = computed(() => {
  if (awsStore.isAccountLoading) return 'Connecting...'
  if (isConnected.value && awsStore.accountInfo?.account_id) {
    return `AWS: ${awsStore.accountInfo.account_id.slice(-4)}`
  }
  return 'AWS Disconnected'
})

const connect = async () => {
  await awsStore.fetchAccountInfo()
}

onMounted(() => {
  // Try to connect to AWS on component mount
  if (!isConnected.value) {
    connect()
  }
})
</script> 