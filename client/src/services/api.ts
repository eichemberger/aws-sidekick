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
  AWSAccount,
  AWSAccountRequest,
  AWSAccountUpdateRequest,
  SetActiveAccountRequest,
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

  // Multi-Account AWS Management endpoints
  async registerAwsAccount(request: AWSAccountRequest): Promise<AWSAccount> {
    const response = await this.client.post<AWSAccount>('/aws/accounts', request)
    return response.data
  }

  async getAwsAccounts(): Promise<AWSAccount[]> {
    const response = await this.client.get<AWSAccount[]>('/aws/accounts')
    return response.data
  }

  async getAwsAccount(alias: string): Promise<AWSAccount> {
    const response = await this.client.get<AWSAccount>(`/aws/accounts/${alias}`)
    return response.data
  }

  async updateAwsAccountCredentials(alias: string, request: AWSAccountUpdateRequest): Promise<AWSAccount> {
    const response = await this.client.put<AWSAccount>(`/aws/accounts/${alias}/credentials`, request)
    return response.data
  }

  async deleteAwsAccount(alias: string): Promise<void> {
    await this.client.delete(`/aws/accounts/${alias}`)
  }

  async getDefaultAwsAccount(): Promise<AWSAccount | null> {
    try {
      const response = await this.client.get<AWSAccount>('/aws/accounts/default')
      return response.data
    } catch (error: any) {
      if (error.response?.status === 404) {
        return null
      }
      throw error
    }
  }

  async setDefaultAwsAccount(alias: string): Promise<void> {
    await this.client.post(`/aws/accounts/${alias}/default`)
  }

  async setActiveAwsAccount(request: SetActiveAccountRequest): Promise<void> {
    await this.client.post('/aws/active-account', request)
  }

  async clearActiveAwsAccount(): Promise<void> {
    await this.client.delete('/aws/active-account')
  }

  async getActiveAccountAlias(): Promise<string | null> {
    try {
      const response = await this.client.get<{ account_alias: string | null }>('/aws/active-account')
      return response.data.account_alias
    } catch (error: any) {
      if (error.response?.status === 404) {
        return null
      }
      throw error
    }
  }

  async validateAwsAccountCredentials(alias: string): Promise<boolean> {
    const response = await this.client.post<{ valid: boolean }>(`/aws/accounts/${alias}/validate`)
    return response.data.valid
  }
}

export const apiService = new ApiService()
export default apiService 