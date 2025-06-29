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
}

export interface ChatResponse {
  response: string
  task_type: string
  timestamp: string
  conversation_id: string
  message_id: string
}

export interface Conversation {
  id: string
  title: string
  created_at: Date
  updated_at: Date
}

export interface TaskRequest {
  description: string
  task_type?: string
}

export interface TaskResponse {
  task_id: string
  description: string
  task_type: string
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

export interface HealthCheck {
  message: string
  status: string
  timestamp: string
}

export enum TaskType {
  ANALYSIS = 'analysis',
  OPTIMIZATION = 'optimization',
  SECURITY_AUDIT = 'security_audit',
  TROUBLESHOOTING = 'troubleshooting',
  DOCUMENTATION = 'documentation',
  DIAGRAM_GENERATION = 'diagram_generation'
}

export enum TaskStatus {
  PENDING = 'pending',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  FAILED = 'failed'
} 