import axios, { AxiosInstance } from 'axios';
import {
  ResearchRequest,
  ResearchResponse,
  ResearchReport,
  ExportRequest,
  ExportResponse,
  HealthStatus,
  ModelOption,
  UserSettings
} from '@/types';

export class ApiClientError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public details?: any
  ) {
    super(message);
    this.name = 'ApiClientError';
  }
}

class ApiClient {
  private client: AxiosInstance;

  constructor(baseURL: string = 'http://localhost:8010/api/v1') {
    this.client = axios.create({
      baseURL,
      timeout: 1800000, // 30 minutes for long research tasks
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor for auth tokens
    this.client.interceptors.request.use(
      (config: any) => {
        // Add auth token if available
        const token = localStorage.getItem('authToken');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error: any) => Promise.reject(error)
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response: any) => response,
      (error: any) => {
        const apiError = new ApiClientError(
          error.response?.data?.detail || error.message,
          error.response?.status || 500,
          error.response?.data
        );
        return Promise.reject(apiError);
      }
    );
  }

  // Health endpoints
  async getHealth(): Promise<HealthStatus> {
    const response = await this.client.get<HealthStatus>('/health/');
    return response.data;
  }

  async getDetailedHealth(): Promise<HealthStatus> {
    const response = await this.client.get<HealthStatus>('/health/detailed');
    return response.data;
  }

  // Research endpoints
  async getAvailableModels(): Promise<ModelOption[]> {
    const response = await this.client.get<ModelOption[]>('/research/models');
    return response.data;
  }

  async startResearch(request: ResearchRequest): Promise<ResearchResponse> {
    const response = await this.client.post<ResearchResponse>('/research/start', request);
    return response.data;
  }

  async getResearchStatus(taskId: string): Promise<ResearchResponse> {
    const response = await this.client.get<ResearchResponse>(`/research/status/${taskId}`);
    return response.data;
  }

  async getResearchReport(taskId: string): Promise<ResearchReport> {
    const response = await this.client.get<ResearchReport>(`/research/report/${taskId}`);
    return response.data;
  }

  // New phase-specific endpoints
  async generateQuestions(request: ResearchRequest): Promise<ResearchResponse> {
    const response = await this.client.post<ResearchResponse>('/research/questions', request);
    return response.data;
  }

  async createResearchPlan(topic: string, feedback: string, request: ResearchRequest): Promise<ResearchResponse> {
    const response = await this.client.post<ResearchResponse>('/research/plan', {
      topic,
      feedback,
      request
    });
    return response.data;
  }

  async executeResearch(topic: string, plan: string, request: ResearchRequest): Promise<ResearchResponse> {
    const response = await this.client.post<ResearchResponse>('/research/execute', {
      topic,
      plan,
      request
    });
    return response.data;
  }

  async generateFinalReport(topic: string, plan: string, findings: string, requirement: string = '', request?: ResearchRequest): Promise<ResearchResponse> {
    const response = await this.client.post<ResearchResponse>('/research/final-report', {
      topic,
      plan,
      findings,
      requirement,
      request
    });
    return response.data;
  }

  async cancelResearch(taskId: string): Promise<{ message: string }> {
    const response = await this.client.delete<{ message: string }>(`/research/cancel/${taskId}`);
    return response.data;
  }

  async listResearchTasks(): Promise<{ tasks: ResearchResponse[]; total_count: number }> {
    const response = await this.client.get<{ tasks: ResearchResponse[]; total_count: number }>('/research/list');
    return response.data;
  }

  // Export endpoints
  async createExport(request: ExportRequest): Promise<ExportResponse> {
    const response = await this.client.post<ExportResponse>('/export/', request);
    return response.data;
  }

  async getExportStatus(exportId: string): Promise<ExportResponse> {
    const response = await this.client.get<ExportResponse>(`/export/status/${exportId}`);
    return response.data;
  }

  async downloadExport(exportId: string): Promise<Blob> {
    const response = await this.client.get(`/export/download/${exportId}`, {
      responseType: 'blob',
    });
    return response.data;
  }

  async cleanupExport(exportId: string): Promise<{ message: string; export_id: string }> {
    const response = await this.client.delete<{ message: string; export_id: string }>(`/export/cleanup/${exportId}`);
    return response.data;
  }

  async listExports(): Promise<{ exports: ExportResponse[]; total_count: number }> {
    const response = await this.client.get<{ exports: ExportResponse[]; total_count: number }>('/export/list');
    return response.data;
  }

  // Settings endpoints
  async getSettings(): Promise<UserSettings> {
    const response = await this.client.get<UserSettings>('/settings/');
    return response.data;
  }

  async updateSettings(settings: UserSettings): Promise<UserSettings> {
    const response = await this.client.put<UserSettings>('/settings/', settings);
    return response.data;
  }

  // Utility methods
  async downloadFile(exportId: string, filename?: string): Promise<void> {
    try {
      const blob = await this.downloadExport(exportId);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename || `export_${exportId}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      throw new Error(`Failed to download file: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  // Stream response helper
  async streamResponse<T>(
    url: string,
    onData: (data: T) => void,
    onError: (error: Error) => void,
    onComplete: () => void
  ): Promise<void> {
    try {
      const response = await fetch(`${this.client.defaults.baseURL}${url}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
          'Accept': 'text/event-stream',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('Failed to get response reader');
      }

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          onComplete();
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              onData(data);
            } catch (parseError) {
              console.warn('Failed to parse SSE data:', line);
            }
          }
        }
      }
    } catch (error) {
      onError(error instanceof Error ? error : new Error('Unknown streaming error'));
    }
  }
}

// Create and export singleton instance
export const apiClient = new ApiClient();

// Export the class for testing
export { ApiClient };
