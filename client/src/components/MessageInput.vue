<template>
  <div class="border-t border-gray-700/50 bg-gray-900/50 backdrop-blur-sm p-6">
    <div class="max-w-4xl mx-auto">
      <!-- Chat Info Row -->
      <div v-if="isInitialized" class="flex justify-between items-center mb-4">
        <div class="text-sm text-gray-400">
          <span v-if="currentConversation" class="font-medium">{{ currentConversation.title }}</span>
          <span v-else-if="conversationCount > 0" class="font-medium">{{ conversationCount }} conversation(s)</span>
          <span v-else class="font-medium">Ready to chat</span>
        </div>
      </div>

      <div class="relative">
        <textarea
          ref="messageInput"
          v-model="inputMessage"
          @keydown="handleKeydown"
          @input="adjustTextareaHeight"
          placeholder="Ask me anything about your AWS infrastructure..."
          class="w-full bg-gray-800/50 border border-gray-600/50 rounded-2xl px-6 py-4 pr-14 text-white placeholder-gray-400 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-200"
          rows="1"
          :disabled="isLoading"
        ></textarea>
        
        <!-- Send Button -->
        <button
          @click="sendMessage"
          :disabled="!inputMessage.trim() || isLoading"
          class="absolute right-3 bottom-3 p-2.5 rounded-xl transition-all duration-200 shadow-lg"
          :class="inputMessage.trim() && !isLoading 
            ? 'bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white shadow-blue-500/25' 
            : 'text-gray-500 cursor-not-allowed bg-gray-700/50'"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path>
          </svg>
        </button>
      </div>
      
      <!-- Footer -->
      <div class="text-center text-xs text-gray-500 mt-4">
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
import { ref, nextTick } from 'vue'
import type { Conversation } from '@/types/api'

interface Props {
  isLoading: boolean
  isInitialized: boolean
  currentConversation: Conversation | null
  conversationCount: number
}

interface Emits {
  (e: 'send-message', message: string): void
  (e: 'use-example', example: string): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const messageInput = ref<HTMLTextAreaElement>()
const inputMessage = ref('')

const adjustTextareaHeight = () => {
  if (messageInput.value) {
    messageInput.value.style.height = 'auto'
    messageInput.value.style.height = Math.min(messageInput.value.scrollHeight, 200) + 'px'
  }
}

const handleKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendMessage()
  }
}

const sendMessage = () => {
  if (!inputMessage.value.trim() || props.isLoading) return

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