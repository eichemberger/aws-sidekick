import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { AWSAccountInfo, AWSCredentialsRequest, AWSCredentialsResponse, AWSCredentialsValidation } from '@/types/api'
import { apiService } from '@/services/api'

export const useAwsStore = defineStore('aws', () => {
  const accountInfo = ref<AWSAccountInfo | null>(null)
  const credentialsInfo = ref<AWSCredentialsResponse | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const isConnected = ref(false)
  const isCredentialsLoading = ref(false)
  const credentialsError = ref<string | null>(null)

  const accountId = computed(() => accountInfo.value?.account_id)
  const region = computed(() => accountInfo.value?.region || credentialsInfo.value?.region)
  const userArn = computed(() => accountInfo.value?.user_arn)
  const hasValidCredentials = computed(() => credentialsInfo.value?.is_valid ?? false)
  const credentialsType = computed(() => {
    if (!credentialsInfo.value) return 'none'
    if (credentialsInfo.value.profile) return 'profile'
    if (credentialsInfo.value.has_access_key) return 'keys'
    return 'none'
  })

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

  const fetchCredentialsInfo = async () => {
    isCredentialsLoading.value = true
    credentialsError.value = null

    try {
      const info = await apiService.getAwsCredentials()
      credentialsInfo.value = info
    } catch (err: any) {
      // 404 means no credentials configured, which is a normal state
      if (err.response?.status === 404) {
        credentialsInfo.value = null
        credentialsError.value = null  // Don't treat this as an error
      } else {
        credentialsError.value = err instanceof Error ? err.message : 'Failed to fetch credentials info'
        credentialsInfo.value = null
      }
    } finally {
      isCredentialsLoading.value = false
    }
  }

  const setCredentials = async (credentials: AWSCredentialsRequest): Promise<AWSCredentialsResponse> => {
    isCredentialsLoading.value = true
    credentialsError.value = null

    try {
      const response = await apiService.setAwsCredentials(credentials)
      credentialsInfo.value = response
      
      // Also refresh account info with new credentials
      await fetchAccountInfo()
      
      return response
    } catch (err) {
      credentialsError.value = err instanceof Error ? err.message : 'Failed to set credentials'
      throw err
    } finally {
      isCredentialsLoading.value = false
    }
  }

  const validateCredentials = async (credentials: AWSCredentialsRequest): Promise<AWSCredentialsValidation> => {
    try {
      return await apiService.validateAwsCredentials(credentials)
    } catch (err) {
      throw err instanceof Error ? err : new Error('Failed to validate credentials')
    }
  }

  const clearCredentials = async () => {
    isCredentialsLoading.value = true
    credentialsError.value = null

    try {
      await apiService.clearAwsCredentials()
      credentialsInfo.value = null
      accountInfo.value = null
      isConnected.value = false
    } catch (err) {
      credentialsError.value = err instanceof Error ? err.message : 'Failed to clear credentials'
      throw err
    } finally {
      isCredentialsLoading.value = false
    }
  }

  const disconnect = () => {
    accountInfo.value = null
    credentialsInfo.value = null
    isConnected.value = false
    error.value = null
    credentialsError.value = null
  }

  // Initialize credentials info when store is created
  fetchCredentialsInfo()

  return {
    // State
    accountInfo,
    credentialsInfo,
    isLoading,
    error,
    isConnected,
    isCredentialsLoading,
    credentialsError,
    
    // Computed
    accountId,
    region,
    userArn,
    hasValidCredentials,
    credentialsType,
    
    // Actions
    fetchAccountInfo,
    fetchCredentialsInfo,
    setCredentials,
    validateCredentials,
    clearCredentials,
    disconnect
  }
}) 