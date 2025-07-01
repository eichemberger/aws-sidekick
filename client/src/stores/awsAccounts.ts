import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { AWSAccount, AWSAccountRequest, AWSAccountUpdateRequest, AWSCredentialsRequest } from '@/types/api'
import { apiService } from '@/services/api'

export const useAwsAccountsStore = defineStore('awsAccounts', () => {
  const accounts = ref<AWSAccount[]>([])
  const activeAccountAlias = ref<string | null>(null)
  const defaultAccount = ref<AWSAccount | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Computed properties
  const activeAccount = computed(() => 
    activeAccountAlias.value ? accounts.value.find(acc => acc.alias === activeAccountAlias.value) || null : null
  )

  const hasAccounts = computed(() => accounts.value.length > 0)

  const sortedAccounts = computed(() => 
    [...accounts.value].sort((a, b) => {
      // Default account first, then alphabetical
      if (a.is_default && !b.is_default) return -1
      if (!a.is_default && b.is_default) return 1
      return a.alias.localeCompare(b.alias)
    })
  )

  // Actions
  const fetchAccounts = async () => {
    isLoading.value = true
    error.value = null

    try {
      const fetchedAccounts = await apiService.getAwsAccounts()
      
      // Ensure we have a valid array
      if (Array.isArray(fetchedAccounts)) {
        accounts.value = fetchedAccounts
        
        // Update default account
        defaultAccount.value = fetchedAccounts.find(acc => acc.is_default) || null
      } else {
        console.warn('API returned non-array response for getAwsAccounts:', fetchedAccounts)
        accounts.value = []
        defaultAccount.value = null
        error.value = 'Invalid response format from server'
      }
    } catch (err) {
      console.error('Failed to fetch AWS accounts:', err)
      
      // Check if it's a 404 error (endpoints not implemented)
      if (err instanceof Error && (err.message.includes('404') || err.message.includes('Not Found'))) {
        error.value = 'Multi-account endpoints not available (404)'
      } else {
        error.value = err instanceof Error ? err.message : 'Failed to fetch AWS accounts'
      }
      
      accounts.value = []
      defaultAccount.value = null
    } finally {
      isLoading.value = false
    }
  }

  const fetchActiveAccount = async () => {
    try {
      activeAccountAlias.value = await apiService.getActiveAccountAlias()
    } catch (err) {
      console.warn('Failed to fetch active account:', err)
      activeAccountAlias.value = null
      // If endpoint doesn't exist (404), don't treat as error
      if (err instanceof Error && err.message.includes('404')) {
        console.info('Multi-account endpoints not available yet')
      }
    }
  }

  const registerAccount = async (request: AWSAccountRequest): Promise<AWSAccount> => {
    isLoading.value = true
    error.value = null

    try {
      const newAccount = await apiService.registerAwsAccount(request)
      
      // Add to accounts list
      accounts.value.push(newAccount)
      
      // Update default account if this one was set as default
      if (newAccount.is_default) {
        // Clear previous default
        accounts.value.forEach(acc => {
          if (acc.alias !== newAccount.alias) {
            acc.is_default = false
          }
        })
        defaultAccount.value = newAccount
      }
      
      return newAccount
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to register AWS account'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const updateAccountCredentials = async (alias: string, credentials: AWSCredentialsRequest): Promise<AWSAccount> => {
    isLoading.value = true
    error.value = null

    try {
      const updatedAccount = await apiService.updateAwsAccountCredentials(alias, { credentials })
      
      // Update in accounts list
      const index = accounts.value.findIndex(acc => acc.alias === alias)
      if (index !== -1) {
        accounts.value[index] = updatedAccount
      }
      
      return updatedAccount
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to update account credentials'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const deleteAccount = async (alias: string): Promise<void> => {
    isLoading.value = true
    error.value = null

    try {
      await apiService.deleteAwsAccount(alias)
      
      // Remove from accounts list
      accounts.value = accounts.value.filter(acc => acc.alias !== alias)
      
      // Clear active account if it was deleted
      if (activeAccountAlias.value === alias) {
        activeAccountAlias.value = null
      }
      
      // Update default account reference
      if (defaultAccount.value?.alias === alias) {
        defaultAccount.value = accounts.value.find(acc => acc.is_default) || null
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to delete AWS account'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const setDefaultAccount = async (alias: string): Promise<void> => {
    isLoading.value = true
    error.value = null

    try {
      await apiService.setDefaultAwsAccount(alias)
      
      // Update accounts list
      accounts.value.forEach(acc => {
        acc.is_default = acc.alias === alias
      })
      
      // Update default account reference
      defaultAccount.value = accounts.value.find(acc => acc.alias === alias) || null
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to set default account'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const setActiveAccount = async (alias: string): Promise<void> => {
    isLoading.value = true
    error.value = null

    try {
      await apiService.setActiveAwsAccount({ account_alias: alias })
      activeAccountAlias.value = alias
    } catch (err) {
      console.error('Failed to set active account:', err)
      error.value = err instanceof Error ? err.message : 'Failed to set active account'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const clearActiveAccount = async (): Promise<void> => {
    isLoading.value = true
    error.value = null

    try {
      await apiService.clearActiveAwsAccount()
      activeAccountAlias.value = null
    } catch (err) {
      console.error('Failed to clear active account:', err)
      error.value = err instanceof Error ? err.message : 'Failed to clear active account'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const validateAccountCredentials = async (alias: string): Promise<boolean> => {
    try {
      return await apiService.validateAwsAccountCredentials(alias)
    } catch (err) {
      console.warn(`Failed to validate credentials for account ${alias}:`, err)
      return false
    }
  }

  const getAccount = (alias: string): AWSAccount | undefined => {
    return accounts.value.find(acc => acc.alias === alias)
  }

  const clearError = () => {
    error.value = null
  }

  const reset = () => {
    accounts.value = []
    activeAccountAlias.value = null
    defaultAccount.value = null
    isLoading.value = false
    error.value = null
  }

  // Initialize on store creation
  const initialize = async () => {
    try {
      await Promise.all([
        fetchAccounts(),
        fetchActiveAccount()
      ])
    } catch (err) {
      console.error('Failed to initialize AWS accounts store:', err)
      // Don't throw - let the app continue to work without multi-account features
    }
  }

  return {
    // State
    accounts,
    activeAccountAlias,
    defaultAccount,
    isLoading,
    error,

    // Computed
    activeAccount,
    hasAccounts,
    sortedAccounts,

    // Actions
    fetchAccounts,
    fetchActiveAccount,
    registerAccount,
    updateAccountCredentials,
    deleteAccount,
    setDefaultAccount,
    setActiveAccount,
    clearActiveAccount,
    validateAccountCredentials,
    getAccount,
    clearError,
    reset,
    initialize
  }
}) 