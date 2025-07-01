import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ChatMessage, Conversation } from '@/types/api'
import { apiService } from '@/services/api'
import { useAwsAccountsStore } from '@/stores/awsAccounts'

// Import router to handle navigation
import router from '@/router'

export const useChatStore = defineStore('chat', () => {
  const messages = ref<ChatMessage[]>([])
  const currentConversation = ref<Conversation | null>(null)
  const conversations = ref<Conversation[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const isInitialized = ref(false)

  const messageCount = computed(() => messages.value.length)
  const lastMessage = computed(() => messages.value[messages.value.length - 1])

  const initializeChat = async () => {
    if (isInitialized.value) return
    
    try {
      // Load recent conversations
      conversations.value = await apiService.getConversations(10, 0)
      isInitialized.value = true
    } catch (err) {
      console.error('Failed to initialize chat:', err)
      error.value = err instanceof Error ? err.message : 'Failed to initialize chat'
      isInitialized.value = true
    }
  }

  const startNewChat = async () => {
    try {
      // Clear current state
      currentConversation.value = null
      messages.value = []
      error.value = null
      
      // Don't add welcome message - let MessageList component handle the welcome screen
      
      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to start new chat'
      return false
    }
  }

  const loadChatById = async (chatId: string) => {
    try {
      isLoading.value = true
      error.value = null
      
      const [conversation, conversationMessages] = await Promise.all([
        apiService.getConversation(chatId),
        apiService.getConversationMessages(chatId)
      ])
      
      currentConversation.value = conversation
      messages.value = conversationMessages
      
      // Update conversations list if this conversation isn't in it yet
      if (!conversations.value.find(c => c.id === chatId)) {
        conversations.value.unshift(conversation)
      }
      
      return true
    } catch (err) {
      console.error('Failed to load chat:', err)
      error.value = err instanceof Error ? err.message : `Failed to load chat: ${chatId}`
      
      // If chat doesn't exist, redirect to new chat
      if (err instanceof Error && err.message.includes('404')) {
        router.push('/')
      }
      
      return false
    } finally {
      isLoading.value = false
    }
  }

  const loadConversation = async (conversationId: string) => {
    try {
      isLoading.value = true
      const [conversation, conversationMessages] = await Promise.all([
        apiService.getConversation(conversationId),
        apiService.getConversationMessages(conversationId)
      ])
      
      currentConversation.value = conversation
      messages.value = conversationMessages
      
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to load conversation'
    } finally {
      isLoading.value = false
    }
  }

  const sendMessage = async (content: string) => {
    if (!content.trim() || isLoading.value) return

    isLoading.value = true
    error.value = null

    try {
      // Get the active AWS account
      const awsAccountsStore = useAwsAccountsStore()
      const activeAccountAlias = awsAccountsStore.activeAccount?.alias
      
      // If no current conversation exists (new user), let backend create one
      const conversationId = currentConversation.value?.id
      
      const response = await apiService.sendChatMessage({
        message: content.trim(),
        conversation_id: conversationId,
        account_alias: activeAccountAlias
      })

      // Update current conversation if it changed or was created
      if (!currentConversation.value || currentConversation.value.id !== response.conversation_id) {
        currentConversation.value = await apiService.getConversation(response.conversation_id)
        
        // Update conversations list if this is a new conversation
        if (!conversations.value.find(c => c.id === response.conversation_id)) {
          conversations.value.unshift(currentConversation.value)
        }
        
        // Navigate to the new chat URL if we're currently at the root
        if (router.currentRoute.value.path === '/') {
          router.replace(`/chat/${response.conversation_id}`)
        }
      }

      // Only add the assistant's response, user message was already added optimistically
      const assistantMessage: ChatMessage = {
        id: response.message_id || `assistant-${Date.now()}`,
        conversation_id: response.conversation_id,
        role: 'assistant',
        content: response.response,
        timestamp: new Date(response.timestamp)
      }
      
      messages.value.push(assistantMessage)

    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to send message'
      
      // Add error message to chat locally
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        conversation_id: currentConversation.value?.id || 'temp',
        role: 'assistant',
        content: `❌ Sorry, I encountered an error: ${error.value}`,
        timestamp: new Date()
      }
      messages.value.push(errorMessage)
    } finally {
      isLoading.value = false
    }
  }

  const createNewConversation = async (title = 'New Conversation') => {
    try {
      const newConversation = await apiService.createConversation(title)
      
      conversations.value.unshift(newConversation)
      currentConversation.value = newConversation
      messages.value = []
      error.value = null
      
      // Navigate to the new chat
      router.push(`/chat/${newConversation.id}`)
      
      return newConversation
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to create conversation'
      throw err
    }
  }

  const updateConversationTitle = async (conversationId: string, title: string) => {
    try {
      const updated = await apiService.updateConversation(conversationId, title)
      const index = conversations.value.findIndex(c => c.id === conversationId)
      if (index !== -1) {
        conversations.value[index] = updated
      }
      if (currentConversation.value?.id === conversationId) {
        currentConversation.value = updated
      }
      return updated
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to update conversation'
      throw err
    }
  }

  const deleteConversation = async (conversationId: string) => {
    try {
      await apiService.deleteConversation(conversationId)
      conversations.value = conversations.value.filter(c => c.id !== conversationId)
      
      if (currentConversation.value?.id === conversationId) {
        // Load the next conversation or clear
        if (conversations.value.length > 0) {
          await loadConversation(conversations.value[0].id)
        } else {
          currentConversation.value = null
          messages.value = []
        }
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to delete conversation'
      throw err
    }
  }

  const clearChat = () => {
    messages.value = []
    error.value = null
  }

  const exportChat = () => {
    const chatText = messages.value
      .map(msg => {
        const role = msg.role === 'user' ? 'You' : 'AWS Agent'
        const timestamp = msg.timestamp.toLocaleString()
        return `[${timestamp}] ${role}: ${msg.content}`
      })
      .join('\n\n')

    const blob = new Blob([chatText], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `aws-agent-chat-${new Date().toISOString().split('T')[0]}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return {
    messages,
    currentConversation,
    conversations,
    isLoading,
    error,
    isInitialized,
    messageCount,
    lastMessage,
    initializeChat,
    startNewChat,
    loadChatById,
    loadConversation,
    sendMessage,
    createNewConversation,
    updateConversationTitle,
    deleteConversation,
    clearChat,
    exportChat
  }
}) 