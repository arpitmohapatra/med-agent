import axios, { AxiosInstance } from 'axios';
import { 
  User, 
  AuthToken, 
  ChatRequest, 
  ChatResponse, 
  MCPServer, 
  MCPServerCreate,
  Source
} from '../types';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token
    this.api.interceptors.request.use((config) => {
      const token = localStorage.getItem('auth_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Response interceptor for error handling
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('auth_token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Auth endpoints
  async register(userData: {
    username: string;
    email: string;
    password: string;
    full_name?: string;
  }): Promise<{ message: string; user: Partial<User> }> {
    const response = await this.api.post('/auth/register', userData);
    return response.data;
  }

  async login(credentials: {
    username: string;
    password: string;
  }): Promise<AuthToken> {
    const response = await this.api.post('/auth/login', credentials);
    const token = response.data;
    localStorage.setItem('auth_token', token.access_token);
    return token;
  }

  async logout(): Promise<void> {
    await this.api.post('/auth/logout');
    localStorage.removeItem('auth_token');
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.api.get('/auth/me');
    return response.data;
  }

  // Chat endpoints
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    const response = await this.api.post('/api/chat', request);
    return response.data;
  }

  // Streaming chat
  async sendStreamingMessage(
    request: ChatRequest,
    onChunk: (chunk: any) => void,
    onError?: (error: any) => void
  ): Promise<void> {
    console.log('🚀 Starting streaming request:', request.message);
    try {
      const response = await fetch(`${this.api.defaults.baseURL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
        },
        body: JSON.stringify({ ...request, stream: true }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body');
      }

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        
        // Process complete lines
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              onChunk(data);
            } catch (e) {
              console.warn('Failed to parse SSE data:', line);
            }
          }
        }
      }
    } catch (error) {
      if (onError) {
        onError(error);
      } else {
        throw error;
      }
    }
  }

  // RAG endpoints
  async searchDocuments(query: string, topK: number = 3, searchType: string = 'semantic'): Promise<{
    documents: Source[];
    query: string;
    total_hits: number;
  }> {
    const response = await this.api.get('/api/rag/search', {
      params: { query, top_k: topK, search_type: searchType }
    });
    return response.data;
  }

  async indexDocuments(documents: any[] | File): Promise<{
    message: string;
    total_documents: number;
    total_chunks: number;
  }> {
    if (documents instanceof File) {
      const formData = new FormData();
      formData.append('file', documents);
      
      const response = await this.api.post('/api/rag/index', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } else {
      const response = await this.api.post('/api/rag/index', { documents });
      return response.data;
    }
  }

  async getIndexStats(): Promise<any> {
    const response = await this.api.get('/api/rag/stats');
    return response.data;
  }

  async deleteIndex(): Promise<{ message: string }> {
    const response = await this.api.delete('/api/rag/index');
    return response.data;
  }

  // MCP endpoints
  async registerMCPServer(serverData: MCPServerCreate): Promise<MCPServer> {
    const response = await this.api.post('/api/mcp/register', serverData);
    return response.data;
  }

  async getMCPServers(): Promise<MCPServer[]> {
    const response = await this.api.get('/api/mcp/servers');
    return response.data;
  }

  async getActiveMCPServers(): Promise<MCPServer[]> {
    const response = await this.api.get('/api/mcp/servers/active');
    return response.data;
  }

  async getMCPTools(): Promise<{ tools: any[] }> {
    const response = await this.api.get('/api/mcp/tools');
    return response.data;
  }

  async discoverMCPTools(serverId: string): Promise<{
    server_id: string;
    tools: string[];
    count: number;
  }> {
    const response = await this.api.post(`/api/mcp/tools/discover/${serverId}`);
    return response.data;
  }

  async removeMCPServer(serverId: string): Promise<{ message: string }> {
    const response = await this.api.delete(`/api/mcp/servers/${serverId}`);
    return response.data;
  }

  async activateMCPServer(serverId: string): Promise<{ message: string }> {
    const response = await this.api.patch(`/api/mcp/servers/${serverId}/activate`);
    return response.data;
  }

  async deactivateMCPServer(serverId: string): Promise<{ message: string }> {
    const response = await this.api.patch(`/api/mcp/servers/${serverId}/deactivate`);
    return response.data;
  }

  // Health check
  async healthCheck(): Promise<{
    status: string;
    app: string;
    version: string;
  }> {
    const response = await this.api.get('/health');
    return response.data;
  }
}

export const apiService = new ApiService();
