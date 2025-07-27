import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useCallback, useState } from 'react';
import { apiClient } from '@/services/api';
import {
  ResearchRequest,
  ResearchResponse,
  ExportRequest,
  UserSettings,
} from '@/types';

// Health check hook
export const useHealth = () => {
  return useQuery({
    queryKey: ['health'],
    queryFn: () => apiClient.getHealth(),
    refetchInterval: 30000, // Check every 30 seconds
    retry: 3,
  });
};

// Models hook
export const useModels = () => {
  return useQuery({
    queryKey: ['models'],
    queryFn: () => apiClient.getAvailableModels(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

// Research hooks
export const useStartResearch = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (request: ResearchRequest) => apiClient.startResearch(request),
    onSuccess: (data) => {
      // Invalidate and refetch research tasks
      queryClient.invalidateQueries({ queryKey: ['research-tasks'] });
      // Cache the new task
      queryClient.setQueryData(['research-status', data.task_id], data);
    },
  });
};

export const useResearchStatus = (taskId: string, enabled: boolean = true) => {
  return useQuery({
    queryKey: ['research-status', taskId],
    queryFn: () => apiClient.getResearchStatus(taskId),
    enabled: enabled && !!taskId,
    refetchInterval: (query) => {
      const data = query.state.data as any;
      const status = data?.status;
      
      console.log('Polling status:', status, 'for task:', taskId);
      
      // Stop polling when completed or failed
      if (status === 'completed' || status === 'failed') {
        console.log('STOPPING POLLING - Status:', status);
        return false;
      }
      
      // Continue polling every 1 second
      return 1000;
    },
    staleTime: 0,
    gcTime: 0,
  });
};

export const useResearchReport = (taskId: string, enabled: boolean = true) => {
  return useQuery({
    queryKey: ['research-report', taskId],
    queryFn: () => apiClient.getResearchReport(taskId),
    enabled: enabled && !!taskId,
    retry: (failureCount, error: any) => {
      // Don't retry if report doesn't exist yet
      if (error?.statusCode === 404) {
        return false;
      }
      return failureCount < 3;
    },
  });
};

export const useCancelResearch = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (taskId: string) => apiClient.cancelResearch(taskId),
    onSuccess: (_, taskId) => {
      // Update cached status
      queryClient.invalidateQueries({ queryKey: ['research-status', taskId] });
      queryClient.invalidateQueries({ queryKey: ['research-tasks'] });
    },
  });
};

// New phase-specific hooks
export const useGenerateQuestions = () => {
  return useMutation({
    mutationFn: (request: ResearchRequest) => 
      apiClient.generateQuestions(request),
  });
};

export const useCreateResearchPlan = () => {
  return useMutation({
    mutationFn: ({ topic, feedback, request }: { topic: string; feedback: string; request: ResearchRequest }) =>
      apiClient.createResearchPlan(topic, feedback, request),
  });
};

export const useExecuteResearch = () => {
  return useMutation({
    mutationFn: ({ topic, plan, request }: { topic: string; plan: string; request: ResearchRequest }) =>
      apiClient.executeResearch(topic, plan, request),
  });
};

export const useGenerateFinalReport = () => {
  return useMutation({
    mutationFn: ({ topic, plan, findings, requirement, request }: { 
      topic: string; 
      plan: string; 
      findings: string; 
      requirement?: string; 
      request?: ResearchRequest 
    }) =>
      apiClient.generateFinalReport(topic, plan, findings, requirement, request),
  });
};

export const useResearchTasks = () => {
  return useQuery({
    queryKey: ['research-tasks'],
    queryFn: () => apiClient.listResearchTasks(),
    refetchInterval: 10000, // Refresh every 10 seconds
  });
};

// Export hooks
export const useCreateExport = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (request: ExportRequest) => apiClient.createExport(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['exports'] });
    },
  });
};

export const useExportStatus = (exportId: string, enabled: boolean = true) => {
  return useQuery({
    queryKey: ['export-status', exportId],
    queryFn: () => apiClient.getExportStatus(exportId),
    enabled: enabled && !!exportId,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data?.status === 'completed' || data?.status === 'failed') {
        return false;
      }
      return 3000; // Poll every 3 seconds for active exports
    },
  });
};

export const useDownloadExport = () => {
  return useMutation({
    mutationFn: ({ exportId, filename }: { exportId: string; filename?: string }) =>
      apiClient.downloadFile(exportId, filename),
    onError: (error) => {
      console.error('Download failed:', error);
    },
  });
};

export const useCleanupExport = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (exportId: string) => apiClient.cleanupExport(exportId),
    onSuccess: (_, exportId) => {
      queryClient.invalidateQueries({ queryKey: ['export-status', exportId] });
      queryClient.invalidateQueries({ queryKey: ['exports'] });
    },
  });
};

export const useDeleteExport = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (exportId: string) => apiClient.cleanupExport(exportId),
    onSuccess: (_, exportId) => {
      queryClient.invalidateQueries({ queryKey: ['export-status', exportId] });
      queryClient.invalidateQueries({ queryKey: ['exports'] });
    },
  });
};

export const useExports = () => {
  return useQuery({
    queryKey: ['exports'],
    queryFn: () => apiClient.listExports(),
    refetchInterval: 15000, // Refresh every 15 seconds
  });
};

// WebSocket hook for real-time updates
// Polling-based research hook (replaces WebSocket)
export const useResearchWithUpdates = (taskId: string) => {
  const statusQuery = useResearchStatus(taskId, !!taskId);
  
  // Backend returns: { task_id, status, message, progress?, report?, websocket_url? }
  const apiStatus = statusQuery.data?.status;
  const isCompleted = apiStatus === 'completed';
  
  const reportQuery = useResearchReport(taskId, isCompleted);

  console.log('useResearchWithUpdates:', {
    taskId,
    status: apiStatus,
    isCompleted,
    hasReport: !!reportQuery.data,
    progress: statusQuery.data?.progress,
    fullResponse: statusQuery.data
  });

  return {
    status: apiStatus,
    progress: statusQuery.data?.progress?.progress_percentage ?? 0,
    currentStep: statusQuery.data?.progress?.current_step ?? statusQuery.data?.message ?? 'Initializing...',
    report: reportQuery.data,
    isLoading: statusQuery.isLoading || reportQuery.isLoading,
    error: statusQuery.error || reportQuery.error,
    refetch: statusQuery.refetch,
  };
};

// Optimistic updates helper
export const useOptimisticResearch = () => {
  const queryClient = useQueryClient();

  const updateTaskOptimistically = useCallback((
    taskId: string,
    updates: Partial<ResearchResponse>
  ) => {
    queryClient.setQueryData(
      ['research-status', taskId],
      (old: ResearchResponse | undefined) => ({
        ...old,
        ...updates,
      } as ResearchResponse)
    );
  }, [queryClient]);

  return { updateTaskOptimistically };
};

// Settings hooks
export const useSettings = () => {
  return useQuery({
    queryKey: ['settings'],
    queryFn: () => apiClient.getSettings(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useUpdateSettings = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (settings: UserSettings) => apiClient.updateSettings(settings),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] });
    },
  });
};

// LocalStorage-based settings hooks for persistence
const SETTINGS_STORAGE_KEY = 'deep-research-settings';

const defaultSettings: UserSettings = {
  theme: 'system',
  notifications: {
    email: false,
    push: false,
    taskCompletion: true,
    errors: true,
  },
  research: {
    defaultDepth: 'standard',
    maxSources: 10,
    autoExport: false,
    preferredFormat: 'markdown',
    defaultThinkingModel: 'chato1',
    defaultTaskModel: 'chat4omini',
  },
  privacy: {
    dataRetention: 30,
    shareAnalytics: false,
    publicReports: false,
  },
  ai: {
    model: 'chato1',
    temperature: 0.7,
    maxTokens: 4000,
  },
  defaultThinkingModel: 'chato1',
  defaultTaskModel: 'chat4omini',
  defaultResearchDepth: 'standard',
  executionMode: 'agents',
  defaultLanguage: 'English',
  enableWebSearchByDefault: true,
  enableNotifications: true,
  autoExportFormat: 'markdown',
  maxConcurrentTasks: 3,
  defaultInstructions: '',
  themePreference: 'system',
  enableTelemetry: false,
};

export const useLocalSettings = () => {
  const [settings, setSettings] = useState<UserSettings>(() => {
    try {
      const stored = localStorage.getItem(SETTINGS_STORAGE_KEY);
      return stored ? { ...defaultSettings, ...JSON.parse(stored) } : defaultSettings;
    } catch (error) {
      console.warn('Failed to load settings from localStorage:', error);
      return defaultSettings;
    }
  });

  const updateSettings = useCallback((newSettings: Partial<UserSettings>) => {
    setSettings(prev => {
      const updated = { ...prev, ...newSettings };
      try {
        localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(updated));
      } catch (error) {
        console.warn('Failed to save settings to localStorage:', error);
      }
      return updated;
    });
  }, []);

  const resetSettings = useCallback(() => {
    setSettings(defaultSettings);
    try {
      localStorage.removeItem(SETTINGS_STORAGE_KEY);
    } catch (error) {
      console.warn('Failed to clear settings from localStorage:', error);
    }
  }, []);

  return {
    data: settings,
    isLoading: false,
    updateSettings,
    resetSettings,
    refetch: () => Promise.resolve({ data: settings }),
  };
};

export const useSystemHealth = () => {
  return useQuery({
    queryKey: ['system-health'],
    queryFn: () => apiClient.getHealth(),
    refetchInterval: 30000, // Check every 30 seconds
    select: (data) => ({
      ...data,
      // Mock additional system health metrics
      cpu_usage: Math.random() * 100,
      memory_usage: Math.random() * 100,
      disk_usage: Math.random() * 100,
      active_tasks: Math.floor(Math.random() * 10),
      queue_size: Math.floor(Math.random() * 5),
    }),
  });
};
