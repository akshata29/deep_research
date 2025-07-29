import React, { createContext, useContext, ReactNode } from 'react';
import { useDeepResearch, DeepResearchState } from '@/hooks/useDeepResearch';

interface DeepResearchContextType extends DeepResearchState {
  createNewResearch: () => void;
  askQuestions: (topic: string) => Promise<void>;
  writeReportPlan: (feedback: string) => Promise<void>;
  runSearchTasks: () => Promise<void>;
  writeFinalReport: (requirement?: string) => Promise<void>;
  updateState: (updates: Partial<DeepResearchState>) => void;
  setSessionId: (sessionId: string | null) => void;
}

const DeepResearchContext = createContext<DeepResearchContextType | undefined>(undefined);

export const useDeepResearchContext = () => {
  const context = useContext(DeepResearchContext);
  if (!context) {
    throw new Error('useDeepResearchContext must be used within a DeepResearchProvider');
  }
  return context;
};

interface DeepResearchProviderProps {
  children: ReactNode;
}

export const DeepResearchProvider: React.FC<DeepResearchProviderProps> = ({ children }) => {
  const deepResearch = useDeepResearch();
  
  return (
    <DeepResearchContext.Provider value={deepResearch}>
      {children}
    </DeepResearchContext.Provider>
  );
};
