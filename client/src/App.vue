<template>
  <div class="flex h-screen bg-gray-900 text-white">
    <!-- Sidebar -->
    <div class="w-64 bg-gray-900 border-r border-gray-700 flex flex-col">
      <!-- Header -->
      <div class="p-4 border-b border-gray-700">
        <button
          @click="createNewChat"
          class="w-full flex items-center gap-3 px-3 py-2 rounded-lg border border-gray-600 hover:bg-gray-800 transition-colors"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
          </svg>
          New chat
        </button>
      </div>

      <!-- Chat History -->
      <div class="flex-1 overflow-y-auto">
        <div class="p-2 space-y-1">
          <div
            v-for="conversation in chatStore.conversations"
            :key="conversation.id"
            @click="selectChat(conversation.id)"
            class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-800 cursor-pointer transition-colors group"
            :class="{ 'bg-gray-800': isCurrentChat(conversation.id) }"
          >
            <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-3.582 8-8 8a8.959 8.959 0 01-4.906-1.471L3 21l2.471-5.094A8.959 8.959 0 013 12c0-4.418 3.582-8 8-8s8 3.582 8 8z"></path>
            </svg>
            <span class="flex-1 text-sm truncate">{{ conversation.title }}</span>
            <button
              @click.stop="deleteChat(conversation.id)"
              class="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-white transition-all"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
              </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- Bottom Menu -->
      <div class="p-4 border-t border-gray-700 space-y-2">
        <router-link
          to="/tasks"
          class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-800 transition-colors text-sm"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>
          </svg>
          Tasks
        </router-link>
        <router-link
          to="/aws"
          class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-800 transition-colors text-sm"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path>
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
          </svg>
          AWS Settings
        </router-link>
      </div>
    </div>

    <!-- Main Content -->
    <div class="flex-1 flex flex-col">
      <router-view />
    </div>
    
    <!-- Performance Monitor (dev only) -->
    <PerformanceMonitor />
  </div>
</template>

<script setup lang="ts">
import { onMounted, defineAsyncComponent, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useChatStore } from '@/stores/chat'

// Lazy load performance monitor
const PerformanceMonitor = defineAsyncComponent(() => import('@/components/PerformanceMonitor.vue'))

const router = useRouter()
const route = useRoute()
const chatStore = useChatStore()

// Initialize chat store on app mount
onMounted(async () => {
  await chatStore.initializeChat()
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
</script> 