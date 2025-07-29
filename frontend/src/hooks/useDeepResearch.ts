import { useState, useCallback } from 'react';
import { 
  useGenerateQuestions, 
  useCreateResearchPlan, 
  useExecuteResearch, 
  useExecuteResearchWithTavily,
  useGenerateFinalReport,
  useLocalSettings 
} from './useApi';
import { ResearchRequest } from '@/types';
import { extractQuestionsFromText } from '@/utils/jsonContentParser';

export interface DeepResearchState {
  // Current phase of research
  phase: 'topic' | 'questions' | 'feedback' | 'research' | 'report';
  
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
  const [, forceRender] = useState(0); // Force re-render helper
  const { data: settings } = useLocalSettings();
  
  // New phase-specific mutations
  const generateQuestionsMutation = useGenerateQuestions();
  const createResearchPlanMutation = useCreateResearchPlan();
  const executeResearchMutation = useExecuteResearch();
  const executeResearchWithTavilyMutation = useExecuteResearchWithTavily();
  const generateFinalReportMutation = useGenerateFinalReport();

  // Get default models from settings or fallback to defaults
  const getDefaultModels = useCallback(() => {
    return {
      thinking: settings?.defaultThinkingModel || 'chato1',
      task: settings?.defaultTaskModel || 'chat4omini'
    };
  }, [settings]);

  const updateState = (updates: Partial<DeepResearchState>) => {
    console.log('updateState called with:', updates);
    setState(prev => {
      const newState = { ...prev, ...updates };
      console.log('State transition:', { 
        from: { phase: prev.phase, status: prev.status }, 
        to: { phase: newState.phase, status: newState.status } 
      });
      return newState;
    });
    // Force component re-render
    forceRender(prev => prev + 1);
  };

  const createNewResearch = () => {
    setState(initialState);
  };

  // Phase 1: Ask Questions (Direct API Call)
  const askQuestions = async (topic: string) => {
    console.log('=== ASK QUESTIONS STARTED ===');
    console.log('Topic:', topic);
    
    updateState({ 
      isThinking: true, 
      topic, 
      phase: 'questions',
      status: 'Generating clarifying questions...' 
    });
    console.log('State updated to questions phase with isThinking=true');

    try {
      const request: ResearchRequest = {
        prompt: `"${topic}"`,
        models_config: getDefaultModels(),
        execution_mode: settings?.executionMode || 'agents',
        research_depth: 'standard',
        enable_web_search: false,
        language: 'en'
      };

      console.log('About to call generateQuestionsMutation with request:', request);
      const response = await generateQuestionsMutation.mutateAsync(request);
      console.log('=== API RESPONSE RECEIVED ===');
      console.log('Full response:', response);
      console.log('Response report:', response.report);
      console.log('Response sections:', response.report?.sections);
      
      // Extract questions from response
      const questionsText = response.report?.sections?.map(s => s.content).join('\n\n') || 
                           response.report?.executive_summary || 
                           'Questions generated successfully';
      
      console.log('Extracted questions text:', questionsText);
      console.log('=== UPDATING STATE TO FEEDBACK PHASE ===');
      
      updateState({ 
        questions: questionsText,
        phase: 'feedback',
        status: 'Questions generated successfully',
        isThinking: false
      });
      
      console.log('State updated - should transition to feedback phase');
      
    } catch (error) {
      console.error('=== ERROR IN ASK QUESTIONS ===');
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
        language: 'en'
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
  }, [state.topic, createResearchPlanMutation, updateState, getDefaultModels, settings?.executionMode]);

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
        language: 'en'
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
  }, [state.reportPlan, state.topic, executeResearchMutation, executeResearchWithTavilyMutation, updateState, getDefaultModels, settings?.executionMode, settings?.searchMethod]);

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
          language: 'en'
        }
      });
      
      // Extract final report from response
      const finalReport = response.report?.sections?.map(section => 
        `# ${section.title}\n\n${section.content}`
      ).join('\n\n') || response.report?.executive_summary || 'Final report generated successfully';
      
      updateState({ 
        finalReport,
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
  }, [state.topic, state.reportPlan, state.searchTasks, generateFinalReportMutation, updateState, getDefaultModels, settings?.executionMode]);

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
  };
};
