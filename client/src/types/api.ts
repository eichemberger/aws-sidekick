export interface ChatMessage {
  id: string
  conversation_id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

export interface ChatRequest {
  message: string
  conversation_id?: string
  account_alias?: string
}

export interface ChatResponse {
  response: string
  timestamp: string
  conversation_id: string
  message_id: string
}

export interface Conversation {
  id: string
  title: string
  account_id: string
  created_at: Date
  updated_at: Date
}

export interface TaskRequest {
  description: string
}

export interface TaskResponse {
  task_id: string
  description: string
  account_alias: string
  status: string
  result?: string
  error_message?: string
  created_at: string
  completed_at?: string
  duration?: number
}

export interface AWSAccountInfo {
  account_id: string
  region: string
  user_arn: string
}

export interface AWSCredentialsRequest {
  access_key_id?: string
  secret_access_key?: string
  session_token?: string
  region: string
  profile?: string
}

export interface AWSCredentialsResponse {
  region: string
  profile?: string
  has_access_key: boolean
  has_session_token: boolean
  is_valid: boolean
}

export interface AWSCredentialsValidation {
  valid: boolean
  error?: string
  account_id?: string
  region?: string
  user_arn?: string
}

// Multi-Account AWS Management Types
export interface AWSAccount {
  alias: string
  account_id?: string
  description?: string
  is_default: boolean
  region: string
  uses_profile: boolean
  created_at: string
  updated_at: string
}

export interface AWSAccountRequest {
  alias: string
  credentials: AWSCredentialsRequest
  description?: string
  set_as_default?: boolean
}

export interface AWSAccountUpdateRequest {
  credentials: AWSCredentialsRequest
}

export interface SetActiveAccountRequest {
  account_alias: string
}

export interface HealthCheck {
  message: string
  status: string
  timestamp: string
}

// Removed TaskType enum - simplified task system

export enum TaskStatus {
  PENDING = 'pending',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  FAILED = 'failed'
} 