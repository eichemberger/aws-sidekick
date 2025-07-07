<template>
  <div class="border-t border-gray-200 dark:border-gray-700/50 bg-white/50 dark:bg-gray-900/50 backdrop-blur-sm p-3">
    <div class="max-w-4xl mx-auto">
      <!-- Chat Info Row -->
      <div v-if="isInitialized" class="flex justify-between items-center mb-2">
        <div class="text-sm text-secondary">
          <span v-if="currentConversation" class="font-medium">{{ currentConversation.title }}</span>
          <span v-else-if="conversationCount > 0" class="font-medium">{{ conversationCount }} conversation(s)</span>
          <span v-else class="font-medium">Ready to chat</span>
        </div>
        <AWSAccountSelector />
      </div>

      <div class="relative">        
        <textarea
          ref="messageInput"
          v-model="inputMessage"
          @keydown="handleKeydown"
          @input="adjustTextareaHeight"
          :placeholder="disabled ? 'Processing...' : !canSendMessage ? 'Please select an AWS account to start chatting...' : 'Ask me anything about your AWS infrastructure...'"
          class="w-full bg-gray-50/50 dark:bg-gray-800/50 border border-gray-300/50 dark:border-gray-600/50 rounded-2xl px-6 py-4 pr-14 text-sm leading-5 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-200 overflow-y-auto custom-scrollbar"
          :class="{ 
            'opacity-60 cursor-not-allowed': disabled || !canSendMessage
          }"
          rows="1"
          :disabled="disabled || !canSendMessage"
        ></textarea>
        
        <!-- Send Button -->
        <button
          @click="sendMessage"
          :disabled="!inputMessage.trim() || disabled || !canSendMessage"
          class="absolute right-2 top-1/2 transform -translate-y-1/2 p-2 rounded-xl transition-all duration-200 shadow-lg"
          :class="inputMessage.trim() && !disabled && canSendMessage
            ? 'bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white shadow-blue-500/25' 
            : 'text-gray-400 dark:text-gray-500 cursor-not-allowed bg-gray-200 dark:bg-gray-700/50'"
        >
          <!-- Send Icon -->
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path>
          </svg>
        </button>
      </div>
      
      <!-- Footer -->
      <div class="text-center text-xs text-muted mt-3">
        <span class="inline-flex items-center gap-1">
          <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path>
          </svg>
          AWS Agent can make mistakes. Consider checking important information.
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, computed } from 'vue'
import { storeToRefs } from 'pinia'
import type { Conversation } from '@/types/api'
import AWSAccountSelector from './AWSAccountSelector.vue'
import { useAwsAccountsStore } from '@/stores/awsAccounts'

interface Props {
  isLoading: boolean
  isInitialized: boolean
  currentConversation: Conversation | null
  conversationCount: number
  disabled?: boolean
}

interface Emits {
  (e: 'send-message', message: string): void
  (e: 'use-example', example: string): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// AWS Account Store
const awsAccountsStore = useAwsAccountsStore()
const { activeAccount } = storeToRefs(awsAccountsStore)

const messageInput = ref<HTMLTextAreaElement>()
const inputMessage = ref('')

// Check if user can send messages (has selected an account)
const canSendMessage = computed(() => Boolean(activeAccount.value))

const adjustTextareaHeight = () => {
  if (messageInput.value) {
    messageInput.value.style.height = 'auto'
    messageInput.value.style.height = Math.min(messageInput.value.scrollHeight, 260) + 'px'
  }
}

const handleKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendMessage()
  }
}

const sendMessage = () => {
  if (!inputMessage.value.trim() || props.disabled || !canSendMessage.value) return

  const messageToSend = inputMessage.value.trim()
  inputMessage.value = ''
  adjustTextareaHeight()

  emit('send-message', messageToSend)
}

const useExample = (example: string) => {
  inputMessage.value = example
  nextTick(() => {
    adjustTextareaHeight()
    messageInput.value?.focus()
  })
}

// Expose method to parent component
defineExpose({
  useExample,
  focus: () => messageInput.value?.focus()
})
</script>

<style scoped>
/* Removed unused animations */
/* @keyframes spin-slow {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.animate-spin-slow {
  animation: spin-slow 3s linear infinite;
} */

/* Improved focus styles for better accessibility */
textarea:focus-visible {
  outline: 2px solid rgb(59 130 246 / 0.5);
  outline-offset: 2px;
}

/* Better disabled state styling */
textarea:disabled {
  background-color: rgb(156 163 175 / 0.1);
}

/* Custom scrollbar styling */
.custom-scrollbar {
  scrollbar-width: thin;
  scrollbar-color: rgb(156 163 175 / 0.5) transparent;
}

.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: rgb(156 163 175 / 0.5);
  border-radius: 2px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background-color: rgb(156 163 175 / 0.8);
}

/* Dark mode scrollbar */
.dark .custom-scrollbar {
  scrollbar-color: rgb(75 85 99 / 0.5) transparent;
}

.dark .custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: rgb(75 85 99 / 0.5);
}

.dark .custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background-color: rgb(75 85 99 / 0.8);
}

@media (prefers-reduced-motion: reduce) {
  button {
    transition: none;
  }
  
  textarea {
    transition: none;
  }
}
</style> 