import axios, { AxiosInstance } from 'axios';
import {
  ResearchRequest,
  ResearchResponse,
  ResearchReport,
  ExportRequest,
  ExportResponse,
  ExportListResponse,
  StorageStats,
  HealthStatus,
  ModelOption,
  UserSettings,
  ResearchPlanRequest,
  ResearchSession,
  SessionListResponse,
  SessionCreateRequest,
  SessionUpdateRequest,
  SessionRestoreRequest,
  SessionStorageStats,
  OrchestrationRequest,
  OrchestrationResponse,
  OrchestrationSession,
  OrchestrationHealth,
  OrchestrationProgress,
  OrchestrationSessionDetails
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

  async createResearchPlan(topic: string, questions: string[], feedback: string, request: ResearchRequest): Promise<ResearchResponse> {
    const planRequest: ResearchPlanRequest = {
      topic,
      questions,
      feedback,
      request
    };
    const response = await this.client.post<ResearchResponse>('/research/plan', planRequest);
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

  async executeResearchWithTavily(topic: string, plan: string, request: ResearchRequest): Promise<ResearchResponse> {
    const response = await this.client.post<ResearchResponse>('/research/execute-tavily', {
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

  async listExports(params?: {
    limit?: number;
    offset?: number;
    format_filter?: string;
    status_filter?: string;
  }): Promise<ExportListResponse> {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    if (params?.offset) searchParams.append('offset', params.offset.toString());
    if (params?.format_filter) searchParams.append('format_filter', params.format_filter);
    if (params?.status_filter) searchParams.append('status_filter', params.status_filter);
    
    const url = `/export/list${searchParams.toString() ? `?${searchParams}` : ''}`;
    const response = await this.client.get<ExportListResponse>(url);
    return response.data;
  }

  async getStorageStats(): Promise<{ success: boolean; data: StorageStats; timestamp: string }> {
    const response = await this.client.get<{ success: boolean; data: StorageStats; timestamp: string }>('/export/storage-stats');
    return response.data;
  }

  async cleanupOldExports(daysOld: number = 30): Promise<{ success: boolean; message: string; cleaned_export_ids: string[]; days_old: number }> {
    const response = await this.client.post<{ success: boolean; message: string; cleaned_export_ids: string[]; days_old: number }>('/export/cleanup-old', { days_old: daysOld });
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

  // Session endpoints
  async createSession(request: SessionCreateRequest): Promise<ResearchSession> {
    const response = await this.client.post<ResearchSession>('/sessions/', request);
    return response.data;
  }

  async listSessions(params?: {
    page?: number;
    page_size?: number;
    status_filter?: string;
    tag_filter?: string;
    search_query?: string;
  }): Promise<SessionListResponse> {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.append('page', params.page.toString());
    if (params?.page_size) searchParams.append('page_size', params.page_size.toString());
    if (params?.status_filter) searchParams.append('status_filter', params.status_filter);
    if (params?.tag_filter) searchParams.append('tag_filter', params.tag_filter);
    if (params?.search_query) searchParams.append('search_query', params.search_query);
    
    const url = `/sessions/list${searchParams.toString() ? `?${searchParams}` : ''}`;
    const response = await this.client.get<SessionListResponse>(url);
    return response.data;
  }

  async getSession(sessionId: string): Promise<ResearchSession> {
    const response = await this.client.get<ResearchSession>(`/sessions/${sessionId}`);
    return response.data;
  }

  async updateSession(sessionId: string, request: SessionUpdateRequest): Promise<ResearchSession> {
    const response = await this.client.put<ResearchSession>(`/sessions/${sessionId}`, request);
    return response.data;
  }

  async deleteSession(sessionId: string): Promise<{ success: boolean; message: string; session_id: string }> {
    const response = await this.client.delete<{ success: boolean; message: string; session_id: string }>(`/sessions/${sessionId}`);
    return response.data;
  }

  async saveSessionState(sessionId: string, stateData: any): Promise<{ success: boolean; message: string; session_id: string; phase: string }> {
    const response = await this.client.post<{ success: boolean; message: string; session_id: string; phase: string }>(`/sessions/${sessionId}/save-state`, stateData);
    return response.data;
  }

  async restoreSession(sessionId: string, request: SessionRestoreRequest): Promise<{ success: boolean; message: string; session_id: string; restoration_data: any }> {
    const response = await this.client.post<{ success: boolean; message: string; session_id: string; restoration_data: any }>(`/sessions/${sessionId}/restore`, request);
    return response.data;
  }

  async getSessionStorageStats(): Promise<{ success: boolean; data: SessionStorageStats; timestamp: string }> {
    const response = await this.client.get<{ success: boolean; data: SessionStorageStats; timestamp: string }>('/sessions/storage/stats');
    return response.data;
  }

  async cleanupOldSessions(daysOld: number = 90): Promise<{ success: boolean; archived_sessions: number; days_old: number; message: string }> {
    const response = await this.client.post<{ success: boolean; archived_sessions: number; days_old: number; message: string }>('/sessions/cleanup', { days_old: daysOld });
    return response.data;
  }

  // === Orchestration Methods ===
  async startOrchestration(request: OrchestrationRequest): Promise<OrchestrationResponse> {
    const response = await this.client.post<OrchestrationResponse>('/orchestration/research', request);
    return response.data;
  }

  async getOrchestrationSession(sessionId: string): Promise<OrchestrationSession> {
    const response = await this.client.get<OrchestrationSession>(`/orchestration/sessions/${sessionId}/summary`);
    return response.data;
  }

  async listOrchestrationSessions(): Promise<OrchestrationSession[]> {
    const response = await this.client.get<OrchestrationSession[]>('/orchestration/sessions');
    return response.data;
  }

  async deleteOrchestrationSession(sessionId: string): Promise<{ success: boolean; message: string }> {
    const response = await this.client.delete<{ success: boolean; message: string }>(`/orchestration/sessions/${sessionId}`);
    return response.data;
  }

  async getOrchestrationHealth(): Promise<OrchestrationHealth> {
    const response = await this.client.get<OrchestrationHealth>('/orchestration/health');
    return response.data;
  }

  // New orchestration progress and session management
  async getOrchestrationProgress(sessionId: string): Promise<OrchestrationProgress> {
    const response = await this.client.get<OrchestrationProgress>(`/orchestration/sessions/${sessionId}/progress`);
    return response.data;
  }

  async getOrchestrationSessionDetails(sessionId: string): Promise<{ success: boolean; session_details: OrchestrationSessionDetails }> {
    const response = await this.client.get<{ success: boolean; session_details: OrchestrationSessionDetails }>(`/sessions/orchestration/${sessionId}/details`);
    return response.data;
  }

  async restoreOrchestrationSession(sessionId: string): Promise<{ success: boolean; restoration_data: any }> {
    const response = await this.client.post<{ success: boolean; restoration_data: any }>(`/sessions/orchestration/${sessionId}/restore`);
    return response.data;
  }
}

// Create and export singleton instance
export const apiClient = new ApiClient();

// Export the class for testing
export { ApiClient };
