<template>
  <div class="h-screen bg-white dark:bg-gray-900 relative flex flex-col">
    <!-- Loading Indicator -->
    <LoadingIndicator 
      :is-loading="isLoading"
      :loading-message="loadingMessage"
      :show-backdrop="isLoading && messages.length === 0"
    />

    <!-- Messages Area with Virtual Scroll -->
    <div class="flex-1 min-h-0">
      <!-- Show skeleton when initializing -->
      <div v-if="!chatStore.isInitialized || (isLoading && messages.length === 0)" class="h-full">
        <SkeletonLoader 
          type="messages"
          :count="5"
          container-class="p-6 h-full overflow-y-auto"
        />
      </div>
      
      <!-- Simple Scrollable Messages -->
      <div v-else-if="displayMessages.length > 0" ref="messagesContainer" class="h-full overflow-y-auto custom-scrollbar">
        <div class="max-w-4xl mx-auto py-4">
          <div
            v-for="(message, index) in displayMessages"
            :key="message.id"
            class="px-4 py-2"
          >
            <!-- User Message (Right Side) -->
            <div v-if="message.role === 'user'" class="flex gap-3 items-start justify-end">
              <!-- Message Bubble -->
              <div class="flex-shrink-0 max-w-3xl">
                <div class="group relative rounded-lg px-4 py-3 bg-blue-600 text-white">
                  <div class="markdown-content pr-8" v-html="formatMessage(message.content)"></div>
                  
                  <!-- Copy Button - Top Right Corner -->
                  <button
                    @click="copyMessage(message.content)"
                    class="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 p-1 rounded hover:bg-black/10"
                    title="Copy message"
                  >
                    <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
                    </svg>
                  </button>
                </div>
              </div>
              
              <!-- Avatar -->
              <div class="flex-shrink-0">
                <div class="w-8 h-8 rounded-lg flex items-center justify-center shadow-sm bg-blue-500">
                  <span class="text-white text-xs font-bold">U</span>
                </div>
              </div>
            </div>

            <!-- AI Message (Left Side) -->
            <div v-else class="flex gap-3 items-start">
              <!-- Avatar -->
              <div class="flex-shrink-0">
                <div class="w-8 h-8 rounded-lg flex items-center justify-center shadow-sm bg-emerald-500">
                  <span class="text-white text-xs font-bold">AI</span>
                </div>
              </div>
              
              <!-- Message Bubble -->
              <div class="flex-shrink-0 max-w-3xl">
                <div class="group relative rounded-lg px-4 py-3 bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white">
                  <div class="markdown-content pr-8" v-html="formatMessage(message.content)"></div>
                  
                  <!-- Copy Button - Top Right Corner -->
                  <button
                    @click="copyMessage(message.content)"
                    class="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 p-1 rounded hover:bg-black/10 dark:hover:bg-white/10"
                    title="Copy message"
                  >
                    <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Welcome Screen -->
      <div v-else class="h-full flex items-center justify-center">
        <div class="text-center max-w-4xl mx-auto px-6">
          <div class="w-20 h-20 mx-auto mb-8 bg-gradient-to-br from-blue-500 via-purple-600 to-indigo-700 rounded-3xl flex items-center justify-center shadow-2xl">
            <svg class="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
            </svg>
          </div>
          <h1 class="text-4xl font-bold text-primary mb-4">AWS Sidekick</h1>
          <p class="text-secondary mb-12 text-xl max-w-2xl mx-auto">How can I help you with your AWS infrastructure today?</p>
          
          <!-- Example Prompts -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-4xl mx-auto">
            <button
              v-for="example in examplePrompts"
              :key="example"
              @click="useExample(example)"
              class="group p-6 text-left rounded-2xl border border-gray-200 dark:border-gray-700 hover:border-blue-500/50 bg-gray-50/50 dark:bg-gray-800/50 hover:bg-gray-100 dark:hover:bg-gray-800 transition-all duration-300 hover:shadow-xl hover:shadow-blue-500/10 hover:scale-[1.02]"
            >
              <div class="text-sm text-secondary group-hover:text-primary transition-colors leading-relaxed">{{ example }}</div>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Fixed Input Area at Bottom -->
    <div class="border-t border-gray-200 dark:border-gray-700/50 bg-white/95 dark:bg-gray-900/95 backdrop-blur-sm">
      <MessageInput
        ref="messageInputRef"
        :is-loading="isLoading"
        :is-initialized="chatStore.isInitialized"
        :current-conversation="chatStore.currentConversation"
        :conversation-count="chatStore.conversations.length"
        :disabled="isLoading"
        @send-message="handleSendMessage"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted, onUpdated, onUnmounted, computed, watch, defineAsyncComponent } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useChatStore } from '@/stores/chat'
import { useTasksStore } from '@/stores/tasks'
import { useAwsAccountsStore } from '@/stores/awsAccounts'

// Lazy load components for better performance
const MessageInput = defineAsyncComponent(() => import('@/components/MessageInput.vue'))
const LoadingIndicator = defineAsyncComponent(() => import('@/components/LoadingIndicator.vue'))
const SkeletonLoader = defineAsyncComponent(() => import('@/components/SkeletonLoader.vue'))

// Define props for route parameters
const props = defineProps<{
  id?: string
}>()

const route = useRoute()
const router = useRouter()
const chatStore = useChatStore()
const tasksStore = useTasksStore()
const awsAccountsStore = useAwsAccountsStore()

const messageInputRef = ref()
const messagesContainer = ref<HTMLElement>()

// Use chat store directly instead of local state
const messages = computed(() => chatStore.messages)
const isLoading = computed(() => chatStore.isLoading || awsAccountsStore.isLoading)

// Display messages with loading indicator
const displayMessages = computed(() => {
  const baseMessages = [...chatStore.messages]
  
  // Add loading message when AI is processing (but not when switching accounts)
  if (chatStore.isLoading && !awsAccountsStore.isLoading) {
    baseMessages.push({
      id: 'loading-message',
      conversation_id: chatStore.currentConversation?.id || 'temp',
      role: 'assistant' as const,
      content: '🤔 *Thinking and analyzing your request...*',
      timestamp: new Date()
    })
  }
  
  return baseMessages
})

const loadingMessage = computed(() => {
  if (awsAccountsStore.isLoading) {
    return 'Switching AWS account...'
  }
  if (chatStore.isLoading) {
    return 'AI is analyzing your request...'
  }
  return 'Loading...'
})

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
  // Check if an AWS account is selected before sending the message
  if (!awsAccountsStore.activeAccount) {
    // Show error notification or alert to user
    console.warn('Cannot send message: No AWS account selected')
    alert('Please select an AWS account before sending messages.')
    return
  }

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
  scrollToBottom() // Immediate scroll for user messages

  try {
    await chatStore.sendMessage(messageToSend)
    // Bot message auto-scroll is now handled by the watcher
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

const scrollToBottom = (smooth = false) => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTo({
      top: messagesContainer.value.scrollHeight,
      behavior: smooth ? 'smooth' : 'auto'
    })
  }
}

// Import markdown-it for proper markdown parsing
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'

// Configure markdown parser with syntax highlighting
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
  breaks: true,
  highlight: function (str: string, lang: string): string {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return `<pre class="hljs-pre"><code class="hljs hljs-${lang}">${hljs.highlight(str, { language: lang }).value}</code></pre>`
      } catch (__) {}
    }
    return `<pre class="hljs-pre"><code class="hljs">${md.utils.escapeHtml(str)}</code></pre>`
  }
})

const formatMessage = (content: string | undefined | null) => {
  try {
    if (!content || typeof content !== 'string') {
      return `<p class="text-yellow-400">⚠️ No content to display</p>`
    }
    
    let cleanContent = content.trim()
    if (!cleanContent) {
      return `<p class="text-yellow-400">⚠️ Empty message</p>`
    }
    
    let html = md.render(cleanContent)
    html = enhanceAWSContent(html)
    
    return html
  } catch (error) {
    console.error('Markdown parsing error:', error)
    return `<p class="text-red-400">Error rendering markdown: ${error}</p>`
  }
}

const enhanceAWSContent = (html: string) => {
  return html
    // Enhance AWS resource IDs with modern styling
    .replace(/(i-[a-f0-9]{8,17})/g, '<span class="aws-resource ec2">$1</span>')
    .replace(/(sg-[a-f0-9]{8,17})/g, '<span class="aws-resource security-group">$1</span>')
    .replace(/(vol-[a-f0-9]{8,17})/g, '<span class="aws-resource volume">$1</span>')
    .replace(/(subnet-[a-f0-9]{8,17})/g, '<span class="aws-resource subnet">$1</span>')
    .replace(/(vpc-[a-f0-9]{8,17})/g, '<span class="aws-resource vpc">$1</span>')
    .replace(/(ami-[a-f0-9]{8,17})/g, '<span class="aws-resource ami">$1</span>')
    .replace(/(eni-[a-f0-9]{8,17})/g, '<span class="aws-resource eni">$1</span>')
    .replace(/(rtb-[a-f0-9]{8,17})/g, '<span class="aws-resource route-table">$1</span>')
    
    // Enhance status indicators
    .replace(/\b(RUNNING|running|Running)\b/g, '<span class="status-badge success">✅ $1</span>')
    .replace(/\b(STOPPED|stopped|Stopped)\b/g, '<span class="status-badge warning">⚠️ $1</span>')
    .replace(/\b(TERMINATED|terminated|Terminated)\b/g, '<span class="status-badge error">❌ $1</span>')
    .replace(/\b(PENDING|pending|Pending)\b/g, '<span class="status-badge info">⏳ $1</span>')
    
    // Enhance AWS regions
    .replace(/\b(us-[a-z]+-\d+|eu-[a-z]+-\d+|ap-[a-z]+-\d+|ca-[a-z]+-\d+|sa-[a-z]+-\d+|af-[a-z]+-\d+|me-[a-z]+-\d+)\b/g, '<span class="aws-region">🌍 $1</span>')
    
    // Enhance table wrapper
    .replace(/<table>/g, '<div class="table-wrapper"><table class="aws-table">')
    .replace(/<\/table>/g, '</table></div>')
}

// No need for container height calculation with simple scroll

onMounted(async () => {
  await handleRouteChange()
})

// Track last message for onUpdated fallback
const lastMessageId = ref<string | null>(null)

onUpdated(() => {
  // Only scroll if we have a new bot message as fallback
  if (displayMessages.value.length > 0) {
    const lastMessage = displayMessages.value[displayMessages.value.length - 1]
    if (lastMessage && 
        lastMessage.role === 'assistant' && 
        lastMessage.id !== 'loading-message' &&
        lastMessage.id !== lastMessageId.value) {
      lastMessageId.value = lastMessage.id
      scrollToBottom(true)
    }
  }
})

onUnmounted(() => {
  // Cleanup if needed
})

// Watch for route changes to handle navigation between chats
watch(() => route.params.id, async (newId, oldId) => {
  if (newId !== oldId) {
    await handleRouteChange()
  }
}, { immediate: false })

// Watch for new bot messages and auto-scroll
watch(displayMessages, (newMessages, oldMessages) => {
  if (newMessages.length > oldMessages.length) {
    const lastMessage = newMessages[newMessages.length - 1]
    // Auto-scroll when bot (assistant) replies (ignore loading message)
    if (lastMessage && lastMessage.role === 'assistant' && lastMessage.id !== 'loading-message') {
      nextTick(() => {
        // Small delay to ensure the message is fully rendered
        setTimeout(() => {
          scrollToBottom(true) // Use smooth scrolling for bot replies
        }, 150)
      })
    }
  }
}, { deep: true })

// Also watch for when messages container becomes available
watch(messagesContainer, (container) => {
  if (container && displayMessages.value.length > 0) {
    nextTick(() => {
      scrollToBottom(false) // Immediate scroll when container becomes available
    })
  }
})

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
  scrollToBottom() // Immediate scroll for initial loading
}
</script>

<style scoped>
/* Enhanced Markdown Styling */
.markdown-content {
  font-size: 14px;
  line-height: 1.6;
}

/* Typography */
.markdown-content :deep(h1) {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 1rem 0 0.5rem 0;
  border-bottom: 1px solid currentColor;
  padding-bottom: 0.25rem;
}

.markdown-content :deep(h2) {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0.75rem 0 0.5rem 0;
  color: inherit;
}

.markdown-content :deep(h3) {
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0.5rem 0 0.25rem 0;
}

.markdown-content :deep(h4),
.markdown-content :deep(h5),
.markdown-content :deep(h6) {
  font-size: 1rem;
  font-weight: 600;
  margin: 0.5rem 0 0.25rem 0;
}

.markdown-content :deep(p) {
  margin: 0 0 0.75rem 0;
}

.markdown-content :deep(p:last-child) {
  margin-bottom: 0;
}

.markdown-content :deep(strong) {
  font-weight: 700;
}

.markdown-content :deep(em) {
  font-style: italic;
}

/* Lists */
.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  margin: 0.5rem 0;
  padding-left: 1.5rem;
}

.markdown-content :deep(li) {
  margin: 0.25rem 0;
}

.markdown-content :deep(ul li) {
  list-style-type: disc;
}

.markdown-content :deep(ol li) {
  list-style-type: decimal;
}

/* Code */
.markdown-content :deep(code) {
  background-color: rgba(0, 0, 0, 0.1);
  padding: 0.125rem 0.25rem;
  border-radius: 0.25rem;
  font-family: 'SFMono-Regular', 'Monaco', 'Cascadia Code', 'Roboto Mono', monospace;
  font-size: 0.875rem;
}

.markdown-content :deep(.hljs-pre) {
  background-color: #2d3748;
  border-radius: 0.5rem;
  padding: 1rem;
  margin: 0.5rem 0;
  overflow-x: auto;
}

.markdown-content :deep(.hljs) {
  background: transparent !important;
  color: #e2e8f0;
  font-family: 'SFMono-Regular', 'Monaco', 'Cascadia Code', 'Roboto Mono', monospace;
  font-size: 0.875rem;
}

/* Links */
.markdown-content :deep(a) {
  color: #3b82f6;
  text-decoration: underline;
}

.markdown-content :deep(a:hover) {
  color: #1d4ed8;
}

/* Blockquotes */
.markdown-content :deep(blockquote) {
  border-left: 4px solid currentColor;
  padding-left: 1rem;
  margin: 0.5rem 0;
  opacity: 0.8;
  font-style: italic;
}

/* Tables */
.markdown-content :deep(.table-wrapper) {
  overflow-x: auto;
  margin: 0.5rem 0;
}

.markdown-content :deep(.aws-table) {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.markdown-content :deep(.aws-table th),
.markdown-content :deep(.aws-table td) {
  border: 1px solid rgba(0, 0, 0, 0.2);
  padding: 0.5rem;
  text-align: left;
}

.markdown-content :deep(.aws-table th) {
  background-color: rgba(0, 0, 0, 0.1);
  font-weight: 600;
}

/* AWS Resource Highlighting */
.markdown-content :deep(.aws-resource) {
  background-color: rgba(59, 130, 246, 0.1);
  color: #1d4ed8;
  padding: 0.125rem 0.25rem;
  border-radius: 0.25rem;
  font-family: monospace;
  font-size: 0.875rem;
}

.markdown-content :deep(.status-badge) {
  padding: 0.125rem 0.375rem;
  border-radius: 0.375rem;
  font-size: 0.75rem;
  font-weight: 600;
}

.markdown-content :deep(.status-badge.success) {
  background-color: rgba(34, 197, 94, 0.1);
  color: #15803d;
}

.markdown-content :deep(.status-badge.warning) {
  background-color: rgba(251, 191, 36, 0.1);
  color: #a16207;
}

.markdown-content :deep(.status-badge.error) {
  background-color: rgba(239, 68, 68, 0.1);
  color: #dc2626;
}

.markdown-content :deep(.status-badge.info) {
  background-color: rgba(59, 130, 246, 0.1);
  color: #1d4ed8;
}

.markdown-content :deep(.aws-region) {
  background-color: rgba(168, 85, 247, 0.1);
  color: #7c3aed;
  padding: 0.125rem 0.25rem;
  border-radius: 0.25rem;
  font-size: 0.875rem;
}

/* User message styling overrides */
.bg-blue-600 .markdown-content {
  color: white;
}

.bg-blue-600 .markdown-content :deep(h1),
.bg-blue-600 .markdown-content :deep(h2),
.bg-blue-600 .markdown-content :deep(h3),
.bg-blue-600 .markdown-content :deep(h4),
.bg-blue-600 .markdown-content :deep(h5),
.bg-blue-600 .markdown-content :deep(h6) {
  color: white;
  border-color: rgba(255, 255, 255, 0.3);
}

.bg-blue-600 .markdown-content :deep(strong) {
  color: white;
}

.bg-blue-600 .markdown-content :deep(em) {
  color: rgba(255, 255, 255, 0.9);
}

.bg-blue-600 .markdown-content :deep(code) {
  background-color: rgba(255, 255, 255, 0.2);
  color: white;
}

.bg-blue-600 .markdown-content :deep(a) {
  color: #bfdbfe;
}

.bg-blue-600 .markdown-content :deep(a:hover) {
  color: white;
}

.bg-blue-600 .markdown-content :deep(blockquote) {
  border-color: rgba(255, 255, 255, 0.3);
}

.bg-blue-600 .markdown-content :deep(.aws-table th),
.bg-blue-600 .markdown-content :deep(.aws-table td) {
  border-color: rgba(255, 255, 255, 0.2);
}

.bg-blue-600 .markdown-content :deep(.aws-table th) {
  background-color: rgba(255, 255, 255, 0.1);
}

/* Custom scrollbar for chat container */
.custom-scrollbar {
  scrollbar-width: thin;
  scrollbar-color: rgba(156, 163, 175, 0.4) transparent;
}

.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(156, 163, 175, 0.4);
  border-radius: 3px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(156, 163, 175, 0.6);
}

.dark .custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(75, 85, 99, 0.4);
}

.dark .custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(75, 85, 99, 0.6);
}

/* Custom scrollbar for virtual list */
:deep(.virtual-list) {
  scrollbar-width: thin;
  scrollbar-color: rgba(156, 163, 175, 0.4) transparent;
}

:deep(.virtual-list::-webkit-scrollbar) {
  width: 6px;
}

:deep(.virtual-list::-webkit-scrollbar-track) {
  background: transparent;
}

:deep(.virtual-list::-webkit-scrollbar-thumb) {
  background: rgba(156, 163, 175, 0.4);
  border-radius: 3px;
}

:deep(.virtual-list::-webkit-scrollbar-thumb:hover) {
  background: rgba(156, 163, 175, 0.6);
}

.dark :deep(.virtual-list::-webkit-scrollbar-thumb) {
  background: rgba(75, 85, 99, 0.4);
}

.dark :deep(.virtual-list::-webkit-scrollbar-thumb:hover) {
  background: rgba(75, 85, 99, 0.6);
}
</style>

 