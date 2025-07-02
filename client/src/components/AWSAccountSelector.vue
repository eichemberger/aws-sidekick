<template>
  <div class="aws-account-selector" ref="dropdownContainer">
    <div class="dropdown">
      <!-- Trigger Button -->
      <button 
        @click="toggleDropdown"
        class="btn btn-sm btn-outline gap-2"
        :class="{ 
          'opacity-50 cursor-not-allowed': isDisabled,
          'opacity-75': isLoading 
        }"
        :disabled="isDisabled || isLoading"
      >
        <!-- Loading spinner when switching -->
        <div v-if="isLoading" class="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></div>
        <!-- Account icon when not loading -->
        <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-4m-5 0H3m2 0h3M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
        <span v-if="activeAccount" class="max-w-24 truncate">{{ activeAccount.alias }}</span>
        <span v-else-if="error && error.includes('404')" class="text-secondary">N/A</span>
        <span v-else class="text-secondary">No Account</span>
        <svg 
          class="w-4 h-4 transition-transform" 
          :class="{ 'rotate-180': isDropdownOpen }"
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      <!-- Dropdown Content -->
      <ul 
        v-show="isDropdownOpen"
        class="dropdown-content menu p-2 shadow-lg bg-white dark:bg-gray-800 rounded-lg w-80 border border-gray-200 dark:border-gray-700"
      >
        <!-- Header -->
        <li class="px-3 py-2 text-xs font-medium text-secondary border-b border-gray-200 dark:border-gray-700 mb-2">
          {{ hasAccounts ? 'Select AWS Account' : 'AWS Accounts' }}
        </li>

        <!-- Loading State -->
        <li v-if="isLoading" class="p-3">
          <div class="flex items-center justify-center">
            <div class="w-4 h-4 border-2 border-gray-300 border-t-blue-600 rounded-full animate-spin"></div>
            <span class="ml-2 text-sm text-secondary">Loading accounts...</span>
          </div>
        </li>

        <!-- Accounts List -->
        <li 
          v-for="account in sortedAccounts" 
          :key="account.alias"
          class="mb-1"
        >
          <a 
            @click="selectAccount(account.alias)"
            class="p-3 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer"
            :class="{ 'pointer-events-none opacity-50': account.alias === activeAccountAlias }"
          >
            <div class="flex items-center justify-between w-full">
              <div class="flex-1">
                <div class="flex items-center gap-2">
                  <span class="font-medium">{{ account.alias }}</span>
                  <div class="flex gap-1">
                    <span v-if="account.is_default" class="badge badge-warning badge-xs">Default</span>
                    <span class="badge badge-xs" :class="account.uses_profile ? 'badge-info' : 'badge-secondary'">
                      {{ account.uses_profile ? 'Profile' : 'Keys' }}
                    </span>
                  </div>
                </div>
                <div class="text-sm text-secondary">{{ account.description || 'No description' }}</div>
                <div class="text-xs text-secondary">
                  {{ account.region }}
                  <span v-if="account.account_id">• {{ account.account_id }}</span>
                </div>
              </div>
            </div>
          </a>
        </li>

        <!-- Empty State -->
        <li v-if="!hasAccounts" class="p-3">
          <div class="text-center text-secondary">
            <svg class="w-8 h-8 mx-auto mb-2 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2V7zm0 0V5a2 2 0 012-2h6l2 2h6a2 2 0 012 2v2M7 13h10" />
            </svg>
            <p v-if="error && error.includes('404')" class="text-sm">Multi-account features not available</p>
            <p v-else class="text-sm">No AWS accounts registered</p>
          </div>
        </li>

        <!-- Divider -->
        <li v-if="hasAccounts" class="border-t border-gray-200 dark:border-gray-700 my-2"></li>

        <!-- Actions -->
        <li v-if="hasAccounts">
          <a 
            @click="clearActiveAccount" 
            class="p-3 text-sm text-secondary hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer rounded-lg flex items-center gap-2"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
            Clear Selection
          </a>
        </li>

        <li>
          <router-link 
            to="/aws" 
            @click="closeDropdown"
            class="p-3 text-sm text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 cursor-pointer rounded-lg flex items-center gap-2"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            Manage AWS Accounts
          </router-link>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useAwsAccountsStore } from '@/stores/awsAccounts'

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
const dropdownContainer = ref<HTMLElement>()
const isDropdownOpen = ref(false)

// Computed
const isDisabled = computed(() => !hasAccounts.value && !isLoading.value)

// Methods
const toggleDropdown = () => {
  if (isDisabled.value) return
  isDropdownOpen.value = !isDropdownOpen.value
}

const closeDropdown = () => {
  isDropdownOpen.value = false
}

const selectAccount = async (alias: string) => {
  try {
    await accountsStore.setActiveAccount(alias)
    closeDropdown()
  } catch (err) {
    console.error('Failed to set active account:', err)
    // Error handling is now done in the store
    closeDropdown()
  }
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
    closeDropdown()
  } catch (err) {
    console.error('Failed to clear active account:', err)
  }
}

// Click outside to close dropdown
const handleClickOutside = (event: Event) => {
  if (dropdownContainer.value && !dropdownContainer.value.contains(event.target as Node)) {
    closeDropdown()
  }
}

// Escape key to close dropdown
const handleEscapeKey = (event: KeyboardEvent) => {
  if (event.key === 'Escape' && isDropdownOpen.value) {
    closeDropdown()
  }
}

// Lifecycle
onMounted(async () => {
  if (!accountsStore.hasAccounts) {
    await accountsStore.initialize()
  }
  
  // Add event listeners
  document.addEventListener('click', handleClickOutside)
  document.addEventListener('keydown', handleEscapeKey)
})

onUnmounted(() => {
  // Remove event listeners
  document.removeEventListener('click', handleClickOutside)
  document.removeEventListener('keydown', handleEscapeKey)
})
</script>

<style scoped>
.aws-account-selector {
  @apply relative;
}

.btn {
  @apply inline-flex items-center justify-center px-3 py-2 rounded-lg font-medium transition-colors;
}

.btn-sm {
  @apply px-2 py-1 text-sm;
}

.btn-outline {
  @apply border border-gray-300 dark:border-gray-600 bg-transparent text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-gray-900 dark:hover:text-white hover:border-gray-400 dark:hover:border-gray-500;
}

.dropdown {
  @apply relative;
}

.dropdown-content {
  @apply absolute left-0 bottom-full mb-2 z-50;
}

.menu {
  @apply py-1;
}

.menu li a {
  @apply block;
}

.badge {
  @apply inline-flex items-center px-2 py-1 rounded-full text-xs font-medium;
}

.badge-warning {
  @apply bg-yellow-100 dark:bg-yellow-900/20 text-yellow-700 dark:text-yellow-300;
}

.badge-info {
  @apply bg-blue-100 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300;
}

.badge-secondary {
  @apply bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300;
}

.badge-xs {
  @apply px-1.5 py-0.5 text-xs;
}

.text-secondary {
  @apply text-gray-600 dark:text-gray-400;
}
</style> 