import { useState, useCallback } from 'react';
import { 
  useGenerateQuestions, 
  useCreateResearchPlan, 
  useExecuteResearch, 
  useExecuteResearchWithTavily,
  useGenerateFinalReport,
  useLocalSettings,
  useCreateSession
} from './useApi';
import { ResearchRequest } from '@/types';
import { extractQuestionsFromText } from '@/utils/jsonContentParser';

export interface DeepResearchState {
  // Current phase of research
  phase: 'topic' | 'questions' | 'feedback' | 'research' | 'report' | 'completed';
  
  // Session management
  sessionId: string | null;
  
  // Research data
  topic: string;
  questions: string;
  feedback: string;
  reportPlan: string;
  searchTasks: SearchTask[];
  finalReport: string;
  
  // Current task ID
  currentTaskId: string | null;
  
  // UI state
  isThinking: boolean;
  isResearching: boolean;
  isWriting: boolean;
  status: string;
}

export interface SearchTask {
  query: string;
  researchGoal: string;
  state: 'unprocessed' | 'processing' | 'completed' | 'failed';
  learning: string;
  sources?: Array<{ url: string; title?: string }>;
  images?: Array<{ url: string; description?: string }>;
}

const initialState: DeepResearchState = {
  phase: 'topic',
  sessionId: null,
  topic: '',
  questions: '',
  feedback: '',
  reportPlan: '',
  searchTasks: [],
  finalReport: '',
  currentTaskId: null,
  isThinking: false,
  isResearching: false,
  isWriting: false,
  status: '',
};

export const useDeepResearch = () => {
  const [state, setState] = useState<DeepResearchState>(initialState);
  const { data: settings } = useLocalSettings();
  
  // New phase-specific mutations
  const generateQuestionsMutation = useGenerateQuestions();
  const createResearchPlanMutation = useCreateResearchPlan();
  const executeResearchMutation = useExecuteResearch();
  const executeResearchWithTavilyMutation = useExecuteResearchWithTavily();
  const generateFinalReportMutation = useGenerateFinalReport();
  const createSessionMutation = useCreateSession();

  // Get default models from settings or fallback to defaults
  const getDefaultModels = useCallback(() => {
    return {
      thinking: settings?.defaultThinkingModel || 'chato1',
      task: settings?.defaultTaskModel || 'chat4omini'
    };
  }, [settings]);

  const updateState = useCallback((updates: Partial<DeepResearchState>) => {
    setState(prev => {
      const newState = { ...prev, ...updates };
      console.log('State transition:', { 
        from: { phase: prev.phase, status: prev.status }, 
        to: { phase: newState.phase, status: newState.status } 
      });
      return newState;
    });
  }, []);

  const createNewResearch = () => {
    setState(initialState);
  };

  // Automatically create session if one doesn't exist
  const ensureSession = async (topic: string) => {
    if (state.sessionId) {
      return state.sessionId; // Session already exists
    }

    try {
      const session = await createSessionMutation.mutateAsync({
        title: `Research: ${topic.length > 50 ? topic.substring(0, 50) + '...' : topic}`,
        description: `Automated research session for: ${topic}`,
        topic: topic,
        tags: ['auto-generated', 'research']
      });

      updateState({ sessionId: session.session_id });
      return session.session_id;
    } catch (error) {
      console.error('Failed to create session:', error);
      return null; // Continue without session
    }
  };

  // Phase 1: Ask Questions (Direct API Call)
  const askQuestions = async (topic: string) => {
    console.log('Starting question generation for topic:', topic);
    
    updateState({ 
      isThinking: true, 
      topic, 
      phase: 'questions',
      status: 'Generating clarifying questions...' 
    });

    try {
      // Ensure session exists before starting research
      const sessionId = await ensureSession(topic);
      
      const request: ResearchRequest = {
        prompt: `"${topic}"`,
        models_config: getDefaultModels(),
        execution_mode: settings?.executionMode || 'agents',
        research_depth: 'standard',
        enable_web_search: false,
        language: 'en',
        session_id: sessionId || undefined
      };

      console.log('Calling API to generate questions...');
      const response = await generateQuestionsMutation.mutateAsync(request);
      
      // Extract questions from response
      const questionsText = response.report?.sections?.map(s => s.content).join('\n\n') || 
                           response.report?.executive_summary || 
                           'Questions generated successfully';
      
      console.log('Questions generated, transitioning to feedback phase');
      
      updateState({ 
        questions: questionsText,
        phase: 'feedback',
        status: 'Questions generated successfully',
        isThinking: false
      });
      
    } catch (error) {
      console.error('Error generating questions:', error);
      updateState({ 
        status: 'Error generating questions',
        isThinking: false 
      });
    }
  };

  // Phase 2: Process Feedback and Generate Report Plan (Direct API Call)
  const writeReportPlan = useCallback(async (feedback: string) => {
    updateState({ 
      isThinking: true, 
      feedback,
      status: 'Creating research plan...' 
    });

    try {
      const request: ResearchRequest = {
        prompt: `Based on the research topic "${state.topic}" and the following feedback: "${feedback}", create a detailed research plan. Include: 1) Research objectives, 2) Key questions to explore, 3) Methodology approach, 4) Expected outcomes. Format as a structured plan.`,
        models_config: getDefaultModels(),
        execution_mode: settings?.executionMode || 'agents',
        research_depth: 'standard',
        enable_web_search: false,
        language: 'en',
        session_id: state.sessionId || undefined
      };

      // Extract questions as array from the questions text
      const questionsArray = extractQuestionsFromText(state.questions);
      
      const response = await createResearchPlanMutation.mutateAsync({
        topic: state.topic,
        questions: questionsArray,
        feedback: feedback,
        request: request
      });
      
      // Extract plan from response
      const reportPlan = response.report?.sections?.map(s => s.content).join('\n\n') || 
                        response.report?.executive_summary || 
                        'Research plan created successfully';
      
      updateState({ 
        reportPlan,
        phase: 'research',
        status: 'Research plan created successfully',
        isThinking: false
      });
      
    } catch (error) {
      console.error('Error creating report plan:', error);
      updateState({ 
        status: 'Error creating report plan',
        isThinking: false 
      });
    }
  }, [state.topic, state.questions, createResearchPlanMutation, updateState, getDefaultModels, settings?.executionMode, state.sessionId]);

  // Phase 3: Execute Search Tasks (Direct API Call)
  const runSearchTasks = useCallback(async () => {
    // Clear existing search tasks if resubmitting
    const isResubmission = state.searchTasks.length > 0;
    
    updateState({ 
      isResearching: true,
      searchTasks: [], // Clear existing tasks for fresh start
      status: isResubmission ? 'Resubmitting search tasks...' : 'Executing search tasks...' 
    });

    try {
      const request: ResearchRequest = {
        prompt: `Execute comprehensive research based on this plan: ${state.reportPlan}. Original topic: ${state.topic}. Conduct thorough research using web search and provide detailed findings with sources.`,
        models_config: getDefaultModels(),
        execution_mode: settings?.executionMode || 'agents',
        research_depth: 'deep',
        enable_web_search: true,
        language: 'en',
        session_id: state.sessionId || undefined
      };

      // Use the selected search method from user settings
      const searchMethod = settings?.searchMethod || 'bing';
      const mutation = searchMethod === 'tavily' ? executeResearchWithTavilyMutation : executeResearchMutation;
      
      updateState({ 
        status: `${isResubmission ? 'Resubmitting' : 'Executing'} search tasks using ${searchMethod === 'tavily' ? 'Tavily Search' : 'Bing Grounding'}...` 
      });

      const response = await mutation.mutateAsync({
        topic: state.topic,
        plan: state.reportPlan,
        request: request
      });
      
      // Convert response to search tasks
      const searchTasks: SearchTask[] = response.report?.sections?.map((section, index) => ({
        query: section.title,
        researchGoal: `Research task ${index + 1}`,
        state: 'completed' as const,
        learning: section.content,
        sources: response.report?.sources || [],
        images: []
      })) || [];
      
      updateState({ 
        searchTasks,
        phase: 'report',
        finalReport: '', // Clear existing final report when resubmitting research
        status: `Research tasks ${isResubmission ? 'resubmitted' : 'completed'} successfully using ${searchMethod === 'tavily' ? 'Tavily Search' : 'Bing Grounding'}`,
        isResearching: false
      });
      
    } catch (error) {
      console.error('Error executing search tasks:', error);
      updateState({ 
        status: 'Error executing search tasks',
        isResearching: false 
      });
    }
  }, [state.reportPlan, state.topic, state.searchTasks.length, executeResearchMutation, executeResearchWithTavilyMutation, updateState, getDefaultModels, settings?.executionMode, settings?.searchMethod, state.sessionId]);

  // Phase 4: Write Final Report (Direct API Call)
  const writeFinalReport = useCallback(async (requirement?: string) => {
    updateState({ 
      isWriting: true,
      status: 'Writing final report...' 
    });

    try {
      const learnings = state.searchTasks.map(task => task.learning).join('\n\n');
      
      const response = await generateFinalReportMutation.mutateAsync({
        topic: state.topic,
        plan: state.reportPlan,
        findings: learnings,
        requirement: requirement || '',
        request: {
          prompt: `Write a comprehensive final report based on:
            Topic: ${state.topic}
            Research Plan: ${state.reportPlan}
            Research Findings: ${learnings}
            ${requirement ? `Additional Requirements: ${requirement}` : ''}
            
            Create a well-structured, professional research report with clear headings, detailed analysis, and actionable insights.`,
          models_config: getDefaultModels(),
          execution_mode: settings?.executionMode || 'agents',
          research_depth: 'deep',
          enable_web_search: false,
          language: 'en',
          session_id: state.sessionId || undefined
        }
      });
      
      // Extract final report from response
      const finalReport = response.report?.sections?.map(section => 
        `# ${section.title}\n\n${section.content}`
      ).join('\n\n') || response.report?.executive_summary || 'Final report generated successfully';
      
      updateState({ 
        finalReport,
        phase: 'completed',
        status: 'Final report completed successfully',
        isWriting: false
      });
      
    } catch (error) {
      console.error('Error writing final report:', error);
      updateState({ 
        status: 'Error writing final report',
        isWriting: false 
      });
    }
  }, [state.topic, state.reportPlan, state.searchTasks, generateFinalReportMutation, updateState, getDefaultModels, settings?.executionMode, state.sessionId]);

  const setSessionId = (sessionId: string | null) => {
    updateState({ sessionId });
  };

  return {
    // State
    ...state,
    
    // Actions
    createNewResearch,
    askQuestions,
    writeReportPlan,
    runSearchTasks,
    writeFinalReport,
    updateState,
    setSessionId,
  };
};
