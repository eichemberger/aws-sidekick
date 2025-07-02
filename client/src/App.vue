<template>
  <div class="flex h-screen bg-white dark:bg-gray-900 text-gray-900 dark:text-white transition-colors duration-200">
    <!-- Sidebar -->
    <div class="w-64 sidebar flex flex-col">
      <!-- Header -->
      <div class="p-4 border-b border-gray-200 dark:border-gray-700">
        <button
          @click="createNewChat"
          class="w-full flex items-center gap-3 px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
          </svg>
          New chat
        </button>
      </div>

      <!-- Chat History -->
      <div class="flex-1 overflow-y-auto custom-scrollbar">
        <div class="p-2 space-y-1">
          <div
            v-for="conversation in chatStore.conversations"
            :key="conversation.id"
            @click="selectChat(conversation.id)"
            class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 cursor-pointer transition-colors group"
            :class="{ 
              'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white': isCurrentChat(conversation.id),
              'text-gray-700 dark:text-gray-300': !isCurrentChat(conversation.id)
            }"
          >
            <svg class="w-4 h-4 text-gray-400 dark:text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-3.582 8-8 8a8.959 8.959 0 01-4.906-1.471L3 21l2.471-5.094A8.959 8.959 0 013 12c0-4.418 3.582-8 8-8s8 3.582 8 8z"></path>
            </svg>
            <span class="flex-1 text-sm truncate">{{ conversation.title }}</span>
            <button
              @click.stop="deleteChat(conversation.id)"
              class="opacity-0 group-hover:opacity-100 text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-all"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
              </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- Bottom Menu -->
      <div class="p-4 border-t border-gray-200 dark:border-gray-700 space-y-2">
        <router-link
          to="/tasks"
          class="nav-item"
          :class="{ 'active': $route.path === '/tasks' }"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>
          </svg>
          Tasks
        </router-link>
        
        <router-link
          to="/aws"
          class="nav-item"
          :class="{ 'active': $route.path === '/aws' }"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path>
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
          </svg>
          AWS Settings
        </router-link>

        <!-- Theme Toggle -->
        <div class="pt-2 border-t border-gray-200 dark:border-gray-700">
          <ThemeToggle />
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="flex-1 flex flex-col bg-white dark:bg-gray-900">
      <router-view />
    </div>

    <!-- Global Credentials Error Modal -->
    <div 
      v-if="awsAccountsStore.showCredentialsErrorModal" 
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" 
      role="dialog"
      aria-modal="true"
      aria-labelledby="credentials-error-title"
      aria-describedby="credentials-error-description"
      @click="closeCredentialsError"
    >
      <div class="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md mx-4 shadow-xl" @click.stop>
        <div class="flex items-start">
          <div class="flex-shrink-0">
            <svg class="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-7.938 4h15.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.082 16.5c-.77.833.19 2.5 1.732 2.5z" />
            </svg>
          </div>
          <div class="ml-3 flex-1">
            <h3 id="credentials-error-title" class="text-lg font-medium text-gray-900 dark:text-white mb-2">
              Credentials Required
            </h3>
            <p id="credentials-error-description" class="text-sm text-gray-600 dark:text-gray-300 mb-4">
              The account <strong>"{{ awsAccountsStore.credentialsErrorAccount }}"</strong> doesn't have valid credentials set up. 
              Please upload your AWS credentials to access this account.
            </p>
            <div class="flex flex-col sm:flex-row gap-3">
              <button
                ref="primaryActionButton"
                @click="navigateToAwsSettings"
                class="flex-1 inline-flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                Go to AWS Settings
              </button>
              <button
                @click="closeCredentialsError"
                class="flex-1 inline-flex justify-center items-center px-4 py-2 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useChatStore } from '@/stores/chat'
import { useThemeStore } from '@/stores/theme'
import { useAwsAccountsStore } from '@/stores/awsAccounts'
import ThemeToggle from '@/components/ThemeToggle.vue'

const router = useRouter()
const route = useRoute()
const chatStore = useChatStore()
const themeStore = useThemeStore()
const awsAccountsStore = useAwsAccountsStore()

// Template refs
const primaryActionButton = ref<HTMLButtonElement>()

// Watch for modal state changes to manage focus
watch(() => awsAccountsStore.showCredentialsErrorModal, async (isOpen) => {
  if (isOpen) {
    await nextTick()
    primaryActionButton.value?.focus()
  }
})

// Initialize stores on app mount
onMounted(async () => {
  await chatStore.initializeChat()
  themeStore.initializeTheme()
  
  // Add keyboard event listener
  document.addEventListener('keydown', handleGlobalKeydown)
})

onUnmounted(() => {
  // Remove keyboard event listener
  document.removeEventListener('keydown', handleGlobalKeydown)
})

const createNewChat = async () => {
  try {
    // Navigate to root path for new chat
    await router.push('/')
  } catch (error) {
    console.error('Failed to navigate to new chat:', error)
  }
}

const selectChat = async (conversationId: string) => {
  try {
    // Navigate to specific chat URL
    await router.push(`/chat/${conversationId}`)
  } catch (error) {
    console.error('Failed to navigate to chat:', error)
  }
}

const deleteChat = async (conversationId: string) => {
  try {
    await chatStore.deleteConversation(conversationId)
    // If we deleted the current chat, navigate to new chat
    if (route.params.id === conversationId) {
      await router.push('/')
    }
  } catch (error) {
    console.error('Failed to delete chat:', error)
  }
}

// Check if a conversation is the currently active one based on URL
const isCurrentChat = (conversationId: string) => {
  return route.params.id === conversationId
}

// Global keyboard handler
const handleGlobalKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Escape' && awsAccountsStore.showCredentialsErrorModal) {
    closeCredentialsError()
  }
}

// Credentials error modal methods
const closeCredentialsError = () => {
  awsAccountsStore.closeCredentialsErrorModal()
}

const navigateToAwsSettings = async () => {
  closeCredentialsError()
  await router.push('/aws')
}
</script> 