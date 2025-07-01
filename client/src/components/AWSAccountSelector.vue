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
        <!-- Current Active Account -->
        <li v-if="activeAccount" class="mb-2">
                     <div class="bg-blue-50 dark:bg-blue-900/10 rounded-lg p-3">
            <div class="flex items-center justify-between">
              <div>
                <div class="font-medium text-primary flex items-center gap-2">
                  <svg class="w-4 h-4 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                  </svg>
                  {{ activeAccount.alias }}
                  <span class="badge badge-success badge-xs">Active</span>
                </div>
                <div class="text-sm text-secondary">{{ activeAccount.description || 'No description' }}</div>
                <div class="text-xs text-secondary mt-1">
                  {{ activeAccount.region }} 
                  <span v-if="activeAccount.account_id">• {{ activeAccount.account_id }}</span>
                </div>
              </div>
              <button
                @click.stop="clearActiveAccount"
                class="btn btn-xs btn-ghost text-secondary hover:text-red-600"
                title="Clear active account"
              >
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        </li>

        <!-- Account List -->
        <li v-if="sortedAccounts.length > 0" class="menu-title mb-2">
          <span>Switch Account</span>
        </li>
        
        <li 
          v-for="account in availableAccounts" 
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
        <li class="border-t border-gray-200 dark:border-gray-700 mt-2 pt-2">
          <router-link @click="closeDropdown" to="/aws" class="p-3 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            Manage Accounts
          </router-link>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, onUnmounted } from 'vue'
import { useAwsAccountsStore } from '@/stores/awsAccounts'
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
const isDropdownOpen = ref(false)
const dropdownContainer = ref<HTMLElement>()

// Computed
const availableAccounts = computed(() => 
  sortedAccounts.value.filter(account => account.alias !== activeAccountAlias.value)
)

const isDisabled = computed(() => 
  Boolean(error.value && error.value.includes('404'))
)

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

.btn-ghost {
  @apply bg-transparent hover:bg-gray-100 dark:hover:bg-gray-700;
}

.btn-xs {
  @apply px-1 py-0.5 text-xs;
}

.dropdown {
  @apply relative;
}

.dropdown-content {
  @apply absolute bottom-full left-0 mb-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl z-10;
}

.menu {
  @apply py-1;
}

.menu li a {
  @apply block px-3 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer rounded-lg;
}

.menu-title {
  @apply px-3 py-1 text-xs font-semibold text-secondary uppercase tracking-wider;
}

.badge {
  @apply inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium;
}

.badge-success {
  @apply bg-green-100 dark:bg-green-900/20 text-green-700 dark:text-green-300;
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
  @apply px-1 py-0 text-xs;
}

.loading {
  @apply animate-spin;
}

.loading-spinner {
  @apply w-4 h-4 border-2 border-current border-t-transparent rounded-full;
}

.loading-sm {
  @apply w-3 h-3;
}
</style> 