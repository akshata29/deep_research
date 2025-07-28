// API Types matching the backend schemas

export type ResearchDepth = 'quick' | 'standard' | 'deep';
export type ExportFormat = 'markdown' | 'pdf' | 'docx' | 'pptx' | 'html' | 'json' | 'custom-pptx';
export type TaskStatus = 'pending' | 'thinking' | 'searching' | 'generating' | 'formatting' | 'completed' | 'failed';
export type ExecutionMode = 'agents' | 'direct' | 'auto';

export interface ModelConfig {
  thinking: string;
  task: string;
}

export interface ResearchRequest {
  prompt: string;
  models_config: ModelConfig;
  execution_mode?: ExecutionMode;
  enable_web_search?: boolean;
  research_depth?: ResearchDepth;
  language?: string;
  max_results?: number;
  custom_instructions?: string;
}

// Alias for backwards compatibility
export type ResearchConfig = ResearchRequest;

export interface ResearchProgress {
  task_id: string;
  status: TaskStatus;
  progress_percentage: number;
  current_step: string;
  estimated_completion?: string;
  tokens_used?: number;
  cost_estimate?: number;
  search_queries_made?: number;
  sources_found?: number;
}

export interface ResearchResponse {
  task_id: string;
  status: TaskStatus;
  message?: string;
  progress?: ResearchProgress;  // This is optional in backend
  report?: ResearchReport;
  websocket_url?: string;
  created_at?: string;
  models_config?: ModelConfig;
}

export interface SearchResult {
  title: string;
  url: string;
  snippet: string;
  relevance_score: number;
  domain: string;
  publish_date?: string;
  author?: string;
}

export interface ResearchSection {
  title: string;
  content: string;
  sources: SearchResult[];
  confidence_score: number;
  word_count: number;
}

export interface ResearchReport {
  task_id: string;
  title: string;
  executive_summary: string;
  sections: ResearchSection[];
  conclusions: string;
  sources: SearchResult[];
  metadata: Record<string, any>;
  word_count: number;
  reading_time_minutes: number;
}

export interface ExportRequest {
  task_id: string;
  format: ExportFormat;
  include_sources?: boolean;
  include_metadata?: boolean;
  template_name?: string;
  custom_branding?: Record<string, any>;
}

export interface ExportOptions {
  format: ExportFormat;
  filename: string;
  include_sections: string[];
  includeTableOfContents?: boolean;
  includePageNumbers?: boolean;
  includeWatermark?: boolean;
  compressionLevel?: string;
}

export interface ExportResponse {
  export_id: string;
  status: TaskStatus;
  format: ExportFormat;
  download_url?: string;
  file_size_bytes?: number;
  expires_at: string;
}

// Removed WebSocketMessage interface - now using direct HTTP polling

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  version: string;
  environment: string;
  azure_services: Record<string, boolean>;
}

// UI-specific types
export interface ResearchTask {
  id: string;
  prompt: string;
  status: TaskStatus;
  progress: number;
  currentStep: string;
  createdAt: Date;
  completedAt?: Date;
  report?: ResearchReport;
  modelConfig: ModelConfig;
  webSearchEnabled: boolean;
  researchDepth: ResearchDepth;
}

export interface ExportTask {
  id: string;
  taskId: string;
  format: ExportFormat;
  status: TaskStatus;
  downloadUrl?: string;
  fileSize?: number;
  createdAt: Date;
  expiresAt: Date;
}

export interface User {
  id: string;
  name: string;
  email: string;
  roles: string[];
}

export interface AppSettings {
  apiBaseUrl: string;
  wsBaseUrl: string;
  defaultModelConfig: ModelConfig;
  maxConcurrentTasks: number;
  autoSaveEnabled: boolean;
  theme: 'light' | 'dark' | 'system';
}

// API Error types
export interface ApiError {
  detail: string;
  status_code: number;
  timestamp: string;
}

// Form types
export interface ResearchFormData {
  prompt: string;
  thinkingModel: string;
  taskModel: string;
  executionMode: ExecutionMode;
  enableWebSearch: boolean;
  researchDepth: ResearchDepth;
  language: string;
  customInstructions?: string;
}

export interface ExportFormData {
  format: ExportFormat;
  includeSources: boolean;
  includeMetadata: boolean;
  templateName?: string;
}

// Component prop types
export interface ProgressStepData {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'current' | 'completed' | 'error';
  progress?: number;
}

export interface ModelOption {
  name: string;
  display_name: string;
  type: 'thinking' | 'task' | 'specialist' | 'embedding';
  max_tokens: number;
  supports_tools: boolean;
  cost_per_1k_tokens: number;
  description: string;
  supports_agents?: boolean; // Whether model supports Azure AI Agents Service
}

export interface TemplateOption {
  id: string;
  name: string;
  description: string;
  preview?: string;
  category: 'business' | 'academic' | 'technical' | 'custom';
}

// User Settings Types
export interface UserSettings {
  theme: 'light' | 'dark' | 'system';
  notifications: {
    email: boolean;
    push: boolean;
    taskCompletion: boolean;
    errors: boolean;
  };
  research: {
    defaultDepth: ResearchDepth;
    maxSources: number;
    autoExport: boolean;
    preferredFormat: ExportFormat;
    defaultThinkingModel?: string;
    defaultTaskModel?: string;
  };
  privacy: {
    dataRetention: number; // days
    shareAnalytics: boolean;
    publicReports: boolean;
  };
  ai: {
    model: string;
    temperature: number;
    maxTokens: number;
  };
  // Additional settings for the form
  defaultThinkingModel?: string;
  defaultTaskModel?: string;
  defaultResearchDepth?: ResearchDepth;
  executionMode?: ExecutionMode;
  defaultLanguage?: string;
  enableWebSearchByDefault?: boolean;
  enableNotifications?: boolean;
  autoExportFormat?: string;
  maxConcurrentTasks?: number;
  defaultInstructions?: string;
  themePreference?: string;
  enableTelemetry?: boolean;
}

// Phase-specific request types
export interface ResearchPlanRequest {
  topic: string;
  questions: string[];
  feedback: string;
  request: ResearchRequest;
}

export interface ExecuteResearchRequest {
  topic: string;
  plan: string;
  request: ResearchRequest;
}

export interface FinalReportRequest {
  topic: string;
  plan: string;
  findings: string;
  requirement?: string;
  request?: ResearchRequest;
}
