<template>
  <div class="aws-account-manager">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h2 class="text-2xl font-bold text-gray-900 dark:text-white">AWS Accounts</h2>
        <p class="text-secondary mt-1">Manage your AWS account credentials</p>
      </div>
      <button
        @click="showRegisterForm = true"
        class="btn btn-primary"
      >
        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
        </svg>
        Add Account
      </button>
    </div>

    <!-- Error Display -->
    <div v-if="error" class="alert alert-error mb-4">
      <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
        <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
      </svg>
      <span>{{ error }}</span>
      <button @click="clearError" class="btn btn-sm btn-ghost ml-auto">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>

    <!-- Active Account Display -->
    <div v-if="activeAccount" class="card bg-blue-50 dark:bg-blue-900/10 border border-blue-200 dark:border-blue-800 mb-6">
      <div class="card-body">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-lg font-semibold text-blue-700 dark:text-blue-300 flex items-center">
              <svg class="w-5 h-5 mr-2 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
              </svg>
              Active: {{ activeAccount.alias }}
            </h3>
            <p class="text-secondary text-sm">{{ activeAccount.description || 'No description' }}</p>
            <div class="flex items-center gap-4 mt-2 text-sm text-secondary">
              <span>{{ activeAccount.region }}</span>
              <span v-if="activeAccount.account_id">ID: {{ activeAccount.account_id }}</span>
              <span class="badge badge-sm" :class="activeAccount.uses_profile ? 'badge-info' : 'badge-secondary'">
                {{ activeAccount.uses_profile ? 'Profile' : 'Keys' }}
              </span>
            </div>
          </div>
          <button
            @click="clearActiveAccount"
            class="btn btn-sm btn-ghost"
            title="Clear active account"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading && !hasAccounts" class="flex justify-center py-8">
      <div class="loading loading-spinner loading-lg"></div>
    </div>

    <!-- Empty State -->
    <div v-else-if="!hasAccounts" class="card bg-gray-100 dark:bg-gray-800">
      <div class="card-body text-center py-12">
        <svg class="w-16 h-16 mx-auto text-secondary mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2V7zm0 0V5a2 2 0 012-2h6l2 2h6a2 2 0 012 2v2M7 13h10" />
        </svg>
        <h3 class="text-xl font-semibold text-gray-900 dark:text-white mb-2">No AWS Accounts</h3>
        <p v-if="error && error.includes('404')" class="text-secondary mb-4">
          Multi-account features are not available yet. Please use the legacy AWS credentials setup.
        </p>
        <p v-else class="text-secondary mb-4">Register your first AWS account to get started</p>
        <button 
          v-if="!error || !error.includes('404')"
          @click="showRegisterForm = true" 
          class="btn btn-primary"
        >
          Add Your First Account
        </button>
      </div>
    </div>

    <!-- Accounts List -->
    <div v-else class="space-y-4">
      <div
        v-for="account in sortedAccounts"
        :key="account.alias"
        class="card bg-white dark:bg-gray-800 border hover:shadow-md transition-shadow"
        :class="{
          'border-blue-500 bg-blue-50 dark:bg-blue-900/10': account.alias === activeAccountAlias,
          'border-yellow-400 bg-yellow-50 dark:bg-yellow-900/10': account.is_default && account.alias !== activeAccountAlias
        }"
      >
        <div class="card-body">
          <div class="flex items-start justify-between">
            <div class="flex-1">
              <div class="flex items-center gap-2 mb-2">
                <h3 class="text-lg font-semibold text-gray-900 dark:text-white">{{ account.alias }}</h3>
                <div class="flex gap-1">
                  <span v-if="account.is_default" class="badge badge-warning badge-sm">Default</span>
                  <span v-if="account.alias === activeAccountAlias" class="badge badge-success badge-sm">Active</span>
                  <span class="badge badge-sm" :class="account.uses_profile ? 'badge-info' : 'badge-secondary'">
                    {{ account.uses_profile ? 'Profile' : 'Keys' }}
                  </span>
                </div>
              </div>
              
              <p v-if="account.description" class="text-secondary text-sm mb-2">{{ account.description }}</p>
              
              <div class="flex items-center gap-4 text-sm text-secondary">
                <span>{{ account.region }}</span>
                <span v-if="account.account_id">ID: {{ account.account_id }}</span>
                <span>Created: {{ formatDate(account.created_at) }}</span>
              </div>
            </div>

                        <!-- Account Actions -->
            <div class="flex items-center gap-2">
              <!-- Set Active Button -->
              <button
                v-if="account.alias !== activeAccountAlias"
                @click="setActiveAccount(account.alias)"
                class="btn btn-sm btn-outline btn-primary"
                :disabled="isLoading"
                title="Set as active account"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Activate
              </button>

              <!-- Dropdown Menu -->
              <div class="relative" :ref="`dropdown-${account.alias}`">
                <button 
                  @click="toggleDropdown(account.alias)"
                  class="btn btn-sm btn-ghost"
                  :class="{ 'bg-gray-100 dark:bg-gray-700': openDropdowns[account.alias] }"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01" />
                  </svg>
                </button>
                
                <!-- Dropdown Content -->
                <div 
                  v-if="openDropdowns[account.alias]"
                  class="absolute right-0 top-full mt-1 w-52 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-50"
                >
                  <div class="py-1">
                    <button
                      v-if="!account.is_default"
                      @click="handleDropdownAction(() => setDefaultAccount(account.alias))"
                      class="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                      </svg>
                      Set as Default
                    </button>
                    <button
                      @click="handleDropdownAction(() => editAccount(account))"
                      class="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                      Edit Credentials
                    </button>
                    <div class="border-t border-gray-200 dark:border-gray-700 my-1"></div>
                    <button
                      @click="handleDropdownAction(() => deleteAccount(account.alias))"
                      class="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                      Delete Account
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Register Account Modal -->
    <div v-if="showRegisterForm" class="modal modal-open">
      <div class="modal-backdrop" @click="!isLoading && (showRegisterForm = false)"></div>
      <div class="modal-box w-11/12 max-w-2xl relative">
        <!-- Loading Overlay -->
        <div v-if="isLoading" class="absolute inset-0 bg-white/80 dark:bg-gray-900/80 flex items-center justify-center z-50 rounded-lg">
          <div class="text-center">
            <div class="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
            <p class="text-sm font-medium text-gray-700 dark:text-gray-300">Registering AWS account...</p>
            <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">Please wait while we validate your credentials</p>
          </div>
        </div>

        <div class="flex items-center justify-between mb-4">
          <h3 class="font-bold text-lg">Register New AWS Account</h3>
          <button 
            @click="showRegisterForm = false" 
            class="btn btn-sm btn-ghost"
            :disabled="isLoading"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <AWSCredentialsManager
          :is-registration="true"
          @credentials-set="handleAccountRegistration"
          @cancel="showRegisterForm = false"
        />
      </div>
    </div>

    <!-- Edit Account Modal -->
    <div v-if="showEditForm && editingAccount" class="modal modal-open">
      <div class="modal-backdrop" @click="!isLoading && cancelEdit()"></div>
      <div class="modal-box w-11/12 max-w-2xl relative">
        <!-- Loading Overlay -->
        <div v-if="isLoading" class="absolute inset-0 bg-white/80 dark:bg-gray-900/80 flex items-center justify-center z-50 rounded-lg">
          <div class="text-center">
            <div class="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
            <p class="text-sm font-medium text-gray-700 dark:text-gray-300">Updating account credentials...</p>
            <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">Please wait while we validate your credentials</p>
          </div>
        </div>

        <div class="flex items-center justify-between mb-4">
          <h3 class="font-bold text-lg">Edit Account: {{ editingAccount.alias }}</h3>
          <button 
            @click="cancelEdit" 
            class="btn btn-sm btn-ghost"
            :disabled="isLoading"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <AWSCredentialsManager
          :is-registration="false"
          @credentials-set="handleAccountUpdate"
          @cancel="cancelEdit"
        />
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div v-if="showDeleteConfirm && deletingAccount" class="modal modal-open">
      <div class="modal-backdrop" @click="cancelDelete"></div>
      <div class="modal-box">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-bold text-lg text-red-600 dark:text-red-400">Delete Account</h3>
          <button @click="cancelDelete" class="btn btn-sm btn-ghost">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <p class="mb-6">
          Are you sure you want to delete the AWS account <strong>{{ deletingAccount }}</strong>?
          This action cannot be undone.
        </p>
        
        <div class="flex justify-end gap-2">
          <button @click="cancelDelete" class="btn btn-ghost">Cancel</button>
          <button @click="confirmDelete" class="btn btn-error" :disabled="isLoading">
            <span v-if="isLoading" class="loading loading-spinner loading-sm"></span>
            Delete Account
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, reactive } from 'vue'
import { useAwsAccountsStore } from '@/stores/awsAccounts'
import AWSCredentialsManager from './AWSCredentialsManager.vue'
import type { AWSAccount, AWSCredentialsRequest } from '@/types/api'
import { storeToRefs } from 'pinia'

// Store
const accountsStore = useAwsAccountsStore()
const {
  accounts,
  activeAccount,
  activeAccountAlias,
  sortedAccounts,
  hasAccounts,
  isLoading,
  error
} = storeToRefs(accountsStore)

// Local state
const showRegisterForm = ref(false)
const showEditForm = ref(false)
const editingAccount = ref<AWSAccount | null>(null)
const showDeleteConfirm = ref(false)
const deletingAccount = ref<string | null>(null)
const openDropdowns = reactive<Record<string, boolean>>({})

// Methods
const clearError = () => {
  accountsStore.clearError()
}

const setActiveAccount = async (alias: string) => {
  try {
    await accountsStore.setActiveAccount(alias)
  } catch (err) {
    console.error('Failed to set active account:', err)
  }
}

const clearActiveAccount = async () => {
  try {
    await accountsStore.clearActiveAccount()
  } catch (err) {
    console.error('Failed to clear active account:', err)
  }
}

const setDefaultAccount = async (alias: string) => {
  try {
    await accountsStore.setDefaultAccount(alias)
  } catch (err) {
    console.error('Failed to set default account:', err)
  }
}

const handleAccountRegistration = async (event: { credentials: AWSCredentialsRequest, alias?: string, description?: string, setAsDefault?: boolean }) => {
  if (!event.alias) {
    console.error('Alias is required for account registration')
    return
  }
  
  try {
    await accountsStore.registerAccount({
      alias: event.alias,
      credentials: event.credentials,
      description: event.description,
      set_as_default: event.setAsDefault
    })
    showRegisterForm.value = false
  } catch (err) {
    console.error('Failed to register account:', err)
  }
}

const editAccount = (account: AWSAccount) => {
  editingAccount.value = account
  showEditForm.value = true
}

const handleAccountUpdate = async (event: { credentials: AWSCredentialsRequest }) => {
  if (!editingAccount.value) return
  
  try {
    await accountsStore.updateAccountCredentials(editingAccount.value.alias, event.credentials)
    cancelEdit()
  } catch (err) {
    console.error('Failed to update account:', err)
  }
}

const cancelEdit = () => {
  editingAccount.value = null
  showEditForm.value = false
}

const deleteAccount = (alias: string) => {
  deletingAccount.value = alias
  showDeleteConfirm.value = true
}

const confirmDelete = async () => {
  if (!deletingAccount.value) return
  
  try {
    await accountsStore.deleteAccount(deletingAccount.value)
    cancelDelete()
  } catch (err) {
    console.error('Failed to delete account:', err)
  }
}

const cancelDelete = () => {
  deletingAccount.value = null
  showDeleteConfirm.value = false
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString()
}

// Dropdown management
const toggleDropdown = (alias: string) => {
  // Close all other dropdowns
  Object.keys(openDropdowns).forEach(key => {
    if (key !== alias) {
      openDropdowns[key] = false
    }
  })
  // Toggle current dropdown
  openDropdowns[alias] = !openDropdowns[alias]
}

const closeAllDropdowns = () => {
  Object.keys(openDropdowns).forEach(key => {
    openDropdowns[key] = false
  })
}

const handleDropdownAction = (action: () => void) => {
  action()
  closeAllDropdowns()
}

// Click outside handler
const handleClickOutside = (event: Event) => {
  const target = event.target as HTMLElement
  if (!target.closest('.relative')) {
    closeAllDropdowns()
  }
}

// Lifecycle
onMounted(async () => {
  await accountsStore.initialize()
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.aws-account-manager {
  @apply p-6 max-w-4xl mx-auto;
}

.alert {
  @apply flex items-center gap-3 p-4 rounded-lg;
}

.alert-error {
  @apply bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800;
}

.btn {
  @apply inline-flex items-center justify-center px-4 py-2 rounded-lg font-medium transition-colors;
}

.btn-primary {
  @apply bg-blue-600 text-white hover:bg-blue-700;
}

.btn-outline {
  @apply border border-current bg-transparent hover:bg-current hover:text-current;
}

.btn-ghost {
  @apply bg-transparent hover:bg-gray-100 dark:hover:bg-gray-700;
}

.btn-error {
  @apply bg-red-600 text-white hover:bg-red-700;
}

.btn-sm {
  @apply px-3 py-1 text-sm;
}

.btn:disabled {
  @apply opacity-50 cursor-not-allowed;
}

.card {
  @apply bg-white dark:bg-gray-800 rounded-lg;
}

.card-body {
  @apply p-6;
}

.badge {
  @apply inline-flex items-center px-2 py-1 rounded-full text-xs font-medium;
}

.badge-warning {
  @apply bg-yellow-100 dark:bg-yellow-900/20 text-yellow-700 dark:text-yellow-300;
}

.badge-success {
  @apply bg-green-100 dark:bg-green-900/20 text-green-700 dark:text-green-300;
}

.badge-info {
  @apply bg-blue-100 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300;
}

.badge-secondary {
  @apply bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300;
}

.badge-sm {
  @apply px-1.5 py-0.5 text-xs;
}

.modal {
  @apply fixed inset-0 z-50 flex items-center justify-center pointer-events-none;
}

.modal-open {
  @apply visible opacity-100 pointer-events-auto;
}

.modal-box {
  @apply relative z-10 bg-white dark:bg-gray-800 p-6 rounded-lg shadow-xl max-h-[90vh] overflow-y-auto;
}

.modal-backdrop {
  @apply absolute inset-0 bg-black/50 z-0 cursor-pointer;
}

.dropdown {
  @apply relative;
}

.dropdown-content {
  @apply absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-20;
}

.menu {
  @apply py-1;
}

.menu li a {
  @apply flex items-center gap-2 px-3 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer;
}

.loading {
  @apply animate-spin;
}

.loading-spinner {
  @apply w-4 h-4 border-2 border-current border-t-transparent rounded-full;
}

.loading-lg {
  @apply w-8 h-8;
}

.loading-sm {
  @apply w-3 h-3;
}
</style> 