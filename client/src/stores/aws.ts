import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { AWSAccountInfo } from '@/types/api'
import { apiService } from '@/services/api'

export const useAwsStore = defineStore('aws', () => {
  const accountInfo = ref<AWSAccountInfo | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const isConnected = ref(false)

  const accountId = computed(() => accountInfo.value?.account_id)
  const region = computed(() => accountInfo.value?.region)
  const userArn = computed(() => accountInfo.value?.user_arn)

  const fetchAccountInfo = async () => {
    isLoading.value = true
    error.value = null

    try {
      const info = await apiService.getAwsAccountInfo()
      accountInfo.value = info
      isConnected.value = true
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch AWS account info'
      isConnected.value = false
      accountInfo.value = null
    } finally {
      isLoading.value = false
    }
  }

  const disconnect = () => {
    accountInfo.value = null
    isConnected.value = false
    error.value = null
  }

  return {
    accountInfo,
    isLoading,
    error,
    isConnected,
    accountId,
    region,
    userArn,
    fetchAccountInfo,
    disconnect
  }
}) 