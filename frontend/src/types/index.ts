export interface User {
  id: string;
  username: string;
  email: string;
  full_name?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
}

export type ChatMode = 'ask' | 'rag' | 'agent';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

export interface ChatRequest {
  message: string;
  mode: ChatMode;
  conversation_history: ChatMessage[];
  provider?: string;
  model?: string;
  stream?: boolean;
}

export interface Source {
  id: string;
  title: string;
  content: string;
  score: number;
  metadata: Record<string, any>;
  url?: string;
}

export interface ChatResponse {
  response: string;
  mode: ChatMode;
  sources?: Source[];
  tool_calls?: any[];
  metadata?: Record<string, any>;
}

export interface MCPServer {
  id: string;
  name: string;
  description?: string;
  base_url: string;
  api_key?: string;
  is_active: boolean;
  tools: string[];
}

export interface MCPServerCreate {
  name: string;
  description?: string;
  base_url: string;
  api_key?: string;
}

export interface Settings {
  provider: 'openai' | 'azure';
  apiKey: string;
  model: string;
  temperature: number;
  maxTokens: number;
  elasticsearchUrl: string;
  mcpServers: MCPServer[];
}

export interface StreamEvent {
  content?: string;
  sources?: Source[];
  action?: any;
  tool_calls?: any[];
  error?: string;
  done?: boolean;
}
