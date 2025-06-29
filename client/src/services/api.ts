import axios, { type AxiosInstance, type AxiosError } from 'axios'
import type {
  ChatRequest,
  ChatResponse,
  ChatMessage,
  Conversation,
  TaskRequest,
  TaskResponse,
  AWSAccountInfo,
  AWSCredentialsRequest,
  AWSCredentialsResponse,
  AWSCredentialsValidation,
  HealthCheck
} from '@/types/api'

class ApiService {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: import.meta.env.VITE_API_URL || '/api',
      timeout: 45000, // Reduced from 60s to 45s for faster failures
      headers: {
        'Content-Type': 'application/json'
      }
    })

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        console.log(`🚀 ${config.method?.toUpperCase()} ${config.url}`)
        return config
      },
      (error) => {
        console.error('❌ Request error:', error)
        return Promise.reject(error)
      }
    )

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => {
        console.log(`✅ ${response.status} ${response.config.url}`)
        return response
      },
      (error: AxiosError) => {
        console.error(`❌ ${error.response?.status} ${error.config?.url}:`, error.message)
        return Promise.reject(this.handleError(error))
      }
    )
  }

  private handleError(error: AxiosError): Error {
    if (error.response) {
      // Server responded with error status
      const message = (error.response.data as any)?.detail || error.response.statusText
      return new Error(`Server Error (${error.response.status}): ${message}`)
    } else if (error.request) {
      // Request made but no response received
      return new Error('Network Error: Unable to connect to the server')
    } else {
      // Something else happened
      return new Error(`Request Error: ${error.message}`)
    }
  }

  // Health check
  async healthCheck(): Promise<HealthCheck> {
    const response = await this.client.get<HealthCheck>('')
    return response.data
  }

  // Chat endpoints
  async sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
    const response = await this.client.post<ChatResponse>('/chat', request, {
      timeout: 35000 // 35 seconds for chat - shorter than other operations
    })
    return response.data
  }

  // Conversation endpoints
  async getConversations(limit = 50, offset = 0): Promise<Conversation[]> {
    const response = await this.client.get<Conversation[]>('/conversations', {
      params: { limit, offset }
    })
    return response.data.map(conv => ({
      ...conv,
      created_at: new Date(conv.created_at),
      updated_at: new Date(conv.updated_at)
    }))
  }

  async getConversation(conversationId: string): Promise<Conversation> {
    const response = await this.client.get<Conversation>(`/conversations/${conversationId}`)
    return {
      ...response.data,
      created_at: new Date(response.data.created_at),
      updated_at: new Date(response.data.updated_at)
    }
  }

  async getConversationMessages(conversationId: string, limit = 100, offset = 0): Promise<ChatMessage[]> {
    const response = await this.client.get<ChatMessage[]>(`/conversations/${conversationId}/messages`, {
      params: { limit, offset }
    })
    return response.data.map(msg => ({
      ...msg,
      timestamp: new Date(msg.timestamp)
    }))
  }

  async createConversation(title = 'New Conversation'): Promise<Conversation> {
    const response = await this.client.post<Conversation>(`/conversations?title=${encodeURIComponent(title)}`)
    return {
      ...response.data,
      created_at: new Date(response.data.created_at),
      updated_at: new Date(response.data.updated_at)
    }
  }

  async updateConversation(conversationId: string, title: string): Promise<Conversation> {
    const response = await this.client.put<Conversation>(`/conversations/${conversationId}`, null, {
      params: { title }
    })
    return {
      ...response.data,
      created_at: new Date(response.data.created_at),
      updated_at: new Date(response.data.updated_at)
    }
  }

  async deleteConversation(conversationId: string): Promise<void> {
    await this.client.delete(`/conversations/${conversationId}`)
  }

  // Task endpoints
  async executeTask(request: TaskRequest): Promise<TaskResponse> {
    const response = await this.client.post<TaskResponse>('/tasks', request)
    return response.data
  }

  async getTasks(limit = 10, offset = 0): Promise<TaskResponse[]> {
    const response = await this.client.get<TaskResponse[]>('/tasks', {
      params: { limit, offset }
    })
    return response.data
  }

  async getTask(taskId: string): Promise<TaskResponse> {
    const response = await this.client.get<TaskResponse>(`/tasks/${taskId}`)
    return response.data
  }

  // AWS endpoints
  async getAwsAccountInfo(): Promise<AWSAccountInfo> {
    const response = await this.client.get<AWSAccountInfo>('/aws/account-info')
    return response.data
  }

  async analyzeAws(): Promise<TaskResponse> {
    const response = await this.client.post<TaskResponse>('/aws/analyze')
    return response.data
  }

  async performSecurityAudit(): Promise<TaskResponse> {
    const response = await this.client.post<TaskResponse>('/aws/security-audit')
    return response.data
  }

  async optimizeCosts(): Promise<TaskResponse> {
    const response = await this.client.post<TaskResponse>('/aws/cost-optimization')
    return response.data
  }

  // AWS Credentials endpoints
  async setAwsCredentials(request: AWSCredentialsRequest): Promise<AWSCredentialsResponse> {
    const response = await this.client.post<AWSCredentialsResponse>('/aws/credentials', request)
    return response.data
  }

  async getAwsCredentials(): Promise<AWSCredentialsResponse> {
    const response = await this.client.get<AWSCredentialsResponse>('/aws/credentials')
    return response.data
  }

  async validateAwsCredentials(request: AWSCredentialsRequest): Promise<AWSCredentialsValidation> {
    const response = await this.client.post<AWSCredentialsValidation>('/aws/credentials/validate', request)
    return response.data
  }

  async clearAwsCredentials(): Promise<void> {
    await this.client.delete('/aws/credentials')
  }
}

export const apiService = new ApiService()
export default apiService 