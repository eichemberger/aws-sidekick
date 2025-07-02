import { defineStore } from 'pinia'
import { ref, readonly } from 'vue'
import type { AWSAccountInfo } from '@/types/api'
import { apiService } from '@/services/api'

export const useAwsStore = defineStore('aws', () => {
  const accountInfo = ref<AWSAccountInfo | null>(null)
  const isAccountLoading = ref(false)
  const accountError = ref<string | null>(null)

  const fetchAccountInfo = async () => {
    isAccountLoading.value = true
    accountError.value = null

    try {
      const info = await apiService.getAwsAccountInfo()
      accountInfo.value = info
    } catch (err: any) {
      accountError.value = err instanceof Error ? err.message : 'Failed to fetch account info'
      accountInfo.value = null
    } finally {
      isAccountLoading.value = false
    }
  }

  return {
    // Account Info
    accountInfo: readonly(accountInfo),
    isAccountLoading: readonly(isAccountLoading),
    accountError: readonly(accountError),
    fetchAccountInfo
  }
}) 