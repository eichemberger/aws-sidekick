<template>
  <div class="flex flex-col h-screen bg-gray-900">
    <!-- Messages Area -->
    <MessageList 
      :messages="messages"
      :is-loading="isLoading"
      :loading-message="loadingMessage"
      :example-prompts="examplePrompts"
      @use-example="useExample"
      @copy-message="copyMessage"
    />

    <!-- Input Area -->
    <MessageInput
      ref="messageInputRef"
      :is-loading="isLoading"
      :is-initialized="chatStore.isInitialized"
      :current-conversation="chatStore.currentConversation"
      :conversation-count="chatStore.conversations.length"
      @send-message="handleSendMessage"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted, onUpdated, onUnmounted, computed, watch, defineAsyncComponent } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useChatStore } from '@/stores/chat'
import { useTasksStore } from '@/stores/tasks'

// Lazy load components for better performance
const MessageList = defineAsyncComponent(() => import('@/components/MessageList.vue'))
const MessageInput = defineAsyncComponent(() => import('@/components/MessageInput.vue'))

// Define props for route parameters
const props = defineProps<{
  id?: string
}>()

const route = useRoute()
const router = useRouter()
const chatStore = useChatStore()
const tasksStore = useTasksStore()

const messageInputRef = ref()

// Use chat store directly instead of local state
const messages = computed(() => chatStore.messages)
const isLoading = computed(() => chatStore.isLoading)

const loadingMessage = ref('AI is thinking...')

// Update loading message periodically to show progress
let loadingInterval: NodeJS.Timeout | null = null

const updateLoadingMessage = () => {
  const messages = [
    'AI is thinking...',
    'Analyzing your request...',
    'Checking AWS resources...',
    'Generating response...'
  ]
  let index = 0
  
  loadingInterval = setInterval(() => {
    loadingMessage.value = messages[index % messages.length]
    index++
  }, 3000) // Change message every 3 seconds
}

// Watch loading state to manage loading messages
watch(isLoading, (newValue) => {
  if (newValue) {
    updateLoadingMessage()
  } else {
    if (loadingInterval) {
      clearInterval(loadingInterval)
      loadingInterval = null
    }
    loadingMessage.value = 'AI is thinking...'
  }
})

// Watch for route changes to handle navigation between chats
watch(() => route.params.id, async (newId, oldId) => {
  if (newId !== oldId) {
    await handleRouteChange()
  }
}, { immediate: false })

const handleRouteChange = async () => {
  await chatStore.initializeChat()
  
  if (route.name === 'new-chat') {
    // Root path - start new chat
    await chatStore.startNewChat()
  } else if (route.name === 'chat' && props.id) {
    // Specific chat ID - load that chat
    const success = await chatStore.loadChatById(props.id)
    if (!success) {
      // Chat loading failed, likely doesn't exist
      router.push('/')
    }
  }
  
  await nextTick()
  scrollToBottom()
}

const examplePrompts = [
  "Analyze my AWS infrastructure for cost optimization opportunities",
  "Perform a security audit of my AWS resources and provide recommendations",
  "List all EC2 instances with their current status and configurations",
  "Help me optimize my S3 storage costs and lifecycle policies"
]

const useExample = (example: string) => {
  messageInputRef.value?.useExample(example)
}

const handleSendMessage = async (messageToSend: string) => {
  // Immediate visual feedback - add user message locally for instant display
  const userMessage = {
    id: `user-${Date.now()}`,
    conversation_id: chatStore.currentConversation?.id || 'temp',
    role: 'user' as const,
    content: messageToSend,
    timestamp: new Date()
  }

  // Add user message immediately for instant feedback
  chatStore.messages.push(userMessage)

  // Scroll to show the user's message immediately
  await nextTick()
  scrollToBottom()

  try {
    await chatStore.sendMessage(messageToSend)
    await nextTick()
    scrollToBottom()
  } catch (error) {
    console.error('Failed to send message:', error)
    // Remove the optimistically added message if there was an error
    const messageIndex = chatStore.messages.findIndex(msg => msg.id === userMessage.id)
    if (messageIndex !== -1) {
      chatStore.messages.splice(messageIndex, 1)
    }
  }
}

const copyMessage = async (content: string) => {
  try {
    await navigator.clipboard.writeText(content)
  } catch (error) {
    console.error('Failed to copy message:', error)
  }
}

const scrollToBottom = () => {
  const container = document.querySelector('.overflow-y-auto')
  if (container) {
    container.scrollTop = container.scrollHeight
  }
}

onMounted(async () => {
  await handleRouteChange()
})

onUpdated(() => {
  scrollToBottom()
})

onUnmounted(() => {
  if (loadingInterval) {
    clearInterval(loadingInterval)
    loadingInterval = null
  }
})
</script>

 