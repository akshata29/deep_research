import { useMutation, useQuery, UseQueryOptions, UseMutationOptions } from '@tanstack/react-query';
import { apiClient } from '@/services/api';
import { 
  OrchestrationRequest,
  OrchestrationResponse,
  OrchestrationSession,
  OrchestrationHealth,
  OrchestrationProgress
} from '@/types';

// API Functions
const orchestrationApi = {
  // Start orchestration research
  startResearch: async (request: OrchestrationRequest): Promise<OrchestrationResponse> => {
    return await apiClient.startOrchestration(request);
  },

  // Get session summary
  getSessionSummary: async (sessionId: string): Promise<OrchestrationSession> => {
    return await apiClient.getOrchestrationSession(sessionId);
  },

  // Cleanup session
  cleanupSession: async (sessionId: string): Promise<{ success: boolean; message: string }> => {
    return await apiClient.deleteOrchestrationSession(sessionId);
  },

  // List active sessions
  listActiveSessions: async (): Promise<OrchestrationSession[]> => {
    return await apiClient.listOrchestrationSessions();
  },

  // Get orchestration health
  getHealth: async (): Promise<OrchestrationHealth> => {
    return await apiClient.getOrchestrationHealth();
  },

  // Get session progress
  getSessionProgress: async (sessionId: string): Promise<OrchestrationProgress> => {
    const response = await fetch(`/api/v1/orchestration/sessions/${sessionId}/progress`);
    if (!response.ok) {
      throw new Error('Failed to fetch session progress');
    }
    return await response.json();
  },
};

// Hooks
export const useOrchestrationResearch = (
  options?: UseMutationOptions<OrchestrationResponse, Error, OrchestrationRequest>
) => {
  return useMutation({
    mutationFn: orchestrationApi.startResearch,
    ...options,
  });
};

export const useSessionSummary = (
  sessionId: string | undefined,
  options?: Omit<UseQueryOptions<OrchestrationSession, Error>, 'queryKey' | 'queryFn'>
) => {
  return useQuery({
    queryKey: ['orchestration', 'session', sessionId],
    queryFn: () => orchestrationApi.getSessionSummary(sessionId!),
    enabled: !!sessionId,
    ...options,
  });
};

export const useCleanupSession = (
  options?: UseMutationOptions<{ success: boolean; message: string }, Error, string>
) => {
  return useMutation({
    mutationFn: orchestrationApi.cleanupSession,
    ...options,
  });
};

export const useActiveSessions = (
  options?: UseQueryOptions<OrchestrationSession[], Error>
) => {
  return useQuery({
    queryKey: ['orchestration', 'sessions'],
    queryFn: orchestrationApi.listActiveSessions,
    refetchInterval: 30000, // Refetch every 30 seconds
    ...options,
  });
};

export const useOrchestrationHealth = (
  options?: UseQueryOptions<OrchestrationHealth, Error>
) => {
  return useQuery({
    queryKey: ['orchestration', 'health'],
    queryFn: orchestrationApi.getHealth,
    refetchInterval: 60000, // Refetch every minute
    ...options,
  });
};

export const useSessionProgress = (
  sessionId: string | undefined,
  options?: Omit<UseQueryOptions<OrchestrationProgress, Error>, 'queryKey' | 'queryFn'>
) => {
  return useQuery({
    queryKey: ['orchestration', 'progress', sessionId],
    queryFn: () => orchestrationApi.getSessionProgress(sessionId!),
    enabled: !!sessionId,
    ...options,
  });
};
